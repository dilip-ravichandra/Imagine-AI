import csv
import sys
from pathlib import Path

from ai_engine.evaluation import get
from ai_engine.evaluation.harness import run_variant
from ai_engine.evaluation.p7b import (TODO, load_review, render_ablation, render_eval_md, render_failure_analysis,
                                      tally_review)
from ai_engine.evaluation.report import build_report, write_review_sheet
from tests.p7_helpers import ENV_GPU, PROMPTS, Clock, GpuFakeEngine, StubClip

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation" / "scripts"))
import build_p7b_report as cli  # noqa: E402


def _results(tmp, ids=("V0", "V2", "V5")):
    for i, vid in enumerate(ids):
        run_variant(get(vid), GpuFakeEngine(), PROMPTS, [1, 2], 3, 0, tmp, ENV_GPU, clip=StubClip(-0.01 * i), clock=Clock())
    return build_report(tmp)


def test_eval_first_line_is_usns_and_unknowns_are_todo(tmp_path):
    md = render_eval_md(_results(tmp_path), ["1AB23CS001", "1AB23CS002"])
    assert md.splitlines()[0] == "1AB23CS001,1AB23CS002"
    assert TODO in md and "NOT DONE" in md  # P3/P5B/P6/P8 gaps are declared, not hidden
    assert "V6" in md and "NOT RUN" in md
    assert render_eval_md(_results(tmp_path), []).splitlines()[0].startswith("TODO(team)")


def test_no_results_means_no_numbers_only_not_run(tmp_path):
    rep = build_report(tmp_path)
    md, ab = render_eval_md(rep, ["U1"]), render_ablation(rep)
    assert "NOT RUN" in md and "Median e2e" in md
    assert "NOT RUN or not a measured GPU run" in ab and "CLIP Δ" not in ab


def test_ablation_numbers_match_report_and_blocked_are_gaps(tmp_path):
    rep = _results(tmp_path)
    ab = render_ablation(rep)
    d = next(r for r in rep["rows"] if r["id"] == "V2")["clip_delta_vs_V0"]
    assert f"mean {d['mean_delta']:.4f}" in ab
    assert "V1" in ab and "COMBINED" in ab  # V4 labelled
    assert "NOT RUN — No approved adapter" in ab and "NOT RUN — Controller exists" in ab
    assert "Fixed variables" in ab and "precision=fp32" in ab.split("## V2")[1].split("## V3")[0]
    assert ab.count(f"**Interpretation:** {TODO}") >= 2  # never auto-interpreted


def test_review_tally_and_failure_cases(tmp_path):
    _results(tmp_path)
    sheet = tmp_path / "sheet.csv"
    write_review_sheet(tmp_path, sheet, {p["id"]: p["prompt"] for p in PROMPTS})
    rows = list(csv.DictReader(open(sheet, encoding="utf-8")))
    c, rcol, art = "objects_and_counts_correct(y/n/partial)", "spatial_relations_correct(y/n/partial/na)", "artifacts_seen"
    rows[0][c], rows[1][c], rows[1][art], rows[1]["notes"] = "Y", "N", "extra limb", "three cubes not two"
    rows[2][rcol] = "partial"
    with open(sheet, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(), w.writerows(rows)
    loaded = load_review(sheet)
    t = tally_review(loaded)
    v0 = t[rows[0]["variant"]]
    assert v0["reviewed"] == 3 and v0["counts"] == {"y": 1, "n": 1} and v0["relations"] == {"partial": 1}
    fa = render_failure_analysis(loaded)
    assert fa.count("## Case ") == 2 and "three cubes not two" in fa and "extra limb" in fa  # only flagged rows
    assert all(cat in fa for cat in ("Wrong object count", "Mobile export/runtime incompatibility"))


def test_failure_analysis_without_review_says_so():
    assert "No review sheet found" in render_failure_analysis([])
    assert load_review(Path("/nonexistent.csv")) == []


def test_cli_writes_files_and_fails_while_todos_remain(tmp_path, capsys):
    res, reps = tmp_path / "res", tmp_path / "rep"
    _results(res)
    rc = cli.main(["--results", str(res), "--reports", str(reps), "--usns", "A1,B2", "--team-id", "T7"])
    assert rc == 1  # TODO(team) markers remain
    assert (reps / "eval_P3_T7.md").read_text(encoding="utf-8").splitlines()[0] == "A1,B2"
    assert (reps / "ablation_study.md").exists() and (reps / "failure_analysis.md").exists()
    assert "unresolved" in capsys.readouterr().out
