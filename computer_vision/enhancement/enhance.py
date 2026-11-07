"""Conservative colour / exposure / contrast tools.

All functions: input uint8 RGB (H,W,3) -> CVResult. Identity parameters or enabled=False -> unchanged copy, applied=False.
`auto_enhance` only acts when a measurement is outside a dead band, so an acceptable image is returned untouched.
IMPORTANT: every default threshold below is PROVISIONAL and untuned. They have NOT been validated on real
SD-Turbo output (none was available when this was written). Do not claim these enhancements improve images
until the before/after evidence on real generations exists (see docs/P5A_CV.md).
"""
from dataclasses import dataclass, asdict
from typing import Optional

import cv2
import numpy as np

from ..common import CVResult, noop, validate_image

_EPS = 1e-6


def luminance(image: np.ndarray) -> np.ndarray:
    """Rec.601 luma in [0,1], float32 (H,W)."""
    img = validate_image(image).astype(np.float32)
    return (0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]) / 255.0


def _finish(out: np.ndarray, stage: str, params: dict) -> CVResult:
    return CVResult(image=np.clip(np.rint(out), 0, 255).astype(np.uint8), applied=True, stage=stage, params=params)


def adjust_brightness_contrast(image: np.ndarray, brightness: float = 0.0, contrast: float = 1.0,
                               enabled: bool = True) -> CVResult:
    """out = contrast * (x - 128) + 128 + brightness * 255, clipped.
    brightness in [-1, 1] (fraction of full scale, additive); contrast >= 0 (1.0 = unchanged, pivot at mid-grey)."""
    img = validate_image(image)
    if not -1.0 <= brightness <= 1.0:
        raise ValueError("brightness must be within [-1, 1]")
    if contrast < 0:
        raise ValueError("contrast must be >= 0")
    params = dict(brightness=brightness, contrast=contrast)
    if not enabled:
        return noop(img, "brightness_contrast", params, "disabled")
    if brightness == 0.0 and contrast == 1.0:
        return noop(img, "brightness_contrast", params, "identity parameters")
    out = contrast * (img.astype(np.float32) - 128.0) + 128.0 + brightness * 255.0
    return _finish(out, "brightness_contrast", params)


def adjust_gamma(image: np.ndarray, gamma: float = 1.0, enabled: bool = True) -> CVResult:
    """out = 255 * (x/255) ** (1/gamma). gamma > 1 brightens, < 1 darkens, 1 = unchanged. gamma must be > 0."""
    img = validate_image(image)
    if gamma <= 0:
        raise ValueError("gamma must be > 0")
    params = dict(gamma=gamma)
    if not enabled:
        return noop(img, "gamma", params, "disabled")
    if gamma == 1.0:
        return noop(img, "gamma", params, "identity parameters")
    lut = np.clip(np.rint(255.0 * (np.arange(256) / 255.0) ** (1.0 / gamma)), 0, 255).astype(np.uint8)
    return CVResult(image=cv2.LUT(img, lut), applied=True, stage="gamma", params=params)


def white_balance_gray_world(image: np.ndarray, strength: float = 1.0, max_gain: float = 1.5,
                             enabled: bool = True) -> CVResult:
    """Gray-world white balance: scale each channel so channel means match the overall mean.
    Per-channel gain is clamped to [1/max_gain, max_gain] and blended toward 1 by `strength` (0..1).
    KNOWN LIMIT: the gray-world assumption is false for scenes dominated by one colour (e.g. an underwater
    scene is legitimately blue); the gain clamp and strength bound the damage but do not remove it."""
    img = validate_image(image)
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be within [0, 1]")
    if max_gain < 1.0:
        raise ValueError("max_gain must be >= 1")
    params = dict(strength=strength, max_gain=max_gain)
    if not enabled:
        return noop(img, "white_balance", params, "disabled")
    means = img.reshape(-1, 3).astype(np.float64).mean(axis=0)
    if means.min() < 1.0:  # a (nearly) empty channel would give a huge, meaningless gain
        return noop(img, "white_balance", params, "a colour channel is ~0; gray-world undefined")
    gains = np.clip(means.mean() / means, 1.0 / max_gain, max_gain)
    gains = 1.0 + strength * (gains - 1.0)
    params["gains_rgb"] = [round(float(g), 4) for g in gains]
    if np.allclose(gains, 1.0, atol=1e-3):
        return noop(img, "white_balance", params, "already balanced")
    return _finish(img.astype(np.float32) * gains.astype(np.float32), "white_balance", params)


def adjust_saturation(image: np.ndarray, factor: float = 1.0, enabled: bool = True) -> CVResult:
    """Scale HSV saturation by `factor` (0 = greyscale, 1 = unchanged, >1 = more vivid). factor >= 0."""
    img = validate_image(image)
    if factor < 0:
        raise ValueError("factor must be >= 0")
    params = dict(factor=factor)
    if not enabled:
        return noop(img, "saturation", params, "disabled")
    if factor == 1.0:
        return noop(img, "saturation", params, "identity parameters")
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * factor, 0, 255)
    out = cv2.cvtColor(np.rint(hsv).astype(np.uint8), cv2.COLOR_HSV2RGB)
    return CVResult(image=out, applied=True, stage="saturation", params=params)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid: tuple[int, int] = (8, 8),
                channel: str = "lab_l", strength: float = 1.0, enabled: bool = True) -> CVResult:
    """Contrast-limited adaptive histogram equalisation on lightness only (colour left alone).
    channel: 'lab_l' (CIELAB L, default) or 'hsv_v' (HSV value). strength 0..1 blends with the original.
    CLAHE can amplify noise/texture in flat regions; keep clip_limit low and strength < 1 for generated images."""
    img = validate_image(image)
    if clip_limit <= 0:
        raise ValueError("clip_limit must be > 0")
    if tile_grid[0] < 1 or tile_grid[1] < 1:
        raise ValueError("tile_grid must be >= (1, 1)")
    if channel not in ("lab_l", "hsv_v"):
        raise ValueError("channel must be 'lab_l' or 'hsv_v'")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be within [0, 1]")
    params = dict(clip_limit=clip_limit, tile_grid=tuple(tile_grid), channel=channel, strength=strength)
    if not enabled:
        return noop(img, "clahe", params, "disabled")
    if strength == 0.0:
        return noop(img, "clahe", params, "strength is 0")
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tuple(int(t) for t in tile_grid))
    if channel == "lab_l":
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        lab[..., 0] = clahe.apply(lab[..., 0])
        eq = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    else:
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        hsv[..., 2] = clahe.apply(hsv[..., 2])
        eq = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    out = eq if strength == 1.0 else img.astype(np.float32) * (1 - strength) + eq.astype(np.float32) * strength
    return _finish(out, "clahe", params)


@dataclass(frozen=True)
class EnhanceConfig:
    """PROVISIONAL, untuned defaults (see module docstring). Each step runs only when its measurement is outside its dead band."""
    white_balance: bool = True
    wb_tolerance: float = 0.08  # act only if some channel gain differs from 1 by more than this
    wb_max_gain: float = 1.25
    wb_strength: float = 0.6
    exposure: bool = True
    mean_low: float = 0.30  # mean luma below this -> brighten toward it (never past it)
    mean_high: float = 0.70  # mean luma above this -> darken toward it
    max_gamma: float = 1.6  # gamma is clamped to [1/max_gamma, max_gamma]
    contrast: bool = True
    std_low: float = 0.12  # luma std below this -> mild CLAHE
    clahe_clip: float = 1.5
    clahe_strength: float = 0.5


def auto_enhance(image: np.ndarray, config: Optional[EnhanceConfig] = None, enabled: bool = True) -> CVResult:
    """Guarded pipeline: white balance -> exposure (gamma) -> contrast (CLAHE). Returns an unchanged copy
    (applied=False) when nothing is outside its dead band. params['measured'] holds the before-measurements,
    params['steps'] the steps that ran; notes list skipped steps and why."""
    img = validate_image(image)
    cfg = config or EnhanceConfig()
    params = dict(config=asdict(cfg))
    if not enabled:
        return noop(img, "auto_enhance", params, "disabled")
    notes, steps = [], []
    cur = img

    luma = luminance(cur)
    params["measured"] = dict(mean_luma=round(float(luma.mean()), 4), std_luma=round(float(luma.std()), 4))

    if cfg.white_balance:
        means = cur.reshape(-1, 3).astype(np.float64).mean(axis=0)
        gains = means.mean() / np.maximum(means, _EPS)
        if means.min() >= 1.0 and np.max(np.abs(gains - 1.0)) > cfg.wb_tolerance:
            r = white_balance_gray_world(cur, strength=cfg.wb_strength, max_gain=cfg.wb_max_gain)
            if r.applied:
                cur, steps = r.image, steps + ["white_balance"]
        else:
            notes.append("white_balance skipped: within tolerance (or undefined)")

    if cfg.exposure:
        m = float(luminance(cur).mean())
        target = cfg.mean_low if m < cfg.mean_low else (cfg.mean_high if m > cfg.mean_high else None)
        if target is not None and 0.0 < m < 1.0:
            g = float(np.clip(np.log(m) / np.log(target), 1.0 / cfg.max_gamma, cfg.max_gamma))
            r = adjust_gamma(cur, g)
            if r.applied:
                cur, steps = r.image, steps + ["exposure_gamma"]
                params["gamma_used"] = round(g, 4)
        else:
            notes.append("exposure skipped: mean luma inside dead band")

    if cfg.contrast:
        s = float(luminance(cur).std())
        if s < cfg.std_low:
            r = apply_clahe(cur, clip_limit=cfg.clahe_clip, strength=cfg.clahe_strength)
            if r.applied:
                cur, steps = r.image, steps + ["clahe"]
        else:
            notes.append("contrast skipped: luma std above threshold")

    params["steps"] = steps
    if not steps:
        return CVResult(image=img.copy(), applied=False, stage="auto_enhance", params=params, notes=notes)
    return CVResult(image=cur, applied=True, stage="auto_enhance", params=params, notes=notes)
