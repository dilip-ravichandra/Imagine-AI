import numpy as np
import pytest

from computer_vision.enhancement import (EnhanceConfig, adjust_brightness_contrast, adjust_gamma,
                                         adjust_saturation, apply_clahe, auto_enhance,
                                         white_balance_gray_world)
from tests.cv_helpers import gradient, luma


def mid(h=32, w=32, v=128):
    return np.full((h, w, 3), v, np.uint8)


def lowcon():
    rng = np.random.default_rng(1)
    base = np.linspace(100, 140, 64, dtype=np.float32)[None, :].repeat(64, 0)
    g = np.clip(base + rng.normal(0, 2, base.shape), 0, 255).astype(np.uint8)
    return np.stack([g, g, g], -1)


def test_brightness_contrast():
    img = gradient()
    up = adjust_brightness_contrast(img, brightness=0.1).image
    assert luma(up).mean() > luma(img).mean() + 10
    hi = adjust_brightness_contrast(img, contrast=1.5).image
    assert luma(hi).std() > luma(img).std()
    assert adjust_brightness_contrast(mid(), contrast=2.0).image.mean() == 128  # pivot is mid-grey
    assert up.dtype == np.uint8 and up.shape == img.shape


def test_brightness_contrast_clips_not_wraps():
    out = adjust_brightness_contrast(mid(v=250), brightness=0.5).image
    assert (out == 255).all()
    assert (adjust_brightness_contrast(mid(v=5), brightness=-0.5).image == 0).all()


def test_gamma_direction_and_identity():
    img = gradient()
    assert luma(adjust_gamma(img, 2.0).image).mean() > luma(img).mean()
    assert luma(adjust_gamma(img, 0.5).image).mean() < luma(img).mean()
    r = adjust_gamma(img, 1.0)
    assert not r.applied and np.array_equal(r.image, img)
    out = adjust_gamma(img, 2.2).image
    assert out[0, 0].tolist() == [0, 0, 0] or out.min() == 0  # black stays black
    assert (adjust_gamma(np.full((4, 4, 3), 255, np.uint8), 2.0).image == 255).all()


def test_white_balance_reduces_colour_cast_within_gain_limit():
    cast = np.stack([np.full((32, 32), 100), np.full((32, 32), 120), np.full((32, 32), 160)], -1).astype(np.uint8)
    spread = lambda a: np.ptp(a.reshape(-1, 3).mean(0))
    r = white_balance_gray_world(cast, strength=1.0, max_gain=1.5)
    assert r.applied and spread(r.image) < spread(cast) * 0.1
    assert max(r.params["gains_rgb"]) <= 1.5 and min(r.params["gains_rgb"]) >= 1 / 1.5


def test_white_balance_max_gain_clamps_strong_cast():
    cast = np.stack([np.full((8, 8), 30), np.full((8, 8), 120), np.full((8, 8), 120)], -1).astype(np.uint8)
    r = white_balance_gray_world(cast, max_gain=1.2)
    assert max(r.params["gains_rgb"]) <= 1.2 + 1e-9
    assert r.image[..., 0].mean() <= 30 * 1.2 + 1


def test_white_balance_noops():
    assert not white_balance_gray_world(mid()).applied  # already neutral
    assert not white_balance_gray_world(gradient(), enabled=False).applied
    black_ch = np.zeros((8, 8, 3), np.uint8)
    black_ch[..., 1:] = 100
    assert not white_balance_gray_world(black_ch).applied  # empty channel -> undefined, refuse


def test_saturation():
    img = gradient()
    grey = adjust_saturation(img, 0.0).image.astype(int)
    assert np.abs(grey[..., 0] - grey[..., 1]).max() <= 2 and np.abs(grey[..., 1] - grey[..., 2]).max() <= 2
    sat = lambda a: (a.max(-1).astype(int) - a.min(-1)).mean()
    assert sat(adjust_saturation(img, 1.5).image) > sat(img) > sat(adjust_saturation(img, 0.5).image)
    assert not adjust_saturation(img, 1.0).applied


def test_clahe_raises_contrast_of_flat_image_and_keeps_colour_channels_shape():
    img = lowcon()
    out = apply_clahe(img, clip_limit=3.0).image
    assert luma(out).std() > luma(img).std() * 1.2 and out.shape == img.shape and out.dtype == np.uint8


def test_clahe_strength_blends_and_hsv_channel():
    img = lowcon()
    full = apply_clahe(img, strength=1.0).image
    half = apply_clahe(img, strength=0.5).image
    assert luma(img).std() < luma(half).std() < luma(full).std()
    assert apply_clahe(img, channel="hsv_v").applied
    assert not apply_clahe(img, strength=0.0).applied


def test_clahe_leaves_hue_roughly_alone():
    # coloured (not grey) low-contrast image: R/B ratio stays within a modest range after L-only CLAHE
    img = np.stack([lowcon()[..., 0], (lowcon()[..., 0] * 0.6).astype(np.uint8), (lowcon()[..., 0] * 0.3).astype(np.uint8)], -1)
    out = apply_clahe(img, strength=0.5).image
    assert out[..., 0].mean() > out[..., 1].mean() > out[..., 2].mean()


@pytest.mark.parametrize("fn,kw", [(adjust_brightness_contrast, dict(brightness=2)), (adjust_brightness_contrast, dict(contrast=-1)),
                                   (adjust_gamma, dict(gamma=0)), (adjust_saturation, dict(factor=-1)),
                                   (apply_clahe, dict(clip_limit=0)), (apply_clahe, dict(channel="x")),
                                   (white_balance_gray_world, dict(strength=2))])
def test_invalid_params_raise(fn, kw):
    with pytest.raises(ValueError):
        fn(gradient(), **kw)


def test_all_bypass_flags_return_unchanged_copies():
    img = gradient()
    for fn in (adjust_brightness_contrast, adjust_gamma, white_balance_gray_world, adjust_saturation, apply_clahe, auto_enhance):
        r = fn(img, enabled=False)
        assert not r.applied and np.array_equal(r.image, img) and r.image is not img


def test_auto_enhance_leaves_acceptable_image_untouched():
    rng = np.random.default_rng(3)
    ok = np.clip(rng.normal(128, 45, (64, 64, 1)).repeat(3, 2), 0, 255).astype(np.uint8)  # neutral, mid, contrasty
    r = auto_enhance(ok)
    assert not r.applied and np.array_equal(r.image, ok) and r.params["steps"] == []


def test_auto_enhance_brightens_dark_image_but_not_past_band():
    rng = np.random.default_rng(4)
    dark = np.clip(rng.normal(40, 30, (64, 64, 1)).repeat(3, 2), 0, 255).astype(np.uint8)
    r = auto_enhance(dark, EnhanceConfig(contrast=False))
    assert r.applied and "exposure_gamma" in r.params["steps"]
    assert luma(dark).mean() < luma(r.image).mean() <= 0.31 * 255 + 8  # moves toward the low edge, not beyond
    assert r.params["gamma_used"] <= 1.6


def test_auto_enhance_corrects_cast_and_reports_measurements():
    rng = np.random.default_rng(5)
    base = rng.normal(128, 40, (64, 64, 1))
    cast = np.clip(np.concatenate([base * 0.7, base * 0.9, base * 1.15], -1), 0, 255).astype(np.uint8)
    r = auto_enhance(cast, EnhanceConfig(exposure=False, contrast=False))
    spread = lambda a: np.ptp(a.reshape(-1, 3).mean(0))
    assert r.applied and r.params["steps"] == ["white_balance"] and spread(r.image) < spread(cast)
    assert {"mean_luma", "std_luma"} <= set(r.params["measured"])


def test_auto_enhance_low_contrast_triggers_clahe():
    r = auto_enhance(lowcon(), EnhanceConfig(white_balance=False, exposure=False))
    assert r.applied and r.params["steps"] == ["clahe"] and luma(r.image).std() > luma(lowcon()).std()


def test_auto_enhance_is_deterministic():
    img = lowcon()
    assert np.array_equal(auto_enhance(img).image, auto_enhance(img).image)
