"""P4 inference-optimization benchmark runner. RUN ON THE GPU LAPTOP (the build sandbox has no GPU).

PowerShell, from repo root, with MODEL_REVISION pinned:
    $env:MODEL_REVISION="<commit hash>"
    python evaluation/scripts/run_p4_benchmarks.py --list
    python evaluation/scripts/run_p4_benchmarks.py --all            # one subprocess per experiment (clean VRAM)
    python evaluation/scripts/run_p4_benchmarks.py --only B0 --only E1
Then:  python evaluation/scripts/analyze_p4_results.py
Outputs: evaluation/results/p4/<ID>.json and evaluation/results/p4/images/<ID>/ (images are git-ignored).
"""
import argparse
import dataclasses
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.optimization import EXPERIMENTS, get, validate_registry  # noqa: E402
from ai_engine.optimization.benchmark import (ClipScorer, collect_environment, run_experiment,  # noqa: E402
                                              select_prompts)
from ai_engine.prompt.suite import load_suite  # noqa: E402


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print the experiment grid and exit")
    ap.add_argument("--all", action="store_true", help="run every experiment, one subprocess each")
    ap.add_argument("--only", action="append", default=[], metavar="ID", help="run this experiment (repeatable)")
    ap.add_argument("--out", default=str(ROOT / "evaluation" / "results" / "p4"))
    ap.add_argument("--prompts-per-category", type=int, default=2)
    ap.add_argument("--seeds", default="1234,5678", help="comma-separated; same for every experiment")
    ap.add_argument("--repeats", type=int, default=2, help="timed repeats per (prompt, seed)")
    ap.add_argument("--warmup", type=int, default=2, help="untimed generations before measuring")
    ap.add_argument("--clip", action="store_true", help="also compute CLIP similarity (downloads a CLIP model)")
    ap.add_argument("--allow-unpinned", action="store_true", help="run without MODEL_REVISION (results not citable)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse(argv)
    validate_registry()
    if args.list:
        for e in EXPERIMENTS:
            print(f"{e.id:3} {'COMBINED ' if e.combined else '         '}{e.title:38} changes={list(e.changed)}  {dataclasses.asdict(e.config)}")
        return 0
    if args.all:
        rc = 0
        passthrough = ["--out", args.out, "--prompts-per-category", str(args.prompts_per_category), "--seeds",
                       args.seeds, "--repeats", str(args.repeats), "--warmup", str(args.warmup)]
        passthrough += (["--clip"] if args.clip else []) + (["--allow-unpinned"] if args.allow_unpinned else [])
        for e in EXPERIMENTS:
            print(f"=== {e.id}: {e.title}", flush=True)
            rc |= subprocess.run([sys.executable, __file__, "--only", e.id, *passthrough]).returncode
        return rc
    if not args.only:
        print("Nothing to do: pass --list, --all, or --only ID.")
        return 2

    from dataclasses import replace
    from backend.app.config import load_settings
    from backend.app.services.engine import SDTurboEngine
    from backend.app.services.generation import process_peak_ram_mb

    base_settings = load_settings()
    if base_settings.model_revision is None and not args.allow_unpinned:
        print("Refusing to run: MODEL_REVISION is not set (project rule: pin the model revision). "
              "Set it, or pass --allow-unpinned for a throwaway run.")
        return 2
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    prompts = select_prompts(load_suite(), args.prompts_per_category)
    env = collect_environment(base_settings.model_id, base_settings.model_revision)
    clip = ClipScorer(device="cuda" if env["gpu_name"] else "cpu", allow_unpinned=args.allow_unpinned) if args.clip else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for exp_id in args.only:
        exp = get(exp_id)
        engine = SDTurboEngine(replace(base_settings, **exp.config.settings_overrides()))
        res = run_experiment(exp, engine, prompts, seeds, args.repeats, args.warmup, out, env,
                             ram_fn=process_peak_ram_mb, clip=clip)
        s = res["summary"]
        lat = s["latency_ms"]
        print(f"{exp.id}: status={res['status']} n_ok={s['n_ok']} "
              f"median_ms={'-' if not lat else round(lat['median'])} error={res['error']}")
        rc |= res["status"] != "ok"
    return int(bool(rc))


if __name__ == "__main__":
    sys.exit(main())
