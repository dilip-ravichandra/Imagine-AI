"""P4 inference optimization: config, torch-free policy, experiment grid, stats."""
from .config import ConfigurationError, OptimizationConfig
from .experiments import BASELINE, BASELINE_ID, EXPERIMENTS, Experiment, get, validate_registry
from .policy import active_optimizations, resolve_precision, validate_runtime, weights_variant
from .stats import pixel_fidelity, summarize

__all__ = ["ConfigurationError", "OptimizationConfig", "BASELINE", "BASELINE_ID", "EXPERIMENTS", "Experiment",
           "get", "validate_registry", "active_optimizations", "resolve_precision", "validate_runtime",
           "weights_variant", "pixel_fidelity", "summarize"]
