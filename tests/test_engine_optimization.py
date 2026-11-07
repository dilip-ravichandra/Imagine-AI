"""SDTurboEngine applying P4 optimizations, checked with FAKE torch/diffusers (our logic, not the libraries)."""
import types

import pytest
from PIL import Image

from backend.app.config import Settings
from backend.app.services import engine as eng
from backend.app.services.errors import ServiceError


def make_fakes(cuda=True, bf16=True):
    torch = types.SimpleNamespace(float16="f16", float32="f32", bfloat16="bf16")
    torch.cuda = types.SimpleNamespace(
        is_available=lambda: cuda, is_bf16_supported=lambda: bf16, OutOfMemoryError=RuntimeError,
        empty_cache=lambda: None, reset_peak_memory_stats=lambda: None, synchronize=lambda: None,
        max_memory_allocated=lambda: 2 * 1048576)

    class _Ctx:
        def __enter__(self): return None
        def __exit__(self, *a): return False

    torch.inference_mode = lambda: _Ctx()
    torch.Generator = lambda device: types.SimpleNamespace(manual_seed=lambda s: ("gen", device, s))
    calls = []
    state = {"calls": calls, "load_kw": None}

    class Vae:
        def enable_slicing(self): calls.append("vae.enable_slicing")

    class Pipe:
        scheduler = types.SimpleNamespace(config={"timestep_spacing": "trailing"})
        vae = Vae()
        def to(self, d): calls.append(f"to:{d}"); return self
        def enable_model_cpu_offload(self): calls.append("offload_model")
        def enable_sequential_cpu_offload(self): calls.append("offload_sequential")
        def enable_attention_slicing(self): calls.append("attention_slicing")
        def set_progress_bar_config(self, **kw): pass
        def __call__(self, **kw):
            return types.SimpleNamespace(images=[Image.new("RGB", (kw["width"], kw["height"]))])

    class Auto:
        @staticmethod
        def from_pretrained(model_id, **kw):
            state["load_kw"] = kw
            return Pipe()

    return torch, Auto, state


@pytest.fixture
def load(monkeypatch):
    def _l(settings: Settings, **fake_kw):
        torch, Auto, state = make_fakes(**fake_kw)
        monkeypatch.setattr(eng, "_import_ml", lambda: (torch, Auto))
        monkeypatch.setattr(eng.SDTurboEngine, "availability", lambda self: (True, ""))
        e = eng.SDTurboEngine(settings)
        return e, state
    return _l


def test_defaults_unchanged_from_p1a(load):
    e, st = load(Settings())
    e.ensure_loaded()
    assert st["load_kw"]["torch_dtype"] == "f16" and st["load_kw"]["variant"] == "fp16"
    assert st["calls"] == ["to:cuda"]
    assert e.load_info == {"device": "cuda", "precision": "fp16", "weights_variant": "fp16",
                           "optimizations": ["precision=fp16"]}


def test_default_on_cpu_still_fp32_with_fp16_variant(load):
    e, st = load(Settings(), cuda=False)
    e.ensure_loaded()
    assert st["load_kw"]["torch_dtype"] == "f32" and st["load_kw"]["variant"] == "fp16" and st["calls"] == ["to:cpu"]


def test_explicit_fp32_uses_full_precision_files(load):
    e, st = load(Settings(precision="fp32"))
    e.ensure_loaded()
    assert st["load_kw"]["torch_dtype"] == "f32" and "variant" not in st["load_kw"]
    assert e.generate("x", 1, 256, 256, 1).precision == "fp32"


def test_explicit_fp16_and_weights_override(load):
    e, st = load(Settings(precision="fp16"))
    e.ensure_loaded()
    assert st["load_kw"]["torch_dtype"] == "f16" and st["load_kw"]["variant"] == "fp16"
    e2, st2 = load(Settings(precision="fp32", weights_variant="fp16"))
    e2.ensure_loaded()
    assert st2["load_kw"]["variant"] == "fp16" and st2["load_kw"]["torch_dtype"] == "f32"


def test_bf16_supported_and_unsupported(load):
    e, st = load(Settings(precision="bf16"))
    e.ensure_loaded()
    assert st["load_kw"]["torch_dtype"] == "bf16" and "variant" not in st["load_kw"]
    e2, _ = load(Settings(precision="bf16"), bf16=False)
    with pytest.raises(ServiceError) as ei:
        e2.ensure_loaded()
    assert ei.value.code == "INTERNAL_ERROR" and e2._pipe is None


def test_fp16_on_cpu_is_clean_error_and_retryable(load):
    e, _ = load(Settings(precision="fp16"), cuda=False)
    with pytest.raises(ServiceError) as ei:
        e.ensure_loaded()
    assert ei.value.code == "INTERNAL_ERROR" and e._pipe is None and e.load_info is None


@pytest.mark.parametrize("mode,call", [("model", "offload_model"), ("sequential", "offload_sequential")])
def test_offload_never_moves_pipe_to_device_first(load, mode, call):
    e, st = load(Settings(offload=mode))
    e.ensure_loaded()
    assert st["calls"] == [call]  # no "to:cuda": diffusers requires offload on a CPU-resident pipe
    assert f"offload={mode}" in e.load_info["optimizations"]


def test_offload_on_cpu_rejected(load):
    e, _ = load(Settings(offload="model"), cuda=False)
    with pytest.raises(ServiceError):
        e.ensure_loaded()


def test_slicing_options_applied(load):
    e, st = load(Settings(attention_slicing=True, vae_slicing=True))
    e.ensure_loaded()
    assert st["calls"] == ["to:cuda", "attention_slicing", "vae.enable_slicing"]
    assert e.load_info["optimizations"] == ["precision=fp16", "attention_slicing", "vae_slicing"]
