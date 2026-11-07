"""P6 runtime fallback: simulated OOM / timeout with a scripted run function and a scripted monitor.
Everything here is synthetic: it tests the control flow, not real GPU behaviour."""
import subprocess
import sys

import pytest

from ai_engine.adaptive import (CappedMonitor, ControllerPolicy, ResourceError, ResourceSnapshot, StaticMonitor,
                                classify_failure, run_with_fallback)
from tests.adaptive_helpers import controller, req, snap


class OOM(RuntimeError):
    pass


class EngineOOM(Exception):  # looks like backend ServiceError out_of_memory()
    status, code = 503, "RESOURCE_EXHAUSTED"


class EngineBusy(Exception):  # looks like backend ServiceError busy()
    status, code = 429, "RESOURCE_EXHAUSTED"


class ScriptedRun:
    """Fails (raising `exc`) for the first `fail_ids` it is asked to run, in any order, then succeeds."""

    def __init__(self, fail_ids=(), exc=lambda: OOM("CUDA out of memory")):
        self.fail_ids, self.exc, self.calls = set(fail_ids), exc, []

    def __call__(self, entry):
        self.calls.append(entry.id)
        if entry.id in self.fail_ids:
            raise self.exc()
        return f"image:{entry.id}"


def mon(budget=12000.0):
    return StaticMonitor(snap(budget))


def test_classify_failure():
    assert classify_failure(OOM("CUDA out of memory. Tried to allocate")) == "oom"
    assert classify_failure(EngineOOM()) == "oom"
    assert classify_failure(EngineBusy()) is None  # busy is NOT an out-of-memory condition
    assert classify_failure(TimeoutError()) == "timeout"
    assert classify_failure(ValueError("boom")) is None
    assert classify_failure(RuntimeError("something else")) is None

    class OutOfMemoryError(Exception):
        pass
    assert classify_failure(OutOfMemoryError()) == "oom"


def test_no_failure_means_no_fallback_and_one_call():
    run = ScriptedRun()
    ex = run_with_fallback(controller(), req("balanced"), mon(), run)
    assert ex.value == "image:A-fp16-s2-r512" and run.calls == ["A-fp16-s2-r512"]
    assert ex.fallback_used is False and ex.reason is None and ex.failures == []


def test_oom_then_fallback_to_lower_resolution_succeeds():
    run = ScriptedRun({"A-fp16-s2-r512"})
    ex = run_with_fallback(controller(), req("balanced"), mon(), run)
    assert run.calls == ["A-fp16-s2-r512", "A-fp16-s2-r384"]
    assert ex.value == "image:A-fp16-s2-r384" and ex.fallback_used and ex.reason == "OOM_DURING_GENERATION"
    assert ex.failures == [{"entry": "A-fp16-s2-r512", "cause": "oom"}]
    assert "failed (out of memory)" in ex.explanation and "512 -> 384" in ex.explanation
    assert ex.decision.log["kind"] == "fallback" and ex.decision.log["inputs"]["failure"]["cause"] == "oom"


def test_engine_service_error_oom_triggers_fallback_but_busy_propagates():
    ex = run_with_fallback(controller(), req("balanced"), mon(), ScriptedRun({"A-fp16-s2-r512"}, exc=EngineOOM))
    assert ex.fallback_used
    run = ScriptedRun({"A-fp16-s2-r512"}, exc=EngineBusy)
    with pytest.raises(EngineBusy):
        run_with_fallback(controller(), req("balanced"), mon(), run)
    assert run.calls == ["A-fp16-s2-r512"]  # no fallback attempted on a busy server


def test_non_resource_errors_propagate_untouched():
    run = ScriptedRun({"A-fp16-s2-r512"}, exc=lambda: ValueError("real bug"))
    with pytest.raises(ValueError, match="real bug"):
        run_with_fallback(controller(), req("balanced"), mon(), run)
    assert run.calls == ["A-fp16-s2-r512"]


def test_repeated_oom_walks_the_ladder_never_repeats_and_ends_in_clear_error():
    ids = ["A-fp16-s2-r512", "A-fp16-s2-r384", "A-fp16-s2-r256"]
    run = ScriptedRun(set(ids) | {"A-fp16-s1-r256"})
    with pytest.raises(ResourceError) as ei:
        run_with_fallback(controller(), req("balanced"), mon(), run)
    assert run.calls == ids  # every fallback was a new config and strictly lighter; then nothing safe remains
    assert len(set(run.calls)) == len(run.calls)
    assert ei.value.code == "NO_SAFE_CONFIGURATION" and ei.value.suggested_action


def test_fallback_uses_a_fresh_snapshot_after_the_failure():
    class Shrinking(StaticMonitor):
        def __init__(self):
            self.n = 0

        def snapshot(self):
            self.n += 1
            return snap(12000.0 if self.n == 1 else 2000.0)  # memory pressure appears after the first OOM

    run = ScriptedRun({"A-fp16-s2-r512"})
    ex = run_with_fallback(controller(), req("balanced"), Shrinking(), run)
    assert run.calls == ["A-fp16-s2-r512", "A-fp16-s2-r256"]  # 384 (needs 2640 MB) no longer fits 2000 MB


def test_max_fallback_attempts_is_enforced():
    pol = ControllerPolicy(max_fallback_attempts=1)
    run = ScriptedRun({"A-fp16-s2-r512", "A-fp16-s2-r384", "A-fp16-s2-r256"})
    with pytest.raises(ResourceError, match="exhausted"):
        run_with_fallback(controller(policy=pol), req("balanced"), mon(), run)
    assert len(run.calls) == 2


def test_timeout_fallback_needs_policy_opt_in_and_picks_a_faster_config():
    run = ScriptedRun({"A-fp16-s2-r512"}, exc=TimeoutError)
    with pytest.raises(TimeoutError):  # default policy: only OOM triggers fallback
        run_with_fallback(controller(), req("balanced"), mon(), run)
    pol = ControllerPolicy(fallback_on=("oom", "timeout"))
    run = ScriptedRun({"A-fp16-s2-r512"}, exc=TimeoutError)
    ex = run_with_fallback(controller(policy=pol), req("balanced"), mon(), run)
    first, second = (controller().profiles.get(i) for i in run.calls)
    assert second.latency_ms_median < first.latency_ms_median and ex.reason == "TIMEOUT_DURING_GENERATION"


def test_initial_plan_time_fallback_is_reported_without_any_failure():
    ex = run_with_fallback(controller(), req("balanced"), mon(3000), ScriptedRun())
    assert ex.fallback_used and ex.failures == [] and ex.reason == "RESOLUTION_REDUCED_FOR_RESOURCES"


def test_simulated_constrained_resources_via_capped_monitor():
    base = StaticMonitor(snap(12000.0))
    for cap, expect in ((12000, "A-fp16-s2-r512"), (3000, "A-fp16-s2-r384"), (2000, "A-fp16-s2-r256")):
        ex = run_with_fallback(controller(), req("balanced"), CappedMonitor(base, gpu_cap_mb=cap), ScriptedRun())
        assert ex.value == f"image:{expect}"
    with pytest.raises(ResourceError):
        run_with_fallback(controller(), req("balanced"), CappedMonitor(base, gpu_cap_mb=500), ScriptedRun())


def test_on_failure_hook_runs_between_attempts():
    hooks = []
    run_with_fallback(controller(), req("balanced"), mon(), ScriptedRun({"A-fp16-s2-r512"}), on_failure=hooks.append)
    assert len(hooks) == 1 and "out of memory" in str(hooks[0])


def test_chain_explanation_mentions_every_hop():
    run = ScriptedRun({"A-fp16-s2-r512", "A-fp16-s2-r384"})
    ex = run_with_fallback(controller(), req("balanced"), mon(), run)
    assert ex.explanation.count(" failed (out of memory)") == 2 and ex.explanation.count("SYNTHETIC") == 1


def test_adaptive_package_is_pure_python():
    code = ("import sys, ai_engine.adaptive; bad=[m for m in ('torch','diffusers','transformers','fastapi',"
            "'pydantic','backend') if m in sys.modules]; print(bad); sys.exit(1 if bad else 0)")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
