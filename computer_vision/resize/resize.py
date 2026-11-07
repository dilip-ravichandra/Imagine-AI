"""Resolution handling: supported sizes, aspect-ratio-aware resize, interpolation choice."""
from typing import Optional, Sequence

import cv2
import numpy as np

from ..common import CVResult, noop, validate_image

STAGE = "resize"
MODES = ("stretch", "fit", "pad", "fill")
_INTERP = {"nearest": cv2.INTER_NEAREST, "linear": cv2.INTER_LINEAR, "cubic": cv2.INTER_CUBIC,
           "lanczos": cv2.INTER_LANCZOS4, "area": cv2.INTER_AREA}
INTERPOLATIONS = ("auto",) + tuple(_INTERP)


def choose_interpolation(src_wh: tuple[int, int], dst_wh: tuple[int, int]) -> str:
    """Downscaling -> 'area' (averages source pixels, avoids aliasing). Upscaling -> 'lanczos'
    (sharper than bicubic; may ring slightly on hard edges, use 'cubic' if that matters).
    Mixed (one axis up, one down) -> 'cubic'. Same size -> 'nearest' (unused: resize is a no-op)."""
    sw, sh = src_wh
    dw, dh = dst_wh
    if (sw, sh) == (dw, dh):
        return "nearest"
    if dw <= sw and dh <= sh:
        return "area"
    if dw >= sw and dh >= sh:
        return "lanczos"
    return "cubic"


def nearest_supported_resolution(value: int, supported: Sequence[int], prefer: str = "nearest") -> int:
    """Snap a requested size to one of the server's supported sizes.
    prefer: 'nearest' (ties go to the smaller), 'down' (largest <= value, else smallest), 'up' (smallest >= value, else largest)."""
    if not supported:
        raise ValueError("supported must not be empty")
    if prefer not in ("nearest", "down", "up"):
        raise ValueError("prefer must be 'nearest', 'down' or 'up'")
    s = sorted(set(int(x) for x in supported))
    if prefer == "down":
        below = [x for x in s if x <= value]
        return below[-1] if below else s[0]
    if prefer == "up":
        above = [x for x in s if x >= value]
        return above[0] if above else s[-1]
    return min(s, key=lambda x: (abs(x - value), x))


def _snap(n: int, multiple_of: int) -> int:
    return max(multiple_of, int(round(n / multiple_of)) * multiple_of)


def resize_image(image: np.ndarray, width: int, height: int, mode: str = "fit",
                 interpolation: str = "auto", multiple_of: int = 1,
                 pad_color: tuple[int, int, int] = (0, 0, 0), allow_upscale: bool = True,
                 enabled: bool = True) -> CVResult:
    """Resize toward a (width, height) box.

    mode:
      'stretch' output is exactly (width, height); aspect ratio NOT preserved.
      'fit'     keeps aspect ratio, largest size that fits inside the box (output may be smaller on one axis).
      'pad'     'fit' then letterbox to exactly (width, height) with pad_color, content centred.
      'fill'    keeps aspect ratio, covers the box, centre-crops to exactly (width, height).
    multiple_of: 'fit' output dims are rounded to this multiple (e.g. 8 for diffusion latents); the others are
      exact by definition, so (width, height) must already be multiples when that matters.
    allow_upscale=False: never enlarge ('fit'/'pad'/'fill' scale is capped at 1.0; 'stretch' is a no-op if it would enlarge).
    No-op (applied=False) when disabled or when the result would equal the input size.
    """
    img = validate_image(image)
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if interpolation not in INTERPOLATIONS:
        raise ValueError(f"interpolation must be one of {INTERPOLATIONS}")
    if width < 1 or height < 1 or multiple_of < 1:
        raise ValueError("width, height and multiple_of must be >= 1")
    params = dict(width=width, height=height, mode=mode, interpolation=interpolation,
                  multiple_of=multiple_of, allow_upscale=allow_upscale)
    if not enabled:
        return noop(img, STAGE, params, "disabled")

    sh, sw = img.shape[:2]
    scale = max(width / sw, height / sh) if mode == "fill" else (
        min(width / sw, height / sh) if mode in ("fit", "pad") else None)
    if scale is not None and not allow_upscale:
        scale = min(scale, 1.0)

    if mode == "stretch":
        dw, dh = (width, height)
        if not allow_upscale and (width > sw or height > sh):
            return noop(img, STAGE, params, "upscale not allowed")
    elif mode == "fit":
        dw, dh = max(1, round(sw * scale)), max(1, round(sh * scale))
        if multiple_of > 1:
            dw, dh = _snap(dw, multiple_of), _snap(dh, multiple_of)
    else:  # pad / fill resize content first
        dw, dh = max(1, round(sw * scale)), max(1, round(sh * scale))
        if mode == "fill":  # rounding must not leave us short of the box
            dw, dh = max(dw, width), max(dh, height)

    interp = choose_interpolation((sw, sh), (dw, dh)) if interpolation == "auto" else interpolation
    params["interpolation_used"] = interp
    out = img if (dw, dh) == (sw, sh) else cv2.resize(img, (dw, dh), interpolation=_INTERP[interp])

    if mode == "fill":
        x0, y0 = (dw - width) // 2, (dh - height) // 2
        out = out[y0:y0 + height, x0:x0 + width]
    elif mode == "pad":
        canvas = np.empty((height, width, 3), np.uint8)
        canvas[:] = np.array(pad_color, np.uint8)
        x0, y0 = (width - dw) // 2, (height - dh) // 2
        canvas[y0:y0 + dh, x0:x0 + dw] = out
        out = canvas
    if out.shape[:2] == (sh, sw) and (dw, dh) == (sw, sh):  # nothing scaled, cropped or padded
        return noop(img, STAGE, params, "output size equals input size")
    params["output_size"] = (out.shape[1], out.shape[0])
    return CVResult(image=np.ascontiguousarray(out), applied=True, stage=STAGE, params=params)


def fit_to_resolution(image: np.ndarray, resolution: int, mode: str = "pad", **kw) -> CVResult:
    """Convenience: produce a square resolution x resolution image (default letterboxed, aspect preserved)."""
    return resize_image(image, resolution, resolution, mode=mode, **kw)
