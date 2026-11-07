"""P6 profile sweep: measure (resolution x precision x steps) on the GPU laptop. RUN THERE (no GPU in the sandbox).

PowerShell, repo root, MODEL_REVISION pinned:
    $env:MODEL_REVISION="<commit hash>"
    python evaluation/scripts/run_p6_profile_sweep.py --list
    python evaluation/scripts/run_p6_profile_sweep.py --all            # one subprocess per config (clean VRAM)
    python evaluation/scripts/build_adaptive_profile.py                # -> evaluation/profiles/profile_<gpu>.json
Reuses the P4 benchmark core, so results have the same schema and measurement definitions
(docs/P4_OPTIMIZATION.md section 7). Output: evaluation/results/p6_profile/<ID>.json (images git-ignored).
An OOM is recorded as a result (the controller then treats that config as known-bad); nothing is retried.
"""
import argparse
import itertools
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.optimization import Experiment, OptimizationConfig  # noqa: E402


def grid(resolutions, precisions, steps) -> list:
    out = []
    for res, prec, st in itertools.product(resolutions, precisions, steps):
        cfg = OptimizationConfig(precision=prec, steps=st, resolution=res)
        out.append(Experiment(f"S-{prec}-s{st}-r{res}", f"Sweep: {prec}, {st} step(s), {res}px",
                              "Profile point for the adaptive controller (measurement only).", cfg,
                              combined=True))
    return out


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", action="append", default=[], metavar="ID")
    ap.add_argument("--resolutions", default="256,384,512,640,768")
    ap.add_argument("--precisions", default="fp16,fp32")
    ap.add_argument("--steps", default="1,2,4")
    ap.add_argument("--out", default=str(ROOT / "evaluation" / "results" / "p6_profile"))
    ap.add_argument("--prompts-per-category", type=int, default=2)
    ap.add_argument("--seeds", default="1234,5678")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--clip", action="store_true", help="also compute CLIP similarity (downloads a CLIP model)")
    ap.add_argument("--allow-unpinned", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse(argv)
    ints = lambda s: [int(x) for x in s.split(",") if x.strip()]  # noqa: E731
    exps = grid(ints(args.resolutions), [p.strip() for p in args.precisions.split(",") if p.strip()], ints(args.steps))
    if args.list:
        for e in exps:
            print(f"{e.id:22} {e.config}")
        return 0
    if args.all:
        rc = 0
        passthrough = ["--out", args.out, "--resolutions", args.resolutions, "--precisions", args.precisions,
                       "--steps", args.steps, "--prompts-per-category", str(args.prompts_per_category),
                       "--seeds", args.seeds, "--repeats", str(args.repeats), "--warmup", str(args.warmup)]
        passthrough += (["--clip"] if args.clip else []) + (["--allow-unpinned"] if args.allow_unpinned else [])
        for e in exps:
            print(f"=== {e.id}", flush=True)
            rc |= subprocess.run([sys.executable, __file__, "--only", e.id, *passthrough]).returncode
        return int(bool(rc))
    if not args.only:
        print("Nothing to do: pass --list, --all, or --only ID.")
        return 2

    from backend.app.config import load_settings
    from backend.app.services.engine import SDTurboEngine
    from backend.app.services.generation import process_peak_ram_mb
    from ai_engine.optimization.benchmark import ClipScorer, collect_environment, run_experiment, select_prompts
    from ai_engine.prompt.suite import load_suite

    base = load_settings()
    if base.model_revision is None and not args.allow_unpinned:
        print("Refusing to run: MODEL_REVISION is not set (project rule: pin the model revision).")
        return 2
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    prompts = select_prompts(load_suite(), args.prompts_per_category)
    env = collect_environment(base.model_id, base.model_revision)
    clip = ClipScorer(device="cuda" if env["gpu_name"] else "cpu", allow_unpinned=args.allow_unpinned) if args.clip else None
    by_id = {e.id: e for e in exps}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for exp_id in args.only:
        exp = by_id[exp_id]
        engine = SDTurboEngine(replace(base, **exp.config.settings_overrides()))
        res = run_experiment(exp, engine, prompts, seeds, args.repeats, args.warmup, out, env,
                             ram_fn=process_peak_ram_mb, clip=clip)
        lat = res["summary"]["latency_ms"]
        print(f"{exp.id}: status={res['status']} n_ok={res['summary']['n_ok']} "
              f"median_ms={'-' if not lat else round(lat['median'])} error={res['error']}")
        rc |= res["status"] != "ok"
    return int(bool(rc))


if __name__ == "__main__":
    sys.exit(main())
