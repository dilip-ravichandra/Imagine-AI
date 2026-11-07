"""Resource snapshots and monitors. torch/psutil are imported lazily and every failure becomes `None`.

`gpu_budget_mb` = memory THIS server could use for one generation = free GPU memory + memory this process has
already reserved (its own cached blocks are reusable by it). That is what a measured peak must fit into.
"""
import importlib
from dataclasses import asdict, dataclass, replace
from typing import Optional

MB = 1048576


@dataclass(frozen=True)
class ResourceSnapshot:
    device: str = "cpu"  # cuda | cpu
    gpu_name: Optional[str] = None
    gpu_total_mb: Optional[float] = None
    gpu_budget_mb: Optional[float] = None
    ram_available_mb: Optional[float] = None
    source: str = "unknown"  # system | static | simulated

    def to_dict(self) -> dict:
        return asdict(self)


class ResourceMonitor:
    def snapshot(self) -> ResourceSnapshot:  # pragma: no cover - interface
        raise NotImplementedError


class StaticMonitor(ResourceMonitor):
    """Always returns the given snapshot (tests, demos, or a fixed deployment budget)."""

    def __init__(self, snap: ResourceSnapshot):
        self._snap = snap

    def snapshot(self) -> ResourceSnapshot:
        return self._snap


class CappedMonitor(ResourceMonitor):
    """Simulated constrained resources: never reports more than the caps. Wraps any monitor."""

    def __init__(self, inner: ResourceMonitor, gpu_cap_mb: Optional[float] = None,
                 ram_cap_mb: Optional[float] = None):
        self.inner, self.gpu_cap_mb, self.ram_cap_mb = inner, gpu_cap_mb, ram_cap_mb

    @staticmethod
    def _cap(value, cap):
        if cap is None:
            return value
        return cap if value is None else min(value, cap)

    def snapshot(self) -> ResourceSnapshot:
        s = self.inner.snapshot()
        return replace(s, gpu_budget_mb=self._cap(s.gpu_budget_mb, self.gpu_cap_mb),
                       ram_available_mb=self._cap(s.ram_available_mb, self.ram_cap_mb),
                       source=f"simulated({s.source})")


class SystemMonitor(ResourceMonitor):
    """Reads live numbers from torch.cuda and psutil. Missing library/driver -> the field is None, never a crash."""

    def __init__(self, torch_module=None, psutil_module=None):
        self._torch, self._psutil = torch_module, psutil_module

    def _mod(self, attr: str, name: str):
        cached = getattr(self, attr)
        if cached is not None:
            return cached
        try:
            return importlib.import_module(name)
        except Exception:  # noqa: BLE001
            return None

    def snapshot(self) -> ResourceSnapshot:
        device, name, total, budget = "cpu", None, None, None
        torch = self._mod("_torch", "torch")
        try:
            if torch is not None and torch.cuda.is_available():
                device = "cuda"
                free, total_b = torch.cuda.mem_get_info()
                total, budget = total_b / MB, (free + torch.cuda.memory_reserved()) / MB
                name = torch.cuda.get_device_name(0)
        except Exception:  # noqa: BLE001 - driver hiccup: keep what we have, mark the rest unknown
            budget = None
        ram = None
        ps = self._mod("_psutil", "psutil")
        try:
            if ps is not None:
                ram = ps.virtual_memory().available / MB
        except Exception:  # noqa: BLE001
            ram = None
        return ResourceSnapshot(device=device, gpu_name=name, gpu_total_mb=total, gpu_budget_mb=budget,
                                ram_available_mb=ram, source="system")
