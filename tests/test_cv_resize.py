import numpy as np
import pytest

from computer_vision.resize import (choose_interpolation, fit_to_resolution, nearest_supported_resolution,
                                    resize_image)
from tests.cv_helpers import checker, gradient


def test_stretch_exact_dims_dtype_channels():
    r = resize_image(gradient(64, 96), 128, 80, mode="stretch")
    assert r.applied and r.image.shape == (80, 128, 3) and r.image.dtype == np.uint8


def test_fit_preserves_aspect_ratio():
    r = resize_image(gradient(64, 128), 256, 256, mode="fit")  # 2:1 source
    h, w = r.image.shape[:2]
    assert (w, h) == (256, 128)
    assert r.params["output_size"] == (256, 128)


def test_fit_multiple_of_8():
    r = resize_image(gradient(100, 150), 300, 300, mode="fit", multiple_of=8)
    h, w = r.image.shape[:2]
    assert h % 8 == 0 and w % 8 == 0


def test_pad_letterboxes_centred_with_pad_colour():
    src = np.full((50, 100, 3), 200, np.uint8)
    r = resize_image(src, 200, 200, mode="pad", pad_color=(0, 0, 255))
    assert r.image.shape == (200, 200, 3)
    assert (r.image[0, 0] == [0, 0, 255]).all() and (r.image[-1, -1] == [0, 0, 255]).all()  # bars
    assert (r.image[100, 100] == 200).all()  # content centred
    assert (r.image[49, 100] == [0, 0, 255]).all() and (r.image[51, 100] == 200).all()  # bar is 50px tall each side


def test_fill_crops_to_exact_box_without_bars():
    r = resize_image(gradient(50, 100), 64, 64, mode="fill")
    assert r.image.shape == (64, 64, 3)
    assert r.image.min() == gradient(50, 100).min() or r.image.max() > 0  # content, not letterbox bars
    src = np.full((50, 100, 3), 123, np.uint8)
    assert (resize_image(src, 64, 64, mode="fill").image == 123).all()  # no pad colour leaked in


def test_auto_interpolation_choice():
    assert choose_interpolation((512, 512), (256, 256)) == "area"
    assert choose_interpolation((256, 256), (512, 512)) == "lanczos"
    assert choose_interpolation((512, 256), (256, 512)) == "cubic"
    assert resize_image(gradient(), 192, 128, mode="stretch").params["interpolation_used"] == "lanczos"
    assert resize_image(gradient(), 48, 32, mode="stretch").params["interpolation_used"] == "area"


def test_area_downscale_avoids_aliasing_unlike_nearest():
    src = checker(64, 1)  # worst case for aliasing: mean is 127.5 everywhere if averaged properly
    area = resize_image(src, 32, 32, mode="stretch", interpolation="area").image.astype(float)
    near = resize_image(src, 32, 32, mode="stretch", interpolation="nearest").image.astype(float)
    assert abs(area.mean() - src.mean()) < 1 and area.std() < 5
    assert abs(near.mean() - src.mean()) > 100  # nearest keeps one phase of the checker -> badly wrong mean (alias)


def test_bypass_and_noop_return_unchanged_copy():
    src = gradient()
    for r in (resize_image(src, 10, 10, enabled=False), resize_image(src, 96, 64, mode="stretch"),
              resize_image(src, 500, 500, mode="stretch", allow_upscale=False)):
        assert r.applied is False and np.array_equal(r.image, src) and r.image is not src


def test_allow_upscale_false_caps_scale():
    r = resize_image(gradient(64, 64), 512, 512, mode="fit", allow_upscale=False)
    assert r.image.shape[:2] == (64, 64) and r.applied is False


def test_input_not_mutated():
    src = gradient()
    before = src.copy()
    resize_image(src, 40, 40, mode="pad")
    assert np.array_equal(src, before)


@pytest.mark.parametrize("bad", [np.zeros((4, 4), np.uint8), np.zeros((4, 4, 4), np.uint8),
                                 np.zeros((4, 4, 3), np.float32), np.zeros((0, 4, 3), np.uint8), [[1]]])
def test_rejects_invalid_images(bad):
    with pytest.raises(ValueError):
        resize_image(bad, 8, 8)


def test_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        resize_image(gradient(), 0, 10)
    with pytest.raises(ValueError):
        resize_image(gradient(), 10, 10, mode="weird")
    with pytest.raises(ValueError):
        resize_image(gradient(), 10, 10, interpolation="magic")


def test_nearest_supported_resolution():
    sup = (256, 384, 512, 640, 768)
    assert nearest_supported_resolution(500, sup) == 512
    assert nearest_supported_resolution(448, sup) == 384  # tie -> smaller
    assert nearest_supported_resolution(1024, sup) == 768 and nearest_supported_resolution(100, sup) == 256
    assert nearest_supported_resolution(500, sup, prefer="down") == 384
    assert nearest_supported_resolution(500, sup, prefer="up") == 512
    assert nearest_supported_resolution(100, sup, prefer="down") == 256
    assert nearest_supported_resolution(900, sup, prefer="up") == 768
    with pytest.raises(ValueError):
        nearest_supported_resolution(512, [])


def test_fit_to_resolution_square_output():
    r = fit_to_resolution(gradient(64, 128), 256)
    assert r.image.shape == (256, 256, 3)
