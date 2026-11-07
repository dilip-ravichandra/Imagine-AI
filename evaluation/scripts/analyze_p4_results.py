"""Turn raw P4 result files into the quality-cost table + a gate check. Mechanical; adds no interpretation.

Usage (repo root):  python evaluation/scripts/analyze_p4_results.py [--results DIR] [--min-runs 10] [--allow-cpu]
Writes evaluation/reports/p4_quality_cost_table.md and .json. Exit 0 if the P4 gate is met, 1 if not.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.optimization.report import build_report, render_markdown  # noqa: E402


def main(argv=None) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "evaluation" / "results" / "p4"))
    ap.add_argument("--out-dir", default=str(ROOT / "evaluation" / "reports"))
    ap.add_argument("--min-runs", type=int, default=10)
    ap.add_argument("--allow-cpu", action="store_true", help="count non-GPU runs as measured (not the target setup)")
    args = ap.parse_args(argv)
    rep = build_report(Path(args.results), min_runs=args.min_runs, require_gpu=not args.allow_cpu)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "p4_quality_cost_table.md").write_text(render_markdown(rep), encoding="utf-8")
    (out / "p4_quality_cost_table.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(render_markdown(rep))
    return 0 if rep["gate"]["met"] else 1


if __name__ == "__main__":
    sys.exit(main())
