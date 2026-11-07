"""Build the P3A adaptation set from locally downloaded COCO files.

    python -m ai_engine.training.build_dataset ^
        --coco-annotations D:\\coco\\annotations\\captions_train2014.json ^
        --coco-images D:\\coco\\train2014 --out training_data\\p3a_small --preset small

You must download COCO yourself (https://cocodataset.org/#download) and accept its terms.
Nothing here uses the network.
"""
import argparse
import sys
from pathlib import Path

from .data import (DataError, assert_no_leakage, build_manifest, load_coco, load_exclusions, select_pairs,
                   split_rows, write_imagefolder)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_EVAL = REPO / "evaluation" / "prompts" / "dataset_prompts.json"
# smoke = prove the whole pipeline in minutes. small = first real (still tiny) adaptation. Both are UNTUNED guesses.
PRESETS = {"smoke": dict(n_train=48, n_val=8), "small": dict(n_train=600, n_val=60)}


def build(args) -> dict:
    preset = PRESETS[args.preset] if args.preset else {}
    n_train = args.n_train if args.n_train is not None else preset.get("n_train")
    n_val = args.n_val if args.n_val is not None else preset.get("n_val")
    if n_train is None or n_val is None or n_train < 1 or n_val < 1:
        raise DataError("Give --preset or both --n-train and --n-val (each at least 1)")
    exclusions = load_exclusions(args.eval_prompts or [DEFAULT_EVAL])
    images, captions, licences, sha = load_coco(args.coco_annotations)
    allowed = {int(x) for x in args.license_ids.split(",")} if args.license_ids else None
    rows, stats = select_pairs(images, captions, licences, args.coco_images, exclusions,
                               n_total=n_train + n_val, seed=args.seed, complex_fraction=args.complex_fraction,
                               min_side=args.min_side, license_ids=allowed)
    if stats["shortfall"]:
        raise DataError(f"Only {stats['selected']} usable pairs found for {n_train + n_val} requested "
                        f"(rejects: {stats['rejects']}). Check --coco-images points at the matching image folder.")
    train, val = split_rows(rows, n_val, args.seed)
    assert_no_leakage(train + val, exclusions)  # independent re-check before anything is written
    params = dict(n_train=n_train, n_val=n_val, seed=args.seed, complex_fraction=args.complex_fraction,
                  min_side=args.min_side, license_ids=sorted(allowed) if allowed else "all", preset=args.preset)
    manifest = build_manifest(params=params, annotations_path=args.coco_annotations, annotations_sha=sha,
                              exclusions=exclusions, stats=stats, train=train, val=val)
    write_imagefolder(args.out, train, val, manifest)
    return manifest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--coco-annotations", required=True, help="captions_train2014.json (official)")
    p.add_argument("--coco-images", required=True, help="folder containing the matching COCO_train2014_*.jpg files")
    p.add_argument("--out", required=True, help="NEW directory (never overwritten)")
    p.add_argument("--preset", choices=sorted(PRESETS))
    p.add_argument("--n-train", type=int)
    p.add_argument("--n-val", type=int)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--complex-fraction", type=float, default=0.5,
                   help="share of the set drawn from images with a moderate/complex caption (default 0.5)")
    p.add_argument("--min-side", type=int, default=384)
    p.add_argument("--license-ids", help="comma list of COCO licence ids to allow, e.g. 4,5,7,8 (default: all)")
    p.add_argument("--eval-prompts", nargs="+", help="evaluation prompt files to exclude (default: bundled file)")
    a = p.parse_args(argv)
    try:
        m = build(a)
    except DataError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    c = m["counts"]
    print(f"Wrote {a.out}: train={c['train']} validation={c['validation']} "
          f"(rich={c['rich_selected']}, plain={c['plain_selected']}) licences={m['licences']}")
    print("Rejected:", c["rejects"] or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
