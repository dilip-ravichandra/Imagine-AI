"""Turn raw P7 result files into the report, CSVs, review sheet and plot. Mechanical; adds no interpretation.

Usage (repo root):
  python evaluation/scripts/analyze_p7_results.py [--results DIR] [--min-runs 10] [--allow-cpu]
        [--model-dir PATH | auto from MODEL_ID+MODEL_REVISION in the HF cache] [--adapter PATH] [--n-real-fid N]
Writes evaluation/reports/p7_report.md/.json, p7_runs.csv, p7_human_review.csv, p7_failure_cases_TEMPLATE.md, p7_quality_cost.png.
Exit 0 if the P7 gate is met, 1 if not.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.evaluation.report import (FAILURE_TEMPLATE, build_report, render_markdown, write_plot,  # noqa: E402
                                         write_raw_csv, write_review_sheet)
from ai_engine.evaluation.sizes import find_hf_snapshot, size_report  # noqa: E402
from ai_engine.prompt.suite import load_suite  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "evaluation" / "results" / "p7"))
    ap.add_argument("--out-dir", default=str(ROOT / "evaluation" / "reports"))
    ap.add_argument("--min-runs", type=int, default=10)
    ap.add_argument("--allow-cpu", action="store_true")
    ap.add_argument("--model-dir", default=None)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--n-real-fid", type=int, default=0, help="size of a real reference image set (0 = none exists)")
    a = ap.parse_args(argv)
    model_dir = Path(a.model_dir) if a.model_dir else find_hf_snapshot(
        os.environ.get("MODEL_ID", "stabilityai/sd-turbo"), os.environ.get("MODEL_REVISION"))
    sizes = size_report(model_dir, Path(a.adapter) if a.adapter else None)
    rep = build_report(Path(a.results), a.min_runs, not a.allow_cpu, sizes, a.n_real_fid)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = render_markdown(rep)
    (out / "p7_report.md").write_text(md, encoding="utf-8")
    (out / "p7_report.json").write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
    write_raw_csv(Path(a.results), out / "p7_runs.csv")
    prompts = {c["id"]: c["prompt"] for c in load_suite()["cases"]}
    write_review_sheet(Path(a.results), out / "p7_human_review.csv", prompts)
    (out / "p7_failure_cases_TEMPLATE.md").write_text(FAILURE_TEMPLATE, encoding="utf-8")
    plotted = write_plot(rep, out / "p7_quality_cost.png")
    print(md)
    print(f"[plot written: {plotted}]")
    return 0 if rep["gate"]["met"] else 1


if __name__ == "__main__":
    sys.exit(main())
