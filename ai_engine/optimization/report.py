"""Build the P4 quality-cost table from raw result files. Mechanical only: no interpretation is generated.

Fidelity = pixel PSNR of an experiment's image against B0's image for the same prompt+seed. It measures DEVIATION
from the baseline (an optimized model is allowed to differ), NOT perceptual quality; read it next to CLIP/human review.
"""
import json
from pathlib import Path
from typing import Optional

from .experiments import BASELINE_ID, EXPERIMENTS
from .stats import pixel_fidelity, summarize

DISCLAIMER = ("Generated mechanically from raw result files by ai_engine/optimization/report.py. It contains no "
              "interpretation. 'Fidelity' is pixel deviation from B0, not perceptual quality. Memory is PyTorch "
              "allocated/reserved GPU memory, not nvidia-smi totals.")


def load_results(results_dir: Path) -> dict:
    out = {}
    for f in sorted(Path(results_dir).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("schema", "").startswith("p4_experiment_result/"):
            out[d["experiment"]["id"]] = d
    return out


def _measured(r: dict, require_gpu: bool) -> bool:
    info = r.get("load_info") or {}
    on_gpu = bool(r["environment"].get("gpu_name")) and info.get("device") == "cuda"
    return r["status"] == "ok" and (on_gpu or not require_gpu)


def _fidelity(results_dir: Path, exp_id: str) -> Optional[dict]:
    from PIL import Image
    base, cur = Path(results_dir) / "images" / BASELINE_ID, Path(results_dir) / "images" / exp_id
    if exp_id == BASELINE_ID or not base.is_dir() or not cur.is_dir():
        return None
    psnrs, mses, identical, n = [], [], 0, 0
    for img in sorted(cur.glob("*.png")):
        ref = base / img.name
        if ref.exists():
            with Image.open(img) as a, Image.open(ref) as b:
                f = pixel_fidelity(a, b)
            n += 1
            mses.append(f["mse"])
            identical += f["identical"]
            if f["psnr_db"] is not None:
                psnrs.append(f["psnr_db"])
    return {"pairs": n, "identical_pairs": identical, "psnr_db": summarize(psnrs), "mse": summarize(mses)} if n else None


def build_report(results_dir: Path, min_runs: int = 10, require_gpu: bool = True) -> dict:
    results_dir = Path(results_dir)
    res = load_results(results_dir)
    base = res.get(BASELINE_ID)
    bs = (base or {}).get("summary") or {}
    b_lat, b_mem, b_clip = bs.get("latency_ms"), bs.get("peak_allocated_mb"), bs.get("clip_score")
    rows = []
    for exp in EXPERIMENTS:
        r = res.get(exp.id)
        row = {"id": exp.id, "title": exp.title, "combined": exp.combined, "changed": list(exp.changed),
               "present": r is not None}
        if r:
            s = r["summary"] or {}
            lat, mem = s.get("latency_ms"), s.get("peak_allocated_mb")
            row.update(status=r["status"], error=r.get("error"), measured=_measured(r, require_gpu),
                       n_ok=s.get("n_ok", 0), latency_ms=lat, peak_allocated_mb=mem,
                       peak_reserved_mb=s.get("peak_reserved_mb_experiment"), model_load_ms=r.get("model_load_ms"),
                       gpu_after_load_mb=r.get("gpu_after_load"), clip=s.get("clip_score"),
                       fidelity_vs_B0=_fidelity(results_dir, exp.id))
            if lat and b_lat and exp.id != BASELINE_ID:
                row["latency_median_ratio_vs_B0"] = lat["median"] / b_lat["median"]
                row["latency_range_overlaps_B0"] = not (lat["max"] < b_lat["min"] or lat["min"] > b_lat["max"])
            if mem and b_mem and exp.id != BASELINE_ID and mem["median"] is not None and b_mem["median"] is not None:
                row["peak_allocated_delta_mb_vs_B0"] = mem["median"] - b_mem["median"]
            if row["clip"] and b_clip and exp.id != BASELINE_ID:
                row["clip_mean_delta_vs_B0"] = row["clip"]["mean"] - b_clip["mean"]
        rows.append(row)

    ok_row = lambda x: x.get("present") and x.get("measured") and x.get("n_ok", 0) >= min_runs  # noqa: E731
    base_ok = any(ok_row(x) for x in rows if x["id"] == BASELINE_ID)
    strategies = [x["id"] for x in rows if x["id"] != BASELINE_ID and not x["combined"] and ok_row(x)]
    warnings = []
    seen = {(r["generation_seen"] or {}).get("scheduler") for r in res.values() if r.get("generation_seen")}
    revs = {(r["generation_seen"] or {}).get("model_revision") for r in res.values() if r.get("generation_seen")}
    protos = {json.dumps([r["protocol"]["prompt_ids"], r["protocol"]["seeds"], r["protocol"]["repeats"]]) for r in res.values()}
    if len(seen) > 1:
        warnings.append(f"schedulers differ across experiments: {sorted(map(str, seen))}")
    if len(revs) > 1:
        warnings.append(f"model revisions differ across experiments: {sorted(map(str, revs))}")
    if any(str(v).startswith("unpinned") for v in revs):
        warnings.append("model revision is UNPINNED; pin MODEL_REVISION before quoting results")
    if len(protos) > 1:
        warnings.append("experiments used different prompt/seed/repeat protocols; comparisons are not like-for-like")
    missing = [x["id"] for x in rows if not x["present"]]
    gate = {"met": bool(base_ok and len(strategies) >= 2), "baseline_measured": base_ok,
            "measured_single_variable_strategies": strategies, "min_runs_per_experiment": min_runs,
            "require_gpu": require_gpu, "missing_experiments": missing}
    return {"disclaimer": DISCLAIMER, "gate": gate, "warnings": warnings, "rows": rows}


def _f(v, nd=1):
    return "-" if v is None else f"{v:.{nd}f}"


def render_markdown(rep: dict) -> str:
    g = rep["gate"]
    lines = ["# P4 quality-cost table", "", f"_{rep['disclaimer']}_", "",
             f"**P4 gate (>=2 measured single-variable strategies + measured baseline): "
             f"{'MET' if g['met'] else 'NOT MET'}** — measured strategies: {g['measured_single_variable_strategies'] or 'none'}; "
             f"baseline measured: {g['baseline_measured']}; missing experiments: {g['missing_experiments'] or 'none'}.", ""]
    for w in rep["warnings"]:
        lines.append(f"- WARNING: {w}")
    lines += ["", "| Exp | Changed | Status | n_ok | Latency median ms [min-max] (sd) | x vs B0 | Peak alloc MB (median) | "
              "Δ MB vs B0 | Peak reserved MB | Fidelity PSNR dB vs B0 (mean; identical/pairs) | CLIP mean (Δ vs B0) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rep["rows"]:
        if not x["present"]:
            lines.append(f"| {x['id']} | {', '.join(x['changed']) or '-'}{' (COMBINED)' if x['combined'] else ''} | NOT RUN | | | | | | | | |")
            continue
        lat, mem, fid, clip = x["latency_ms"], x["peak_allocated_mb"], x["fidelity_vs_B0"], x["clip"]
        status = x["status"] + ("" if x["measured"] else " (not GPU-measured)")
        lat_s = "-" if not lat else f"{lat['median']:.0f} [{lat['min']:.0f}-{lat['max']:.0f}] ({_f(lat['stdev'], 0)})"
        fid_s = "-"
        if fid:
            p = fid["psnr_db"]
            fid_s = f"{_f(p['mean']) if p else 'n/a'}; {fid['identical_pairs']}/{fid['pairs']}"
        clip_s = "-" if not clip else f"{clip['mean']:.3f} ({_f(x.get('clip_mean_delta_vs_B0'), 3)})"
        ov = x.get("latency_range_overlaps_B0")
        ratio = x.get("latency_median_ratio_vs_B0")
        ratio_s = "-" if ratio is None else f"{ratio:.2f}" + (" (ranges overlap B0)" if ov else "")
        lines.append(f"| {x['id']} | {', '.join(x['changed']) or '-'}{' (COMBINED)' if x['combined'] else ''} | {status} | "
                     f"{x['n_ok']} | {lat_s} | {ratio_s} | {_f(mem['median']) if mem else '-'} | "
                     f"{_f(x.get('peak_allocated_delta_mb_vs_B0'))} | {_f(x['peak_reserved_mb'])} | {fid_s} | {clip_s} |")
    lines += ["", "Failed experiments (OOM/error) are results; see each JSON's `error` field."]
    return "\n".join(lines) + "\n"
