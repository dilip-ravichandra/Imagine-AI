"""Runs a generation under the controller and applies the fallback sequence on OOM. Pure Python (no torch).

`run(entry)` is supplied by the caller (it calls the real engine). Only failures classified as resource
failures trigger a fallback; every other exception propagates untouched so real bugs are never masked.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .controller import AdaptiveController, ControllerRequest, Decision, ResourceError
from .resources import ResourceMonitor


def classify_failure(exc: BaseException) -> Optional[str]:
    """'oom' | 'timeout' | None (not a resource failure -> do not fall back).

    Matches the engine's mapped ServiceError (503 RESOURCE_EXHAUSTED = out of memory; the 429 'busy' error is
    deliberately NOT an OOM), raw CUDA/torch OOM errors, and TimeoutError. Duck-typed: no backend/torch import.
    """
    if isinstance(exc, TimeoutError):
        return "timeout"
    if getattr(exc, "code", None) == "RESOURCE_EXHAUSTED":
        return "oom" if getattr(exc, "status", None) == 503 else None
    if type(exc).__name__ == "OutOfMemoryError":
        return "oom"
    if isinstance(exc, RuntimeError) and "out of memory" in str(exc).lower():
        return "oom"
    return None


_SYNTH_TAG = " [Profile is SYNTHETIC test data, not measurements.]"


def _chain_explanation(decisions: list) -> str:
    """One readable sentence chain: the first choice, then every runtime fallback hop."""
    if len(decisions) == 1:
        return decisions[0].explanation
    parts = [d.explanation.replace(_SYNTH_TAG, "") for d in decisions]
    tag = _SYNTH_TAG if decisions[-1].explanation.endswith(_SYNTH_TAG) else ""
    return " Then: ".join(parts) + tag


@dataclass
class ExecutionResult:
    value: Any
    decision: Decision  # the configuration that finally produced `value`
    fallback_used: bool
    reason: Optional[str]
    explanation: str
    failures: list = field(default_factory=list)  # [{"entry": id, "cause": "oom"}]
    decisions: list = field(default_factory=list)  # every Decision, in order

    def to_resource_decision(self) -> dict:
        return {"fallback_used": self.fallback_used, "reason": self.reason, "explanation": self.explanation}


def run_with_fallback(controller: AdaptiveController, request: ControllerRequest, monitor: ResourceMonitor,
                      run: Callable, on_failure: Optional[Callable[[BaseException], None]] = None) -> ExecutionResult:
    decision = controller.decide(request, monitor.snapshot())
    decisions, failures, attempted = [decision], [], []
    while True:
        try:
            value = run(decision.selected)
        except Exception as exc:  # noqa: BLE001
            cause = classify_failure(exc)
            if cause is None or cause not in controller.policy.fallback_on:
                raise
            failures.append({"entry": decision.selected.id, "cause": cause})
            if on_failure is not None:
                on_failure(exc)
            if len(failures) > controller.policy.max_fallback_attempts:
                last = decisions[-1].log
                raise ResourceError("Fallback attempts exhausted.", last,
                                    "Retry later, choose a smaller resolution or the quick quality mode.") from None
            attempted.append(decision.selected.id)
            try:
                decision = controller.fallback(decision, cause, request, monitor.snapshot(), attempted)
            except ResourceError:
                raise
            decisions.append(decision)
            continue
        first, last = decisions[0], decisions[-1]
        used = bool(failures) or first.fallback_used
        reason = last.reason if failures else first.reason
        return ExecutionResult(value, last, used, reason, _chain_explanation(decisions), failures, decisions)
