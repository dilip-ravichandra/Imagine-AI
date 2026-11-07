"""P6 controller: modes, safety, fallback, determinism, explanations. All numbers come from the SYNTHETIC fixture."""
import dataclasses
import json

import pytest

from ai_engine.adaptive import ControllerPolicy, ControllerRequest, ResourceError
from tests.adaptive_helpers import controller, jsonable, profile, req, snap, variant

AMPLE = 12000.0


# ---- the three modes, ample resources --------------------------------------------------------------------------
@pytest.mark.parametrize("mode,expected", [("quick", "A-fp16-s1-r512"), ("balanced", "A-fp16-s2-r512"),
                                           ("best", "A-fp32-s4-r512")])
def test_modes_with_ample_memory_use_requested_resolution_and_no_fallback(mode, expected):
    d = controller().decide(req(mode), snap(AMPLE))
    assert d.selected.id == expected and d.selected.resolution == 512
    assert d.fallback_used is False and d.reason is None
    assert d.log["outcome"] == "selected" and d.log["ideal_id"] == expected


def test_quick_is_never_slower_than_balanced_than_best_when_unconstrained():
    lat = {m: controller().decide(req(m), snap(AMPLE)).selected.latency_ms_median for m in ("quick", "balanced", "best")}
    assert lat["quick"] <= lat["balanced"] <= lat["best"]


def test_guardrail_excludes_low_quality_and_remote_and_known_bad():
    d = controller().decide(req("quick"), snap(AMPLE))
    ev = d.log["evaluations"]
    assert ev["B-fp16-s1-r512"]["verdict"] == "accepted"  # safe, but below the quick guardrail (clip .25 < .26)
    assert d.log["guardrail"]["basis"] == "clip_mean" and d.log["guardrail"]["threshold"] > 0.25
    assert ev["R-remote-s2-r512"]["code"] == "REMOTE_NOT_ALLOWED"
    assert ev["A-fp32-s4-r768"]["code"] == "BENCHMARK_FAILED"  # known-bad is reported before the resolution rule
    assert ev["A-fp16-s1-r256"]["code"] == "SAFE" or ev["A-fp16-s1-r256"]["verdict"] == "accepted"
    d768 = controller().decide(req("best", 768), snap(AMPLE))
    assert d768.log["evaluations"]["A-fp32-s4-r768"]["code"] == "BENCHMARK_FAILED"
    assert d768.selected.resolution == 512 and d768.reason == "RESOLUTION_NOT_PROFILED"  # OOM'd size is never used


# ---- resource limits and fallback ------------------------------------------------------------------------------
@pytest.mark.parametrize("budget,mode,expected,reason", [
    (4000, "best", "A-fp16-s4-r512", "PRECISION_CHANGED_FOR_RESOURCES"),
    (3000, "quick", "A-fp16-s1-r384", "RESOLUTION_REDUCED_FOR_RESOURCES"),
    (3000, "balanced", "A-fp16-s2-r384", "RESOLUTION_REDUCED_FOR_RESOURCES"),
    (3000, "best", "A-fp16-s4-r384", "PRECISION_CHANGED_FOR_RESOURCES"),
    (2000, "quick", "A-fp16-s1-r256", "RESOLUTION_REDUCED_FOR_RESOURCES"),
    (2000, "balanced", "A-fp16-s2-r256", "RESOLUTION_REDUCED_FOR_RESOURCES"),
])
def test_fallback_follows_the_ladder_resolution_first(budget, mode, expected, reason):
    d = controller().decide(req(mode), snap(budget))
    assert d.selected.id == expected and d.fallback_used and d.reason == reason
    assert "Fallback" in d.explanation and d.log["ideal_id"] != d.selected.id


def test_selected_config_always_fits_the_budget_with_headroom():
    ctl, pol = controller(), ControllerPolicy()
    for budget in (1800 * 1.1, 2000, 2640, 3000, 3410, 4000, 5720, 12000):
        for mode in ("quick", "balanced", "best"):
            try:
                d = ctl.decide(req(mode), snap(budget))
            except ResourceError:
                continue
            assert d.selected.peak_gpu_mb_max * (1 + pol.headroom_fraction) <= budget + 1e-6


def test_headroom_boundary_is_inclusive():
    ctl = controller()
    assert ctl.decide(req("balanced"), snap(3410.0)).selected.id == "A-fp16-s2-r512"  # 3100 * 1.1 exactly
    assert ctl.decide(req("balanced"), snap(3409.9)).selected.id != "A-fp16-s2-r512"


def test_no_fit_gives_clear_resource_error_with_full_log():
    with pytest.raises(ResourceError) as ei:
        controller().decide(req("quick"), snap(1000))
    e = ei.value
    assert e.code == "NO_SAFE_CONFIGURATION" and e.suggested_action and "fits" in e.message
    ev = e.log["evaluations"]
    assert ev["A-fp16-s1-r256"]["code"] == "EXCEEDS_GPU_BUDGET" and "1980" in ev["A-fp16-s1-r256"]["detail"]
    assert e.log["outcome"] == "no_safe_configuration"


def test_best_mode_refuses_quality_loss_and_says_so():
    with pytest.raises(ResourceError) as ei:
        controller().decide(req("best"), snap(2000))
    assert "guardrail" in ei.value.message and "Quick or Balanced" in ei.value.suggested_action
    assert any(v["code"] == "GUARDRAIL_BLOCKS_STEP_REDUCTION" for v in ei.value.log["evaluations"].values())


def test_remote_is_last_resort_and_needs_consent():
    ctl = controller()
    with pytest.raises(ResourceError):
        ctl.decide(req("balanced"), snap(1000))  # no consent -> clear error
    d = ctl.decide(req("balanced", allow_remote=True), snap(1000))
    assert d.selected.id == "R-remote-s2-r512" and d.reason == "REMOTE_BACKEND_FOR_RESOURCES"
    # with consent but plenty of memory, remote is NOT preferred
    assert ctl.decide(req("best", allow_remote=True), snap(AMPLE)).selected.id == "A-fp32-s4-r512"


def test_requested_resolution_not_profiled_is_a_flagged_fallback():
    d = controller().decide(req("balanced", 640), snap(AMPLE))
    assert d.selected.resolution == 512 and d.fallback_used and d.reason == "RESOLUTION_NOT_PROFILED"
    assert "No measured profile exists at 640px" in d.explanation
    d256 = controller().decide(req("quick", 256), snap(AMPLE))
    assert d256.selected.resolution == 256 and not d256.fallback_used  # never upscales past the request


# ---- missing / unknown metrics ---------------------------------------------------------------------------------
def test_missing_memory_metric_rejects_that_config_and_falls_back():
    ps = variant(profile(), **{"A-fp16-s2-r512": {"peak_gpu_mb_max": None}})
    d = controller(ps).decide(req("balanced"), snap(AMPLE))
    assert d.log["evaluations"]["A-fp16-s2-r512"]["code"] == "MISSING_MEMORY_METRIC"
    assert d.selected.id != "A-fp16-s2-r512" and d.fallback_used


def test_missing_latency_metric_rejected():
    ps = variant(profile(), **{"A-fp16-s2-r512": {"latency_ms_median": None}})
    d = controller(ps).decide(req("balanced"), snap(AMPLE))
    assert d.log["evaluations"]["A-fp16-s2-r512"]["code"] == "MISSING_LATENCY_METRIC"


def test_unknown_budget_rejects_by_default_and_can_be_allowed_but_is_flagged():
    unknown = snap(None)
    with pytest.raises(ResourceError) as ei:
        controller().decide(req("balanced"), unknown)
    assert ei.value.log["evaluations"]["A-fp16-s2-r512"]["code"] == "UNKNOWN_BUDGET"
    d = controller(policy=ControllerPolicy(unknown_memory="allow")).decide(req("balanced"), unknown)
    assert d.selected.id == "A-fp16-s2-r512"
    assert "UNVERIFIED_GPU_BUDGET" in d.log["evaluations"]["A-fp16-s2-r512"]["notes"]


def test_cuda_config_on_cpu_machine_is_rejected():
    with pytest.raises(ResourceError) as ei:
        controller().decide(req("balanced"), snap(None, device="cpu"))
    assert ei.value.log["evaluations"]["A-fp16-s2-r512"]["code"] == "DEVICE_MISMATCH"


def test_ram_check_is_opt_in_for_gpu_entries():
    low_ram = snap(AMPLE, ram=100.0)
    assert controller().decide(req("balanced"), low_ram).selected.id == "A-fp16-s2-r512"
    with pytest.raises(ResourceError) as ei:
        controller(policy=ControllerPolicy(require_ram_check=True)).decide(req("balanced"), low_ram)
    assert ei.value.log["evaluations"]["A-fp16-s2-r512"]["code"] == "EXCEEDS_RAM_BUDGET"


# ---- locked runtime (the loaded engine cannot change precision/model without a reload) ------------------------
def test_locked_runtime_excludes_configs_needing_a_reload():
    lock = {"model_id": "synthetic/model-a", "precision": "fp16", "device": "cuda", "attention_slicing": False,
            "vae_slicing": False, "offload": "none"}
    d = controller().decide(req("best", locked_runtime=lock), snap(AMPLE))
    ev = d.log["evaluations"]
    assert ev["A-fp32-s4-r512"]["code"] == "RUNTIME_LOCKED" and "reload" in ev["A-fp32-s4-r512"]["detail"]
    assert ev["B-fp16-s1-r512"]["code"] == "RUNTIME_LOCKED"
    assert d.selected.id == "A-fp16-s4-r512" and d.selected.precision == "fp16"
    assert not d.fallback_used  # the lock defines what is available; it is not a resource fallback


# ---- policy effects --------------------------------------------------------------------------------------------
def test_complexity_has_no_effect_by_default_but_can_be_enabled():
    base = controller().decide(req("quick"), snap(AMPLE)).selected.id
    assert controller().decide(req("quick", complexity_level="complex"), snap(AMPLE)).selected.id == base
    pol = ControllerPolicy(complexity_tolerance_scale={"simple": 1.0, "moderate": 1.0, "complex": 0.0})
    d = controller(policy=pol).decide(req("quick", complexity_level="complex"), snap(AMPLE))
    assert d.selected.id == "A-fp32-s4-r512"  # tolerance 0 -> highest measured quality
    assert d.log["inputs"]["effective_tolerance"] == 0.0


def test_without_quality_metric_falls_back_to_labelled_unmeasured_proxy():
    ps = variant(profile(), **{e.id: {"clip_mean": None} for e in profile().entries})
    d = controller(ps).decide(req("quick"), snap(AMPLE))
    assert d.log["guardrail"]["basis"] == "steps_proxy_UNMEASURED"
    assert d.selected.id == "A-fp16-s2-r512" and "UNMEASURED" in d.explanation
    assert controller(ps).decide(req("balanced"), snap(AMPLE)).selected.id == "A-fp16-s4-r512"


def test_disabled_fallback_stage_blocks_that_path():
    pol = ControllerPolicy(fallback_order=("precision", "steps", "model", "remote"))  # no resolution reduction
    d = controller(policy=pol).decide(req("balanced"), snap(3000))
    assert d.log["evaluations"]["A-fp16-s2-r384"]["code"] == "STAGE_DISABLED_BY_POLICY"
    assert d.selected.resolution == 512 and d.selected.id == "A-fp16-s2-r512-offload"
    assert d.reason == "PRECISION_CHANGED_FOR_RESOURCES"


# ---- determinism, explainability, logging ----------------------------------------------------------------------
def test_decisions_are_deterministic_across_calls_and_instances():
    outs = []
    for _ in range(3):
        d = controller().decide(req("balanced"), snap(3000))
        outs.append((d.selected.id, d.reason, d.explanation, jsonable(d.log)))
    assert len(set(outs)) == 1
    assert controller().decide(req("balanced"), snap(3000)).log["input_hash"] == \
        controller().decide(req("balanced"), snap(3000)).log["input_hash"]
    assert controller().decide(req("balanced"), snap(3000)).log["input_hash"] != \
        controller().decide(req("balanced"), snap(3001)).log["input_hash"]


def test_profile_row_order_does_not_change_the_decision():
    ps = profile()
    shuffled = dataclasses.replace(ps, entries=tuple(reversed(ps.entries)))
    for mode in ("quick", "balanced", "best"):
        for budget in (AMPLE, 4000, 3000, 2000):
            try:
                a = controller(ps).decide(req(mode), snap(budget)).selected.id
            except ResourceError:
                a = None
            try:
                b = controller(shuffled).decide(req(mode), snap(budget)).selected.id
            except ResourceError:
                b = None
            assert a == b


def test_log_is_json_serialisable_complete_and_has_no_prompt():
    seen = []
    d = controller(sink=seen.append).decide(req("balanced"), snap(3000))
    text = json.dumps(d.log)
    assert seen == [d.log] and d.log["schema"] == "adaptive_decision/1"
    assert set(d.log["inputs"]) >= {"request", "snapshot", "profile", "policy", "effective_tolerance"}
    assert d.log["inputs"]["profile"]["synthetic"] is True and d.log["inputs"]["policy"]["calibrated"] is False
    assert len(d.log["evaluations"]) == len(profile().entries)  # every entry accounted for
    assert "prompt" not in text.lower()
    sel = d.log["selected"]
    assert sel["expected"]["latency_ms_median"] == d.selected.latency_ms_median  # measured numbers only


def test_explanation_is_honest_about_synthetic_profile_and_reports_measured_values():
    d = controller().decide(req("balanced"), snap(AMPLE))
    assert "SYNTHETIC" in d.explanation and "800 ms" in d.explanation and "Balanced mode" in d.explanation
    rd = d.to_resource_decision()
    assert set(rd) == {"fallback_used", "reason", "explanation"}


def test_invalid_requests_raise_value_error():
    with pytest.raises(ValueError):
        ControllerRequest("turbo", 512)
    with pytest.raises(ValueError):
        ControllerRequest("quick", 512, complexity_level="epic")
    with pytest.raises(ValueError):
        ControllerRequest("quick", 512, locked_runtime={"colour": "red"})
    with pytest.raises(ValueError):
        ControllerRequest("quick", 0)


def test_controller_does_not_mutate_inputs():
    ps, sn = profile(), snap(3000)
    before = (ps.profile_id, sn)
    controller(ps).decide(req("balanced"), sn)
    assert (ps.profile_id, sn) == before
