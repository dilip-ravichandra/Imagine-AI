import cv2
import numpy as np
import pytest

from computer_vision.edge_aware import (bilateral_smooth, edge_density, edge_map, edge_preserving_sharpen,
                                        guided_filter_smooth)
from tests.cv_helpers import gradient, noisy, step


def edge_step(im):  # intensity jump across the centre edge, adjacent columns (strict)
    return float(im[:, 32].mean() - im[:, 31].mean())


def flat_std(im):
    return float(im[:, 5:20].std())


def test_canny_finds_step_edge_and_nothing_in_flat():
    em = edge_map(step())
    assert em.dtype == np.uint8 and em.shape == (64, 64) and set(np.unique(em)) <= {0, 255}
    cols = np.nonzero(em.any(axis=0))[0]
    assert len(cols) >= 1 and all(abs(c - 31.5) <= 1.5 for c in cols)
    assert np.count_nonzero(edge_map(np.full((32, 32, 3), 128, np.uint8))) == 0
    assert edge_density(np.full((32, 32, 3), 128, np.uint8)) == 0.0


def test_sobel_magnitude_peaks_at_edge():
    sm = edge_map(step(), "sobel")
    assert sm.dtype == np.uint8 and sm[:, 31:33].min() >= 240 and sm[:, :20].max() == 0 and sm[:, 45:].max() == 0
    assert edge_map(np.full((8, 8, 3), 5, np.uint8), "sobel").max() == 0  # no gradient -> zeros, no div-by-zero


def test_edge_density_more_for_busier_image():
    busy = noisy(np.full((64, 64, 3), 128, np.uint8), sigma=40)
    assert edge_density(busy) > edge_density(step()) > 0


def test_edge_map_param_validation():
    with pytest.raises(ValueError):
        edge_map(step(), "laplace")
    with pytest.raises(ValueError):
        edge_map(step(), low=100, high=50)
    with pytest.raises(ValueError):
        edge_map(step(), blur_ksize=4)


def test_bilateral_preserves_edge_while_cutting_noise_gaussian_does_not():
    n = noisy(step(), 8.0)
    b = bilateral_smooth(n).image
    g = cv2.GaussianBlur(n, (0, 0), 2)  # a plain blur is the comparison point
    assert edge_step(b) >= 0.95 * edge_step(n)
    assert flat_std(b) <= 0.4 * flat_std(n)
    assert edge_step(g) < 0.5 * edge_step(n)  # the blur destroys the edge the bilateral keeps
    assert b.dtype == np.uint8 and b.shape == n.shape


def test_guided_filter_preserves_edge_better_than_gaussian_and_cuts_noise():
    n = noisy(step(), 8.0)
    gf = guided_filter_smooth(n).image
    g = cv2.GaussianBlur(n, (0, 0), 2)
    assert edge_step(gf) > 2 * edge_step(g) and edge_step(gf) >= 0.6 * edge_step(n)
    assert flat_std(gf) <= 0.2 * flat_std(n)


def test_guided_filter_custom_guide_and_validation():
    n = noisy(step(), 8.0)
    guide = step()[..., 0]  # clean edge map as guide -> edge fully preserved
    gf = guided_filter_smooth(n, guide=guide, eps=0.001).image
    assert edge_step(gf) >= 0.9 * edge_step(step())
    with pytest.raises(ValueError):
        guided_filter_smooth(n, guide=np.zeros((3, 3), np.uint8))
    with pytest.raises(ValueError):
        guided_filter_smooth(n, radius=0)


def test_strength_blends_between_original_and_filtered():
    n = noisy(step(), 8.0)
    half = bilateral_smooth(n, strength=0.5).image
    assert flat_std(bilateral_smooth(n).image) < flat_std(half) < flat_std(n)
    assert not bilateral_smooth(n, strength=0.0).applied and not guided_filter_smooth(n, strength=0.0).applied


def soft_step():
    return cv2.GaussianBlur(step(), (0, 0), 2.0)


def test_sharpen_steepens_mildly_blurred_edge():
    s = cv2.GaussianBlur(step(), (0, 0), 1.0)  # mild blur; wider blur needs larger radius (see docs/P5A_CV.md)
    out = edge_preserving_sharpen(s, amount=1.0).image
    grad = lambda a: np.abs(np.diff(a[:, :, 1].astype(float), axis=1)).max()
    assert grad(out) > grad(s) * 1.2


def test_sharpen_touches_edges_not_flat_noise():
    base = noisy(soft_step(), 3.0, seed=2)
    out = edge_preserving_sharpen(base, amount=1.0).image.astype(float)
    flat_change = np.abs(out[:, :10] - base[:, :10]).mean()
    edge_change = np.abs(out[:, 28:36] - base[:, 28:36]).mean()
    assert flat_change < 0.2 and edge_change > 10 * max(flat_change, 0.05)


def test_sharpen_halo_guard_prevents_overshoot():
    s = step()  # hard edge: the classic case where unsharp masking rings
    guarded = edge_preserving_sharpen(s, amount=2.0, halo_guard=True).image
    assert guarded.min() >= s.min() and guarded.max() <= s.max()  # no ringing beyond input range
    unguarded = edge_preserving_sharpen(s, amount=2.0, halo_guard=False).image
    assert unguarded.min() < s.min() and unguarded.max() > s.max()  # the guard is doing real work


def test_sharpen_noop_and_validation():
    s = soft_step()
    for r in (edge_preserving_sharpen(s, amount=0.0), edge_preserving_sharpen(s, enabled=False)):
        assert not r.applied and np.array_equal(r.image, s) and r.image is not s
    with pytest.raises(ValueError):
        edge_preserving_sharpen(s, amount=5.0)
    with pytest.raises(ValueError):
        edge_preserving_sharpen(s, radius=0)


def test_filters_do_not_mutate_input_and_keep_contract():
    img = noisy(gradient(48, 64), 5.0)
    before = img.copy()
    for fn in (bilateral_smooth, guided_filter_smooth, edge_preserving_sharpen):
        r = fn(img)
        assert r.image.dtype == np.uint8 and r.image.shape == img.shape
    assert np.array_equal(img, before)
