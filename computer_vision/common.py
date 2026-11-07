"""Shared contract for every classical-CV stage.

Image format everywhere: numpy uint8 array, shape (H, W, 3), RGB order, H and W >= 1.
(PIL <-> array helpers below; OpenCV's BGR order is handled inside each function, never exposed.)
Every stage returns a CVResult so stages can be chained: next_stage(result.image).
Stages never mutate their input. Bypass: `enabled=False` or identity parameters return an unchanged copy
with applied=False.
"""
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CVResult:
    image: np.ndarray  # uint8 (H, W, 3) RGB
    applied: bool  # False = bypass / no-op (image is an unchanged copy of the input)
    stage: str
    params: dict[str, Any] = field(default_factory=dict)  # parameters actually used
    notes: list[str] = field(default_factory=list)  # why a no-op happened, clamps applied, etc.


def validate_image(image: Any) -> np.ndarray:
    """Return `image` if it satisfies the contract, else raise ValueError (never silently coerce)."""
    if not isinstance(image, np.ndarray):
        raise ValueError("image must be a numpy array (use to_array() for PIL images)")
    if image.dtype != np.uint8:
        raise ValueError(f"image dtype must be uint8, got {image.dtype}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"image must have shape (H, W, 3), got {image.shape}")
    if image.shape[0] < 1 or image.shape[1] < 1:
        raise ValueError("image must not be empty")
    return image


def noop(image: np.ndarray, stage: str, params: dict, why: str) -> CVResult:
    return CVResult(image=image.copy(), applied=False, stage=stage, params=params, notes=[why])


def to_array(pil_image) -> np.ndarray:
    """PIL image -> uint8 RGB array (alpha dropped, palette/gray converted)."""
    return np.asarray(pil_image.convert("RGB"), dtype=np.uint8).copy()


def to_pil(image: np.ndarray):
    from PIL import Image
    return Image.fromarray(validate_image(image), mode="RGB")
