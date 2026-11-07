"""P4 benchmark runner + report. ALL numbers here are SYNTHETIC outputs of a fake engine and a scripted clock.
They test the plumbing (counts, failure handling, stats, gate logic); they say nothing about real performance."""
import importlib.util
import json
import math
import pathlib

import pytest
from PIL import Image

from ai_engine.optimization import get
from ai_engine.optimization.benchmark import run_experiment, select_prompts
from ai_engine.optimization.report import build_report, load_results, render_markdown
from ai_engine.prompt.suite import load_suite
from backend.app.services.engine import EngineResult
from backend.app.services.errors import out_of_memory
from tests.conftest import FakeEngine

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = [{"id": "p1", "category": "simple", "prompt": "a cat"}, {"id": "p2", "category": "simple", "prompt": "a dog"}]
SEEDS = [1, 2]
GPU_ENV = {"gpu_name": "SYNTHETIC GPU", "model_id": "fake/model", "model_revision": "rev-test"}


class StepClock:
    """Each call advances by `ms`; a timed run reads it at start and end, so every run lasts exactly `ms`."""
    def __init__(self, ms):
        self.t, self.ms = 0.0, ms / 1000.0

    def __call__(self):
        self.t += self.ms
        return self.t


class ColorEngine(FakeEngine):
    """Image colour depends on steps, so pixel fidelity vs the 4-step baseline is known exactly."""
    def __init__(self, cuda=True):
        super().__init__()
        self.load_info = {"device": "cuda" if cuda else "cpu", "precision": "fp32", "optimizations": []}

    def generate(self, prompt, seed, width, height, steps):
        r = super().generate(prompt, seed, width, height, steps)
        return EngineResult(image=Image.new("RGB", (width, height), (200 + 10 * (4 - steps), 30, 30)),
                            model=r.model, model_revision=r.model_revision, precision=r.precision,
                            scheduler=r.scheduler, steps=steps, width=width, height=height, seed=seed,
                            peak_gpu_mb=1000.0 + 100 * steps)


def run(tmp_path, exp_id, engine=None, ms=10, repeats=2, warmup=1, env=GPU_ENV, clip=None, prompts=PROMPTS):
    engine = engine or ColorEngine()
    return run_experiment(get(exp_id), engine, prompts, SEEDS, repeats, warmup, tmp_path, dict(env),
                          ram_fn=lambda: 777.0, clip=clip, clock=StepClock(ms)), engine


# ---- prompt selection -------------------------------------------------------
def test_select_prompts_is_deterministic_dev_only():
    suite = load_suite()
    a, b = select_prompts(suite, 2), select_prompts(suite, 2)
    assert a == b and a
    holdout_ids = {c["id"] for c in suite["cases"] if c["split"] == "holdout"}
    assert not holdout_ids & {p["id"] for p in a}
    from collections import Counter
    assert max(Counter(p["category"] for p in a).values()) <= 2
    assert {"ambiguous", "unseen"}.isdisjoint({p["category"] for p in a})


# ---- run_experiment ---------------------------------------------------------
def test_run_counts_args_images_and_json(tmp_path):
    res, eng = run(tmp_path, "E2")  # steps=2
    assert res["status"] == "ok" and len(res["runs"]) == 2 * 2 * 2
    assert len(eng.calls) == 1 + 8  # warm-up generation + timed runs
    assert all(c["steps"] == 2 and c["width"] == 512 for c in eng.calls)
    assert len(list((tmp_path / "images" / "E2").glob("*.png"))) == 4  # first repeat only
    on_disk = json.loads((tmp_path / "E2.json").read_text())
    assert on_disk["experiment"]["changed_fields"] == ["steps"] and on_disk["schema"].startswith("p4_experiment")
    assert on_disk["generation_seen"]["steps"] == 2 and on_disk["protocol"]["seeds"] == SEEDS
    lat = res["summary"]["latency_ms"]
    assert lat["n"] == 8 and lat["median"] == pytest.approx(10.0) and res["summary"]["peak_process_ram_mb"] == 777.0
    assert res["summary"]["peak_allocated_mb"]["median"] == pytest.approx(1200.0)


def test_clip_scored_only_first_repeat_outside_timing(tmp_path):
    class Clip:
        calls = 0
        def score(self, prompt, image):
            Clip.calls += 1
            return 0.25
    res, _ = run(tmp_path, "B0", clip=Clip())
    assert Clip.calls == 4 and res["summary"]["clip_score"]["n"] == 4
    assert res["summary"]["latency_ms"]["median"] == pytest.approx(10.0)  # scoring did not enter the timing


def test_oom_during_generation_is_recorded_and_stops(tmp_path):
    e = ColorEngine()
    e.gen_error, e.gen_error_once = out_of_memory(), False
    res, _ = run(tmp_path, "B0", engine=e, warmup=0)
    assert res["status"] == "oom" and res["summary"]["n_ok"] == 0 and len(res["runs"]) == 1
    assert (tmp_path / "B0.json").exists()


def test_oom_at_load_and_warmup(tmp_path):
    e = ColorEngine()
    e.load_error = out_of_memory()
    res, _ = run(tmp_path, "B0", engine=e)
    assert res["status"] == "oom" and res["runs"] == []
    e2 = ColorEngine()
    e2.gen_error, e2.gen_error_once = out_of_memory(), False
    res2, _ = run(tmp_path / "w", "B0", engine=e2, warmup=1)
    assert res2["status"] == "oom" and res2["runs"] == []


def test_unexpected_error_is_recorded_as_error(tmp_path):
    e = ColorEngine()
    e.gen_error, e.gen_error_once = ValueError("boom"), False
    res, _ = run(tmp_path, "B0", engine=e, warmup=0)
    assert res["status"] == "error" and res["error"].startswith("ValueError")


# ---- report / gate ----------------------------------------------------------
def _results(tmp_path, ids_ms, env=GPU_ENV, cuda=True, repeats=2):
    for exp_id, ms in ids_ms.items():
        run(tmp_path, exp_id, engine=ColorEngine(cuda=cuda), ms=ms, repeats=repeats, env=env)


def test_gate_met_with_baseline_and_two_strategies(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60, "E2": 50})
    rep = build_report(tmp_path, min_runs=8)
    assert rep["gate"]["met"] and rep["gate"]["measured_single_variable_strategies"] == ["E1", "E2"]
    rows = {r["id"]: r for r in rep["rows"]}
    assert rows["E1"]["latency_median_ratio_vs_B0"] == pytest.approx(0.6)
    assert rows["E1"]["latency_range_overlaps_B0"] is False
    assert rows["E2"]["peak_allocated_delta_mb_vs_B0"] == pytest.approx(-200.0)  # steps 2 vs 4 in the fake peak
    assert rows["E3"]["present"] is False and "E3" in rep["gate"]["missing_experiments"]


def test_fidelity_exact_and_identical(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60, "E2": 50})
    rows = {r["id"]: r for r in build_report(tmp_path, min_runs=8)["rows"]}
    assert rows["E1"]["fidelity_vs_B0"]["identical_pairs"] == 4 == rows["E1"]["fidelity_vs_B0"]["pairs"]
    assert rows["E1"]["fidelity_vs_B0"]["psnr_db"] is None  # identical images: no infinite PSNR
    f = rows["E2"]["fidelity_vs_B0"]
    assert f["identical_pairs"] == 0 and f["psnr_db"]["mean"] == pytest.approx(10 * math.log10(255 ** 2 / (20 ** 2 / 3)))
    assert rows["B0"]["fidelity_vs_B0"] is None


def test_gate_not_met_cases(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60})
    assert not build_report(tmp_path, min_runs=8)["gate"]["met"]  # only one strategy
    _results(tmp_path, {"E2": 50})
    assert build_report(tmp_path, min_runs=8)["gate"]["met"]
    assert not build_report(tmp_path, min_runs=99)["gate"]["met"]  # too few runs per experiment


def test_gate_requires_gpu_measurements_by_default(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60, "E2": 50}, env={"gpu_name": None, "model_revision": "r"}, cuda=False)
    assert not build_report(tmp_path, min_runs=8)["gate"]["met"]
    assert build_report(tmp_path, min_runs=8, require_gpu=False)["gate"]["met"]


def test_combined_experiment_does_not_count_as_strategy(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60, "C1": 40})
    g = build_report(tmp_path, min_runs=8)["gate"]
    assert not g["met"] and g["measured_single_variable_strategies"] == ["E1"]


def test_failed_baseline_blocks_gate_and_is_reported(tmp_path):
    e = ColorEngine()
    e.gen_error, e.gen_error_once = out_of_memory(), False
    run(tmp_path, "B0", engine=e, warmup=0)
    _results(tmp_path, {"E1": 60, "E2": 50})
    rep = build_report(tmp_path, min_runs=8)
    assert not rep["gate"]["met"] and not rep["gate"]["baseline_measured"]
    assert "oom" in render_markdown(rep)


def test_warnings_for_mixed_scheduler_unpinned_and_protocol(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60})
    p = tmp_path / "E1.json"
    d = json.loads(p.read_text())
    d["generation_seen"]["scheduler"] = "OtherScheduler"
    d["generation_seen"]["model_revision"] = "unpinned (hub default)"
    d["protocol"]["seeds"] = [9]
    p.write_text(json.dumps(d))
    w = " ".join(build_report(tmp_path, min_runs=8)["warnings"])
    assert "schedulers differ" in w and "UNPINNED" in w and "protocols" in w


def test_markdown_labels_and_no_data(tmp_path):
    _results(tmp_path, {"B0": 100, "E1": 60, "C1": 40})
    md = render_markdown(build_report(tmp_path, min_runs=8))
    assert "COMBINED" in md and "NOT RUN" in md and "no interpretation" in md and "NOT MET" in md
    empty = build_report(tmp_path / "missing", min_runs=8)
    assert not empty["gate"]["met"] and len(empty["gate"]["missing_experiments"]) == 8
    assert load_results(tmp_path / "missing") == {}


# ---- CLI scripts ------------------------------------------------------------
def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "evaluation" / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_runner_cli_list_noargs_and_unpinned_refusal(monkeypatch, capsys):
    m = _load("run_p4_benchmarks")
    assert m.main(["--list"]) == 0 and "E1" in capsys.readouterr().out
    assert m.main([]) == 2
    monkeypatch.delenv("MODEL_REVISION", raising=False)
    assert m.main(["--only", "B0"]) == 2 and "MODEL_REVISION" in capsys.readouterr().out


def test_analyzer_cli_exit_codes(tmp_path):
    m = _load("analyze_p4_results")
    assert m.main(["--results", str(tmp_path / "none"), "--out-dir", str(tmp_path / "rep")]) == 1
    assert (tmp_path / "rep" / "p4_quality_cost_table.md").exists()
    _results(tmp_path / "res", {"B0": 100, "E1": 60, "E2": 50})
    assert m.main(["--results", str(tmp_path / "res"), "--out-dir", str(tmp_path / "rep"), "--min-runs", "8"]) == 0
