import numpy as np

from computer_vision import CVPipelineConfig, run_pipeline
from computer_vision.artifacts import SEMANTIC_FLAG, semantic_review
from tests.cv_helpers import blur, darker, noisy, scene


def test_default_config_measures_but_changes_nothing():
    s = noisy(scene(), 8.0)
    r = run_pipeline(s)
    assert not r.changed and np.array_equal(r.image, s) and r.image is not s and r.stages == []
    assert r.report_before is not None and r.report_after is r.report_before and "noise" in r.flag_names
    assert r.cv_ms > 0


def test_all_stages_off_including_assess_is_pure_bypass():
    s = scene()
    r = run_pipeline(s, CVPipelineConfig(assess=False))
    assert not r.changed and np.array_equal(r.image, s) and r.report_before is None and r.flag_names == []


def test_correct_stage_changes_and_reassesses():
    s = noisy(scene(), 8.0)
    r = run_pipeline(s, CVPipelineConfig(correct=True))
    assert r.changed and not np.array_equal(r.image, s)
    assert "noise" in r.report_before.names and "noise" not in r.report_after.names
    assert r.flag_names == r.report_after.names


def test_stage_order_and_toggles():
    s = scene(300)
    cfg = CVPipelineConfig(resolution=256, enhance=True, smooth=True, sharpen=True, correct=True)
    r = run_pipeline(darker(s, 0.3), cfg)
    stages = [getattr(x, "stage", "correction") for x in r.stages]
    assert stages == ["resize", "auto_enhance", "bilateral", "sharpen", "correction"]
    assert r.image.shape == (256, 256, 3) and r.changed
    only = run_pipeline(s, CVPipelineConfig(smooth=True))
    assert [x.stage for x in only.stages] == ["bilateral"]


def test_semantic_flag_is_reported_but_never_pixel_fixed():
    s = scene()
    sem = semantic_review(["cat", "sofa"], [2, 1], 1, 0)
    r = run_pipeline(s, CVPipelineConfig(correct=True), sem)
    assert SEMANTIC_FLAG in r.flag_names and r.semantic is sem
    assert np.array_equal(r.image, s)  # nothing pixel-wise to fix, and the flag stays
    assert SEMANTIC_FLAG not in run_pipeline(s, semantic=semantic_review(["lighthouse"], [1], 0, 0)).flag_names


def test_suppress_passes_through_to_correction():
    dark = darker(scene(), 0.3)
    r = run_pipeline(dark, CVPipelineConfig(correct=True, suppress=frozenset({"dark", "low_contrast", "clipped_shadows", "colour_cast"})))
    assert not r.changed and "dark" not in r.flag_names


def test_input_not_mutated_and_invalid_rejected():
    s = noisy(scene(), 8.0)
    before = s.copy()
    run_pipeline(s, CVPipelineConfig(correct=True, enhance=True, smooth=True, sharpen=True))
    assert np.array_equal(s, before)
    import pytest
    with pytest.raises(ValueError):
        run_pipeline(np.zeros((4, 4), np.uint8))
