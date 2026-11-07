"""No-reference image quality MEASUREMENTS (numbers only; judging them is artifacts/detect.py).

Input: uint8 RGB (H,W,3). Every metric is a heuristic about the pixels. None of them measures whether the
image matches the prompt or looks good to a person, and none is calibrated on real SD-Turbo output.
"""
from dataclasses import asdict, dataclass

import cv2
import numpy as np

from ..common import validate_image

_NOISE_KERNEL = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)  # Immerkaer: edge/gradient-free response
_NOISE_NORM = 6.0  # sqrt(sum(kernel^2)) = 6: response of white noise sigma has std 6*sigma
_BLUR_SIGMA = 1.5
HALO_BORDER = 9


@dataclass(frozen=True)
class QualityReport:
    sharpness: float  # variance of the Laplacian of the grey image (0..255 scale). Unbounded; depends on content AND resolution
    blur_ratio: float  # Laplacian variance after an extra Gaussian blur / before. ~1 = already soft, small = had fine detail
    brightness: float  # mean luma, 0..1
    contrast: float  # luma standard deviation, 0..1
    saturation: float  # mean HSV saturation, 0..1
    noise_sigma: float  # estimated Gaussian noise std on the 0..255 scale (robust Immerkaer/MAD estimate)
    clipped_dark: float  # fraction of pixels with luma <= 2
    clipped_bright: float  # fraction of pixels with luma >= 253
    colour_cast: float  # max over channels of |channel mean / overall mean - 1| (gray-world deviation)
    edge_density: float  # fraction of Canny edge pixels
    gradient_p99: float  # 99th percentile of luma gradient magnitude (levels/px) on a denoised copy: 'is there any structure at all'

    halo_score: float  # share of evaluated hard edges with overshoot (ringing); 0 when too few edges to judge
    halo_edges: int  # number of edges that were evaluated for halo_score

    def to_dict(self) -> dict:
        return asdict(self)


def _luma255(img: np.ndarray) -> np.ndarray:
    f = img.astype(np.float32)
    return 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]


def estimate_noise_sigma(image: np.ndarray) -> float:
    """Robust per-channel noise std estimate (0..255 scale): median absolute deviation of the Immerkaer high-pass response.
    The median ignores the sparse edge/texture responses, but dense fine texture still inflates it
    (a heavily textured image can read as 'noisy')."""
    img = validate_image(image)
    if min(img.shape[:2]) < 3:
        return 0.0
    sig = []
    for c in range(3):  # per channel: luma would shrink independent channel noise by ~0.67
        resp = cv2.filter2D(img[..., c].astype(np.float32), cv2.CV_32F, _NOISE_KERNEL,
                            borderType=cv2.BORDER_REFLECT)[1:-1, 1:-1]
        sig.append(np.median(np.abs(resp - np.median(resp))) / 0.6745 / _NOISE_NORM)
    return float(np.mean(sig))


def blur_metrics(image: np.ndarray) -> tuple[float, float]:
    """(sharpness, blur_ratio). sharpness = raw Laplacian variance (noise INFLATES it).
    blur_ratio uses the re-blur idea (Crete et al.): blurring an already-soft image changes little. It is measured on
    a denoised copy (median 5x5, then Gaussian sigma 1) so that noise does not hide blur (noise raises Laplacian
    variance and would fake 'sharp'). On synthetic cases this separated sharp (<=0.26) from soft (>=0.40) images even
    with noise up to sigma 15; that margin is small and was NOT checked on real model output."""
    gray = _luma255(validate_image(image))
    v0 = float(cv2.Laplacian(gray, cv2.CV_32F).var())
    base = cv2.GaussianBlur(cv2.medianBlur(np.clip(gray, 0, 255).astype(np.uint8), 5).astype(np.float32), (0, 0), 1.0)
    b0 = float(cv2.Laplacian(base, cv2.CV_32F).var())
    if b0 < 1e-6:
        return v0, 1.0
    b1 = float(cv2.Laplacian(cv2.GaussianBlur(base, (0, 0), _BLUR_SIGMA), cv2.CV_32F).var())
    return v0, min(1.0, b1 / b0)


def gradient_p99(image: np.ndarray) -> float:
    """Structure indicator that survives blur: ~0 for flat or smoothly shaded images and noise, tens for scenes with edges.
    (Synthetic scene: 27.9 sharp, 10.6 at blur sigma 3, 5.2 at sigma 5; smooth sky 0.3; flat+noise 1.4.)"""
    g = _luma255(validate_image(image))
    base = cv2.GaussianBlur(cv2.medianBlur(np.clip(g, 0, 255).astype(np.uint8), 5).astype(np.float32), (0, 0), 1.0)
    mag = np.hypot(cv2.Sobel(base, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(base, cv2.CV_32F, 0, 1, ksize=3)) / 8.0
    return float(np.percentile(mag, 99))


def halo_score(image: np.ndarray, min_contrast: float = 40.0, overshoot_frac: float = 0.08,
               plateau_tol: float = 0.10, min_edges: int = 20) -> tuple[float, int]:
    """Ringing detector for HARD, roughly straight edges (axis-aligned sampling only).
    For each strong edge pixel the luma profile is sampled across the edge. If both sides have a flat plateau
    (offsets +-6..+-8, spread <= plateau_tol * contrast) a halo is an excursion at offsets 2..4 beyond that plateau by more than
    max(overshoot_frac * edge contrast, 2.5 * noise sigma). Returns (share of evaluated edges that ring, edges evaluated).
    Returns (0.0, n) when fewer than min_edges qualify: not enough evidence to claim anything.
    Thin lines/ridges, soft, textured and diagonal edges fail the plateau test and are skipped, not judged."""
    L = _luma255(validate_image(image))
    h, w = L.shape
    b = HALO_BORDER
    if h <= 2 * b + 1 or w <= 2 * b + 1:
        return 0.0, 0
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    sigma = estimate_noise_sigma(image)
    strong = 4.0 * min_contrast * 0.6  # Sobel response of a step of height c is ~4c
    ax, ay = np.abs(gx), np.abs(gy)
    horiz = (ax >= ay) & (ax >= strong)  # gradient along x -> vertical edge -> sample along x
    vert = (ay > ax) & (ay >= strong)
    # non-maximum suppression along the sampling axis (ties keep both pixels of a hard step)
    horiz &= (ax >= np.roll(ax, 1, 1)) & (ax >= np.roll(ax, -1, 1))
    vert &= (ay >= np.roll(ay, 1, 0)) & (ay >= np.roll(ay, -1, 0))
    mask = np.zeros_like(horiz)
    mask[b:-b, b:-b] = True
    evaluated = rings = 0
    for sel, g, axis in ((horiz & mask, gx, 1), (vert & mask, gy, 0)):
        ys, xs = np.nonzero(sel)
        if ys.size == 0:
            continue
        s = np.sign(g[ys, xs]).astype(np.int64)  # sample toward the brighter side
        def P(k):
            return L[ys, xs + k * s] if axis == 1 else L[ys + k * s, xs]
        hi_s = np.stack([P(6), P(7), P(8)])
        lo_s = np.stack([P(-6), P(-7), P(-8)])
        hi_plat, lo_plat = hi_s.mean(0), lo_s.mean(0)
        c = hi_plat - lo_plat
        ok = ((c >= min_contrast) & (np.ptp(hi_s, axis=0) <= plateau_tol * c)
              & (np.ptp(lo_s, axis=0) <= plateau_tol * c))
        if not ok.any():
            continue
        hi_max = np.maximum.reduce([P(2), P(3), P(4)])
        lo_min = np.minimum.reduce([P(-2), P(-3), P(-4)])
        over = np.maximum(hi_max - hi_plat, lo_plat - lo_min)
        thresh = np.maximum(overshoot_frac * c, 2.5 * sigma)
        evaluated += int(ok.sum())
        rings += int((ok & (over > thresh)).sum())
    if evaluated < min_edges:
        return 0.0, evaluated
    return rings / evaluated, evaluated


def assess_quality(image: np.ndarray) -> QualityReport:
    img = validate_image(image)
    luma = _luma255(img)
    sharp, ratio = blur_metrics(img)
    gray8 = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    means = img.reshape(-1, 3).astype(np.float64).mean(axis=0)
    overall = float(means.mean())
    cast = float(np.max(np.abs(means / overall - 1.0))) if overall > 1.0 else 0.0
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    med = float(np.median(gray8))
    edges = cv2.Canny(gray8, max(10.0, 0.66 * med), max(30.0, 1.33 * med))
    hs, hn = halo_score(img)
    return QualityReport(
        sharpness=sharp, blur_ratio=ratio, brightness=float(luma.mean() / 255.0),
        contrast=float(luma.std() / 255.0), saturation=float(hsv[..., 1].mean() / 255.0),
        noise_sigma=estimate_noise_sigma(img), clipped_dark=float((luma <= 2).mean()),
        clipped_bright=float((luma >= 253).mean()), colour_cast=cast,
        edge_density=float(np.count_nonzero(edges)) / edges.size, gradient_p99=gradient_p99(img),
        halo_score=hs, halo_edges=hn)
