"""P6 integration at service level: GenerationService + controller with a local fake engine (no torch, no fastapi).
Synthetic numbers only; checks wiring, the response's resource_decision, locked runtime and error mapping."""
import time

import pytest
from PIL import Image

from ai_engine.adaptive import ControllerPolicy, StaticMonitor
from backend.app.config import Settings
from backend.app.schemas.v1 import GenerateRequest
from backend.app.services.engine import DiffusionEngine, EngineResult
from backend.app.services.errors import ServiceError, out_of_memory
from backend.app.services.generation import GenerationService
from backend.app.services.storage import ImageStore
from tests.adaptive_helpers import controller, snap


class LocalFakeEngine(DiffusionEngine):
    def __init__(self, precision="fp16"):
        self.calls, self.fail_ids, self.loaded = [], [], False
        self.load_info = {"device": "cuda", "precision": precision}

    def availability(self): return True, ""
    def ensure_loaded(self):
        first, self.loaded = not self.loaded, True
        return 1.0 if first else None

    def generate(self, prompt, seed, width, height, steps):
        self.calls.append((width, steps))
        if self.fail_ids and width in self.fail_ids:
            self.fail_ids.remove(width)
            raise out_of_memory()
        return EngineResult(image=Image.new("RGB", (width, height), (9, 9, 9)), model="fake", model_revision="r",
                            precision=self.load_info["precision"], scheduler="S", steps=steps, width=width,
                            height=height, seed=seed)


def service(tmp_path, engine, budget=12000.0, ctl=None):
    st = Settings(output_dir=tmp_path / "out", supported_resolutions=(256, 384, 512), model_id="synthetic/model-a")
    return GenerationService(engine, ImageStore(st.output_dir, 10), st, ctl or controller(),
                             StaticMonitor(snap(budget)))


def gen(svc, mode="balanced", res=512):
    req = GenerateRequest(prompt="a red robot beside a blue submarine", quality_mode=mode, resolution=res, seed=1)
    return svc.generate(req, "http://t", "ab12" * 8)


def test_controller_picks_steps_and_resolution_and_explains(tmp_path):
    eng = LocalFakeEngine()
    r = gen(service(tmp_path, eng), "balanced", 512)
    assert eng.calls == [(512, 2)]
    assert r.generation.steps == 2 and r.resource_decision.fallback_used is False
    assert "Balanced mode" in r.resource_decision.explanation


def test_constrained_memory_changes_resolution_and_reports_it(tmp_path):
    eng = LocalFakeEngine()
    r = gen(service(tmp_path, eng, budget=3000.0), "balanced", 512)
    assert eng.calls == [(384, 2)] and r.generation.width == 384
    assert r.resource_decision.fallback_used and r.resource_decision.reason == "RESOLUTION_REDUCED_FOR_RESOURCES"


def test_runtime_oom_falls_back_and_succeeds(tmp_path):
    eng = LocalFakeEngine()
    eng.fail_ids = [512]
    r = gen(service(tmp_path, eng), "balanced", 512)
    assert eng.calls == [(512, 2), (384, 2)] and r.resource_decision.reason == "OOM_DURING_GENERATION"


def test_loaded_precision_locks_the_choice(tmp_path):
    r = gen(service(tmp_path, LocalFakeEngine(precision="fp32")), "best", 512)
    # profile has fp32 s4 r512 (needs fp32): allowed because the engine runs fp32; fp16 variants are locked out
    assert r.generation.precision == "fp32" and r.generation.steps == 4


def test_no_safe_configuration_maps_to_resource_exhausted(tmp_path):
    with pytest.raises(ServiceError) as ei:
        gen(service(tmp_path, LocalFakeEngine(), budget=500.0), "balanced", 512)
    e = ei.value
    assert e.status == 503 and e.code == "RESOURCE_EXHAUSTED" and e.retryable and e.action
    assert "/" not in e.message and "Traceback" not in e.message  # safe message


def test_without_controller_behaviour_is_the_old_fixed_mapping(tmp_path):
    st = Settings(output_dir=tmp_path / "o2", supported_resolutions=(256, 384, 512))
    eng = LocalFakeEngine()
    svc = GenerationService(eng, ImageStore(st.output_dir, 10), st)
    r = svc.generate(GenerateRequest(prompt="a cat", quality_mode="best", resolution=512, seed=1), "http://t", "a" * 32)
    assert eng.calls == [(512, 4)] and "No adaptive controller" in r.resource_decision.explanation
