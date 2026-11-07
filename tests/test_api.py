import io
import re

from PIL import Image

from backend.app.schemas.v1 import ErrorResponse, GenerateResponse
from backend.app.services.errors import model_load_failed, out_of_memory
from tests.conftest import GOOD


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_capabilities_available(client):
    j = client.get("/api/v1/capabilities").json()
    assert j["quality_modes"] == ["quick", "balanced", "best"]
    assert j["generation_available"] is True
    assert (j["min_resolution"], j["max_resolution"]) == (256, 512)  # reflects server's supported set
    assert j["deployment_mode"] == "hybrid/cloud"


def test_capabilities_unavailable(client, engine):
    engine.available, engine.reason = False, "Install ML dependencies"
    assert client.get("/api/v1/capabilities").json()["generation_available"] is False


def test_generate_success_matches_contract(client, engine, settings):
    r = client.post("/api/v1/generate", json=GOOD)
    assert r.status_code == 200
    body = GenerateResponse.model_validate(r.json())  # exact frozen schema
    j = r.json()
    assert j["status"] == "success"
    assert re.fullmatch(r"http://testserver/images/[0-9a-f]{32}\.png", j["image_url"])
    assert j["request_id"] in j["image_url"]
    assert str(settings.output_dir) not in r.text and "\\" not in j["image_url"]
    g = j["generation"]
    assert (g["seed"], g["steps"], g["width"], g["height"]) == (42, 2, 512, 512)
    assert g["model"] == "fake/model" and g["model_revision"] == "rev-test"
    assert j["quality"] is None
    p = j["performance"]
    assert p["end_to_end_ms"] is not None
    for unmeasured in ("prompt_encode_ms", "denoise_ms", "decode_ms", "cv_ms", "peak_gpu_mb"):
        assert p[unmeasured] is None, unmeasured
    rd = j["resource_decision"]
    assert rd["fallback_used"] is False and "No adaptive controller" in rd["explanation"]
    assert engine.calls[0]["prompt"] == GOOD["prompt"]  # original prompt preserved


def test_image_is_served_over_http(client):
    url = client.post("/api/v1/generate", json=GOOD).json()["image_url"]
    img = client.get(url.replace("http://testserver", ""))
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(img.content)).size == (512, 512)


def test_mode_to_steps(client, engine):
    for mode, steps in (("quick", 1), ("balanced", 2), ("best", 4)):
        r = client.post("/api/v1/generate", json={**GOOD, "quality_mode": mode})
        assert r.json()["generation"]["steps"] == steps


def test_seed_omitted_server_picks_and_reports(client, engine):
    body = {k: v for k, v in GOOD.items() if k != "seed"}
    j = client.post("/api/v1/generate", json=body).json()
    assert 0 <= j["generation"]["seed"] < 2**32
    assert engine.calls[0]["seed"] == j["generation"]["seed"]


def test_defaults_applied(client, engine):
    j = client.post("/api/v1/generate", json={"prompt": "a cat"}).json()
    assert (j["generation"]["width"], j["generation"]["steps"]) == (512, 2)


def test_validation_errors_are_stable(client, engine):
    for bad in ({"prompt": ""}, {"prompt": "x", "quality_mode": "ultra"},
                {"prompt": "x", "resolution": 100}, {"prompt": "x" * 501}, {}):
        r = client.post("/api/v1/generate", json=bad)
        j = ErrorResponse.model_validate(r.json()).model_dump()
        assert r.status_code == 422 and j["error"]["code"] == "INVALID_REQUEST"
        assert "Traceback" not in r.text
    assert engine.calls == []


def test_unsupported_resolution_rejected_before_engine(client, engine):
    r = client.post("/api/v1/generate", json={**GOOD, "resolution": 1024})  # valid for contract, not supported
    j = r.json()
    assert r.status_code == 422 and j["error"]["code"] == "INVALID_REQUEST"
    assert "256, 384, 512" in j["error"]["suggested_action"]
    assert engine.calls == []


def test_engine_unavailable_is_safe_503(client, engine):
    engine.available, engine.reason = False, "Install ML dependencies: pip install -r requirements-ml.txt"
    r = client.post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 503 and j["error"]["code"] == "INTERNAL_ERROR"
    assert j["error"]["retryable"] is False and "requirements-ml.txt" in j["error"]["suggested_action"]


def test_oom_is_retryable_resource_exhausted_and_recovers(client, engine):
    engine.gen_error = out_of_memory()
    r = client.post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 503 and j["error"]["code"] == "RESOURCE_EXHAUSTED" and j["error"]["retryable"]
    assert client.post("/api/v1/generate", json=GOOD).status_code == 200  # guard released


def test_unexpected_engine_error_does_not_leak_details(client, engine):
    engine.gen_error = RuntimeError(r"boom at C:\Users\secret\path.py line 9")
    r = client.post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 500 and j["error"]["code"] == "INTERNAL_ERROR" and j["error"]["retryable"]
    assert "secret" not in r.text and "Traceback" not in r.text and j["request_id"]
    assert client.post("/api/v1/generate", json=GOOD).status_code == 200


def test_model_load_failure_then_retry_succeeds(client, engine):
    engine.load_error = model_load_failed()
    r = client.post("/api/v1/generate", json=GOOD)
    assert r.status_code == 500 and r.json()["error"]["retryable"] is True
    assert client.post("/api/v1/generate", json=GOOD).status_code == 200


def test_static_path_traversal_blocked(client):
    for p in ("/images/%2e%2e/README.md", "/images/../README.md", "/images/nope.png"):
        assert client.get(p).status_code == 404
