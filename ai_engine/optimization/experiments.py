"""The fixed P4 experiment grid (docs/08 section 8.4/8.5): one baseline, single-variable ablations, labelled combos.

Baseline is deliberately the highest-fidelity setting (fp32, 4 steps, 512, no memory tricks) so that
"reduced precision" and "reduced steps" are real reductions. If B0 itself runs out of memory on the laptop,
that is a result: record it, then follow docs/P4_OPTIMIZATION.md section 6.
"""
from dataclasses import dataclass

from .config import ConfigurationError, OptimizationConfig

BASELINE_ID = "B0"
BASELINE = OptimizationConfig()


@dataclass(frozen=True)
class Experiment:
    id: str
    title: str
    hypothesis: str
    config: OptimizationConfig
    combined: bool = False  # True = more than one variable changed; must be labelled as such in reports

    @property
    def changed(self) -> tuple[str, ...]:
        return self.config.changed_fields(BASELINE)


def _c(**kw) -> OptimizationConfig:
    return OptimizationConfig(**kw)


EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment("B0", "Baseline (fp32, 4 steps, 512)", "Reference point; nothing is optimized.", BASELINE),
    Experiment("E1", "Reduced precision: fp16", "fp16 cuts weight memory and latency with small output change.",
               _c(precision="fp16")),
    Experiment("E2", "Reduced steps: 2", "Halving steps roughly halves denoising time at some fidelity cost.",
               _c(steps=2)),
    Experiment("E3", "Reduced steps: 1", "Single-step is fastest; expect the largest fidelity drop of E2/E3.",
               _c(steps=1)),
    Experiment("E4", "Attention slicing", "Lower peak VRAM, small latency cost.", _c(attention_slicing=True)),
    Experiment("E5", "VAE slicing", "Lower decode-time VRAM; little effect for batch size 1.",
               _c(vae_slicing=True)),
    Experiment("E6", "Model CPU offload", "Large VRAM saving, large latency cost (PCIe transfers).",
               _c(offload="model")),
    Experiment("C1", "COMBINED: fp16 + 2 steps", "Likely practical default; effects may not add up.",
               _c(precision="fp16", steps=2), combined=True),
)


def get(exp_id: str) -> Experiment:
    for e in EXPERIMENTS:
        if e.id == exp_id:
            return e
    raise KeyError(f"unknown experiment {exp_id!r}; known: {[e.id for e in EXPERIMENTS]}")


def validate_registry(experiments=EXPERIMENTS) -> None:
    """Enforces the one-variable-at-a-time rule. Raised at test time, so a bad edit cannot ship."""
    ids = [e.id for e in experiments]
    if len(set(ids)) != len(ids):
        raise ConfigurationError("duplicate experiment ids")
    if not any(e.id == BASELINE_ID and not e.changed for e in experiments):
        raise ConfigurationError("registry needs a baseline identical to BASELINE")
    for e in experiments:
        n = len(e.changed)
        if e.id == BASELINE_ID and n:
            raise ConfigurationError("baseline must not differ from itself")
        if e.id != BASELINE_ID and not e.combined and n != 1:
            raise ConfigurationError(f"{e.id}: single-variable experiment changes {n} fields {e.changed}")
        if e.combined and n < 2:
            raise ConfigurationError(f"{e.id}: marked combined but changes {n} field(s)")
