"""P6 scripts and startup wiring: profile builder CLI, demo, sweep grid, build_controller. No GPU, no torch."""
import importlib.util
import json
import os
import pathlib

import pytest

from backend.app.config import Settings, load_settings
from backend.app.services.adaptive import build_controller
from tests.adaptive_helpers import FIXTURE
from tests.test_adaptive_profiles import _result, _write

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "evaluation" / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_profile_cli_writes_profile_from_measured_results(tmp_path):
    res = tmp_path / "res"
    res.mkdir()
    _write(res, _result("E1"), _result("E2", steps=1, lat=(450.0, 500.0)))
    out = tmp_path / "profile.json"
    assert _load("build_adaptive_profile").main(["--results-dir", str(res), "--out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["synthetic"] is False and len(data["entries"]) == 2 and data["hardware"]["gpu_name"] == "SYNTH GPU"


def test_build_profile_cli_exit_2_when_nothing_measured(tmp_path):
    empty = tmp_path / "e"
    empty.mkdir()
    assert _load("build_adaptive_profile").main(["--results-dir", str(empty), "--out", str(tmp_path / "x.json")]) == 2
    assert not (tmp_path / "x.json").exists()


def test_demo_runs_and_labels_output_synthetic(tmp_path):
    out = tmp_path / "d.json"
    assert _load("demo_p6_controller").main(["--out", str(out)]) == 0
    d = json.loads(out.read_text())
    assert d["synthetic"] is True and any(r.get("simulated_oom") for r in d["rows"])


def test_sweep_grid_is_unique_and_valid():
    sweep = _load("run_p6_profile_sweep")
    g = sweep.grid([256, 512], ["fp16", "fp32"], [1, 2, 4])
    assert len(g) == 12 and len({e.id for e in g}) == 12
    assert {e.config.resolution for e in g} == {256, 512}


def test_build_controller_off_by_default_and_refuses_synthetic_unless_allowed(tmp_path):
    assert build_controller(Settings(output_dir=tmp_path)) == (None, None)
    with pytest.raises(ValueError, match="synthetic"):
        build_controller(Settings(output_dir=tmp_path, adaptive_profile=FIXTURE))
    log = tmp_path / "logs" / "decisions.jsonl"
    ctl, mon = build_controller(Settings(output_dir=tmp_path, adaptive_profile=FIXTURE, adaptive_allow_synthetic=True,
                                         adaptive_decision_log=log))
    assert ctl is not None and mon is not None
    from ai_engine.adaptive import ControllerRequest
    from tests.adaptive_helpers import snap
    ctl.decide(ControllerRequest("quick", 512), snap())
    line = json.loads(log.read_text().splitlines()[0])
    assert line["schema"] == "adaptive_decision/1"


def test_settings_read_adaptive_env_and_default_to_off():
    keys = ["ADAPTIVE_PROFILE", "ADAPTIVE_POLICY", "ADAPTIVE_ALLOW_SYNTHETIC", "ADAPTIVE_DECISION_LOG"]
    saved = {k: os.environ.pop(k, None) for k in keys}
    try:
        s = load_settings()
        assert s.adaptive_profile is None and s.adaptive_allow_synthetic is False
        os.environ["ADAPTIVE_PROFILE"] = "p.json"
        os.environ["ADAPTIVE_ALLOW_SYNTHETIC"] = "true"
        s = load_settings()
        assert s.adaptive_profile == pathlib.Path("p.json") and s.adaptive_allow_synthetic is True
    finally:
        for k in keys:
            os.environ.pop(k, None)
            if saved[k] is not None:
                os.environ[k] = saved[k]
