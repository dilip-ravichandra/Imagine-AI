"""P4 pure-logic tests: config validation, one-variable-at-a-time registry, torch-free policy, Settings, stats."""
import math
from dataclasses import replace

import pytest
from PIL import Image

from ai_engine.optimization import (BASELINE, EXPERIMENTS, ConfigurationError, Experiment, OptimizationConfig,
                                    active_optimizations, get, pixel_fidelity, resolve_precision, summarize,
                                    validate_registry, validate_runtime, weights_variant)
from backend.app.config import Settings, load_settings


# ---- config -----------------------------------------------------------------
@pytest.mark.parametrize("kw", [dict(precision="int8"), dict(offload="disk"), dict(steps=0), dict(steps=5),
                                dict(resolution=500), dict(resolution=128), dict(resolution=2048)])
def test_config_rejects_invalid(kw):
    with pytest.raises(ConfigurationError):
        OptimizationConfig(**kw)


def test_changed_fields_and_overrides():
    c = OptimizationConfig(precision="fp16", steps=2)
    assert set(c.changed_fields(BASELINE)) == {"precision", "steps"}
    assert BASELINE.changed_fields(BASELINE) == ()
    assert c.settings_overrides() == {"precision": "fp16", "attention_slicing": False, "vae_slicing": False,
                                      "offload": "none"}  # steps/resolution are per-request, not settings


# ---- experiment registry ----------------------------------------------------
def test_shipped_registry_is_valid_and_complete():
    validate_registry()
    ids = [e.id for e in EXPERIMENTS]
    assert ids[0] == "B0" and len(set(ids)) == len(ids)
    assert get("B0").changed == ()
    for e in EXPERIMENTS:
        if e.id != "B0" and not e.combined:
            assert len(e.changed) == 1, e.id
    assert [e.id for e in EXPERIMENTS if e.combined] == ["C1"]
    # the plan's two mandatory strategies are present as single-variable experiments
    assert {"precision"} in [set(get(i).changed) for i in ("E1",)] and {"steps"} == set(get("E2").changed)


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get("nope")


def _exp(i, cfg, combined=False):
    return Experiment(i, "t", "h", cfg, combined)


@pytest.mark.parametrize("reg", [
    (_exp("B0", BASELINE), _exp("X", replace(BASELINE, precision="fp16", steps=2))),  # 2 changes, not combined
    (_exp("B0", BASELINE), _exp("X", replace(BASELINE, steps=2), combined=True)),  # combined but 1 change
    (_exp("B0", BASELINE), _exp("B0", BASELINE)),  # duplicate id
    (_exp("E1", replace(BASELINE, steps=2)),),  # no baseline
])
def test_registry_rule_violations_are_caught(reg):
    with pytest.raises(ConfigurationError):
        validate_registry(reg)


# ---- policy -----------------------------------------------------------------
def test_resolve_precision():
    assert resolve_precision("auto", "cuda") == "fp16" and resolve_precision("auto", "cpu") == "fp32"
    assert resolve_precision("fp32", "cuda") == "fp32" and resolve_precision("fp32", "cpu") == "fp32"
    assert resolve_precision("fp16", "cuda") == "fp16"
    with pytest.raises(ConfigurationError):
        resolve_precision("fp16", "cpu")
    with pytest.raises(ConfigurationError):
        resolve_precision("bf16", "cuda", lambda: False)
    assert resolve_precision("bf16", "cuda", lambda: True) == "bf16"
    with pytest.raises(ConfigurationError):
        resolve_precision("fp8", "cuda")


def test_weights_variant_matrix():
    assert weights_variant("auto", "fp16") == "fp16" and weights_variant("auto", "fp32") == "fp16"  # P1A unchanged
    assert weights_variant("fp16", "fp16") == "fp16"
    assert weights_variant("fp32", "fp32") is None and weights_variant("bf16", "bf16") is None
    assert weights_variant("fp32", "fp32", "fp16") == "fp16" and weights_variant("auto", "fp16", "none") is None
    with pytest.raises(ConfigurationError):
        weights_variant("auto", "fp16", "weird")


def test_validate_runtime_and_labels():
    validate_runtime("cuda", "model")
    validate_runtime("cpu", "none")
    with pytest.raises(ConfigurationError):
        validate_runtime("cpu", "model")
    with pytest.raises(ConfigurationError):
        validate_runtime("cuda", "swap")
    assert active_optimizations("fp16", True, True, "model") == ("precision=fp16", "attention_slicing",
                                                                 "vae_slicing", "offload=model")
    assert active_optimizations("fp32", False, False, "none") == ("precision=fp32",)


# ---- Settings ---------------------------------------------------------------
def test_settings_defaults_reproduce_p1a():
    s = Settings()
    assert (s.precision, s.attention_slicing, s.vae_slicing, s.offload, s.weights_variant) == \
           ("auto", False, False, "none", "auto")


def test_settings_from_env(monkeypatch):
    for k, v in dict(PRECISION="FP16", ATTENTION_SLICING="true", VAE_SLICING="1", OFFLOAD="Model",
                     WEIGHTS_VARIANT="none").items():
        monkeypatch.setenv(k, v)
    s = load_settings()
    assert (s.precision, s.attention_slicing, s.vae_slicing, s.offload, s.weights_variant) == \
           ("fp16", True, True, "model", "none")


@pytest.mark.parametrize("name,val", [("PRECISION", "int4"), ("OFFLOAD", "disk"), ("WEIGHTS_VARIANT", "x")])
def test_settings_reject_bad_env(monkeypatch, name, val):
    monkeypatch.setenv(name, val)
    with pytest.raises(ValueError):
        load_settings()


# ---- stats ------------------------------------------------------------------
def test_summarize():
    assert summarize([]) is None and summarize([None]) is None
    s = summarize(range(1, 21))
    assert (s["n"], s["mean"], s["median"], s["min"], s["max"], s["p95"]) == (20, 10.5, 10.5, 1, 20, 19)
    assert summarize([5])["stdev"] is None
    assert summarize([2, 4])["stdev"] == pytest.approx(math.sqrt(2))


def test_pixel_fidelity():
    a, b = Image.new("RGB", (8, 8), (0, 0, 0)), Image.new("RGB", (8, 8), (10, 10, 10))
    f = pixel_fidelity(a, b)
    assert f["mse"] == pytest.approx(100.0) and f["psnr_db"] == pytest.approx(10 * math.log10(255 ** 2 / 100))
    same = pixel_fidelity(a, a.copy())
    assert same == {"mse": 0.0, "psnr_db": None, "identical": True}  # never inf (JSON-safe)
    with pytest.raises(ValueError):
        pixel_fidelity(a, Image.new("RGB", (4, 4)))
