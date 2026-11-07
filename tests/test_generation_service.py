import threading
import time

from tests.conftest import GOOD


def test_model_load_reported_once_and_excluded_from_end_to_end(client, engine):
    engine.load_delay, engine.gen_delay = 0.3, 0.02
    first = client.post("/api/v1/generate", json=GOOD).json()["performance"]
    second = client.post("/api/v1/generate", json=GOOD).json()["performance"]
    assert first["model_load_ms"] >= 280
    assert first["end_to_end_ms"] < 250  # load time not folded into generation latency
    assert second["model_load_ms"] is None


def test_concurrent_request_gets_retryable_429_and_health_stays_up(client, engine):
    engine.block = True
    results = {}

    def first():
        results["a"] = client.post("/api/v1/generate", json=GOOD)

    t = threading.Thread(target=first)
    t.start()
    assert engine.entered.wait(5)
    r = client.post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 429 and j["error"]["code"] == "RESOURCE_EXHAUSTED" and j["error"]["retryable"]
    assert client.get("/health").status_code == 200  # event loop not blocked by generation
    engine.release.set()
    t.join(10)
    assert results["a"].status_code == 200
    assert len(engine.calls) == 1  # the rejected request never reached the engine
    engine.block = False
    assert client.post("/api/v1/generate", json=GOOD).status_code == 200
