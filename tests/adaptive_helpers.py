"""Shared helpers for the P6 tests. The fixture profile is SYNTHETIC (invented numbers); see its `note`."""
import dataclasses
import json
import pathlib

from ai_engine.adaptive import (AdaptiveController, ControllerPolicy, ControllerRequest, ProfileSet,
                                ResourceSnapshot, load_profile_set)

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "adaptive_profile_synthetic.json"


def profile() -> ProfileSet:
    return load_profile_set(FIXTURE)


def variant(ps: ProfileSet = None, **changes_by_id) -> ProfileSet:
    """Copy of the profile with entries modified: variant(ps, **{"A-fp16-s2-r512": {"peak_gpu_mb_max": None}}).
    Use id=None to drop an entry. Keys with '__' stand for '-' to keep kwargs legal: use dict unpacking instead."""
    ps = ps or profile()
    out = []
    for e in ps.entries:
        ch = changes_by_id.get(e.id, {})
        if ch is None:
            continue
        out.append(dataclasses.replace(e, **ch))
    return dataclasses.replace(ps, entries=tuple(out))


def all_entries(**fields) -> dict:
    return {e.id: dict(fields) for e in profile().entries}


def snap(budget=12000.0, device="cuda", ram=32000.0, **kw) -> ResourceSnapshot:
    return ResourceSnapshot(device=device, gpu_name="SYNTHETIC GPU", gpu_total_mb=8000.0, gpu_budget_mb=budget,
                            ram_available_mb=ram, source="static", **kw)


def req(mode="balanced", res=512, **kw) -> ControllerRequest:
    return ControllerRequest(mode, res, **kw)


def controller(ps=None, policy=None, sink=None) -> AdaptiveController:
    return AdaptiveController(ps or profile(), policy or ControllerPolicy(), log_sink=sink)


def jsonable(d) -> str:
    return json.dumps(d, sort_keys=True)
