"""The fixed P7 variant grid (docs/08 section 8.4). Pure Python (no torch).

A variant = (OptimizationConfig, cv_pipeline, adapter). Exactly one of those fields may differ from V0 unless the
variant is labelled combined. Variants that cannot run yet (no approved adapter yet; controller not wired in here and no measured profile) stay in
the registry with status "blocked" and a reason, so reports list them as NOT RUN instead of silently omitting them.
"""
from dataclasses import dataclass
from typing import Optional

from ai_engine.optimization.config import ConfigurationError, OptimizationConfig

BASELINE_ID = "V0"


@dataclass(frozen=True)
class Variant:
    id: str
    title: str
    hypothesis: str
    config: OptimizationConfig = OptimizationConfig()
    cv: Optional[str] = None  # None = CV off; else a key of cv_pipelines.PIPELINES
    adapter: Optional[str] = None  # path/id of a LoRA; None = base model
    combined: bool = False
    blocked_reason: Optional[str] = None  # set => cannot run; reported as NOT RUN

    @property
    def runnable(self) -> bool:
        return self.blocked_reason is None

    def changed_vs(self, other: "Variant") -> tuple[str, ...]:
        out = [f"config.{n}" for n in self.config.changed_fields(other.config)]
        if self.cv != other.cv:
            out.append("cv")
        if self.adapter != other.adapter:
            out.append("adapter")
        return tuple(out)

    @property
    def changed(self) -> tuple[str, ...]:
        return self.changed_vs(VARIANTS[0]) if self.id != BASELINE_ID else ()


def _c(**kw) -> OptimizationConfig:
    return OptimizationConfig(**kw)


VARIANTS: tuple[Variant, ...] = (
    Variant("V0", "Baseline (fp32, 4 steps, 512, CV off)", "Reference point; nothing optimized."),
    Variant("V1", "Reduced precision: fp16", "fp16 lowers memory/latency with small output change.", _c(precision="fp16")),
    Variant("V2", "Reduced steps: 2", "Fewer steps cut denoising time at some alignment cost.", _c(steps=2)),
    Variant("V3", "Reduced steps: 1", "Single step is fastest; largest expected drop.", _c(steps=1)),
    Variant("V4", "COMBINED: fp16 + 2 steps", "Likely practical default; effects may not add up.",
            _c(precision="fp16", steps=2), combined=True),
    Variant("V5", "CV on (P5A auto_enhance)", "Dead-banded enhancement leaves most images untouched; effect on CLIP "
            "is small. Untuned thresholds: may help or hurt.", cv="p5a_auto_enhance"),
    Variant("V6", "Adapted model (LoRA)", "Adapter improves alignment on the adapted domain.", adapter="TBD",
            blocked_reason="No approved adapter exists: P3A training was never run (code and a gated loader exist). Train and approve one, or declare the gap (DL-02 open)."),
    Variant("V7", "Adaptive controller modes across profiles", "Controller picks cheaper settings under constraint "
            "with bounded quality loss.", blocked_reason="Controller exists (P6) but is not wired into this harness and no MEASURED profile exists. Run the P6 profile sweep on the GPU first."),
)


def get(variant_id: str) -> Variant:
    for v in VARIANTS:
        if v.id == variant_id:
            return v
    raise KeyError(f"unknown variant {variant_id!r}; known: {[v.id for v in VARIANTS]}")


def validate_registry(variants=VARIANTS) -> None:
    """One-variable-at-a-time rule; raised at test time so a bad edit cannot ship."""
    ids = [v.id for v in variants]
    if len(set(ids)) != len(ids):
        raise ConfigurationError("duplicate variant ids")
    base = variants[0]
    if base.id != BASELINE_ID or base.cv is not None or base.adapter is not None:
        raise ConfigurationError("first variant must be the plain baseline V0")
    for v in variants[1:]:
        if v.blocked_reason and v.changed_vs(base) == ():  # placeholder for work that does not exist yet (e.g. P6)
            continue
        n = len(v.changed_vs(base))
        if not v.combined and n != 1:
            raise ConfigurationError(f"{v.id}: single-variable variant changes {n} fields {v.changed_vs(base)}")
        if v.combined and n < 2:
            raise ConfigurationError(f"{v.id}: marked combined but changes {n} field(s)")
