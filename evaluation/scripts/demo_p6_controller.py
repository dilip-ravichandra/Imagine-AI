"""P6 demo: controller decisions across simulated resource budgets, plus a simulated OOM fallback.

Uses the SYNTHETIC fixture profile by default, so every number printed is INVENTED test data, not a measurement.
Pass --profile <measured profile.json> to run the same simulation against a real profile.
    python evaluation/scripts/demo_p6_controller.py
Writes evaluation/results/p6/demo_decisions.json (decision logs; contains no prompts).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_engine.adaptive import (AdaptiveController, CappedMonitor, ControllerRequest, ResourceError,  # noqa: E402
                                ResourceSnapshot, StaticMonitor, load_profile_set, run_with_fallback)

FIXTURE = ROOT / "tests" / "fixtures" / "adaptive_profile_synthetic.json"


class SimulatedOOM(RuntimeError):
    pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=str(FIXTURE))
    ap.add_argument("--budgets", default="12000,4000,3000,2000,1000", help="simulated GPU budgets in MB")
    ap.add_argument("--resolution", type=int, default=512)
    ap.add_argument("--out", default=str(ROOT / "evaluation" / "results" / "p6" / "demo_decisions.json"))
    args = ap.parse_args(argv)
    profile = load_profile_set(args.profile)
    ctl = AdaptiveController(profile)
    print(f"profile_id={profile.profile_id} synthetic={profile.synthetic}"
          + ("   (INVENTED NUMBERS - not a measurement)" if profile.synthetic else ""))
    rows = []
    print(f"\n{'budget MB':>10} {'mode':9} {'selected':26} {'fallback':8} reason")
    for budget in [float(b) for b in args.budgets.split(",")]:
        snap = ResourceSnapshot(device="cuda", gpu_name=profile.hardware.get("gpu_name"),
                                gpu_total_mb=profile.hardware.get("gpu_total_vram_mb"), gpu_budget_mb=budget,
                                source="simulated")
        for mode in ("quick", "balanced", "best"):
            try:
                d = ctl.decide(ControllerRequest(mode, args.resolution), snap)
                print(f"{budget:>10.0f} {mode:9} {d.selected.id:26} {str(d.fallback_used):8} {d.reason or '-'}")
                rows.append({"budget_mb": budget, "mode": mode, "selected": d.selected.id, "log": d.log})
            except ResourceError as exc:
                print(f"{budget:>10.0f} {mode:9} {'NO SAFE CONFIGURATION':26} {'-':8} {exc.suggested_action}")
                rows.append({"budget_mb": budget, "mode": mode, "selected": None, "log": exc.log})

    print("\nSimulated OOM during generation (balanced, ample memory; every config above 2000 MB 'OOMs'):")
    mon = CappedMonitor(StaticMonitor(ResourceSnapshot(device="cuda", gpu_budget_mb=12000, source="simulated")))

    def run(entry):
        if (entry.peak_gpu_mb_max or 0) > 2000:
            raise SimulatedOOM("CUDA out of memory (simulated)")
        return f"image from {entry.id}"

    try:
        ex = run_with_fallback(ctl, ControllerRequest("balanced", args.resolution), mon, run)
        print(f"  result: {ex.value}; failures={ex.failures}")
        print(f"  {ex.explanation}")
        rows.append({"simulated_oom": True, "failures": ex.failures, "final": ex.decision.selected.id,
                     "logs": [d.log for d in ex.decisions]})
    except ResourceError as exc:
        print(f"  ended with a clear resource error: {exc.message}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"synthetic": profile.synthetic, "profile_id": profile.profile_id, "rows": rows},
                              indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
