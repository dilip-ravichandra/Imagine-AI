"""P6 policy validation and resource monitors (all with fakes; no torch, no GPU)."""
import json

import pytest

from ai_engine.adaptive import (CappedMonitor, ControllerPolicy, PolicyError, ResourceSnapshot, StaticMonitor,
                                SystemMonitor, load_policy, policy_from_dict)


# ---- policy ----------------------------------------------------------------------------------------------------
def test_default_policy_is_uncalibrated_and_complexity_neutral():
    p = ControllerPolicy()
    assert p.calibrated is False
    for m in ("quick", "balanced", "best"):
        assert p.tolerance(m, None) == p.tolerance(m, "complex") == p.tolerance(m, "simple")


def test_policy_roundtrip_and_unknown_key(tmp_path):
    p = ControllerPolicy(headroom_fraction=0.2, fallback_on=("oom", "timeout"), calibrated=True)
    path = tmp_path / "pol.json"
    path.write_text(json.dumps(p.to_dict()))
    assert load_policy(path) == p
    with pytest.raises(PolicyError, match="unknown"):
        policy_from_dict({"headroom": 0.1})
    with pytest.raises(PolicyError):
        load_policy(tmp_path / "nope.json")


@pytest.mark.parametrize("bad", [
    dict(headroom_fraction=-0.1), dict(headroom_fraction=1.5), dict(memory_statistic="mean"),
    dict(quality_tolerance={"quick": 0.5}), dict(quality_tolerance={"quick": 2, "balanced": 0, "best": 0}),
    dict(unknown_memory="maybe"), dict(fallback_on=("crash",)), dict(fallback_order=("resolution", "resolution")),
    dict(fallback_order=("warp",)), dict(max_fallback_attempts=-1),
    dict(complexity_tolerance_scale={"simple": 1.0}),
])
def test_policy_validation_rejects(bad):
    with pytest.raises(PolicyError):
        ControllerPolicy(**bad)


def test_complexity_scale_applies_and_clamps():
    p = ControllerPolicy(complexity_tolerance_scale={"simple": 1.0, "moderate": 1.0, "complex": 0.0})
    assert p.tolerance("quick", "complex") == 0.0
    big = ControllerPolicy(complexity_tolerance_scale={"simple": 5.0, "moderate": 1.0, "complex": 1.0})
    assert big.tolerance("quick", "simple") == 1.0


# ---- monitors --------------------------------------------------------------------------------------------------
class _Cuda:
    def __init__(self, avail=True, free=2 * 1048576 * 1000, total=8 * 1048576 * 1000, reserved=1048576 * 500,
                 boom=False):
        self.avail, self.free, self.total, self.reserved, self.boom = avail, free, total, reserved, boom

    def is_available(self): return self.avail
    def mem_get_info(self):
        if self.boom:
            raise RuntimeError("driver error")
        return self.free, self.total
    def memory_reserved(self): return self.reserved
    def get_device_name(self, i): return "FAKE GPU"


class _Torch:
    def __init__(self, **kw): self.cuda = _Cuda(**kw)


class _PsUtil:
    class _VM:
        available = 4 * 1048576 * 1000
    def virtual_memory(self): return self._VM()


def test_system_monitor_budget_is_free_plus_own_reserved():
    s = SystemMonitor(_Torch(), _PsUtil()).snapshot()
    assert s.device == "cuda" and s.gpu_name == "FAKE GPU" and s.source == "system"
    assert s.gpu_budget_mb == 2000 + 500 and s.gpu_total_mb == 8000 and s.ram_available_mb == 4000


def test_system_monitor_degrades_to_none_not_crash():
    no_gpu = SystemMonitor(_Torch(avail=False), _PsUtil()).snapshot()
    assert no_gpu.device == "cpu" and no_gpu.gpu_budget_mb is None and no_gpu.ram_available_mb == 4000
    broken = SystemMonitor(_Torch(boom=True), _PsUtil()).snapshot()
    assert broken.gpu_budget_mb is None  # unknown, never a made-up number

    class _BadPs:
        def virtual_memory(self): raise OSError("x")
    assert SystemMonitor(_Torch(), _BadPs()).snapshot().ram_available_mb is None


def test_capped_monitor_only_lowers():
    base = StaticMonitor(ResourceSnapshot(device="cuda", gpu_budget_mb=5000.0, ram_available_mb=9000.0, source="s"))
    s = CappedMonitor(base, gpu_cap_mb=2000, ram_cap_mb=10000).snapshot()
    assert s.gpu_budget_mb == 2000 and s.ram_available_mb == 9000 and s.source == "simulated(s)"
    unknown = StaticMonitor(ResourceSnapshot(device="cuda"))
    assert CappedMonitor(unknown, gpu_cap_mb=1500).snapshot().gpu_budget_mb == 1500
    assert CappedMonitor(unknown).snapshot().gpu_budget_mb is None
