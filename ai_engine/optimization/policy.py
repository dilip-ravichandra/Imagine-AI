"""Torch-free decisions the engine makes when applying optimizations. Unit-testable without a GPU."""
from typing import Callable, Optional

from .config import OFFLOADS, PRECISIONS, ConfigurationError

PRECISION_SETTINGS = ("auto",) + PRECISIONS
WEIGHTS_VARIANTS = ("auto", "fp16", "none")


def resolve_precision(requested: str, device: str, bf16_supported: Callable[[], bool] = lambda: False) -> str:
    """'auto' keeps the P1A behaviour (fp16 on CUDA, fp32 on CPU). Reduced precision is CUDA-only here."""
    if requested not in PRECISION_SETTINGS:
        raise ConfigurationError(f"unknown precision {requested!r}")
    if requested == "auto":
        return "fp16" if device == "cuda" else "fp32"
    if requested in ("fp16", "bf16") and device != "cuda":
        raise ConfigurationError(f"{requested} inference is only enabled on CUDA (device={device})")
    if requested == "bf16" and not bf16_supported():
        raise ConfigurationError("bf16 requested but this CUDA device does not report bf16 support")
    return requested


def weights_variant(requested_precision: str, resolved_precision: str, override: str = "auto") -> Optional[str]:
    """Which Hugging Face file variant to load.

    auto + precision 'auto' -> "fp16" (exactly what P1A did, so default behaviour is unchanged).
    auto + explicit precision -> "fp16" files only for fp16; otherwise the full-precision files (None).
    override 'fp16' / 'none' forces it (e.g. if the hub lacks full-precision files for the pinned revision).
    """
    if override not in WEIGHTS_VARIANTS:
        raise ConfigurationError(f"WEIGHTS_VARIANT must be one of {WEIGHTS_VARIANTS}")
    if override != "auto":
        return None if override == "none" else override
    if requested_precision == "auto":
        return "fp16"
    return "fp16" if resolved_precision == "fp16" else None


def validate_runtime(device: str, offload: str) -> None:
    if offload not in OFFLOADS:
        raise ConfigurationError(f"unknown offload {offload!r}")
    if offload != "none" and device != "cuda":
        raise ConfigurationError("CPU offload needs a CUDA device to offload from")


def active_optimizations(resolved_precision: str, attention_slicing: bool, vae_slicing: bool, offload: str) -> tuple:
    """Human-readable list of what is switched on, for logs and result files."""
    out = [f"precision={resolved_precision}"]
    if attention_slicing:
        out.append("attention_slicing")
    if vae_slicing:
        out.append("vae_slicing")
    if offload != "none":
        out.append(f"offload={offload}")
    return tuple(out)
