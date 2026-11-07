"""Resource-Adaptive Quality Controller. Deterministic, explainable, profile-driven. Pure Python (no torch).

decide():   (request, resource snapshot, profile, policy) -> one measured configuration + a structured log.
fallback(): after a runtime failure (OOM/timeout) -> the next proven configuration, in the order docs/04 §4.10 lists.
Both raise ResourceError (with the full evaluation log) when nothing safe remains. No randomness, no clock,
no network: the same inputs always give the same decision (checked by `input_hash` in the log).
"""
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from .policy import COMPLEXITY_LEVELS, MODES, ControllerPolicy
from .profiles import RUNTIME_KEYS, ProfileEntry, ProfileSet
from .resources import ResourceSnapshot

log = logging.getLogger("imagineai.adaptive")
DECISION_SCHEMA = "adaptive_decision/1"
EPS = 1e-9
PROXY_BASIS = "steps_proxy_UNMEASURED"
CHANGE_FIELDS = ("resolution", "precision", "steps", "model_id", "location", "device",
                 "attention_slicing", "vae_slicing", "offload")


class ResourceError(Exception):
    """No safe, proven configuration exists. `log` holds every candidate and why it was rejected."""
    code = "NO_SAFE_CONFIGURATION"

    def __init__(self, message: str, decision_log: dict, suggested_action: str):
        super().__init__(message)
        self.message, self.log, self.suggested_action = message, decision_log, suggested_action


@dataclass(frozen=True)
class ControllerRequest:
    quality_mode: str
    resolution: int
    complexity_level: Optional[str] = None  # from P2 analysis; scaled by policy (default: no effect)
    locked_runtime: Optional[dict] = None  # settings fixed by the already-loaded engine (subset of RUNTIME_KEYS)
    allow_remote: bool = False  # only True when the user has been told and agreed to hybrid/cloud processing

    def __post_init__(self):
        if self.quality_mode not in MODES:
            raise ValueError(f"quality_mode must be one of {MODES}")
        if self.complexity_level is not None and self.complexity_level not in COMPLEXITY_LEVELS:
            raise ValueError(f"complexity_level must be one of {COMPLEXITY_LEVELS}")
        if not isinstance(self.resolution, int) or self.resolution <= 0:
            raise ValueError("resolution must be a positive int")
        if self.locked_runtime and set(self.locked_runtime) - set(RUNTIME_KEYS):
            raise ValueError(f"locked_runtime keys must be within {RUNTIME_KEYS}")

    def to_dict(self) -> dict:
        return {"quality_mode": self.quality_mode, "resolution": self.resolution,
                "complexity_level": self.complexity_level, "locked_runtime": self.locked_runtime,
                "allow_remote": self.allow_remote}


@dataclass(frozen=True)
class Decision:
    selected: ProfileEntry
    fallback_used: bool
    reason: Optional[str]  # stable code, None when no fallback
    explanation: str  # human readable, safe to show to users
    log: dict  # structured; JSON-serialisable

    def to_resource_decision(self) -> dict:
        """Shape of the frozen API's `resource_decision` object."""
        return {"fallback_used": self.fallback_used, "reason": self.reason, "explanation": self.explanation}


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def _quality(entries: Sequence[ProfileEntry]) -> tuple:
    """(basis, {id: value}). Measured CLIP if EVERY entry has it, otherwise the unmeasured steps proxy."""
    if entries and all(e.clip_mean is not None for e in entries):
        return "clip_mean", {e.id: e.clip_mean for e in entries}
    return PROXY_BASIS, {e.id: float(e.steps) for e in entries}


def _changes(a: ProfileEntry, b: ProfileEntry) -> list:
    return [f for f in CHANGE_FIELDS if getattr(a, f) != getattr(b, f)]


_FIELD_RUNG = {"resolution": "resolution", "precision": "precision", "attention_slicing": "precision",
               "vae_slicing": "precision", "offload": "precision", "device": "precision", "steps": "steps",
               "model_id": "model", "location": "remote"}
STAGE_LABEL = {"resolution": "lower resolution", "precision": "different precision/memory option",
               "steps": "fewer steps", "model": "smaller model", "remote": "remote backend (consented)",
               "same": "equivalent configuration"}
STAGE_REASON = {"resolution": "RESOLUTION_REDUCED_FOR_RESOURCES", "precision": "PRECISION_CHANGED_FOR_RESOURCES",
                "steps": "STEPS_REDUCED_FOR_RESOURCES", "model": "MODEL_CHANGED_FOR_RESOURCES",
                "remote": "REMOTE_BACKEND_FOR_RESOURCES", "same": "CONFIG_CHANGED_FOR_RESOURCES"}


def _rungs(changes: list) -> set:
    return {_FIELD_RUNG[f] for f in changes}


def _stage_name(changes: list, order: Sequence[str] = ("resolution", "precision", "steps", "model", "remote")) -> str:
    """Deepest ladder rung a candidate touches (docs/04 §4.10): a candidate that changes resolution AND
    precision sits on the 'precision' rung. Names not in `order` rank deepest."""
    rungs = _rungs(changes)
    if not rungs:
        return "same"
    pos = lambda r: order.index(r) if r in order else len(order)  # noqa: E731
    return max(rungs, key=pos)


class AdaptiveController:
    def __init__(self, profiles: ProfileSet, policy: Optional[ControllerPolicy] = None,
                 log_sink: Optional[Callable[[dict], None]] = None):
        self.profiles = profiles
        self.policy = policy or ControllerPolicy()
        self.log_sink = log_sink

    # ------------------------------------------------------------------ screening
    def _screen(self, e: ProfileEntry, req: ControllerRequest, snap: ResourceSnapshot, attempted) -> Optional[tuple]:
        """Filters that do not depend on how much memory is free. Returns (code, detail) or None if it passes."""
        if e.id in attempted:
            return "ALREADY_ATTEMPTED", "failed earlier in this request"
        if e.status != "ok":
            return "BENCHMARK_FAILED", f"benchmark status was {e.status!r}: known not to work on the profiled machine"
        if e.location == "remote" and not req.allow_remote:
            return "REMOTE_NOT_ALLOWED", "remote processing needs explicit user disclosure and consent"
        if e.resolution > req.resolution:
            return "ABOVE_REQUESTED_RESOLUTION", f"{e.resolution}px > requested {req.resolution}px"
        if e.latency_ms_median is None:
            return "MISSING_LATENCY_METRIC", "no measured latency, cannot rank"
        if req.locked_runtime:
            for k, want in req.locked_runtime.items():
                if getattr(e, k) != want:
                    return "RUNTIME_LOCKED", f"needs {k}={getattr(e, k)!r} but the loaded engine has {want!r} (reload required)"
        if e.location == "local" and e.device == "cuda" and snap.device != "cuda":
            return "DEVICE_MISMATCH", "needs CUDA but this machine reports no usable GPU"
        return None

    def _resource_check(self, e: ProfileEntry, snap: ResourceSnapshot) -> tuple:
        """(rejection or None, notes). Compares MEASURED peaks (+ headroom) with the live budget."""
        pol, notes = self.policy, []
        if e.location == "remote":
            return None, notes
        head = 1.0 + pol.headroom_fraction
        if e.device == "cuda":
            mem = e.gpu_mb(pol.memory_statistic)
            if mem is None:
                return ("MISSING_MEMORY_METRIC", "no measured GPU peak for this configuration"), notes
            if snap.gpu_budget_mb is None:
                if pol.unknown_memory == "reject":
                    return ("UNKNOWN_BUDGET", "available GPU memory could not be read"), notes
                notes.append("UNVERIFIED_GPU_BUDGET")
            elif mem * head > snap.gpu_budget_mb + EPS:
                return ("EXCEEDS_GPU_BUDGET",
                        f"needs {mem * head:.0f} MB (measured {pol.memory_statistic} peak {mem:.0f} MB "
                        f"+ {pol.headroom_fraction:.0%} headroom) but only {snap.gpu_budget_mb:.0f} MB available"), notes
        # RAM: peak working set includes weights that may already be resident, so for GPU entries this check
        # is opt-in (policy.require_ram_check); for CPU-only entries it always applies.
        if e.device == "cpu" or pol.require_ram_check:
            if e.peak_ram_mb is None:
                return ("MISSING_MEMORY_METRIC", "no measured process RAM peak"), notes
            if snap.ram_available_mb is None:
                if pol.unknown_memory == "reject":
                    return ("UNKNOWN_BUDGET", "available RAM could not be read"), notes
                notes.append("UNVERIFIED_RAM_BUDGET")
            elif e.peak_ram_mb * head > snap.ram_available_mb + EPS:
                return ("EXCEEDS_RAM_BUDGET", f"needs {e.peak_ram_mb * head:.0f} MB RAM but only "
                                              f"{snap.ram_available_mb:.0f} MB available"), notes
        return None, notes

    # ------------------------------------------------------------------ ranking
    def _rank(self, pool: Sequence[ProfileEntry], tol: float) -> tuple:
        """Scale-free guardrail, then lowest measured latency. Returns (winner, guardrail_info)."""
        basis, q = _quality(pool)
        best, worst = max(q.values()), min(q.values())
        thr = best - tol * (best - worst)
        passing = [e for e in pool if q[e.id] >= thr - EPS]
        mem = lambda e: (e.gpu_mb(self.policy.memory_statistic) or 0.0) if e.location == "local" else 0.0  # noqa: E731
        winner = min(passing, key=lambda e: (e.latency_ms_median, -q[e.id], mem(e), e.id))
        info = {"basis": basis, "tolerance": tol, "best": best, "worst": worst, "threshold": thr,
                "n_pool": len(pool), "n_passing": len(passing), "quality_of_selected": q[winner.id]}
        return winner, info

    # ------------------------------------------------------------------ fallback ladder (shared)
    def _ladder_pick(self, failed: ProfileEntry, pool: Sequence[ProfileEntry], tol: float, evals: dict,
                     require_improvement: bool, cause: str) -> Optional[tuple]:
        """Closest safe configuration to `failed`, walking the policy's fallback order. Mutates `evals`
        with every rejection. Returns (chosen, basis, threshold) or None. Never asks for more compute."""
        pol, cands = self.policy, []
        for e in pool:
            rej = None
            ch = _changes(failed, e)
            if e.resolution > failed.resolution or (e.location == "local" and e.steps > failed.steps):
                rej = ("HEAVIER_THAN_PREFERRED", "a fallback never raises resolution or local steps")
            elif require_improvement and not self._improves(e, failed, cause):
                rej = ("NO_IMPROVEMENT", "does not reduce " + ("memory" if cause == "oom" else "latency")
                       + " relative to the failed configuration (or the metric is missing)")
            elif not _rungs(ch) <= set(pol.fallback_order):
                off = sorted(_rungs(ch) - set(pol.fallback_order))
                rej = ("STAGE_DISABLED_BY_POLICY", f"fallback stage(s) {off} not in policy.fallback_order")
            if rej:
                evals[e.id] = {"verdict": "rejected", "code": rej[0], "detail": rej[1]}
            else:
                cands.append(e)
        if not cands:
            return None
        basis, q = _quality([*cands, failed])
        best, worst = max(q.values()), min(q.values())
        thr = best - tol * (best - worst)
        kept = []
        for e in cands:
            if "steps" in _rungs(_changes(failed, e)) and q[e.id] < thr - EPS:
                evals[e.id] = {"verdict": "rejected", "code": "GUARDRAIL_BLOCKS_STEP_REDUCTION",
                               "detail": f"{basis} {q[e.id]:g} is below the guardrail {thr:g}"}
            else:
                kept.append(e)
        if not kept:
            return None
        order = list(pol.fallback_order)
        rank = lambda e: order.index(_stage_name(_changes(failed, e), order)) if _changes(failed, e) else len(order)  # noqa: E731
        mem = lambda e: (e.gpu_mb(pol.memory_statistic) or 0.0) if e.location == "local" else 0.0  # noqa: E731
        chosen = min(kept, key=lambda e: (rank(e), len(_changes(failed, e)), -q[e.id], e.latency_ms_median,
                                          mem(e), e.id))
        return chosen, basis, thr

    def _change_text(self, failed: ProfileEntry, chosen: ProfileEntry) -> str:
        ch = _changes(failed, chosen)
        return (f"{STAGE_LABEL[_stage_name(ch, self.policy.fallback_order)]}: "
                + ", ".join(f"{f} {getattr(failed, f)} -> {getattr(chosen, f)}" for f in ch))

    def _no_fit(self, lg: dict, evals: dict, request: ControllerRequest, msg: str) -> ResourceError:
        lg["outcome"] = "no_safe_configuration"
        blocked = sum(1 for v in evals.values() if v["code"] == "GUARDRAIL_BLOCKS_STEP_REDUCTION")
        action = "Retry later, choose a smaller resolution or the quick quality mode."
        if blocked:
            msg += (f" {blocked} safe configuration(s) were rejected because they would lower quality below "
                    f"the {request.quality_mode} guardrail.")
            action = "Choose Quick or Balanced mode, a smaller resolution, or free GPU memory."
        self._emit(lg)
        return ResourceError(msg, lg, action)

    # ------------------------------------------------------------------ decide
    def decide(self, request: ControllerRequest, snapshot: ResourceSnapshot) -> Decision:
        """Plan-time choice. 1) rank the proven configs by mode as if resources were unlimited -> `ideal`.
        2) if ideal is safe, use it. 3) otherwise walk the fallback ladder to the closest safe config."""
        pol = self.policy
        evals, notes_by_id, screened, safe = {}, {}, [], []
        for e in self.profiles.entries:
            rej = self._screen(e, request, snapshot, ())
            if rej is None:
                screened.append(e)
            else:
                evals[e.id] = {"verdict": "rejected", "code": rej[0], "detail": rej[1]}
        for e in screened:
            rej, notes = self._resource_check(e, snapshot)
            notes_by_id[e.id] = notes
            if rej is None:
                safe.append(e)
            else:
                evals[e.id] = {"verdict": "rejected", "code": rej[0], "detail": rej[1]}

        tol = pol.tolerance(request.quality_mode, request.complexity_level)
        lg = self._base_log("initial", request, snapshot, (), None, evals, tol)
        if not safe:
            raise self._no_fit(lg, evals, request, "No profiled configuration fits the available resources.")

        # The preferred config is always LOCAL when one exists: remote is a consented last resort, never a first pick.
        base_pool = [e for e in screened if e.location == "local"] or screened
        ideal_res = max(e.resolution for e in base_pool)  # <= requested; highest profiled resolution
        ideal, guard = self._rank([e for e in base_pool if e.resolution == ideal_res], tol)
        requested_profiled = any(e.resolution == request.resolution for e in screened)
        safe_ids = {e.id for e in safe}
        resource_reason, why = None, ""
        selected = ideal
        if ideal.id not in safe_ids:
            why = evals[ideal.id]["detail"]
            pick = self._ladder_pick(ideal, [e for e in safe], tol, evals, False, "oom")
            if pick is None:
                lg["ideal_id"] = ideal.id
                raise self._no_fit(lg, evals, request,
                                   "The preferred configuration is unsafe and no allowed fallback is safe.")
            selected, _basis, _thr = pick
            resource_reason = STAGE_REASON[_stage_name(_changes(ideal, selected), pol.fallback_order)]
        for e in safe:  # keep a more specific ladder rejection if one was recorded
            if e.id not in evals:
                evals[e.id] = {"verdict": "accepted", "code": "SAFE", "detail": "fits the resource budget",
                               "notes": notes_by_id.get(e.id, [])}
        evals[selected.id] = {"verdict": "selected", "code": "SAFE", "detail": "selected",
                              "notes": notes_by_id.get(selected.id, [])}

        reason = resource_reason or ("RESOLUTION_NOT_PROFILED" if selected.resolution != request.resolution
                                     else None)
        fallback_used = reason is not None
        expl = self._explain(request, ideal, guard, tol)
        if resource_reason:
            expl += (f" Fallback: preferred {ideal.id} is not safe ({why}); using {selected.id} "
                     f"({self._change_text(ideal, selected)}).")
        if not requested_profiled:
            expl += f" No measured profile exists at {request.resolution}px; {ideal_res}px is the closest profiled size."
        if self.profiles.synthetic:
            expl += " [Profile is SYNTHETIC test data, not measurements.]"
        lg.update({"ideal_id": ideal.id, "guardrail": guard, "selected": self._selected_block(selected),
                   "fallback_used": fallback_used, "reason": reason, "explanation": expl, "outcome": "selected"})
        lg["input_hash"] = self._input_hash(lg)
        self._emit(lg)
        return Decision(selected, fallback_used, reason, expl, lg)

    # ------------------------------------------------------------------ runtime fallback
    def fallback(self, previous: Decision, cause: str, request: ControllerRequest, snapshot: ResourceSnapshot,
                 attempted: Sequence[str]) -> Decision:
        """Next proven configuration after `previous.selected` failed with `cause` ('oom' | 'timeout')."""
        if cause not in ("oom", "timeout"):
            raise ValueError("cause must be 'oom' or 'timeout'")
        failed, pol = previous.selected, self.policy
        attempted = tuple(dict.fromkeys([*attempted, failed.id]))
        evals, pool = {}, []
        for e in self.profiles.entries:
            rej = self._screen(e, request, snapshot, attempted)
            if rej is None:
                rej, _ = self._resource_check(e, snapshot)
            if rej is None:
                pool.append(e)
            else:
                evals[e.id] = {"verdict": "rejected", "code": rej[0], "detail": rej[1]}
        tol = pol.tolerance(request.quality_mode, request.complexity_level)
        lg = self._base_log("fallback", request, snapshot, attempted, (failed.id, cause), evals, tol)
        pick = self._ladder_pick(failed, pool, tol, evals, True, cause)
        if pick is None:
            raise self._no_fit(lg, evals, request, "No remaining configuration is safe after the failure.")
        chosen, basis, thr = pick
        for e in pool:
            evals.setdefault(e.id, {"verdict": "accepted", "code": "SAFE_FALLBACK_CANDIDATE",
                                    "detail": "proven and safe"})
        evals[chosen.id] = {"verdict": "selected", "code": "SAFE_FALLBACK_CANDIDATE", "detail": "selected"}
        label = "OOM" if cause == "oom" else "TIMEOUT"
        expl = (f"{failed.id} failed ({'out of memory' if cause == 'oom' else 'timeout'}); switched to {chosen.id} "
                f"({self._change_text(failed, chosen)}).")
        if self.profiles.synthetic:
            expl += " [Profile is SYNTHETIC test data, not measurements.]"
        ch = _changes(failed, chosen)
        lg.update({"ideal_id": previous.log.get("ideal_id"), "guardrail": {"basis": basis, "tolerance": tol,
                                                                           "threshold": thr},
                   "selected": self._selected_block(chosen), "fallback_used": True,
                   "reason": f"{label}_DURING_GENERATION", "explanation": expl, "outcome": "selected",
                   "changed_from_failed": ch, "ladder_stage": _stage_name(ch, pol.fallback_order)})
        lg["input_hash"] = self._input_hash(lg)
        self._emit(lg)
        return Decision(chosen, True, lg["reason"], expl, lg)

    def _improves(self, cand: ProfileEntry, failed: ProfileEntry, cause: str) -> bool:
        if cause == "timeout":
            return cand.latency_ms_median is not None and failed.latency_ms_median is not None \
                and cand.latency_ms_median < failed.latency_ms_median - EPS
        stat = self.policy.memory_statistic

        def footprint(e: ProfileEntry):
            if e.location == "remote":
                return 0.0
            if failed.device == "cpu":  # the failure was RAM pressure
                return e.peak_ram_mb
            return 0.0 if e.device == "cpu" else e.gpu_mb(stat)  # failure was VRAM pressure

        a, b = footprint(cand), footprint(failed)
        return a is not None and b is not None and a < b - EPS

    # ------------------------------------------------------------------ logging helpers
    def _explain(self, req, sel, guard, tol) -> str:
        head = (f"{req.quality_mode.capitalize()} mode -> {sel.id}: {sel.precision}, {sel.steps} step(s), "
                f"{sel.resolution}x{sel.resolution}.")
        if tol == 0:
            why = (f"Best {guard['basis']} among {guard['n_pool']} profiled configuration(s) at "
                   f"{sel.resolution}px")
        else:
            why = (f"Lowest measured median latency ({sel.latency_ms_median:.0f} ms) among {guard['n_passing']} of "
                   f"{guard['n_pool']} profiled configuration(s) passing the quality guardrail "
                   f"({guard['basis']} >= {guard['threshold']:.3g})")
        if guard["basis"] == PROXY_BASIS:
            why += "; quality is an UNMEASURED proxy (steps), no quality metric in the profile"
        return f"{head} {why}."

    @staticmethod
    def _selected_block(e: ProfileEntry) -> dict:
        return {**e.config(), "expected": e.measured(), "source": e.source}

    def _base_log(self, kind, req, snap, attempted, failure, evals, tol) -> dict:
        p = self.profiles
        return {"schema": DECISION_SCHEMA, "kind": kind,
                "inputs": {"request": req.to_dict(), "snapshot": snap.to_dict(),
                           "profile": {"id": p.profile_id, "synthetic": p.synthetic, "hardware": p.hardware,
                                       "model_revision": p.model_revision},
                           "policy": self.policy.to_dict(), "effective_tolerance": tol,
                           "attempted": list(attempted),
                           "failure": None if failure is None else {"entry": failure[0], "cause": failure[1]}},
                "evaluations": evals}

    @staticmethod
    def _input_hash(lg: dict) -> str:
        return _hash(lg["inputs"])

    def _emit(self, lg: dict) -> None:
        lg.setdefault("input_hash", self._input_hash(lg))
        log.info("adaptive_decision %s", json.dumps(lg, sort_keys=True, default=str))
        if self.log_sink is not None:
            self.log_sink(lg)
