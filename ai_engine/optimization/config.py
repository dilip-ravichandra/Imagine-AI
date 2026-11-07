"""One optimization configuration = one point in the P4 experiment grid. Pure Python (no torch)."""
from dataclasses import dataclass, fields

PRECISIONS = ("fp32", "fp16", "bf16")
OFFLOADS = ("none", "model", "sequential")
MAX_TURBO_STEPS = 4  # SD-Turbo model card: 1-4 steps


class ConfigurationError(ValueError):
    """Invalid or unsupported optimization setting. Message is for logs, never for API clients."""


@dataclass(frozen=True)
class OptimizationConfig:
    precision: str = "fp32"
    steps: int = 4
    resolution: int = 512
    attention_slicing: bool = False
    vae_slicing: bool = False
    offload: str = "none"  # none | model (enable_model_cpu_offload) | sequential

    def __post_init__(self):
        if self.precision not in PRECISIONS:
            raise ConfigurationError(f"precision must be one of {PRECISIONS}, got {self.precision!r}")
        if self.offload not in OFFLOADS:
            raise ConfigurationError(f"offload must be one of {OFFLOADS}, got {self.offload!r}")
        if not 1 <= self.steps <= MAX_TURBO_STEPS:
            raise ConfigurationError(f"steps must be 1..{MAX_TURBO_STEPS} for SD-Turbo, got {self.steps}")
        if self.resolution % 8 or not 256 <= self.resolution <= 1024:
            raise ConfigurationError("resolution must be a multiple of 8 within 256-1024")

    def changed_fields(self, other: "OptimizationConfig") -> tuple[str, ...]:
        """Names of fields that differ from `other` (used to enforce one-variable-at-a-time)."""
        return tuple(f.name for f in fields(self) if getattr(self, f.name) != getattr(other, f.name))

    def settings_overrides(self) -> dict:
        """Backend `Settings` fields this config controls. steps/resolution are per-request, not settings."""
        return {"precision": self.precision, "attention_slicing": self.attention_slicing,
                "vae_slicing": self.vae_slicing, "offload": self.offload}
