"""Build an adaptive-controller profile from MEASURED benchmark results (P4 grid and/or the P6 sweep).

    python evaluation/scripts/build_adaptive_profile.py                       # reads p4 + p6_profile result dirs
    python evaluation/scripts/build_adaptive_profile.py --results-dir evaluation/results/p6_profile --min-runs 10
Writes evaluation/profiles/profile_<gpu>.json. Refuses to mix machines/models/revisions. Exit 2 = nothing usable.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.adaptive import ProfileError, build_profile_set, save_profile_set  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-dir", action="append", default=[], help="repeatable; default: p4 and p6_profile")
    ap.add_argument("--out", help="output file (default evaluation/profiles/profile_<gpu>.json)")
    ap.add_argument("--min-runs", type=int, default=10)
    ap.add_argument("--allow-cpu", action="store_true", help="also accept results not measured on CUDA")
    args = ap.parse_args(argv)
    dirs = [Path(d) for d in args.results_dir] or [ROOT / "evaluation" / "results" / "p4",
                                                    ROOT / "evaluation" / "results" / "p6_profile"]
    try:
        ps, skipped = build_profile_set([d for d in dirs if d.is_dir()], args.min_runs, not args.allow_cpu)
    except ProfileError as exc:
        print(f"Cannot build a profile: {exc}")
        return 2
    gpu = re.sub(r"[^A-Za-z0-9]+", "_", str(ps.hardware.get("gpu_name") or "cpu")).strip("_")
    out = Path(args.out) if args.out else ROOT / "evaluation" / "profiles" / f"profile_{gpu}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    save_profile_set(ps, out)
    print(f"wrote {out}  profile_id={ps.profile_id}  entries={len(ps.entries)}")
    for e in ps.entries:
        print(f"  {e.id:28} {e.status:5} {e.precision} s{e.steps} r{e.resolution} lat_med={e.latency_ms_median} "
              f"gpu_max_mb={e.peak_gpu_mb_max}")
    for src, why in skipped:
        print(f"  SKIPPED {src}: {why}")
    if not ps.model_revision:
        print("WARNING: results carry no pinned MODEL_REVISION; do not cite this profile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
