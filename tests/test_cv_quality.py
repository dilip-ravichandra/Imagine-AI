import numpy as np
import pytest

from computer_vision.edge_aware import edge_preserving_sharpen
from computer_vision.quality import (QualityReport, assess_quality, blur_metrics, estimate_noise_sigma,
                                     gradient_p99, halo_score)
from tests.cv_helpers import blur, gradient, noisy, scene, step


def test_report_fields_and_to_dict():
    q = assess_quality(scene())
    d = q.to_dict()
    assert set(d) == set(QualityReport.__dataclass_fields__) and all(isinstance(v, (int, float)) for v in d.values())


def test_noise_estimate_tracks_true_sigma_per_channel():
    base = scene()
    assert estimate_noise_sigma(base) < 0.5
    for true in (4.0, 8.0, 15.0):
        est = estimate_noise_sigma(noisy(base, true, seed=1))
        assert abs(est - true) / true < 0.15, (true, est)


def test_noise_estimate_ignores_hard_edges():
    assert estimate_noise_sigma(step()) < 0.5  # a big edge is not noise


def test_sharpness_and_blur_ratio_separate_sharp_from_soft():
    s = scene()
    sharp_v, sharp_r = blur_metrics(s)
    soft_v, soft_r = blur_metrics(blur(s, 1.5))
    assert sharp_v > 10 * soft_v and sharp_r < 0.33 < soft_r


def test_blur_ratio_survives_noise():
    s = scene()
    assert blur_metrics(noisy(s, 8.0))[1] < 0.33  # noisy but sharp stays "sharp"
    assert blur_metrics(noisy(blur(s, 1.5), 8.0))[1] > 0.33  # noise does not hide blur


def test_raw_sharpness_is_inflated_by_noise_documented_limit():
    s = scene()
    assert blur_metrics(noisy(s, 8.0))[0] > 2 * blur_metrics(s)[0]


def test_brightness_contrast_saturation_known_values():
    grey = np.full((32, 32, 3), 128, np.uint8)
    q = assess_quality(grey)
    assert abs(q.brightness - 128 / 255) < 0.01 and q.contrast == 0 and q.saturation == 0
    bw = np.zeros((32, 32, 3), np.uint8)
    bw[:, 16:] = 255
    q = assess_quality(bw)
    assert abs(q.contrast - 0.5) < 0.01 and abs(q.brightness - 0.5) < 0.01
    assert assess_quality(np.dstack([np.full((8, 8), 255), np.zeros((8, 8)), np.zeros((8, 8))]).astype(np.uint8)).saturation > 0.99


def test_clipping_fractions():
    im = np.zeros((10, 10, 3), np.uint8)
    im[:, 5:] = 255
    q = assess_quality(im)
    assert q.clipped_dark == 0.5 and q.clipped_bright == 0.5


def test_colour_cast_value():
    cast = np.stack([np.full((8, 8), 100), np.full((8, 8), 120), np.full((8, 8), 160)], -1).astype(np.uint8)
    assert abs(assess_quality(cast).colour_cast - (160 / (380 / 3) - 1)) < 1e-3
    assert assess_quality(np.full((8, 8, 3), 90, np.uint8)).colour_cast == 0


def test_gradient_p99_is_structure_indicator():
    assert gradient_p99(np.full((64, 64, 3), 128, np.uint8)) < 0.1
    assert gradient_p99(gradient(128, 128)) < 2.0  # smooth shading (2 levels/px), far below the blur guard of 4
    assert gradient_p99(scene()) > 20 and gradient_p99(blur(scene(), 3)) > 4


def test_halo_score_hard_step_clean_vs_oversharpened():
    s, n = halo_score(step())
    assert s == 0.0 and n >= 20
    over = edge_preserving_sharpen(step(), amount=2.0, halo_guard=False).image
    s2, n2 = halo_score(over)
    assert s2 > 0.9 and n2 >= 20


def test_halo_score_guarded_sharpen_and_soft_edges_not_flagged():
    sc = scene()
    assert halo_score(edge_preserving_sharpen(sc, amount=1.0).image)[0] == 0.0
    assert halo_score(blur(step(), 2.0))[0] == 0.0


def test_halo_score_thin_line_is_not_mistaken_for_ringing():
    assert halo_score(blur(scene(), 1.5))[0] == 0.0  # regression: blurred thin line looked like overshoot


def test_halo_score_oversharpened_scene_detected_and_noise_gives_no_claim():
    over = edge_preserving_sharpen(scene(), amount=2.0, halo_guard=False, edge_threshold=0.05).image
    s, n = halo_score(over)
    assert s > 0.5 and n >= 20
    s, n = halo_score(noisy(step(), 8.0))
    assert s == 0.0  # too noisy to judge (few/no qualifying edges) -> no evidence, no claim


def test_halo_score_needs_evidence_and_big_enough_image():
    assert halo_score(np.full((64, 64, 3), 128, np.uint8)) == (0.0, 0)
    assert halo_score(np.zeros((10, 10, 3), np.uint8)) == (0.0, 0)


def test_validation_and_no_mutation():
    img = scene()
    before = img.copy()
    assess_quality(img)
    assert np.array_equal(img, before)
    for bad in (np.zeros((8, 8), np.uint8), np.zeros((8, 8, 3), np.float32)):
        with pytest.raises(ValueError):
            assess_quality(bad)
