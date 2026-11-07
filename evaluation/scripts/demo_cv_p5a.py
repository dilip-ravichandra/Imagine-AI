"""P5A before/after demo for resize -> enhance -> edge-aware smoothing -> sharpen.

  python evaluation/scripts/demo_cv_p5a.py                       # synthetic degraded scene (no external images)
  python evaluation/scripts/demo_cv_p5a.py --input my_image.png  # YOUR OWN generated image (do not use copyrighted images)

Writes before.png, after.png, strip.png and metrics.json to --out (default evaluation/results/p5a).
metrics.json holds MEASUREMENTS ONLY (no verdict). On the synthetic scene it only demonstrates behaviour:
it is NOT evidence that the pipeline improves real SD-Turbo output. That needs real generations + review.
"""
import argparse
import json
import pathlib
import sys
import time

import cv2
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from computer_vision import to_array, to_pil  # noqa: E402
from computer_vision.edge_aware import bilateral_smooth, edge_density, edge_preserving_sharpen  # noqa: E402
from computer_vision.enhancement import auto_enhance, luminance  # noqa: E402
from computer_vision.resize import fit_to_resolution  # noqa: E402


def synthetic_degraded(seed: int = 0) -> np.ndarray:
    """Procedural 384x384 scene, then deliberately degraded: dark, blue cast, soft focus, noise."""
    n = 384
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    img = np.zeros((n, n, 3), np.float32)
    img[..., 0], img[..., 1], img[..., 2] = 120 + 0.25 * yy, 170 - 0.15 * yy, 220 - 0.3 * yy  # sky -> ground
    cv2.circle(img, (130, 150), 70, (230, 60, 50), -1)
    cv2.rectangle(img, (220, 190), (340, 320), (40, 160, 70), -1)
    cv2.line(img, (0, 330), (n, 300), (240, 240, 240), 6)
    rng = np.random.default_rng(seed)
    img = img * 0.55 * np.array([0.8, 0.95, 1.2], np.float32)  # dark + blue cast
    img = cv2.GaussianBlur(img, (0, 0), 1.6) + rng.normal(0, 5, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def measure(img: np.ndarray) -> dict:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    luma = luminance(img)
    return dict(mean_luma=round(float(luma.mean()), 4), std_luma=round(float(luma.std()), 4),
                laplacian_variance=round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2),
                edge_density=round(edge_density(img), 4),
                channel_means_rgb=[round(float(m), 1) for m in img.reshape(-1, 3).mean(0)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "evaluation/results/p5a")
    ap.add_argument("--resolution", type=int, default=512)
    a = ap.parse_args()
    synthetic = a.input is None
    src = synthetic_degraded() if synthetic else to_array(Image.open(a.input))
    stages = [("resize", lambda x: fit_to_resolution(x, a.resolution, mode="pad")),
              ("auto_enhance", auto_enhance),
              ("bilateral", lambda x: bilateral_smooth(x, strength=0.5)),
              ("sharpen", lambda x: edge_preserving_sharpen(x, amount=0.6))]
    report, cur = [], src
    report_before = measure(src)
    for name, fn in stages:
        t0 = time.perf_counter()
        r = fn(cur)
        ms = (time.perf_counter() - t0) * 1000
        report.append(dict(stage=name, applied=r.applied, ms=round(ms, 2), params=r.params, notes=r.notes,
                           measured_after=measure(r.image)))
        cur = r.image
    a.out.mkdir(parents=True, exist_ok=True)
    before = fit_to_resolution(src, a.resolution, mode="pad").image
    to_pil(before).save(a.out / "before.png")
    to_pil(cur).save(a.out / "after.png")
    strip = np.concatenate([before, np.full((before.shape[0], 8, 3), 255, np.uint8), cur], axis=1)
    to_pil(strip).save(a.out / "strip.png")
    (a.out / "metrics.json").write_text(json.dumps(dict(
        source="synthetic degraded scene" if synthetic else "user-supplied image",
        note=("Synthetic image with deliberate degradation: shows behaviour only, NOT evidence of improvement on real "
              "model output." if synthetic else "Measurements only; judge quality by looking at before/after."),
        measured_input=report_before, stages=report), indent=2, default=str))
    print(f"wrote {a.out}/before.png after.png strip.png metrics.json")
    for s in report:
        print(f"  {s['stage']:<13} applied={s['applied']!s:<5} {s['ms']:>7.2f} ms")


if __name__ == "__main__":
    main()
