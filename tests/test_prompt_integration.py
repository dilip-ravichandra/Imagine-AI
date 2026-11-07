from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.generation import GenerationService
from tests.conftest import GOOD

EXPECTED_KEYS = {"status", "request_id", "image_url", "generation", "performance", "quality", "resource_decision"}


def test_engine_receives_raw_prompt_unchanged(client, engine):
    raw = "  A red robot\tbeside   a blue submarine \n"
    r = client.post("/api/v1/generate", json={**GOOD, "prompt": raw})
    assert r.status_code == 200
    assert engine.calls[0]["prompt"] == raw  # no trimming, no rewriting from the analysis


def test_generate_response_schema_unchanged(client):
    j = client.post("/api/v1/generate", json=GOOD).json()
    assert set(j) == EXPECTED_KEYS  # analysis is NOT added to the frozen response


def test_parser_failure_does_not_break_generation(engine, settings, monkeypatch):
    import backend.app.services.generation as g
    monkeypatch.setattr(g, "analyze_prompt", lambda p: (_ for _ in ()).throw(RuntimeError("boom")))
    c = TestClient(create_app(engine=engine, settings=settings), raise_server_exceptions=False)
    assert c.post("/api/v1/generate", json=GOOD).status_code == 200
    assert GenerationService.analyze("a cat") is None


def test_blank_prompt_rejected_on_generate(client, engine):
    for p in ["   ", "\n\t"]:
        r = client.post("/api/v1/generate", json={**GOOD, "prompt": p})
        assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_REQUEST"
    assert engine.calls == []


def test_analysis_endpoint_ok(client):
    r = client.post("/api/v1/prompt/analysis", json={"prompt": GOOD["prompt"]})
    assert r.status_code == 200
    j = r.json()
    assert j["raw_prompt"] == GOOD["prompt"] and j["validation"]["valid"] is True
    assert [o["name"] for o in j["objects"]] == ["robot", "submarine"]
    assert j["relations"][0]["relation"] == "beside" and [e["name"] for e in j["environment"]] == ["underwater"]


def test_analysis_endpoint_does_not_touch_engine(client, engine):
    client.post("/api/v1/prompt/analysis", json={"prompt": "a cat"})
    assert engine.calls == [] and engine.loaded is False


def test_analysis_endpoint_validation(client):
    for body in [{"prompt": ""}, {"prompt": "   "}, {"prompt": "a" * 501}, {}, {"prompt": 5}]:
        r = client.post("/api/v1/prompt/analysis", json=body)
        j = r.json()
        assert r.status_code == 422 and j["error"]["code"] == "INVALID_REQUEST" and "Traceback" not in r.text


def test_analysis_endpoint_accepts_500_chars(client):
    assert client.post("/api/v1/prompt/analysis", json={"prompt": "a cat " * 83 + "ab"}).status_code == 200
