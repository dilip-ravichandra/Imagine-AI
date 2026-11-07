"""Edge analysis and edge-aware filtering. Input uint8 RGB (H,W,3); filters return CVResult."""
from typing import Optional

import cv2
import numpy as np

from ..common import CVResult, noop, validate_image


def _gray(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(validate_image(image), cv2.COLOR_RGB2GRAY)


def edge_map(image: np.ndarray, method: str = "canny", low: Optional[float] = None,
             high: Optional[float] = None, blur_ksize: int = 3) -> np.ndarray:
    """Analysis only (does not change the image). Returns uint8 (H,W).
    'canny': binary 0/255. If low/high are None they come from the grey median (0.66x / 1.33x, floors 10 / 30),
    a common heuristic that is NOT tuned for generated images.
    'sobel': gradient magnitude scaled to 0..255 by the image's own maximum (all-zero if there is no gradient)."""
    gray = _gray(image)
    if blur_ksize not in (0, 1) and (blur_ksize < 0 or blur_ksize % 2 == 0):
        raise ValueError("blur_ksize must be 0/1 (off) or a positive odd number")
    if blur_ksize > 1:
        gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    if method == "canny":
        med = float(np.median(gray))
        lo = low if low is not None else max(10.0, 0.66 * med)
        hi = high if high is not None else max(30.0, 1.33 * med)
        if lo >= hi:
            raise ValueError("canny low must be < high")
        return cv2.Canny(gray, lo, hi)
    if method == "sobel":
        g = gray.astype(np.float32)
        mag = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
        mx = float(mag.max())
        return np.zeros(gray.shape, np.uint8) if mx <= 0 else np.clip(mag / mx * 255.0, 0, 255).astype(np.uint8)
    raise ValueError("method must be 'canny' or 'sobel'")


def edge_density(image: np.ndarray, **canny_kwargs) -> float:
    """Fraction of pixels marked as Canny edges (0..1). A rough 'how much structure' indicator, not a quality score."""
    return float(np.count_nonzero(edge_map(image, "canny", **canny_kwargs))) / float(image.shape[0] * image.shape[1])


def _blend(img: np.ndarray, filtered: np.ndarray, strength: float) -> np.ndarray:
    if strength >= 1.0:
        return filtered
    return np.clip(np.rint(img.astype(np.float32) * (1 - strength) + filtered.astype(np.float32) * strength),
                   0, 255).astype(np.uint8)


def bilateral_smooth(image: np.ndarray, d: int = 7, sigma_color: float = 30.0, sigma_space: float = 5.0,
                     strength: float = 1.0, enabled: bool = True) -> CVResult:
    """Edge-preserving smoothing (OpenCV bilateral filter). Pixels are averaged only with neighbours that are
    spatially close AND similar in colour (sigma_color, 0-255 scale), so strong edges survive while small
    fluctuations (noise, fine grain) are flattened. Larger d / sigma = stronger smoothing and slower."""
    img = validate_image(image)
    if d < 1 or sigma_color <= 0 or sigma_space <= 0 or not 0.0 <= strength <= 1.0:
        raise ValueError("d >= 1, sigma_color > 0, sigma_space > 0 and 0 <= strength <= 1 are required")
    params = dict(d=d, sigma_color=sigma_color, sigma_space=sigma_space, strength=strength)
    if not enabled:
        return noop(img, "bilateral", params, "disabled")
    if strength == 0.0:
        return noop(img, "bilateral", params, "strength is 0")
    out = cv2.bilateralFilter(img, d, sigma_color, sigma_space)
    return CVResult(image=_blend(img, out, strength), applied=True, stage="bilateral", params=params)


def _box(x: np.ndarray, r: int) -> np.ndarray:
    return cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1), normalize=True, borderType=cv2.BORDER_REFLECT)


def guided_filter_smooth(image: np.ndarray, radius: int = 4, eps: float = 0.01,
                         guide: Optional[np.ndarray] = None, strength: float = 1.0,
                         enabled: bool = True) -> CVResult:
    """Guided filter (He et al.), implemented with box filters so it needs no opencv-contrib.
    Each channel is smoothed as a local linear function of a grey guide (default: the image's own luma), which
    follows the guide's edges. eps is on a 0..1 intensity scale: small eps keeps edges, large eps smooths more."""
    img = validate_image(image)
    if radius < 1 or eps <= 0 or not 0.0 <= strength <= 1.0:
        raise ValueError("radius >= 1, eps > 0 and 0 <= strength <= 1 are required")
    params = dict(radius=radius, eps=eps, strength=strength)
    if not enabled:
        return noop(img, "guided", params, "disabled")
    if strength == 0.0:
        return noop(img, "guided", params, "strength is 0")
    if guide is None:
        I = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    else:
        g = np.asarray(guide)
        if g.shape != img.shape[:2]:
            raise ValueError("guide must be (H, W) matching the image")
        I = g.astype(np.float32) / (255.0 if g.dtype == np.uint8 else 1.0)
    mean_I, corr_I = _box(I, radius), _box(I * I, radius)
    var_I = corr_I - mean_I * mean_I
    out = np.empty(img.shape, np.float32)
    for c in range(3):
        p = img[..., c].astype(np.float32) / 255.0
        mean_p = _box(p, radius)
        cov_Ip = _box(I * p, radius) - mean_I * mean_p
        a = cov_Ip / (var_I + eps)
        b = mean_p - a * mean_I
        out[..., c] = (_box(a, radius) * I + _box(b, radius)) * 255.0
    filtered = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    return CVResult(image=_blend(img, filtered, strength), applied=True, stage="guided", params=params)


def edge_preserving_sharpen(image: np.ndarray, amount: float = 0.6, radius: float = 1.0,
                            edge_threshold: float = 0.2, halo_guard: bool = True,
                            max_amount: float = 2.0, enabled: bool = True) -> CVResult:
    """Unsharp-mask sharpening applied only near clear edges.
    detail = image - gaussian(image, radius); added back as amount * detail * edge_weight, where edge_weight ramps
    0 -> 1 as the smoothed luma gradient magnitude (Sobel, luma in 0..1) goes from edge_threshold to 2x edge_threshold.
    Flat regions and low-contrast texture/noise therefore stay (nearly) untouched.
    halo_guard: clip each output pixel to the min..max of its 3x3 input neighbourhood, so no overshoot/ringing
    beyond values already present locally (this also limits how steep an edge can become).
    amount must be within [0, max_amount]."""
    img = validate_image(image)
    if not 0.0 <= amount <= max_amount:
        raise ValueError(f"amount must be within [0, {max_amount}]")
    if radius <= 0 or edge_threshold <= 0:
        raise ValueError("radius and edge_threshold must be > 0")
    params = dict(amount=amount, radius=radius, edge_threshold=edge_threshold, halo_guard=halo_guard)
    if not enabled:
        return noop(img, "sharpen", params, "disabled")
    if amount == 0.0:
        return noop(img, "sharpen", params, "amount is 0")
    f = img.astype(np.float32)
    detail = f - cv2.GaussianBlur(f, (0, 0), radius)
    luma = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0, (0, 0), 1.0)
    mag = np.hypot(cv2.Sobel(luma, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(luma, cv2.CV_32F, 0, 1, ksize=3))
    w = np.clip((mag - edge_threshold) / edge_threshold, 0.0, 1.0)
    w = cv2.GaussianBlur(cv2.dilate(w, np.ones((3, 3), np.uint8)), (0, 0), 1.0)  # cover pixels beside the edge
    out = f + amount * detail * w[..., None]
    if halo_guard:
        k = np.ones((3, 3), np.uint8)
        out = np.minimum(np.maximum(out, cv2.erode(f, k)), cv2.dilate(f, k))
    return CVResult(image=np.clip(np.rint(out), 0, 255).astype(np.uint8), applied=True, stage="sharpen",
                    params=params)
