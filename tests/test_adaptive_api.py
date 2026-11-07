"""P6 through the real HTTP layer (needs fastapi/pydantic installed, as the other API tests do)."""
import dataclasses

from fastapi.testclient import TestClient

from backend.app.main import create_app
from ai_engine.adaptive import StaticMonitor
from tests.adaptive_helpers import controller, snap
from tests.conftest import GOOD


def _client(engine, settings, budget):
    # The synthetic fixture profile describes "synthetic/model-a"; the controller refuses entries whose model_id
    # differs from the loaded engine's (RUNTIME_LOCKED), so align the test settings with the fixture.
    settings = dataclasses.replace(settings, model_id="synthetic/model-a")
    app = create_app(engine=engine, settings=settings, controller=controller(), monitor=StaticMonitor(snap(budget)))
    return TestClient(app, raise_server_exceptions=False)


def test_resource_decision_reports_controller_choice(engine, settings):
    r = _client(engine, settings, 12000.0).post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 200 and j["generation"]["steps"] == 2
    assert j["resource_decision"]["fallback_used"] is False and "Balanced mode" in j["resource_decision"]["explanation"]


def test_no_safe_configuration_is_a_retryable_503_with_the_frozen_error_shape(engine, settings):
    r = _client(engine, settings, 500.0).post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 503 and j["status"] == "error" and j["error"]["code"] == "RESOURCE_EXHAUSTED"
    assert j["error"]["retryable"] is True and j["request_id"] and engine.calls == []
