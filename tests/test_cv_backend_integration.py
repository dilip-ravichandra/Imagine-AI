import dataclasses
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import computer_vision
from backend.app.config import load_settings
from backend.app.main import create_app
from backend.app.schemas.v1 import GenerateResponse
from computer_vision.quality import estimate_noise_sigma
from tests.conftest import GOOD, FakeEngine
from tests.cv_helpers import darker, noisy, scene


class ImageEngine(FakeEngine):
    """Fake engine that returns a chosen numpy image (and remembers it)."""

    def __init__(self, make):
        super().__init__()
        self.make, self.last = make, None

    def generate(self, prompt, seed, width, height, steps):
        res = super().generate(prompt, seed, width, height, steps)
        self.last = self.make(width)
        res.image = Image.fromarray(self.last)
        return res


def client_for(engine, settings, mode):
    return TestClient(create_app(engine=engine, settings=dataclasses.replace(settings, cv_mode=mode)),
                      raise_server_exceptions=False)


def fetch(client, url):
    r = client.get(url.replace("http://testserver", ""))
    assert r.status_code == 200
    return np.asarray(Image.open(io.BytesIO(r.content)).convert("RGB"))


def test_default_is_off_and_response_unchanged(settings):
    eng = ImageEngine(lambda n: noisy(scene(n), 8.0))
    c = client_for(eng, settings, "off")
    j = c.post("/api/v1/generate", json=GOOD).json()
    assert j["quality"] is None and j["performance"]["cv_ms"] is None
    assert np.array_equal(fetch(c, j["image_url"]), eng.last)
    assert load_settings().cv_mode == "off"


def test_assess_reports_quality_and_leaves_pixels_alone(settings):
    eng = ImageEngine(lambda n: noisy(scene(n), 8.0))
    c = client_for(eng, settings, "assess")
    r = c.post("/api/v1/generate", json={**GOOD, "prompt": "a lighthouse on a cliff"})
    GenerateResponse.model_validate(r.json())
    j = r.json()
    q = j["quality"]
    assert "noise" in q["artifact_flags"] and q["clip_score"] is None
    assert q["sharpness"] > 0 and 0 <= q["brightness"] <= 1 and 0 <= q["contrast"] <= 1
    assert j["performance"]["cv_ms"] > 0 and j["performance"]["end_to_end_ms"] >= j["performance"]["cv_ms"]
    assert np.array_equal(fetch(c, j["image_url"]), eng.last)  # assess never alters the image


def test_correct_serves_corrected_image_and_reports_final_flags(settings):
    eng = ImageEngine(lambda n: noisy(scene(n), 8.0))
    c = client_for(eng, settings, "correct")
    j = c.post("/api/v1/generate", json={**GOOD, "prompt": "a lighthouse on a cliff"}).json()
    served = fetch(c, j["image_url"])
    assert not np.array_equal(served, eng.last)
    assert estimate_noise_sigma(served) < 0.5 * estimate_noise_sigma(eng.last)
    assert "noise" not in j["quality"]["artifact_flags"]  # flags describe the FINAL image


def test_semantic_flag_comes_from_prompt_not_pixels(settings):
    eng = ImageEngine(lambda n: scene(n))
    c = client_for(eng, settings, "assess")
    j = c.post("/api/v1/generate", json={**GOOD, "prompt": "two red cats beside a blue sofa"}).json()
    assert "semantic_review_recommended" in j["quality"]["artifact_flags"]
    j2 = c.post("/api/v1/generate", json={**GOOD, "prompt": "a lighthouse"}).json()
    assert j2["quality"]["artifact_flags"] == []  # clean synthetic scene + simple prompt
    j3 = c.post("/api/v1/generate", json={**GOOD, "prompt": "a lighthouse on a cliff"}).json()
    assert "semantic_review_recommended" in j3["quality"]["artifact_flags"]  # ANY spatial relation triggers it: frequent by design


def test_prompt_intent_suppresses_dark_correction(settings):
    eng = ImageEngine(lambda n: darker(scene(n), 0.3))
    c = client_for(eng, settings, "correct")
    j = c.post("/api/v1/generate", json={**GOOD, "prompt": "a lighthouse at night"}).json()
    assert np.array_equal(fetch(c, j["image_url"]), eng.last) and "dark" not in j["quality"]["artifact_flags"]
    j2 = c.post("/api/v1/generate", json={**GOOD, "prompt": "a lighthouse on a cliff"}).json()
    assert not np.array_equal(fetch(c, j2["image_url"]), eng.last)  # without the hint it IS brightened


def test_cv_failure_never_breaks_generation(settings, monkeypatch):
    eng = ImageEngine(lambda n: noisy(scene(n), 8.0))
    c = client_for(eng, settings, "correct")
    monkeypatch.setattr(computer_vision, "run_pipeline", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom C:\\secret")))
    r = c.post("/api/v1/generate", json=GOOD)
    assert r.status_code == 200 and "secret" not in r.text
    j = r.json()
    assert j["quality"] is None and j["performance"]["cv_ms"] is None
    assert np.array_equal(fetch(c, j["image_url"]), eng.last)


def test_invalid_cv_mode_rejected(monkeypatch):
    monkeypatch.setenv("CV_MODE", "turbo")
    with pytest.raises(ValueError):
        load_settings()
    monkeypatch.setenv("CV_MODE", "Correct")
    assert load_settings().cv_mode == "correct"
