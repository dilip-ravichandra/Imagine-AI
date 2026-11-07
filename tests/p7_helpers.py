"""Fakes for P7 tests. Values here are test fixtures, never results."""
from dataclasses import dataclass
from typing import Optional

from PIL import Image


@dataclass
class R:
    image: object
    model: str = "fake"
    model_revision: str = "rev"
    precision: str = "fp32"
    scheduler: str = "S"
    steps: int = 4
    width: int = 64
    height: int = 64
    seed: int = 0
    peak_gpu_mb: Optional[float] = 1000.0
    stage_ms: Optional[dict] = None


class GpuFakeEngine:
    """Looks like a CUDA run (load_info.device == cuda) so the report treats it as measured. Fixture only."""
    load_info = {"device": "cuda", "precision": "fp32", "weights_variant": None, "optimizations": []}

    def __init__(self, ms_per_call=0.0, raise_on=None, color=(120, 130, 140)):
        self.calls, self.loaded, self.raise_on, self.color = [], False, raise_on, color

    def availability(self):
        return True, ""

    def ensure_loaded(self):
        if self.loaded:
            return None
        self.loaded = True
        return 5.0

    def generate(self, prompt, seed, w, h, steps):
        self.calls.append((prompt, seed, w, h, steps))
        if self.raise_on is not None and len(self.calls) == self.raise_on:
            e = RuntimeError("CUDA out of memory")
            e.code = "RESOURCE_EXHAUSTED"
            raise e
        return R(Image.new("RGB", (w, h), self.color), steps=steps, width=w, height=h, seed=seed)


class StubClip:
    """Scripted scorer: score = base + per-variant offset, deterministic in the prompt. Fixture only."""
    model_id = "stub-clip"

    def __init__(self, offset=0.0):
        self.offset, self.calls = offset, 0

    def score(self, prompt, image):
        self.calls += 1
        return 0.25 + 0.01 * (len(prompt) % 5) + self.offset


class Clock:
    """Deterministic clock: each call advances by step seconds."""
    def __init__(self, step=0.01):
        self.t, self.step = 0.0, step

    def __call__(self):
        self.t += self.step
        return self.t


PROMPTS = [{"id": f"p{i}", "category": "simple" if i < 2 else "relations", "prompt": "a red cube " * (i + 1)}
           for i in range(4)]
ENV_GPU = {"gpu_name": "TestGPU", "gpu_total_vram_mb": 8000, "model_id": "m", "model_revision": "r", "python": "3"}
