"""Small, dependency-light statistics and pixel-fidelity helpers for P4 (Pillow + stdlib only)."""
import math
import statistics
from typing import Iterable, Optional


def summarize(values: Iterable[float]) -> Optional[dict]:
    """n, mean, median, sample stdev (None if n<2), min, max, p95 (nearest-rank). None for no data."""
    v = sorted(float(x) for x in values if x is not None)
    if not v:
        return None
    p95 = v[max(0, math.ceil(0.95 * len(v)) - 1)]
    return {"n": len(v), "mean": statistics.fmean(v), "median": statistics.median(v),
            "stdev": statistics.stdev(v) if len(v) > 1 else None, "min": v[0], "max": v[-1], "p95": p95}


def pixel_fidelity(a, b) -> dict:
    """MSE / PSNR between two PIL images of equal size. Measures DEVIATION from a reference image,
    not perceptual quality. psnr_db is None when the images are identical (PSNR would be infinite)."""
    from PIL import ImageChops
    a, b = a.convert("RGB"), b.convert("RGB")
    if a.size != b.size:
        raise ValueError(f"size mismatch {a.size} vs {b.size}")
    hist = ImageChops.difference(a, b).histogram()  # 3 x 256 bins (R, G, B)
    n = a.size[0] * a.size[1] * 3
    mse = sum(count * (i % 256) ** 2 for i, count in enumerate(hist)) / n
    return {"mse": mse, "psnr_db": None if mse == 0 else 10 * math.log10(255 ** 2 / mse), "identical": mse == 0}
