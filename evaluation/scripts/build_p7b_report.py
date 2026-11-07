"""P7B: write eval_P3_TeamID.md, ablation_study.md, failure_analysis.md from REAL P7A outputs. Mechanical + TODO(team) gaps.

Run after run_p7_eval.py and analyze_p7_results.py, and after filling evaluation/reports/p7_human_review.csv:
  python evaluation/scripts/build_p7b_report.py --usns 1XX23AB001,1XX23AB002 [--team-id TeamID]
Outputs go to evaluation/reports/. Exit 0 if no TODO(team) is left, else 1 (so you cannot forget to finish it).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.evaluation.p7b import (TODO, load_review, render_ablation, render_eval_md,  # noqa: E402
                                      render_failure_analysis, tally_review)
from ai_engine.evaluation.report import build_report  # noqa: E402
from ai_engine.evaluation.sizes import find_hf_snapshot, size_report  # noqa: E402
import os  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "evaluation" / "results" / "p7"))
    ap.add_argument("--reports", default=str(ROOT / "evaluation" / "reports"))
    ap.add_argument("--usns", default="", help="comma-separated team USNs (first line of eval file)")
    ap.add_argument("--team-id", default="TeamID")
    ap.add_argument("--min-runs", type=int, default=10)
    ap.add_argument("--allow-cpu", action="store_true")
    ap.add_argument("--n-real-fid", type=int, default=0)
    a = ap.parse_args(argv)
    usns = [u.strip() for u in a.usns.split(",") if u.strip()]
    md = find_hf_snapshot(os.environ.get("MODEL_ID", "stabilityai/sd-turbo"), os.environ.get("MODEL_REVISION"))
    rep = build_report(Path(a.results), a.min_runs, not a.allow_cpu, size_report(md), a.n_real_fid)
    reports = Path(a.reports)
    reports.mkdir(parents=True, exist_ok=True)
    rows = load_review(reports / "p7_human_review.csv")
    review = tally_review(rows)
    texts = {f"eval_P3_{a.team_id}.md": render_eval_md(rep, usns, review),
             "ablation_study.md": render_ablation(rep, review),
             "failure_analysis.md": render_failure_analysis(rows)}
    todo = 0
    for name, text in texts.items():
        (reports / name).write_text(text, encoding="utf-8")
        todo += text.count(TODO)
        print(f"wrote {reports / name}")
    print(f"P7 gate met: {rep['gate']['met']}; unresolved {TODO} markers: {todo}")
    return 0 if (todo == 0 and rep["gate"]["met"]) else 1


if __name__ == "__main__":
    sys.exit(main())
