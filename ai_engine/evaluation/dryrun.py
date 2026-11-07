"""Synthetic engine for validating the harness plumbing WITHOUT a GPU/model. Output is procedural noise; every result
file written with it carries synthetic=true and is rejected by the report gate. Never cite its numbers."""
import hashlib
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image


@dataclass
class _Res:
    image: object
    model: str
    model_revision: str
    precision: str
    scheduler: str
    steps: int
    width: int
    height: int
    seed: int
    peak_gpu_mb: Optional[float] = None


class SyntheticEngine:
    is_synthetic = True
    load_info = {"device": "synthetic", "precision": "n/a", "weights_variant": None, "optimizations": []}

    def __init__(self, precision: str = "fp32"):
        self.precision, self._loaded = precision, False

    def availability(self):
        return True, ""

    def ensure_loaded(self):
        if self._loaded:
            return None
        self._loaded = True
        return 0.0

    def generate(self, prompt, seed, width, height, steps):
        h = int(hashlib.sha256(f"{prompt}|{seed}|{steps}".encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(h)
        base = rng.integers(40, 215, size=3)
        arr = np.clip(base + rng.normal(0, 18, (height, width, 3)), 0, 255).astype(np.uint8)
        return _Res(Image.fromarray(arr, "RGB"), "synthetic/none", "none", self.precision, "none", steps, width,
                    height, seed)
