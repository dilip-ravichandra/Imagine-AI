import numpy as np
import pytest

from ai_engine.evaluation import (bootstrap_ci_clustered, cosine_similarity, fid_gate, frechet_distance,
                                  gaussian_stats, paired_deltas)
from ai_engine.evaluation.metrics import cv_percent


def test_cosine_basic_properties():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)
    assert cosine_similarity([2, 4], [1, 2]) == pytest.approx(1.0)  # scale invariant
    with pytest.raises(ValueError):
        cosine_similarity([0, 0], [1, 1])
    with pytest.raises(ValueError):
        cosine_similarity([1, 2], [1, 2, 3])


def test_frechet_identical_is_zero_and_known_value():
    rng = np.random.default_rng(0)
    f = rng.normal(size=(500, 6))
    mu, s = gaussian_stats(f)
    assert frechet_distance(mu, s, mu, s) == pytest.approx(0.0, abs=1e-8)
    # equal covariances (identity), mean shift d -> FID = ||d||^2 exactly
    d = np.array([3.0, 4.0])
    assert frechet_distance(np.zeros(2), np.eye(2), d, np.eye(2)) == pytest.approx(25.0)
    # scalar-covariance case: mu equal, S1=a I, S2=b I -> d*(a + b - 2 sqrt(ab)) = d*(sqrt a - sqrt b)^2
    assert frechet_distance(np.zeros(3), 4 * np.eye(3), np.zeros(3), 1 * np.eye(3)) == pytest.approx(3.0)


def test_frechet_symmetric_nonnegative_and_shape_check():
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=(300, 4)), rng.normal(0.5, 1.3, size=(300, 4))
    (m1, s1), (m2, s2) = gaussian_stats(a), gaussian_stats(b)
    d12, d21 = frechet_distance(m1, s1, m2, s2), frechet_distance(m2, s2, m1, s1)
    assert d12 == pytest.approx(d21, rel=1e-6) and d12 > 0
    with pytest.raises(ValueError):
        frechet_distance(np.zeros(2), np.eye(2), np.zeros(3), np.eye(3))
    with pytest.raises(ValueError):
        gaussian_stats(np.zeros((1, 4)))


def test_fid_gate_refuses_tiny_samples():
    g = fid_gate(0, 60)
    assert not g["allowed"] and any("no real" in r for r in g["reasons"])
    g = fid_gate(500, 60)  # feature dim 2048 -> singular covariance
    assert not g["allowed"] and not g["citable"] and len(g["reasons"]) == 2
    g = fid_gate(5000, 5000)
    assert g["allowed"] and not g["citable"] and "biased" in g["reasons"][0]
    g = fid_gate(50_000, 10_000)
    assert g["allowed"] and g["citable"] and g["reasons"] == []


def test_paired_deltas_only_common_non_null_keys():
    base = {("a", 1): 0.30, ("a", 2): 0.31, ("b", 1): None, ("c", 1): 0.2}
    oth = {("a", 1): 0.33, ("a", 2): 0.30, ("b", 1): 0.5, ("d", 1): 0.9}
    d = paired_deltas(base, oth)
    assert set(d) == {("a", 1), ("a", 2)}
    assert d[("a", 1)] == pytest.approx(0.03) and d[("a", 2)] == pytest.approx(-0.01)


def test_bootstrap_clustered_ci_contains_mean_and_is_deterministic():
    deltas = {(f"p{i}", s): 0.02 + 0.005 * ((i * 7 + s) % 5 - 2) for i in range(12) for s in (1, 2, 3)}
    r1, r2 = bootstrap_ci_clustered(deltas, seed=3), bootstrap_ci_clustered(deltas, seed=3)
    assert r1 == r2
    assert r1["n_pairs"] == 36 and r1["n_prompts"] == 12
    assert r1["ci_low"] <= r1["mean_delta"] <= r1["ci_high"]
    assert bootstrap_ci_clustered(deltas, seed=4)["mean_delta"] == r1["mean_delta"]  # mean is data, not seed


def test_bootstrap_edge_cases():
    assert bootstrap_ci_clustered({}) is None
    one = bootstrap_ci_clustered({("p", 1): 0.1, ("p", 2): 0.3})
    assert one["n_prompts"] == 1 and one["ci_low"] is None and one["mean_delta"] == pytest.approx(0.2)


def test_bootstrap_resamples_prompts_not_pairs():
    # 2 prompts with opposite deltas, many seeds each: pair-level bootstrap would give a tight CI around 0;
    # prompt-level bootstrap must span the two prompt means.
    d = {("a", s): 1.0 for s in range(50)} | {("b", s): -1.0 for s in range(50)}
    r = bootstrap_ci_clustered(d, n_boot=500, seed=0)
    assert r["ci_low"] == pytest.approx(-1.0) and r["ci_high"] == pytest.approx(1.0)


def test_cv_percent():
    assert cv_percent([10, 10, 10]) == pytest.approx(0.0)
    assert cv_percent([1]) is None and cv_percent([0, 0]) is None
    assert cv_percent([8, 12]) == pytest.approx(np.std([8, 12], ddof=1) / 10 * 100)
