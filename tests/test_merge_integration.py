"""Cross-phase integration tests added when the P3B / P5B / P6 / P7B branches were combined.

These cover the places where independently built phases touch the same code:
  * GenerationService.generate(): P5B CV hook + P6 adaptive controller in ONE request;
  * SDTurboEngine.ensure_loaded(): P3B adapter loading + P4 precision/offload/slicing in one load.
They use the fake engine / fake ML stack only: they prove wiring, NOT real-GPU behaviour.
"""
import dataclasses

from fastapi.testclient import TestClient

from ai_engine.adaptive import StaticMonitor
from backend.app.main import create_app
from tests.adaptive_helpers import controller, snap
from tests.conftest import GOOD


def _client(engine, settings, **changes):
    s = dataclasses.replace(settings, model_id="synthetic/model-a", **changes)  # match the synthetic profile
    app = create_app(engine=engine, settings=s, controller=controller(), monitor=StaticMonitor(snap(12000.0)))
    return TestClient(app, raise_server_exceptions=False)


def test_cv_assess_and_adaptive_controller_in_one_request(engine, settings):
    r = _client(engine, settings, cv_mode="assess").post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 200, j
    assert len(engine.calls) == 1  # generated exactly once (a bad merge once generated twice)
    assert j["quality"] is not None and j["performance"]["cv_ms"] is not None  # P5B ran
    assert j["resource_decision"]["fallback_used"] is False  # P6 decided
    assert "Balanced mode" in j["resource_decision"]["explanation"]
    assert j["generation"]["steps"] == 2


def test_cv_off_with_controller_leaves_quality_null(engine, settings):
    r = _client(engine, settings, cv_mode="off").post("/api/v1/generate", json=GOOD)
    j = r.json()
    assert r.status_code == 200 and j["quality"] is None and j["performance"]["cv_ms"] is None
    assert len(engine.calls) == 1


def test_settings_expose_all_phase_knobs_with_safe_defaults():
    from backend.app.config import Settings
    s = Settings()
    assert s.adapter_path is None and s.cv_mode == "off" and s.adaptive_profile is None
    assert s.precision == "auto" and s.offload == "none"


# ---- P3B adapter + P4 optimisation settings in ONE engine load ---------------------------------------------
import types  # noqa: E402

from backend.app.config import Settings  # noqa: E402
from backend.app.services import engine as eng  # noqa: E402
from tests.adapter_fixture import REV, make_approved  # noqa: E402
from tests.test_adapter_engine import FakeOOM, install  # noqa: E402


def _optimised_stack(monkeypatch, lora_error=None):
    st = install(monkeypatch, lora_error=lora_error)
    torch, Auto = eng._import_ml()
    st.update(kwargs=[], applied=[])

    class AutoOpt:
        @staticmethod
        def from_pretrained(model_id, **kw):
            st["kwargs"].append(kw)
            p = Auto.from_pretrained(model_id, **kw)
            p.enable_attention_slicing = lambda: st["applied"].append("attention_slicing")
            p.vae = types.SimpleNamespace(enable_slicing=lambda: st["applied"].append("vae_slicing"))
            return p

    monkeypatch.setattr(eng, "_import_ml", lambda: (torch, AutoOpt))
    return st


def _opt_settings(tmp_path, adapter):
    return Settings(output_dir=tmp_path / "out", supported_resolutions=(256,), model_revision=REV, device="cpu",
                    precision="fp32", attention_slicing=True, vae_slicing=True, adapter_path=adapter)


def test_adapter_and_p4_settings_apply_together(tmp_path, monkeypatch):
    st = _optimised_stack(monkeypatch)
    d = make_approved(tmp_path)
    e = eng.SDTurboEngine(_opt_settings(tmp_path, d))
    e.ensure_loaded()
    assert st["kwargs"][0]["torch_dtype"] == "f32"  # P4 precision reached from_pretrained
    assert st["applied"] == ["attention_slicing", "vae_slicing"]  # P4 slicing applied
    assert len(st["lora_calls"]) == 1 and e.adapter_status()["active"]  # P3B adapter active on that same pipe
    assert e.load_info["precision"] == "fp32"
    assert e.generate("a red cup", 1, 256, 256, 1).precision == "fp32"


def test_failed_adapter_rebuild_keeps_p4_settings(tmp_path, monkeypatch):
    st = _optimised_stack(monkeypatch, lora_error=ValueError("bad lora"))
    e = eng.SDTurboEngine(_opt_settings(tmp_path, make_approved(tmp_path)))
    e.ensure_loaded()
    assert st["loads"] == 2 and not e.adapter_status()["active"]  # clean base pipe rebuilt, adapter dropped
    assert all(k["torch_dtype"] == "f32" for k in st["kwargs"])
    assert st["applied"] == ["attention_slicing", "vae_slicing"] * 2  # rebuilt pipe got the same P4 settings
