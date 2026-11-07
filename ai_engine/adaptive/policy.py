"""Controller policy: every tunable number lives here, in an external, loggable object. Pure Python.

THE DEFAULTS ARE PROVISIONAL AND UNCALIBRATED. `headroom_fraction` and the tolerances are starting points, not
facts about any GPU. Calibrate them against your own profile (docs/P6_ADAPTIVE.md section 6) and then set
`calibrated=true` in your policy file so decision logs say so.
"""
import json
import math
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

MODES = ("quick", "balanced", "best")
COMPLEXITY_LEVELS = ("simple", "moderate", "complex")
FALLBACK_CAUSES = ("oom", "timeout")
UNKNOWN_MEMORY = ("reject", "allow")
FALLBACK_STAGES = ("resolution", "precision", "steps", "model", "remote")


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ControllerPolicy:
    # Fraction of extra memory required on top of the measured peak (guards against run-to-run variation).
    headroom_fraction: float = 0.10
    memory_statistic: str = "max"  # which measured GPU peak to compare: max (worst run) | median
    # Scale-free quality guardrail: a candidate passes if quality >= best - tol * (best - worst) over the safe set.
    # tol 0 = only the best; tol 1 = anything. Latency then decides among passing candidates.
    quality_tolerance: dict = field(default_factory=lambda: {"quick": 0.8, "balanced": 0.4, "best": 0.0})
    # Multiplies the tolerance by prompt complexity. 1.0 everywhere = complexity has NO effect (no evidence yet).
    complexity_tolerance_scale: dict = field(
        default_factory=lambda: {"simple": 1.0, "moderate": 1.0, "complex": 1.0})
    unknown_memory: str = "reject"  # snapshot has no memory figure: reject (safe) | allow (logged as UNVERIFIED)
    require_ram_check: bool = False  # True: an entry/snapshot without RAM numbers is rejected
    fallback_on: tuple = ("oom",)  # failure causes that trigger a runtime fallback
    # Order in which a fallback may change things (docs/04 §4.10). "steps" is further gated by the quality
    # guardrail. A stage left out is disabled. Multi-parameter changes are always the very last resort.
    fallback_order: tuple = ("resolution", "precision", "steps", "model", "remote")
    max_fallback_attempts: int = 3
    calibrated: bool = False

    def __post_init__(self):
        if not (isinstance(self.headroom_fraction, (int, float)) and math.isfinite(self.headroom_fraction)
                and 0 <= self.headroom_fraction <= 1):
            raise PolicyError("headroom_fraction must be within [0, 1]")
        if self.memory_statistic not in ("max", "median"):
            raise PolicyError("memory_statistic must be 'max' or 'median'")
        if set(self.quality_tolerance) != set(MODES):
            raise PolicyError(f"quality_tolerance needs exactly the keys {MODES}")
        if set(self.complexity_tolerance_scale) != set(COMPLEXITY_LEVELS):
            raise PolicyError(f"complexity_tolerance_scale needs exactly the keys {COMPLEXITY_LEVELS}")
        for k, v in {**self.quality_tolerance}.items():
            if not (isinstance(v, (int, float)) and 0 <= v <= 1):
                raise PolicyError(f"quality_tolerance[{k}] must be within [0, 1]")
        for k, v in self.complexity_tolerance_scale.items():
            if not (isinstance(v, (int, float)) and math.isfinite(v) and v >= 0):
                raise PolicyError(f"complexity_tolerance_scale[{k}] must be >= 0")
        if self.unknown_memory not in UNKNOWN_MEMORY:
            raise PolicyError(f"unknown_memory must be one of {UNKNOWN_MEMORY}")
        if not set(self.fallback_on) <= set(FALLBACK_CAUSES):
            raise PolicyError(f"fallback_on must be a subset of {FALLBACK_CAUSES}")
        if (not set(self.fallback_order) <= set(FALLBACK_STAGES)
                or len(set(self.fallback_order)) != len(self.fallback_order)):
            raise PolicyError(f"fallback_order must be unique names from {FALLBACK_STAGES}")
        if not isinstance(self.max_fallback_attempts, int) or not 0 <= self.max_fallback_attempts <= 10:
            raise PolicyError("max_fallback_attempts must be an int within [0, 10]")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["fallback_on"] = list(self.fallback_on)
        d["fallback_order"] = list(self.fallback_order)
        return d

    def tolerance(self, mode: str, complexity_level) -> float:
        tol = self.quality_tolerance[mode]
        if complexity_level is not None:
            tol *= self.complexity_tolerance_scale[complexity_level]
        return min(1.0, max(0.0, tol))


def policy_from_dict(d: dict) -> ControllerPolicy:
    known = {f.name for f in fields(ControllerPolicy)}
    extra = set(d) - known
    if extra:
        raise PolicyError(f"unknown policy keys: {sorted(extra)}")
    d = dict(d)
    for k in ("fallback_on", "fallback_order"):
        if k in d:
            d[k] = tuple(d[k])
    return ControllerPolicy(**d)


def load_policy(path) -> ControllerPolicy:
    try:
        return policy_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot read policy {path}: {exc}") from None
