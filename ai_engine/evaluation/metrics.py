"""Metric maths (numpy only, unit-tested without any model).

CLIP: cosine similarity of text and image embeddings (docs/08 section 8.3). FID: dataset-level Frechet distance with a
hard sample-size gate -- a tiny-sample FID is refused rather than reported (task card: no misleading FID).
Paired comparison: variants share prompts+seeds, so deltas are computed per (prompt, seed) and the bootstrap resamples
PROMPTS (seeds of one prompt are correlated), not individual pairs.
"""
import math
from typing import Iterable, Optional

import numpy as np

FID_MIN_SAMPLES_PER_DIM = 1  # covariance is singular unless n > feature dim; this is the hard floor
FID_RECOMMENDED_N = 10_000  # commonly cited minimum for a stable FID; below it, results are not citable as FID


def cosine_similarity(a, b) -> float:
    a, b = np.asarray(a, dtype=np.float64).ravel(), np.asarray(b, dtype=np.float64).ravel()
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch {a.shape} vs {b.shape}")
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        raise ValueError("zero-norm embedding")
    return float(a @ b / (na * nb))


def gaussian_stats(features) -> tuple[np.ndarray, np.ndarray]:
    f = np.asarray(features, dtype=np.float64)
    if f.ndim != 2 or f.shape[0] < 2:
        raise ValueError("features must be (n>=2, d)")
    return f.mean(axis=0), np.cov(f, rowvar=False)


def frechet_distance(mu1, s1, mu2, s2) -> float:
    """||mu1-mu2||^2 + Tr(S1 + S2 - 2 (S1 S2)^(1/2)). Trace of the matrix sqrt = sum of sqrt of eigenvalues of S1 S2
    (real parts; tiny negative values from round-off are clipped to 0)."""
    mu1, mu2 = np.asarray(mu1, dtype=np.float64), np.asarray(mu2, dtype=np.float64)
    s1, s2 = np.atleast_2d(np.asarray(s1, dtype=np.float64)), np.atleast_2d(np.asarray(s2, dtype=np.float64))
    if mu1.shape != mu2.shape or s1.shape != s2.shape or s1.shape[0] != mu1.shape[0]:
        raise ValueError("mean/covariance shapes do not match")
    eig = np.linalg.eigvals(s1 @ s2)
    tr_sqrt = float(np.sum(np.sqrt(np.clip(eig.real, 0.0, None))))
    return float(np.sum((mu1 - mu2) ** 2) + np.trace(s1) + np.trace(s2) - 2.0 * tr_sqrt)


def fid_gate(n_real: int, n_generated: int, feature_dim: int = 2048) -> dict:
    """Decide whether an FID may be computed AND reported. Never returns a number itself."""
    reasons = []
    if n_real <= 0:
        reasons.append("no real reference images")
    if n_generated <= 0:
        reasons.append("no generated images")
    floor = feature_dim * FID_MIN_SAMPLES_PER_DIM
    for name, n in (("real", n_real), ("generated", n_generated)):
        if 0 < n <= floor:
            reasons.append(f"{name} sample count {n} <= feature dim {feature_dim}: covariance is singular")
    if not reasons and min(n_real, n_generated) < FID_RECOMMENDED_N:
        return {"allowed": True, "citable": False, "n_real": n_real, "n_generated": n_generated,
                "reasons": [f"n < {FID_RECOMMENDED_N}: FID is computable but biased/high-variance; label it "
                            "'small-sample FID' and do not compare against published numbers"]}
    return {"allowed": not reasons, "citable": not reasons, "n_real": n_real, "n_generated": n_generated,
            "reasons": reasons}


def paired_deltas(base: dict, other: dict) -> dict:
    """base/other: {(prompt_id, seed): value}. Returns deltas (other - base) over keys present in BOTH with non-None."""
    keys = sorted(k for k in base if k in other and base[k] is not None and other[k] is not None)
    return {k: other[k] - base[k] for k in keys}


def bootstrap_ci_clustered(deltas: dict, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0) -> Optional[dict]:
    """Mean paired delta with a percentile bootstrap CI that resamples prompts (cluster = prompt_id).
    None when there is no data. With a single prompt the CI is degenerate and is reported as None."""
    if not deltas:
        return None
    by_prompt: dict = {}
    for (pid, _seed), d in deltas.items():
        by_prompt.setdefault(pid, []).append(d)
    prompts = sorted(by_prompt)
    means = np.array([np.mean(by_prompt[p]) for p in prompts])
    vals = [d for v in by_prompt.values() for d in v]
    out = {"n_pairs": len(vals), "n_prompts": len(prompts), "mean_delta": float(np.mean(vals)),
           "median_delta": float(np.median(vals)), "frac_positive": float(np.mean([d > 0 for d in vals])),
           "ci_low": None, "ci_high": None, "ci_level": 1 - alpha, "n_boot": n_boot}
    if len(prompts) < 2:
        return out
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(prompts), size=(n_boot, len(prompts)))
    boots = means[idx].mean(axis=1)
    out["ci_low"], out["ci_high"] = (float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2)))
    return out


def cv_percent(values: Iterable[float]) -> Optional[float]:
    """Coefficient of variation in % (stdev/mean). None if <2 values or mean 0."""
    v = [float(x) for x in values if x is not None]
    if len(v) < 2:
        return None
    m = float(np.mean(v))
    return None if m == 0 else float(np.std(v, ddof=1) / abs(m) * 100.0)


__all__ = ["cosine_similarity", "gaussian_stats", "frechet_distance", "fid_gate", "paired_deltas",
           "bootstrap_ci_clustered", "cv_percent", "math"]
