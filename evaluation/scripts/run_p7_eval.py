"""P7A evaluation runner. RUN ON THE GPU LAPTOP for real numbers (the build sandbox has no GPU/model).

PowerShell, repo root, MODEL_REVISION pinned (commit hash of the model repo):
    $env:MODEL_REVISION="<commit hash>"
    python evaluation/scripts/run_p7_eval.py --list
    python evaluation/scripts/run_p7_eval.py --all --clip            # hold-out prompts, one subprocess per variant
    python evaluation/scripts/run_p7_eval.py --only V0 --only V1 --clip --prompts-per-category 2   # subset (recorded)
    python evaluation/scripts/run_p7_eval.py --only V0 --dry-run     # plumbing check, synthetic, NOT a measurement
Then:  python evaluation/scripts/analyze_p7_results.py
Outputs: evaluation/results/p7/<ID>.json and images/ (images are git-ignored). Blocked variants (V6, V7) are skipped.
"""
import argparse
import dataclasses
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.evaluation import VARIANTS, get, validate_registry  # noqa: E402
from ai_engine.evaluation.harness import run_variant, select_eval_prompts  # noqa: E402
from ai_engine.optimization.benchmark import ClipScorer, collect_environment  # noqa: E402
from ai_engine.prompt.suite import load_suite  # noqa: E402


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true", help="every runnable variant, one subprocess each")
    ap.add_argument("--only", action="append", default=[], metavar="ID")
    ap.add_argument("--out", default=str(ROOT / "evaluation" / "results" / "p7"))
    ap.add_argument("--split", default="holdout", choices=["holdout", "dev"], help="prompt split (default: frozen hold-out)")
    ap.add_argument("--prompts-per-category", type=int, default=None, help="subset for smoke runs (recorded)")
    ap.add_argument("--limit", type=int, default=None, help="cap number of prompts (recorded)")
    ap.add_argument("--seeds", default="1234,5678,9012", help="comma-separated; identical for every variant")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--clip", action="store_true", help="CLIP similarity (downloads openai/clip-vit-base-patch32)")
    ap.add_argument("--dry-run", action="store_true", help="synthetic engine; results flagged synthetic, not citable")
    ap.add_argument("--allow-unpinned", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse(argv)
    validate_registry()
    if args.list:
        for v in VARIANTS:
            state = "RUNNABLE" if v.runnable else f"BLOCKED: {v.blocked_reason}"
            print(f"{v.id:3} {'COMBINED ' if v.combined else '         '}{v.title:42} changes={list(v.changed)} [{state}]")
        return 0
    if args.all:
        rc = 0
        pt = ["--out", args.out, "--split", args.split, "--seeds", args.seeds, "--repeats", str(args.repeats),
              "--warmup", str(args.warmup)]
        pt += ["--prompts-per-category", str(args.prompts_per_category)] if args.prompts_per_category else []
        pt += ["--limit", str(args.limit)] if args.limit else []
        pt += (["--clip"] if args.clip else []) + (["--dry-run"] if args.dry_run else []) + (
            ["--allow-unpinned"] if args.allow_unpinned else [])
        for v in VARIANTS:
            if not v.runnable:
                print(f"=== {v.id}: SKIPPED ({v.blocked_reason})", flush=True)
                continue
            print(f"=== {v.id}: {v.title}", flush=True)
            rc |= subprocess.run([sys.executable, __file__, "--only", v.id, *pt]).returncode
        return rc
    if not args.only:
        print("Nothing to do: pass --list, --all, or --only ID.")
        return 2

    suite = load_suite()
    prompts = select_eval_prompts(suite, args.split, args.prompts_per_category, args.limit)
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    suite_info = {"version": suite.get("suite_version"), "split": args.split, "n_prompts": len(prompts),
                  "per_category": args.prompts_per_category, "limit": args.limit,
                  "subset": bool(args.prompts_per_category or args.limit)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    if args.dry_run:
        from ai_engine.evaluation.dryrun import SyntheticEngine
        env = {"synthetic": True, "python": sys.version.split()[0], "gpu_name": None, "model_id": None, "model_revision": None}
        ram_fn, clip, make_engine = (lambda: None), None, (lambda v: SyntheticEngine(v.config.precision))
    else:
        from backend.app.config import load_settings
        from backend.app.services.engine import SDTurboEngine
        from backend.app.services.generation import process_peak_ram_mb
        base = load_settings()
        if base.model_revision is None and not args.allow_unpinned:
            print("Refusing to run: MODEL_REVISION is not set (pin the model revision), or pass --allow-unpinned.")
            return 2
        env = collect_environment(base.model_id, base.model_revision)
        ram_fn = process_peak_ram_mb
        clip = ClipScorer(device="cuda" if env["gpu_name"] else "cpu", allow_unpinned=args.allow_unpinned) if args.clip else None
        make_engine = lambda v: SDTurboEngine(dataclasses.replace(base, **v.config.settings_overrides()))  # noqa: E731
    for vid in args.only:
        v = get(vid)
        if not v.runnable:
            print(f"{vid}: SKIPPED — {v.blocked_reason}")
            continue
        res = run_variant(v, make_engine(v), prompts, seeds, args.repeats, args.warmup, out, env, ram_fn, clip,
                          suite_info=suite_info)
        s = res["summary"]
        e2e = s["end_to_end_ms"]
        print(f"{vid}: status={res['status']} synthetic={res['synthetic']} n_ok={s['n_ok']} "
              f"median_e2e_ms={'-' if not e2e else round(e2e['median'])} error={res['error']}")
        rc |= res["status"] != "ok"
    return int(bool(rc))


if __name__ == "__main__":
    sys.exit(main())
