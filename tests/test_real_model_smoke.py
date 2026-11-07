"""REAL-MODEL SMOKE TEST — downloads/loads stabilityai/sd-turbo and generates one image.
Skipped by default. Run on the GPU laptop:  set RUN_REAL_MODEL=1  (PowerShell: $env:RUN_REAL_MODEL="1")
then: python -m pytest tests/test_real_model_smoke.py -s -m real_model"""
import io
import json
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.config import load_settings
from backend.app.main import create_app

pytestmark = [pytest.mark.real_model,
              pytest.mark.skipif(os.getenv("RUN_REAL_MODEL") != "1", reason="set RUN_REAL_MODEL=1 to run")]


def test_real_generation_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    client = TestClient(create_app(settings=load_settings()), raise_server_exceptions=False)
    assert client.get("/api/v1/capabilities").json()["generation_available"] is True
    body = {"prompt": "A red robot beside a blue submarine underwater",
            "quality_mode": "balanced", "resolution": 512, "seed": 42}
    r = client.post("/api/v1/generate", json=body)
    print(json.dumps(r.json(), indent=2))  # paste this into TEST_RESULTS.md
    assert r.status_code == 200, r.text
    j = r.json()
    img = client.get(j["image_url"].replace("http://testserver", ""))
    assert img.status_code == 200
    assert Image.open(io.BytesIO(img.content)).size == (512, 512)
    assert j["performance"]["model_load_ms"] is not None
    # second call must reuse the loaded pipeline
    j2 = client.post("/api/v1/generate", json=body).json()
    assert j2["performance"]["model_load_ms"] is None
    print("second-call end_to_end_ms:", j2["performance"]["end_to_end_ms"])
