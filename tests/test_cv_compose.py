import ast
import pathlib

import numpy as np
import pytest

from computer_vision import CVResult, to_array, to_pil, validate_image
from computer_vision.edge_aware import bilateral_smooth, edge_preserving_sharpen
from computer_vision.enhancement import auto_enhance
from computer_vision.resize import fit_to_resolution, resize_image
from tests.cv_helpers import gradient, noisy

ROOT = pathlib.Path(__file__).resolve().parents[1] / "computer_vision"


def test_stages_chain_through_cvresult_image():
    img = noisy(gradient(100, 150), 6.0)
    r1 = fit_to_resolution(img, 256, mode="pad")
    r2 = auto_enhance(r1.image)
    r3 = bilateral_smooth(r2.image, strength=0.5)
    r4 = edge_preserving_sharpen(r3.image, amount=0.5)
    for r in (r1, r2, r3, r4):
        assert isinstance(r, CVResult) and r.image.shape == (256, 256, 3) and r.image.dtype == np.uint8
    assert [r.stage for r in (r1, r2, r3, r4)] == ["resize", "auto_enhance", "bilateral", "sharpen"]


def test_bypassing_every_stage_is_identity():
    img = noisy(gradient(64, 64), 6.0)
    cur = img
    for stage in (lambda a: resize_image(a, 64, 64, enabled=False), lambda a: auto_enhance(a, enabled=False),
                  lambda a: bilateral_smooth(a, enabled=False), lambda a: edge_preserving_sharpen(a, enabled=False)):
        r = stage(cur)
        assert not r.applied
        cur = r.image
    assert np.array_equal(cur, img)


def test_pil_roundtrip_and_validation_helpers():
    from PIL import Image
    pil = Image.fromarray(gradient(20, 30))
    arr = to_array(pil)
    assert arr.dtype == np.uint8 and arr.shape == (20, 30, 3) and np.array_equal(to_array(to_pil(arr)), arr)
    assert to_array(Image.new("RGBA", (4, 4), (10, 20, 30, 0))).shape == (4, 4, 3)  # alpha dropped
    assert to_array(Image.new("L", (4, 4), 9)).shape == (4, 4, 3)
    with pytest.raises(ValueError):
        validate_image(np.zeros((4, 4, 3), np.int16))


def _imports(path: pathlib.Path) -> set:
    mods = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(("." * node.level) + node.module)
        elif isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
    return mods


@pytest.mark.parametrize("pkg,others", [("resize", ("enhancement", "edge_aware", "quality", "artifacts")),
                                        ("enhancement", ("resize", "edge_aware", "quality", "artifacts")),
                                        ("edge_aware", ("resize", "enhancement", "quality", "artifacts")),
                                        ("quality", ("resize", "enhancement", "edge_aware", "artifacts")),
                                        ("artifacts", ("resize",))])
def test_modules_are_independent(pkg, others):
    for f in (ROOT / pkg).glob("*.py"):
        for m in _imports(f):
            assert not any(o in m for o in others), f"{f.name} imports sibling stage via {m}"


def test_cv_package_has_no_torch_or_backend_dependency():
    for f in ROOT.rglob("*.py"):
        for m in _imports(f):
            assert m.split(".")[0] not in {"torch", "diffusers", "backend", "ai_engine", "fastapi"}, (f.name, m)
