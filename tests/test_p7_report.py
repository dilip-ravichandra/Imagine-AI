import csv
import json

import pytest

from ai_engine.evaluation import get
from ai_engine.evaluation.dryrun import SyntheticEngine
from ai_engine.evaluation.harness import run_variant
from ai_engine.evaluation.report import (build_report, load_results, render_markdown, write_plot, write_raw_csv,
                                         write_review_sheet)
from tests.p7_helpers import ENV_GPU, PROMPTS, Clock, GpuFakeEngine, StubClip


def _run(tmp, vid, offset=0.0, n_prompts=4, seeds=(1, 2), repeats=3):
    return run_variant(get(vid), GpuFakeEngine(), PROMPTS[:n_prompts], list(seeds), repeats, 0, tmp, ENV_GPU,
                       clip=StubClip(offset), clock=Clock())


def test_gate_not_met_when_empty_and_never_crashes(tmp_path):
    rep = build_report(tmp_path)
    assert not rep["gate"]["met"] and rep["measured_variants"] == []
    md = render_markdown(rep)
    assert "NOT MET" in md and "NOT RUN" in md and "No approved adapter" in md and "not wired into this harness" in md


def test_gate_met_with_measured_baseline_optimized_and_clip(tmp_path):
    _run(tmp_path, "V0"), _run(tmp_path, "V2", offset=-0.02)
    rep = build_report(tmp_path, min_runs=10)
    assert rep["gate"]["met"], rep["gate"]
    v2 = next(r for r in rep["rows"] if r["id"] == "V2")
    d = v2["clip_delta_vs_V0"]
    assert d["mean_delta"] == pytest.approx(-0.02) and d["n_pairs"] == 8 and d["n_prompts"] == 4
    assert v2["n_ok"] == 24 and v2["measured"]


def test_gate_requires_min_runs_clip_and_optimized(tmp_path):
    _run(tmp_path, "V0", repeats=1)  # 8 timed runs < 10, and no optimized variant
    g = build_report(tmp_path, min_runs=10)["gate"]
    assert not g["met"] and any("only 8 timed runs" in p for p in g["problems"])
    assert any("no measured optimized" in p for p in g["problems"])


def test_synthetic_results_never_count_as_measured(tmp_path):
    for vid in ("V0", "V2"):
        run_variant(get(vid), SyntheticEngine(), PROMPTS, [1, 2], 3, 0, tmp_path, {"synthetic": True}, clock=Clock())
    rep = build_report(tmp_path, require_gpu=False)
    assert rep["measured_variants"] == [] and not rep["gate"]["met"]
    assert any("synthetic" in p for p in rep["gate"]["problems"])
    assert "SYNTHETIC" in render_markdown(rep)
    sheet = tmp_path / "sheet.csv"
    assert write_review_sheet(tmp_path, sheet, {}) == 0  # synthetic images are never offered for review


def test_cpu_run_is_not_measured_unless_allowed(tmp_path):
    env = {**ENV_GPU, "gpu_name": None}
    run_variant(get("V0"), GpuFakeEngine(), PROMPTS, [1], 3, 0, tmp_path, env, clip=StubClip(), clock=Clock())
    assert build_report(tmp_path, require_gpu=True)["measured_variants"] == []
    assert build_report(tmp_path, require_gpu=False)["measured_variants"] == ["V0"]


def test_failed_variant_is_not_measured(tmp_path):
    run_variant(get("V0"), GpuFakeEngine(raise_on=2), PROMPTS, [1], 3, 0, tmp_path, ENV_GPU, clock=Clock())
    row = next(r for r in build_report(tmp_path)["rows"] if r["id"] == "V0")
    assert row["status"] == "oom" and not row["measured"]


def test_cv_effect_isolated_from_generation_noise(tmp_path):
    _run(tmp_path, "V0"), _run(tmp_path, "V5")
    rep = build_report(tmp_path)
    v5 = next(r for r in rep["rows"] if r["id"] == "V5")
    own = v5["cv_clip_delta_vs_own_raw"]
    assert own["n_pairs"] == 8 and own["mean_delta"] == pytest.approx(0.0)  # stub CLIP ignores pixels: delta is exactly 0
    assert 0.0 <= v5["cv_applied_fraction"] <= 1.0
    assert "CV off vs on" in render_markdown(rep)


def test_fid_section_refuses_tiny_sets_with_alternative(tmp_path):
    _run(tmp_path, "V0")
    md = render_markdown(build_report(tmp_path, n_real_fid=0))
    assert "FID NOT computed" in md and "paired CLIP deltas" in md
    rep = build_report(tmp_path, n_real_fid=300)
    assert not rep["fid"]["allowed"]


def test_model_size_not_measured_is_stated(tmp_path):
    _run(tmp_path, "V0")
    assert "NOT MEASURED" in render_markdown(build_report(tmp_path, sizes=None))
    sizes = {"base_total_dir_bytes": 5 * 1048576, "base_weight_files": {"unet/x.safetensors": 3 * 1048576},
             "adapter_bytes": None, "extra": {}}
    md = render_markdown(build_report(tmp_path, sizes=sizes))
    assert "5 MB" in md and "3 MB" in md and "none / not measured" in md


def test_csv_review_sheet_plot_and_json_roundtrip(tmp_path):
    _run(tmp_path, "V0"), _run(tmp_path, "V2", offset=-0.01)
    csv_path = tmp_path / "runs.csv"
    assert write_raw_csv(tmp_path, csv_path) == 2 * 4 * 2 * 3
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    assert rows[0]["variant"] in ("V0", "V2") and "generation_ms" in rows[0]
    sheet = tmp_path / "sheet.csv"
    n = write_review_sheet(tmp_path, sheet, {p["id"]: p["prompt"] for p in PROMPTS})
    assert n == 2 * 4 * 2
    review = list(csv.DictReader(open(sheet, encoding="utf-8")))
    assert all(r["objects_and_counts_correct(y/n/partial)"] == "" for r in review)  # never pre-filled
    rep = build_report(tmp_path)
    assert write_plot(rep, tmp_path / "plot.png") and (tmp_path / "plot.png").stat().st_size > 0
    json.dumps(rep, default=str)
    assert set(load_results(tmp_path)) == {"V0", "V2"}


def test_plot_skips_when_not_enough_measured(tmp_path):
    _run(tmp_path, "V0")
    assert write_plot(build_report(tmp_path), tmp_path / "p.png") is False
