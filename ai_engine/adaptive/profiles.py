"""Benchmark profiles: the MEASURED facts the controller is allowed to reason from. Pure Python (no torch).

A profile is a JSON file (schema `adaptive_profile/1`). Each entry is one configuration that was actually run
(or failed) on one machine. The controller never extrapolates: a resolution/precision/steps combination that is
not in the profile does not exist for it.
"""
import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from ai_engine.optimization.config import OFFLOADS, PRECISIONS

SCHEMA = "adaptive_profile/1"
DEVICES = ("cuda", "cpu")
LOCATIONS = ("local", "remote")
STATUSES = ("ok", "oom", "error")
MEMORY_STATISTICS = ("max", "median")
RUNTIME_KEYS = ("model_id", "precision", "device", "attention_slicing", "vae_slicing", "offload")


class ProfileError(ValueError):
    """The profile file is malformed or internally inconsistent."""


def _num(name: str, v, allow_none=True):
    if v is None:
        if allow_none:
            return None
        raise ProfileError(f"{name} is required")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        raise ProfileError(f"{name} must be a finite number >= 0, got {v!r}")
    return float(v)


@dataclass(frozen=True)
class ProfileEntry:
    id: str
    model_id: str
    precision: str
    steps: int
    resolution: int
    device: str = "cuda"
    attention_slicing: bool = False
    vae_slicing: bool = False
    offload: str = "none"
    location: str = "local"  # "remote" = hybrid/cloud endpoint; only usable with explicit consent
    status: str = "ok"  # outcome of the benchmark: ok | oom | error (failed entries are known-bad, never selected)
    n_runs: int = 0
    latency_ms_median: Optional[float] = None
    latency_ms_p95: Optional[float] = None
    peak_gpu_mb_max: Optional[float] = None  # PyTorch peak ALLOCATED, worst run
    peak_gpu_mb_median: Optional[float] = None
    peak_ram_mb: Optional[float] = None  # process peak working set during the experiment
    clip_mean: Optional[float] = None  # optional; broad text-image alignment only
    source: str = ""  # where the numbers came from (experiment id / file)

    def __post_init__(self):
        if not self.id or not self.model_id:
            raise ProfileError("entry needs id and model_id")
        if self.precision not in PRECISIONS:
            raise ProfileError(f"{self.id}: precision must be one of {PRECISIONS}")
        if self.offload not in OFFLOADS:
            raise ProfileError(f"{self.id}: offload must be one of {OFFLOADS}")
        if self.device not in DEVICES or self.location not in LOCATIONS or self.status not in STATUSES:
            raise ProfileError(f"{self.id}: bad device/location/status")
        if not isinstance(self.steps, int) or isinstance(self.steps, bool) or self.steps < 1:
            raise ProfileError(f"{self.id}: steps must be an int >= 1")
        if not isinstance(self.resolution, int) or self.resolution % 8 or not 64 <= self.resolution <= 2048:
            raise ProfileError(f"{self.id}: resolution must be a multiple of 8")
        if not isinstance(self.n_runs, int) or self.n_runs < 0:
            raise ProfileError(f"{self.id}: n_runs must be an int >= 0")
        for f in ("latency_ms_median", "latency_ms_p95", "peak_gpu_mb_max", "peak_gpu_mb_median", "peak_ram_mb"):
            _num(f"{self.id}.{f}", getattr(self, f))
        if self.clip_mean is not None and (not isinstance(self.clip_mean, (int, float))
                                           or not math.isfinite(self.clip_mean)):
            raise ProfileError(f"{self.id}: clip_mean must be a finite number")

    @property
    def runtime(self) -> dict:
        """Settings fixed when the engine loads. Changing any of them needs a reload."""
        return {k: getattr(self, k) for k in RUNTIME_KEYS}

    def gpu_mb(self, statistic: str) -> Optional[float]:
        return self.peak_gpu_mb_max if statistic == "max" else self.peak_gpu_mb_median

    def config(self) -> dict:
        return {"id": self.id, "model_id": self.model_id, "precision": self.precision, "steps": self.steps,
                "resolution": self.resolution, "device": self.device, "location": self.location,
                "attention_slicing": self.attention_slicing, "vae_slicing": self.vae_slicing,
                "offload": self.offload}

    def measured(self) -> dict:
        return {"n_runs": self.n_runs, "latency_ms_median": self.latency_ms_median,
                "latency_ms_p95": self.latency_ms_p95, "peak_gpu_mb_max": self.peak_gpu_mb_max,
                "peak_gpu_mb_median": self.peak_gpu_mb_median, "peak_ram_mb": self.peak_ram_mb,
                "clip_mean": self.clip_mean}


@dataclass(frozen=True)
class ProfileSet:
    entries: tuple
    synthetic: bool  # True = invented test data, NOT measurements. Required field: no silent default.
    hardware: dict = field(default_factory=dict)  # gpu_name, gpu_total_vram_mb, ...
    model_revision: Optional[str] = None
    note: str = ""
    schema: str = SCHEMA

    def __post_init__(self):
        ids = [e.id for e in self.entries]
        if len(set(ids)) != len(ids):
            raise ProfileError("duplicate entry ids in profile")
        if not self.entries:
            raise ProfileError("profile has no entries")

    def to_dict(self) -> dict:
        return {"schema": self.schema, "synthetic": self.synthetic, "note": self.note, "hardware": self.hardware,
                "model_revision": self.model_revision, "entries": [asdict(e) for e in self.entries]}

    @property
    def profile_id(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]

    def get(self, entry_id: str) -> ProfileEntry:
        for e in self.entries:
            if e.id == entry_id:
                return e
        raise KeyError(entry_id)


def profile_set_from_dict(d: dict) -> ProfileSet:
    if not isinstance(d, dict) or d.get("schema") != SCHEMA:
        raise ProfileError(f"profile schema must be {SCHEMA!r}")
    if not isinstance(d.get("synthetic"), bool):
        raise ProfileError("profile must state 'synthetic': true|false explicitly")
    raw = d.get("entries")
    if not isinstance(raw, list):
        raise ProfileError("profile 'entries' must be a list")
    entries = []
    for r in raw:
        try:
            entries.append(ProfileEntry(**r))
        except TypeError as exc:  # unknown / missing keys
            raise ProfileError(f"bad entry {r.get('id', '?') if isinstance(r, dict) else r!r}: {exc}") from None
    return ProfileSet(entries=tuple(entries), synthetic=d["synthetic"], hardware=dict(d.get("hardware") or {}),
                      model_revision=d.get("model_revision"), note=str(d.get("note") or ""))


def load_profile_set(path) -> ProfileSet:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileError(f"cannot read profile {path}: {exc}") from None
    return profile_set_from_dict(data)


def save_profile_set(ps: ProfileSet, path) -> None:
    Path(path).write_text(json.dumps(ps.to_dict(), indent=1), encoding="utf-8")
