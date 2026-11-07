"""P7A metrics harness: CLIP, FID gate, latency, memory, model size, paired comparison, report. Torch-free core."""
from .metrics import (bootstrap_ci_clustered, cosine_similarity, fid_gate, frechet_distance, gaussian_stats,
                      paired_deltas)
from .sizes import find_hf_snapshot, size_report
from .variants import VARIANTS, Variant, get, validate_registry

__all__ = ["bootstrap_ci_clustered", "cosine_similarity", "fid_gate", "frechet_distance", "gaussian_stats",
           "paired_deltas", "find_hf_snapshot", "size_report", "VARIANTS", "Variant", "get", "validate_registry"]
