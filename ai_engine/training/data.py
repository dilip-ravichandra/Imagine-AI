"""P3A adaptation data: select COCO caption/image pairs with leakage guards and provenance.

Pure Python + Pillow. No torch, no network. Importing this never touches a GPU.

What this module guarantees (all covered by tests):
  * No image, file name or caption that appears in an evaluation prompt file is ever selected.
  * Train and validation never share an image id or identical image bytes.
  * The same inputs and seed always give the same selection.
  * Every selected row carries its source ids and licence so the dataset can be audited.

What it does NOT guarantee: near-duplicate images are not detected, and SD-Turbo's own (undisclosed)
pretraining data may already contain COCO images. See docs/ADAPTATION.md.
"""
import hashlib
import json
import random
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from ai_engine.prompt import PARSER_VERSION, SCHEMA_VERSION, analyze_prompt

MANIFEST_SCHEMA = "p3a-dataset-1"
MIN_WORDS, MAX_WORDS = 4, 50
LEVEL_RANK = {"simple": 0, "moderate": 1, "complex": 2}
RICH_LEVELS = ("moderate", "complex")


class DataError(ValueError):
    """Raised for any input that would make the adaptation set unsafe or unauditable."""


# ---------------------------------------------------------------- captions
def clean_caption(text) -> Optional[str]:
    """Whitespace-normalised caption, or None if unusable (non-string, too short/long, non-ASCII)."""
    if not isinstance(text, str):
        return None
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()
    n = len(t.split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        return None
    if re.search(r"[^\x20-\x7E]", t):
        return None
    return t


def norm_caption(text: str) -> str:
    """Key used to compare captions for leakage: lower-case, letters/digits/spaces only."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def _stable(seed: int, *parts) -> int:
    """Deterministic integer from a seed and parts (Python's hash() is salted per process; this is not)."""
    return int(hashlib.sha256("|".join(map(str, (seed, *parts))).encode()).hexdigest()[:12], 16)


def caption_level(caption: str) -> Optional[str]:
    """Prompt-structure level from the P2 rule parser (simple/moderate/complex), None if invalid.

    Used ONLY to stratify the training mix. The parser scored 12/20 on unseen prompts, so this is a
    rough heuristic, never a claim about what the image contains.
    """
    a = analyze_prompt(caption)
    return a.complexity.level if a.validation.valid else None


# ---------------------------------------------------------------- exclusions
@dataclass
class Exclusions:
    image_ids: dict  # dataset name -> set of str ids
    file_names: set
    captions: set  # norm_caption() keys
    sources: list  # evaluation files that were read

    def hits(self, dataset: str, image_id, file_name: str, caption: str) -> Optional[str]:
        if str(image_id) in self.image_ids.get(dataset, set()):
            return "image_id"
        if file_name in self.file_names:
            return "file_name"
        if norm_caption(caption) in self.captions:
            return "caption"
        return None


def load_exclusions(paths: Iterable) -> Exclusions:
    """Collect every image id, file name and caption from evaluation prompt files (all splits)."""
    ids, files, caps, used = {}, set(), set(), []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            raise DataError(f"Evaluation prompt file not found: {p}")
        rows = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not rows:
            raise DataError(f"Evaluation prompt file is empty or not a list: {p}")
        for r in rows:
            if "source_image_id" in r:
                ids.setdefault(r.get("dataset", "COCO"), set()).add(str(r["source_image_id"]))
            if r.get("source_filename"):
                files.add(r["source_filename"])
            if r.get("prompt"):
                caps.add(norm_caption(r["prompt"]))
        used.append(str(p))
    if not used:
        raise DataError("At least one evaluation prompt file is required for the leakage guard")
    return Exclusions(ids, files, caps, used)


# ---------------------------------------------------------------- COCO annotations
def load_coco(path) -> tuple:
    """Read an official COCO captions JSON. Returns (images_by_id, captions_by_image, licences, sha256)."""
    path = Path(path)
    if not path.is_file():
        raise DataError(f"COCO annotation file not found: {path}")
    raw = path.read_bytes()
    data = json.loads(raw)
    for key in ("images", "annotations"):
        if key not in data:
            raise DataError(f"Not a COCO captions file: missing '{key}'")
    licences = {int(x["id"]): x.get("name", "unknown") for x in data.get("licenses", [])}
    images = {int(x["id"]): x for x in data["images"]}
    caps = {}
    for a in data["annotations"]:
        caps.setdefault(int(a["image_id"]), []).append((int(a["id"]), a["caption"]))
    return images, caps, licences, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------- selection
def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def default_image_check(path: Path, min_side: int) -> Optional[str]:
    """None if the image decodes and is large enough, otherwise a short reject reason."""
    from PIL import Image
    try:
        with Image.open(path) as im:
            im.load()
            if min(im.size) < min_side:
                return "too_small"
    except Exception:  # noqa: BLE001 - any decode failure means "do not train on it"
        return "unreadable"
    return None


def select_pairs(images, captions, licences, images_dir, exclusions: Exclusions, *, n_total: int, seed: int,
                 complex_fraction: float = 0.5, min_side: int = 384, license_ids: Optional[set] = None,
                 dataset: str = "COCO", image_check: Callable = default_image_check) -> tuple:
    """Pick up to n_total (image, caption) pairs. Returns (rows, stats).

    Strata: images that own a moderate/complex caption ("rich") vs the rest ("plain"). `complex_fraction`
    of the set is drawn from rich images using their richest caption; the remainder from plain images
    so the adapter still sees simple prompts. If a stratum runs short the other fills in (recorded).
    """
    if not 0 <= complex_fraction <= 1:
        raise DataError("complex_fraction must be between 0 and 1")
    if n_total < 2:
        raise DataError("n_total must be at least 2")
    images_dir = Path(images_dir)
    rejects = {}

    def reject(reason):
        rejects[reason] = rejects.get(reason, 0) + 1

    pool = {"rich": [], "plain": []}
    for image_id in sorted(images):
        meta = images[image_id]
        fname = meta["file_name"]
        if license_ids is not None and meta.get("license") not in license_ids:
            reject("licence_not_allowed")
            continue
        scored = []
        for cid, text in captions.get(image_id, []):
            cap = clean_caption(text)
            if cap is None:
                continue
            hit = exclusions.hits(dataset, image_id, fname, cap)
            if hit:
                reject("excluded_" + hit)
                scored = None
                break  # one hit on an image excludes the whole image, all its captions
            lvl = caption_level(cap)
            if lvl is not None:
                scored.append((LEVEL_RANK[lvl], cid, cap, lvl))
        if not scored:
            if scored is not None:
                reject("no_usable_caption")
            continue
        best = max(r for r, *_ in scored)
        if best >= LEVEL_RANK["moderate"]:
            top = sorted((s for s in scored if s[0] == best), key=lambda s: _stable(seed, "cap", s[1]))
            pool["rich"].append((image_id, top[0]))
        else:
            pick = sorted(scored, key=lambda s: _stable(seed, "cap", s[1]))[0]
            pool["plain"].append((image_id, pick))
    for k in pool:
        pool[k].sort(key=lambda x: _stable(seed, "img", x[0]))

    want_rich = round(n_total * complex_fraction)
    rows, seen_hash, taken, failed = [], set(), set(), set()

    def take(stratum, quota):
        got = 0
        for image_id, (_, cid, cap, lvl) in pool[stratum]:
            if got >= quota:
                break
            if image_id in taken or image_id in failed:
                continue  # already used, or already rejected (and counted) in an earlier pass
            meta = images[image_id]
            path = images_dir / meta["file_name"]
            why = "image_file_missing" if not path.is_file() else image_check(path, min_side)
            digest = None if why else _sha256_file(path)
            if not why and digest in seen_hash:
                why = "duplicate_image_bytes"
            if why:
                failed.add(image_id)
                reject(why)
                continue
            seen_hash.add(digest)
            taken.add(image_id)
            rows.append(dict(image_id=image_id, file_name=meta["file_name"], path=str(path.resolve()), sha256=digest,
                             caption=cap, caption_id=cid, level=lvl, stratum=stratum,
                             license=licences.get(meta.get("license"), "unknown"),
                             width=meta.get("width"), height=meta.get("height")))
            got += 1

    take("rich", want_rich)
    take("plain", n_total - want_rich)
    for stratum in ("rich", "plain"):  # a short stratum is topped up from the other one
        if len(rows) < n_total:
            take(stratum, n_total - len(rows))
    stats = dict(requested=n_total, selected=len(rows), rich_selected=sum(r["stratum"] == "rich" for r in rows),
                 plain_selected=sum(r["stratum"] == "plain" for r in rows),
                 shortfall=max(0, n_total - len(rows)), rejects=dict(sorted(rejects.items())),
                 candidates_rich=len(pool["rich"]), candidates_plain=len(pool["plain"]))
    return rows, stats


def split_rows(rows: list, n_val: int, seed: int) -> tuple:
    """Deterministic split by image. Train and validation share no image id or image bytes."""
    if not 0 < n_val < len(rows):
        raise DataError("Validation size must be between 1 and the number of rows minus 1")
    order = sorted(rows, key=lambda r: _stable(seed, "split", r["image_id"]))
    val, train = order[:n_val], order[n_val:]
    if {r["image_id"] for r in val} & {r["image_id"] for r in train} or \
       {r["sha256"] for r in val} & {r["sha256"] for r in train}:
        raise DataError("Split leaked an image across train and validation")
    return train, val


def assert_no_leakage(rows: Iterable, exclusions: Exclusions, dataset: str = "COCO") -> None:
    """Independent re-check used at build time AND again by the training launcher."""
    for r in rows:
        hit = exclusions.hits(dataset, r["image_id"], r["file_name"], r["caption"])
        if hit:
            raise DataError(f"Evaluation leakage: {r['file_name']} matches an evaluation {hit}")


# ---------------------------------------------------------------- output
def write_imagefolder(out, train: list, val: list, manifest: dict) -> None:
    """Write train/ and validation/ (images + metadata.jsonl, the format diffusers' trainer reads) + manifest."""
    out = Path(out)
    if out.exists():
        raise DataError(f"Output directory already exists, choose a new one: {out}")
    out.mkdir(parents=True)
    for name, items in (("train", train), ("validation", val)):
        folder = out / name
        folder.mkdir()
        lines = []
        for i, r in enumerate(items):
            suffix = Path(r["file_name"]).suffix.lower() or ".jpg"
            target = f"{i:06d}{suffix}"
            shutil.copyfile(r["path"], folder / target)
            r["file"] = target
            lines.append(json.dumps({"file_name": target, "text": r["caption"]}))
        (folder / "metadata.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest["train"] = [_public(r) for r in train]
    manifest["validation"] = [_public(r) for r in val]
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _public(r: dict) -> dict:
    return {k: v for k, v in r.items() if k != "path"}  # never write local absolute paths into the manifest


def build_manifest(*, params: dict, annotations_path, annotations_sha: str, exclusions: Exclusions,
                   stats: dict, train: list, val: list) -> dict:
    lic = {}
    for r in train + val:
        lic[r["license"]] = lic.get(r["license"], 0) + 1
    return {
        "schema": MANIFEST_SCHEMA,
        "dataset": "COCO 2014 captions (official annotation file)",
        "params": params,
        "source": {"annotations_file": Path(annotations_path).name, "annotations_sha256": annotations_sha},
        "parser": {"version": PARSER_VERSION, "schema": SCHEMA_VERSION,
                   "use": "stratifying the training mix only; parser scored 12/20 on unseen prompts"},
        "leakage_guard": {"evaluation_files": [Path(s).name for s in exclusions.sources],
                          "image_ids_checked": sum(len(v) for v in exclusions.image_ids.values()),
                          "captions_checked": len(exclusions.captions),
                          "rule": "an image is excluded entirely if its id, file name or any caption matches"},
        "counts": {"train": len(train), "validation": len(val), **stats},
        "licences": dict(sorted(lic.items())),
        "limitations": [
            "Near-duplicate images are not detected; only identical bytes and ids.",
            "SD-Turbo's pretraining data is not public and may overlap COCO.",
            "Stratification uses a rule parser (12/20 on unseen prompts); the mix is approximate.",
            "Captions describe the image; they are human-written and can be wrong or biased.",
            "Check each licence listed above before redistributing images or an adapter trained on them.",
        ],
    }
