import dataclasses

import pytest

from ai_engine.evaluation import VARIANTS, find_hf_snapshot, get, size_report, validate_registry
from ai_engine.evaluation.variants import Variant
from ai_engine.optimization import ConfigurationError, OptimizationConfig


def test_registry_valid_and_one_variable_rule():
    validate_registry()
    assert VARIANTS[0].id == "V0" and VARIANTS[0].changed == ()
    for v in VARIANTS[1:]:
        if v.runnable:
            assert (len(v.changed) >= 2) == v.combined


def test_blocked_variants_are_listed_with_reason_not_dropped():
    blocked = {v.id: v.blocked_reason for v in VARIANTS if not v.runnable}
    assert set(blocked) == {"V6", "V7"}
    assert "P3A" in blocked["V6"] and "P6" in blocked["V7"]


def test_cv_variant_changes_only_cv():
    assert get("V5").changed == ("cv",)
    assert get("V5").config == get("V0").config


def test_bad_registry_is_rejected():
    base = VARIANTS[0]
    two = Variant("X", "x", "h", OptimizationConfig(precision="fp16", steps=2))  # 2 changes, not labelled combined
    with pytest.raises(ConfigurationError):
        validate_registry((base, two))
    lone = dataclasses.replace(two, combined=True, config=OptimizationConfig(precision="fp16"))
    with pytest.raises(ConfigurationError):
        validate_registry((base, lone))
    with pytest.raises(ConfigurationError):
        validate_registry((base, base))
    with pytest.raises(KeyError):
        get("nope")


def test_find_snapshot_needs_exact_revision(tmp_path):
    snap = tmp_path / "models--stabilityai--sd-turbo" / "snapshots" / "abc123"
    snap.mkdir(parents=True)
    assert find_hf_snapshot("stabilityai/sd-turbo", "abc123", tmp_path) == snap
    assert find_hf_snapshot("stabilityai/sd-turbo", None, tmp_path) is None  # never guess
    assert find_hf_snapshot("stabilityai/sd-turbo", "zzz", tmp_path) is None


def test_size_report_counts_bytes_and_leaves_missing_null(tmp_path):
    d = tmp_path / "snap"
    (d / "unet").mkdir(parents=True)
    (d / "unet" / "diffusion_pytorch_model.safetensors").write_bytes(b"x" * 1000)
    (d / "unet" / "diffusion_pytorch_model.fp16.safetensors").write_bytes(b"x" * 500)
    (d / "model_index.json").write_text("{}")
    ad = tmp_path / "lora.safetensors"
    ad.write_bytes(b"y" * 40)
    rep = size_report(d, ad)
    assert rep["base_total_dir_bytes"] == 1502
    assert rep["base_weight_files"] == {"unet/diffusion_pytorch_model.fp16.safetensors": 500,
                                        "unet/diffusion_pytorch_model.safetensors": 1000}
    assert rep["adapter_bytes"] == 40
    none = size_report(tmp_path / "missing", None)
    assert none["base_total_dir_bytes"] is None and none["adapter_bytes"] is None
