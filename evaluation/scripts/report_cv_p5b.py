"""P5B before/after report on SYNTHETIC degradations (no external images).

  python evaluation/scripts/report_cv_p5b.py [--out evaluation/results/p5b]

Writes report.md, report.json, cases.png. It records what the detector flagged, which correction steps were accepted or
rejected (and why), and what remained flagged. READ THIS FIRST: the thresholds were chosen while looking at images like
these, so "flag raised on its own degradation" is a sanity check, NOT a measured detection rate. Nothing here says how the
pipeline behaves on real SD-Turbo output. Controls at the bottom show false alarms and wrong corrections on purpose.
"""
import argparse
import json
import pathlib
import sys

import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from computer_vision import to_pil  # noqa: E402
from computer_vision.artifacts import correct_artifacts, intent_suppressions  # noqa: E402
from computer_vision.edge_aware import edge_preserving_sharpen  # noqa: E402

N = 384


def clean_scene() -> np.ndarray:
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    img = np.zeros((N, N, 3), np.float32)
    img[..., 0], img[..., 1], img[..., 2] = 120 + 0.25 * yy, 170 - 0.15 * yy, 220 - 0.3 * yy
    cv2.circle(img, (130, 150), 70, (230, 60, 50), -1)
    cv2.rectangle(img, (220, 190), (340, 320), (40, 160, 70), -1)
    cv2.line(img, (0, 330), (N, 300), (240, 240, 240), 6)
    return np.clip(img, 0, 255).astype(np.uint8)


def build_cases() -> list[dict]:
    s, rng = clean_scene(), np.random.default_rng(0)
    noise = lambda a, g: np.clip(a.astype(float) + rng.normal(0, g, a.shape), 0, 255).astype(np.uint8)
    blur = lambda a, g: cv2.GaussianBlur(a, (0, 0), g)
    dark = lambda a, f: np.clip(a.astype(np.float32) * f, 0, 255).astype(np.uint8)
    cast = lambda a, m: np.clip(a * np.array(m), 0, 255).astype(np.uint8)
    C = lambda name, img, prompt="", group="degradation": dict(name=name, image=img, prompt=prompt, group=group)
    return [
        C("clean scene", s, group="control"),
        C("blur sigma 1.5", blur(s, 1.5)), C("blur sigma 3", blur(s, 3)),
        C("noise sigma 8", noise(s, 8)), C("noise sigma 15", noise(s, 15)),
        C("dark x0.3", dark(s, 0.3)),
        C("low contrast", np.clip((s.astype(float) - 128) * 0.25 + 128, 0, 255).astype(np.uint8)),
        C("colour cast", cast(s, [0.7, 1, 1.3])),
        C("overexposed x1.8", np.clip(s.astype(float) * 1.8, 0, 255).astype(np.uint8)),
        C("oversharpened (halo)", edge_preserving_sharpen(s, amount=2.0, halo_guard=False, edge_threshold=0.05).image),
        C("blur 2 + noise 8", noise(blur(s, 2), 8)), C("dark + noise 6", noise(dark(s, 0.3), 6)),
        C("night scene, prompt says night", dark(s, 0.3), "a lighthouse at night", "control: intended look"),
        C("same dark image, prompt silent", dark(s, 0.3), "a lighthouse", "control: intended look"),
        C("blue underwater tint, prompt says underwater", cast(s, [0.55, 0.9, 1.35]), "a diver underwater", "control: intended look"),
        C("same tint, prompt silent", cast(s, [0.55, 0.9, 1.35]), "a diver", "control: intended look"),
        C("INTENDED fine grain (sigma 8)", noise(s, 8), "film grain photo", "control: detector cannot tell grain from noise"),
    ]


def metrics(q) -> dict:
    return {k: round(float(getattr(q, k)), 3) for k in ("noise_sigma", "blur_ratio", "brightness", "contrast",
                                                         "colour_cast", "clipped_bright", "halo_score")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "evaluation/results/p5b")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows, tiles = [], []
    for c in build_cases():
        sup = intent_suppressions(c["prompt"], [], []) if c["prompt"] else frozenset()
        r = correct_artifacts(c["image"], suppress=sup)
        rows.append(dict(case=c["name"], group=c["group"], prompt=c["prompt"], suppressed=sorted(r.before.suppressed),
                         flags_before=r.before.names, flags_after=r.after.names, changed=r.applied,
                         steps=[dict(name=s.name, flag=s.flag, accepted=s.accepted, reason=s.reason,
                                     before=round(s.target_before, 3), after=None if s.target_after is None else round(s.target_after, 3))
                                for s in r.steps],
                         notes=r.notes, metrics_before=metrics(r.before.quality), metrics_after=metrics(r.after.quality)))
        pair = np.concatenate([cv2.resize(c["image"], (192, 192), interpolation=cv2.INTER_AREA),
                               cv2.resize(r.image, (192, 192), interpolation=cv2.INTER_AREA)], axis=1)
        tiles.append(cv2.putText(pair.copy(), c["name"][:30], (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA))
    cols = 2
    pad = [np.zeros_like(tiles[0])] * (-len(tiles) % cols)
    grid = np.concatenate([np.concatenate((tiles + pad)[i:i + cols], axis=1) for i in range(0, len(tiles + pad), cols)], axis=0)
    to_pil(grid).save(a.out / "cases.png")
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    (a.out / "report.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    md = ["# P5B before/after report (SYNTHETIC images)\n",
          "> Thresholds were set while looking at images like these. A flag on its own degradation is a sanity check, not a detection rate. "
          "This says nothing about real SD-Turbo output. `cases.png` shows before (left) / after (right) per case.\n",
          "| case | flags before | steps (accepted ✔ / rejected ✘) | flags after | key measurement before → after |", "|---|---|---|---|---|"]
    for r in rows:
        steps = "; ".join(f"{'✔' if s['accepted'] else '✘'} {s['name']}" + ("" if s["accepted"] else f" ({s['reason'].replace('rejected: ', '')})") for s in r["steps"]) or "none"
        key = "; ".join(f"{k} {r['metrics_before'][k]} → {r['metrics_after'][k]}" for k in ("noise_sigma", "blur_ratio", "brightness", "colour_cast")
                        if r["metrics_before"][k] != r["metrics_after"][k]) or "unchanged"
        sup = f" (suppressed: {', '.join(r['suppressed'])})" if r["suppressed"] else ""
        md.append(f"| {r['case']} | {', '.join(r['flags_before']) or '-'}{sup} | {steps} | {', '.join(r['flags_after']) or '-'} | {key} |")
    (a.out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print((a.out / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
