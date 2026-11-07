"""Run the versioned prompt suite and write evaluation/results/prompt_suite_v1_results.json.

Usage (from repo root):  python evaluation/scripts/run_prompt_suite.py [dev|holdout]
Exit code 0 always (this is a report, not a gate); failures are listed.
"""
import datetime
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.prompt import PARSER_VERSION  # noqa: E402
from ai_engine.prompt.suite import load_suite, run_suite, summarize  # noqa: E402


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else None
    suite = load_suite()
    res = run_suite(suite, split)
    out = {"suite_version": suite["suite_version"], "parser_version": PARSER_VERSION,
           "split": split or "all", "date": datetime.date.today().isoformat(), "python": platform.python_version(),
           "summary": summarize(res), "cases": res}
    (ROOT / "evaluation" / "results" / "prompt_suite_v1_results.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out["summary"], indent=1))
    for r in res:
        if not r["passed"]:
            print(f"FAIL {r['id']} [{r['split']}]: {r['prompt']}")
            for f in r["failures"]:
                print("   -", f[:200])


if __name__ == "__main__":
    main()
