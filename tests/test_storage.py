import pytest
from PIL import Image

from backend.app.services.storage import ImageStore


def test_save_atomic_png_and_name(tmp_path):
    store = ImageStore(tmp_path / "o", 10)
    name = store.save(Image.new("RGB", (8, 8)), "a" * 32)
    assert name == "a" * 32 + ".png"
    assert [p.name for p in (tmp_path / "o").iterdir()] == [name]  # no temp file left behind


@pytest.mark.parametrize("bad", ["../evil", "abc", "A" * 32, "a" * 31 + "/", ""])
def test_rejects_unsafe_ids(tmp_path, bad):
    with pytest.raises(ValueError):
        ImageStore(tmp_path, 10).save(Image.new("RGB", (8, 8)), bad)


def test_prune_keeps_newest_and_never_deletes_current(tmp_path):
    import os, time
    store = ImageStore(tmp_path, 3)
    base = time.time() - 100
    for i in range(5):
        store.save(Image.new("RGB", (8, 8)), f"{i:032x}")
        os.utime(tmp_path / f"{i:032x}.png", (base + i, base + i))
    assert sorted(p.name for p in tmp_path.glob("*.png")) == [f"{i:032x}.png" for i in (2, 3, 4)]


def test_prune_with_tied_timestamps_keeps_just_saved(tmp_path):
    import os
    store = ImageStore(tmp_path, 2)
    for i in range(3):
        store.save(Image.new("RGB", (8, 8)), f"{i:032x}")
        os.utime(tmp_path / f"{i:032x}.png", (1000, 1000))  # identical mtimes
    names = {p.name for p in tmp_path.glob("*.png")}
    assert f"{2:032x}.png" in names and len(names) == 2
