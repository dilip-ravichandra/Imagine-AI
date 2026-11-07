import dataclasses

import numpy as np
import pytest

import computer_vision.artifacts.correct as correct_mod
from computer_vision.artifacts import (FLAGS, SEMANTIC_FLAG, ArtifactThresholds, correct_artifacts,
                                       detect_artifacts, intent_suppressions, semantic_review)
from computer_vision.edge_aware import edge_preserving_sharpen
from computer_vision.quality import assess_quality
from tests.cv_helpers import blur, darker, noisy, scene


def names(img, **kw):
    return detect_artifacts(img, **kw).names


def test_clean_scene_has_no_flags():
    assert names(scene()) == []


@pytest.mark.parametrize("label,make,expected", [
    ("blur", lambda s: blur(s, 1.5), {"blur"}),
    ("heavy blur", lambda s: blur(s, 3), {"blur"}),
    ("noise", lambda s: noisy(s, 8.0), {"noise"}),
    ("dark", lambda s: darker(s, 0.3), {"dark", "low_contrast"}),
    ("low contrast", lambda s: np.clip((s.astype(float) - 128) * 0.25 + 128, 0, 255).astype(np.uint8), {"low_contrast"}),
    ("colour cast", lambda s: np.clip(s * np.array([0.7, 1, 1.3]), 0, 255).astype(np.uint8), {"colour_cast"}),
    ("overexposed", lambda s: np.clip(s.astype(float) * 1.8, 0, 255).astype(np.uint8), {"bright", "clipped_highlights"}),
    ("oversharpened", lambda s: edge_preserving_sharpen(s, amount=2.0, halo_guard=False, edge_threshold=0.05).image, {"halo"}),
])
def test_each_synthetic_degradation_raises_its_flag(label, make, expected):
    assert set(names(make(scene()))) == expected, label


def test_smooth_or_flat_images_are_not_called_blurry():
    sky = np.zeros((128, 128, 3), np.uint8)
    sky[..., 2] = np.linspace(120, 220, 128).astype(np.uint8)[:, None]
    assert "blur" not in names(sky) and "blur" not in names(np.full((128, 128, 3), 128, np.uint8))


def test_flag_metadata_and_correctable_markers():
    rep = detect_artifacts(noisy(scene(), 8.0))
    f = rep.flags[0]
    assert f.name == "noise" and f.value > f.threshold and f.correctable and f.note
    assert FLAGS["clipped_shadows"][1] is False and FLAGS["clipped_highlights"][1] is False and FLAGS["halo"][1] is False
    assert all(FLAGS[n][1] for n in ("blur", "noise", "dark", "bright", "low_contrast", "colour_cast"))


def test_thresholds_are_configurable_and_frozen():
    strict = ArtifactThresholds(noise_sigma_max=1.0)
    assert "noise" in names(noisy(scene(), 3.0), thresholds=strict) and "noise" not in names(noisy(scene(), 3.0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        strict.noise_sigma_max = 9


def test_suppress_hides_flag_but_records_it_and_rejects_typos():
    dark = darker(scene(), 0.3)
    rep = detect_artifacts(dark, suppress={"dark"})
    assert "dark" not in rep.names and "dark" in rep.suppressed
    with pytest.raises(ValueError):
        detect_artifacts(dark, suppress={"darkk"})


def test_detect_reuses_given_quality():
    img = noisy(scene(), 8.0)
    q = assess_quality(img)
    assert detect_artifacts(img, quality=q).quality is q


# ---------------- correction ----------------
def step_map(r):
    return {s.name: s for s in r.steps}


def test_clean_image_is_left_untouched():
    s = scene()
    r = correct_artifacts(s)
    assert not r.applied and r.steps == [] and np.array_equal(r.image, s) and r.image is not s


def test_denoise_accepted_and_reduces_noise():
    img = noisy(scene(), 8.0)
    r = correct_artifacts(img)
    st = step_map(r)["denoise"]
    assert r.applied and st.accepted and st.target_after < 0.5 * st.target_before
    assert "noise" not in r.after.names and "noise" in r.before.names


def test_white_balance_accepted_for_cast():
    img = np.clip(scene() * np.array([0.7, 1, 1.3]), 0, 255).astype(np.uint8)
    r = correct_artifacts(img)
    st = step_map(r)["white_balance"]
    assert st.accepted and st.target_after < 0.9 * st.target_before and "colour_cast" not in r.after.names


def test_exposure_accepted_for_dark_image():
    img = darker(scene(), 0.3)
    r = correct_artifacts(img)
    assert step_map(r)["exposure"].accepted
    assert r.after.quality.brightness > r.before.quality.brightness and "dark" not in r.after.names


def test_unfixable_flags_stay_flagged_and_are_not_claimed_fixed():
    over = np.clip(scene().astype(float) * 1.8, 0, 255).astype(np.uint8)
    r = correct_artifacts(over)
    assert "clipped_highlights" in r.after.names
    assert any("not correctable" in n and "clipped_highlights" in n for n in r.notes)
    halo = edge_preserving_sharpen(scene(), amount=2.0, halo_guard=False, edge_threshold=0.05).image
    r2 = correct_artifacts(halo)
    assert "halo" in r2.after.names and not r2.applied and np.array_equal(r2.image, halo)


def test_mild_blur_is_not_fixed_by_conservative_sharpen_documented_limit():
    img = blur(scene(), 1.5)
    r = correct_artifacts(img)
    st = step_map(r)["sharpen"]
    assert not st.accepted and "did not improve" in st.reason
    assert "blur" in r.after.names and np.array_equal(r.image, img)  # honest: image unchanged, still flagged


def test_suppressed_flags_are_not_corrected():
    dark = darker(scene(), 0.3)
    r = correct_artifacts(dark, suppress={"dark", "low_contrast", "clipped_shadows", "colour_cast"})
    assert r.steps == [] and not r.applied and np.array_equal(r.image, dark)


def test_harmful_step_is_rejected_and_image_kept(monkeypatch):
    dark = darker(scene(), 0.3)
    bad = [("exposure", "dark", lambda im, q: np.full_like(im, 255), lambda q: q.brightness, lambda b, a: True)]
    monkeypatch.setattr(correct_mod, "_steps", lambda t: bad)
    r = correct_artifacts(dark)
    assert not r.applied and not r.steps[0].accepted and r.steps[0].reason.startswith("rejected: introduced")
    assert np.array_equal(r.image, dark)


def test_step_that_does_not_move_target_is_rejected(monkeypatch):
    img = noisy(scene(), 8.0)
    noop_step = [("denoise", "noise", lambda im, q: im.copy(), lambda q: q.noise_sigma,
                  lambda b, a: a <= b * 0.9)]
    monkeypatch.setattr(correct_mod, "_steps", lambda t: noop_step)
    r = correct_artifacts(img)
    assert not r.steps[0].accepted and "did not improve" in r.steps[0].reason and not r.applied


def test_correction_disabled_returns_copy_and_does_not_mutate():
    img = noisy(scene(), 8.0)
    before = img.copy()
    r = correct_artifacts(img, enabled=False)
    assert not r.applied and np.array_equal(r.image, img) and r.notes == ["disabled"]
    correct_artifacts(img)
    assert np.array_equal(img, before)


def test_denoise_then_exposure_on_combined_degradation():
    img = noisy(darker(scene(), 0.3), 6.0)
    r = correct_artifacts(img)
    acc = [s.name for s in r.steps if s.accepted]
    assert "denoise" in acc and "exposure" in acc
    assert "noise" not in r.after.names and "dark" not in r.after.names


# ---------------- semantic ----------------
def test_semantic_review_reasons():
    r = semantic_review(["cat", "sofa"], [2, 1], 1, 0)
    assert r.recommended and len(r.reasons) == 2 and "2 cat" in r.reasons[0]
    assert semantic_review(["robot", "submarine"], [1, 1], 1, 2).recommended
    assert any("anatomy" in x for x in semantic_review(["woman", "sign"], [1, 1], 0, 0).reasons)
    assert any("anatomy" in x for x in semantic_review(["hands"], [None], 0, 0).reasons)


def test_semantic_review_quiet_for_simple_prompt_and_states_its_limit():
    r = semantic_review(["lighthouse"], [1], 0, 0)
    assert not r.recommended and r.reasons == ()
    assert "no pixels" in r.note and SEMANTIC_FLAG == "semantic_review_recommended"


def test_intent_suppressions():
    assert {"dark", "colour_cast"} <= intent_suppressions("a lighthouse at night", [], [])
    assert intent_suppressions("a diver", [], ["underwater"]) == {"colour_cast"}
    assert intent_suppressions("a red apple on a table", [], []) == frozenset()
    assert "colour_cast" in intent_suppressions("a street", ["neon"], [])
    assert "colour_cast" in intent_suppressions("Sunset over the sea.", [], [])  # punctuation/case tolerant
