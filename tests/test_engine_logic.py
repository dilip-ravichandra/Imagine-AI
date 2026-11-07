"""Exercises SDTurboEngine logic with FAKE torch/diffusers modules.
This checks OUR logic (device choice, load-once, OOM translation, call arguments),
not the real libraries. The real path is covered only by test_real_model_smoke.py."""
import threading
import types

import pytest
from PIL import Image

from backend.app.config import Settings
from backend.app.services import engine as eng
from backend.app.services.errors import ServiceError


class FakeOOM(RuntimeError):
    pass


def make_fakes(cuda=False, load_error=None, gen_error=None):
    torch = types.SimpleNamespace(float16="f16", float32="f32")
    torch.cuda = types.SimpleNamespace(
        is_available=lambda: cuda, OutOfMemoryError=FakeOOM, empty_cache=lambda: None,
        reset_peak_memory_stats=lambda: None, synchronize=lambda: None,
        max_memory_allocated=lambda: 3 * 1048576)

    class _Ctx:
        def __enter__(self): return None
        def __exit__(self, *a): return False

    torch.inference_mode = lambda: _Ctx()
    torch.Generator = lambda device: types.SimpleNamespace(manual_seed=lambda s: ("gen", device, s))
    state = {"loads": 0, "kwargs": None, "device": None}

    class Pipe:
        scheduler = types.SimpleNamespace(config={"timestep_spacing": "trailing"})
        def to(self, d): state["device"] = d; return self
        def set_progress_bar_config(self, **kw): pass
        def __call__(self, **kw):
            state["kwargs"] = kw
            if gen_error: raise gen_error
            return types.SimpleNamespace(images=[Image.new("RGB", (kw["width"], kw["height"]))])

    class Auto:
        @staticmethod
        def from_pretrained(model_id, **kw):
            state["loads"] += 1; state["load_kw"] = (model_id, kw)
            if load_error: raise load_error
            return Pipe()

    return torch, Auto, state


@pytest.fixture
def patch(monkeypatch):
    def _p(**kw):
        torch, Auto, state = make_fakes(**kw)
        monkeypatch.setattr(eng, "_import_ml", lambda: (torch, Auto))
        monkeypatch.setattr(eng.SDTurboEngine, "availability", lambda self: (True, ""))
        return state
    return _p


def test_import_safe_and_unavailable_without_ml(monkeypatch):
    monkeypatch.setattr(eng.importlib.util, "find_spec", lambda name: None)
    ok, reason = eng.SDTurboEngine(Settings()).availability()
    assert ok is False and "requirements-ml.txt" in reason


def test_cpu_path_uses_fp32_and_model_card_settings(patch):
    st = patch(cuda=False)
    e = eng.SDTurboEngine(Settings(model_revision=None))
    assert e.ensure_loaded() is not None and e.ensure_loaded() is None  # loaded exactly once
    r = e.generate("a cat", 7, 384, 384, 2)
    assert st["loads"] == 1 and st["device"] == "cpu"
    assert st["load_kw"][0] == "stabilityai/sd-turbo" and st["load_kw"][1]["torch_dtype"] == "f32"
    assert st["kwargs"]["guidance_scale"] == 0.0 and st["kwargs"]["num_inference_steps"] == 2
    assert "negative_prompt" not in st["kwargs"] and st["kwargs"]["generator"] == ("gen", "cpu", 7)
    assert (r.precision, r.peak_gpu_mb, r.model_revision) == ("fp32", None, "unpinned (hub default)")
    assert r.scheduler == "SimpleNamespace(timestep_spacing=trailing)"


def test_cuda_path_uses_fp16_and_reports_peak(patch):
    st = patch(cuda=True)
    e = eng.SDTurboEngine(Settings(model_revision="abc123"))
    e.ensure_loaded()
    r = e.generate("a cat", 1, 512, 512, 1)
    assert st["device"] == "cuda" and st["load_kw"][1]["torch_dtype"] == "f16"
    assert st["load_kw"][1]["revision"] == "abc123"
    assert (r.precision, r.peak_gpu_mb, r.model_revision) == ("fp16", 3.0, "abc123")


def test_cuda_forced_but_missing_is_clean_load_error(patch):
    patch(cuda=False)
    with pytest.raises(ServiceError) as ei:
        eng.SDTurboEngine(Settings(device="cuda")).ensure_loaded()
    assert ei.value.code == "INTERNAL_ERROR" and "CUDA" not in ei.value.message


def test_load_oom_and_failure_translated_and_retryable(patch):
    patch(load_error=FakeOOM("CUDA out of memory"))
    with pytest.raises(ServiceError) as ei:
        eng.SDTurboEngine(Settings()).ensure_loaded()
    assert ei.value.code == "RESOURCE_EXHAUSTED"
    patch(load_error=OSError(r"C:\secret\cache missing"))
    e = eng.SDTurboEngine(Settings())
    with pytest.raises(ServiceError) as ei:
        e.ensure_loaded()
    assert ei.value.code == "INTERNAL_ERROR" and "secret" not in ei.value.message
    assert e._pipe is None  # failed load leaves engine retryable


def test_generation_oom_translated(patch):
    patch(cuda=True, gen_error=FakeOOM("CUDA out of memory"))
    e = eng.SDTurboEngine(Settings())
    e.ensure_loaded()
    with pytest.raises(ServiceError) as ei:
        e.generate("x", 1, 512, 512, 1)
    assert ei.value.code == "RESOURCE_EXHAUSTED" and ei.value.retryable


def test_runtime_error_with_oom_text_also_detected(patch):
    patch(cuda=True, gen_error=RuntimeError("CUDA error: out of memory"))
    e = eng.SDTurboEngine(Settings())
    e.ensure_loaded()
    with pytest.raises(ServiceError):
        e.generate("x", 1, 512, 512, 1)


def test_concurrent_ensure_loaded_loads_once(patch):
    st = patch()
    e = eng.SDTurboEngine(Settings())
    ts = [threading.Thread(target=e.ensure_loaded) for _ in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert st["loads"] == 1
