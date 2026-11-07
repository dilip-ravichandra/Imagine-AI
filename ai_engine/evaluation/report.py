"""Build the P7 report from raw variant result files: raw CSV, summary CSV, JSON, Markdown, human-review sheet, plot.

Mechanical only: numbers + methodology + gate checks. No winner is declared and no interpretation is generated; the
team writes that (docs/08 section 8.5/8.6). Synthetic (dry-run) files are never counted as measurements.
"""
import csv
import json
from pathlib import Path
from typing import Optional

from ai_engine.optimization.stats import summarize

from .metrics import bootstrap_ci_clustered, cv_percent, fid_gate, paired_deltas
from .variants import BASELINE_ID, VARIANTS

DISCLAIMER = ("Generated mechanically by ai_engine/evaluation/report.py from raw result files. It contains no "
              "interpretation and declares no winner. CLIP is a broad text-image alignment signal; it does not verify "
              "object counts or spatial relations (see the human review sheet). Memory is PyTorch GPU memory or process "
              "RAM as labelled, never nvidia-smi totals; VRAM and RAM are never mixed.")

RUN_FIELDS = ["variant", "prompt_id", "category", "seed", "repeat", "status", "generation_ms", "cv_ms", "end_to_end_ms",
              "peak_gpu_mb", "clip_score", "clip_score_raw", "cv_applied", "image"]


def load_results(results_dir: Path) -> dict:
    out = {}
    for f in sorted(Path(results_dir).glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if str(d.get("schema", "")).startswith("p7_variant_result/"):
            out[d["variant"]["id"]] = d
    return out


def _measured(r: dict, require_gpu: bool) -> bool:
    if r.get("synthetic") or r["status"] != "ok":
        return False
    info = r.get("load_info") or {}
    on_gpu = bool(r["environment"].get("gpu_name")) and info.get("device") == "cuda"
    return on_gpu or not require_gpu


def _clip_map(r: dict, field: str = "clip_score") -> dict:
    return {(x["prompt_id"], x["seed"]): x.get(field) for x in r["runs"]
            if x["status"] == "ok" and x["repeat"] == 0 and x.get(field) is not None}


def _by_category(r: dict) -> dict:
    cats: dict = {}
    for x in r["runs"]:
        if x["status"] == "ok" and x["repeat"] == 0 and x.get("clip_score") is not None:
            cats.setdefault(x["category"], []).append(x["clip_score"])
    return {c: summarize(v) for c, v in sorted(cats.items())}


def build_report(results_dir: Path, min_runs: int = 10, require_gpu: bool = True, sizes: Optional[dict] = None,
                 n_real_fid: int = 0, fid_feature_dim: int = 2048, seed: int = 0) -> dict:
    res = load_results(results_dir)
    base = res.get(BASELINE_ID)
    base_clip = _clip_map(base) if base else {}
    rows, gate_problems = [], []
    for v in VARIANTS:
        r = res.get(v.id)
        row = {"id": v.id, "title": v.title, "combined": v.combined, "changed": list(v.changed),
               "present": r is not None, "blocked_reason": v.blocked_reason}
        if r:
            s = r["summary"] or {}
            n_imgs = sum(1 for x in r["runs"] if x["status"] == "ok" and x["repeat"] == 0)
            clip_pairs = paired_deltas(base_clip, _clip_map(r)) if v.id != BASELINE_ID and base else {}
            row.update(
                status=r["status"], error=r.get("error"), synthetic=bool(r.get("synthetic")),
                measured=_measured(r, require_gpu), n_ok=s.get("n_ok", 0), n_images=n_imgs,
                model_load_ms=r.get("model_load_ms"), generation_ms=s.get("generation_ms"), cv_ms=s.get("cv_ms"),
                end_to_end_ms=s.get("end_to_end_ms"), latency_cv_percent=cv_percent(
                    x["end_to_end_ms"] for x in r["runs"] if x["status"] == "ok"),
                peak_gpu_mb=s.get("peak_gpu_mb"), peak_reserved_mb=s.get("peak_reserved_mb"),
                peak_process_ram_mb=s.get("peak_process_ram_mb"), clip=s.get("clip_score"),
                clip_by_category=_by_category(r), cv_applied_fraction=s.get("cv_applied_fraction"),
                clip_delta_vs_V0=bootstrap_ci_clustered(clip_pairs, seed=seed) if clip_pairs else None,
                environment=r["environment"], protocol=r["protocol"])
            if v.cv:  # CV on vs the SAME generated images before CV: isolates the CV effect from generation noise
                raw_pairs = paired_deltas(_clip_map(r, "clip_score_raw"), _clip_map(r))
                row["cv_clip_delta_vs_own_raw"] = bootstrap_ci_clustered(raw_pairs, seed=seed) if raw_pairs else None
            if row["measured"] and row["n_ok"] < min_runs:
                gate_problems.append(f"{v.id}: only {r['summary']['n_ok']} timed runs (< {min_runs})")
        rows.append(row)

    measured_ids = [x["id"] for x in rows if x.get("measured")]
    if not base or not _measured(base, require_gpu):
        gate_problems.insert(0, "V0 baseline missing or not a measured GPU run")
    synth = [x["id"] for x in rows if x.get("synthetic")]
    if synth:
        gate_problems.append(f"synthetic dry-run files present for {synth}; they are excluded from measured results")
    optimized = [x for x in rows if x["id"] in ("V1", "V2", "V3", "V4") and x.get("measured")]
    if not optimized:
        gate_problems.append("no measured optimized variant (P7 needs baseline vs optimized comparison)")
    if not any(x.get("clip") for x in rows if x.get("measured")):
        gate_problems.append("no measured CLIP scores (run with --clip)")
    n_gen = max((x.get("n_images", 0) for x in rows if x.get("measured")), default=0)
    fid = fid_gate(n_real_fid, n_gen, fid_feature_dim)
    fid["decision"] = ("FID may be computed (still label small-sample if not citable)" if fid["allowed"] else
                       "FID NOT computed. Justified alternative: paired CLIP deltas with prompt-cluster bootstrap CI "
                       "+ pixel fidelity vs V0 + human review sheet")
    return {"disclaimer": DISCLAIMER, "rows": rows, "measured_variants": measured_ids, "sizes": sizes, "fid": fid,
            "gate": {"met": not gate_problems, "problems": gate_problems, "min_runs": min_runs}}


def _f(x, nd=1, none="-"):
    return none if x is None else f"{x:.{nd}f}"


def _stat(s, key="median", nd=1):
    return "-" if not s else _f(s[key], nd)


def _mb(x):
    return "-" if x is None else f"{x / 1048576:.0f} MB"


def render_markdown(rep: dict) -> str:
    L = ["# P7 evaluation report (mechanical)", "", rep["disclaimer"], ""]
    g = rep["gate"]
    L += [f"**P7 gate: {'MET' if g['met'] else 'NOT MET'}**"] + [f"- {p}" for p in g["problems"]] + [""]
    first = next((r for r in rep["rows"] if r.get("present")), None)
    if first:
        e, p = first["environment"], first["protocol"]
        L += ["## Environment and protocol", f"- GPU: {e.get('gpu_name')} ({_f(e.get('gpu_total_vram_mb'), 0)} MB VRAM); "
              f"OS: {e.get('os')}; Python {e.get('python')}; torch {e.get('torch')}; diffusers {e.get('diffusers')}",
              f"- Model: {e.get('model_id')} @ {e.get('model_revision')}; CLIP model: {p.get('clip_model')}",
              f"- Prompts: {len(p['prompt_ids'])} ({p.get('suite')}); seeds: {p['seeds']}; timed repeats per "
              f"(prompt, seed): {p['repeats']}; warm-up generations: {p['warmup']}",
              f"- Latency: {p['latency_definition']}", f"- Memory: {p['memory_definition']}", ""]
    L += ["## Results (median; n = timed generations)",
          "| Variant | Status | n | CLIP mean | Median e2e ms | CV% | Peak alloc MB | Peak reserved MB | Peak RAM MB | Load ms |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rep["rows"]:
        if not r["present"]:
            why = f"NOT RUN — {r['blocked_reason']}" if r["blocked_reason"] else "NOT RUN (no result file)"
            L.append(f"| {r['id']} {r['title']} | {why} | | | | | | | | |")
            continue
        tag = "SYNTHETIC" if r["synthetic"] else ("measured" if r["measured"] else f"unmeasured ({r['status']})")
        L.append(f"| {r['id']} {r['title']} | {tag} | {r['n_ok']} | {_stat(r['clip'], 'mean', 3)} | "
                 f"{_stat(r['end_to_end_ms'])} | {_f(r['latency_cv_percent'])} | {_stat(r['peak_gpu_mb'], 'median', 0)} | "
                 f"{_f(r['peak_reserved_mb'], 0)} | {_f(r['peak_process_ram_mb'], 0)} | {_f(r['model_load_ms'], 0)} |")
    L += ["", "Spread (stdev / p95 of end-to-end ms):"]
    for r in rep["rows"]:
        s = r.get("end_to_end_ms") if r["present"] else None
        if s:
            L.append(f"- {r['id']}: stdev {_f(s['stdev'])}, p95 {_f(s['p95'])}, min {_f(s['min'])}, max {_f(s['max'])}")
    L += ["", "## CLIP: paired delta vs V0 (same prompts and seeds; bootstrap resamples prompts)",
          "| Variant | n pairs | n prompts | mean Δ | 95% CI | share Δ>0 |", "|---|---:|---:|---:|---|---:|"]
    for r in rep["rows"]:
        d = r.get("clip_delta_vs_V0") if r["present"] else None
        if d:
            ci = "n/a (1 prompt)" if d["ci_low"] is None else f"[{d['ci_low']:.4f}, {d['ci_high']:.4f}]"
            L.append(f"| {r['id']} | {d['n_pairs']} | {d['n_prompts']} | {d['mean_delta']:.4f} | {ci} | {d['frac_positive']:.2f} |")
    cvr = next((r for r in rep["rows"] if r["present"] and r.get("cv_clip_delta_vs_own_raw")), None)
    if cvr:
        d = cvr["cv_clip_delta_vs_own_raw"]
        ci = "n/a" if d["ci_low"] is None else f"[{d['ci_low']:.4f}, {d['ci_high']:.4f}]"
        L += ["", f"## CV off vs on ({cvr['id']}, same generated images before/after CV)",
              f"- mean CLIP Δ {d['mean_delta']:.4f}, 95% CI {ci}, n={d['n_pairs']}; CV bypassed (dead band) on "
              f"{_f(100 * (1 - (cvr['cv_applied_fraction'] or 0)), 0)}% of images; median cv_ms {_stat(cvr['cv_ms'])}"]
    L += ["", "## CLIP by prompt category (mean per category, one image per (prompt, seed))"]
    for r in rep["rows"]:
        if r["present"] and r.get("clip_by_category"):
            L.append(f"- {r['id']}: " + "; ".join(f"{c}={_stat(s, 'mean', 3)} (n={s['n']})"
                                                  for c, s in r["clip_by_category"].items()))
    f = rep["fid"]
    L += ["", "## FID", f"- real reference images: {f['n_real']}; generated: {f['n_generated']}",
          f"- decision: {f['decision']}"] + [f"- reason: {x}" for x in f["reasons"]]
    sz = rep.get("sizes")
    L += ["", "## Model size (file bytes on disk; not parameter count; app package size is separate)"]
    if sz and sz.get("base_total_dir_bytes") is not None:
        L.append(f"- base snapshot dir total: {_mb(sz['base_total_dir_bytes'])}")
        for n, b in (sz.get("base_weight_files") or {}).items():
            L.append(f"  - {n}: {_mb(b)}")
        L.append(f"- adapter: {_mb(sz.get('adapter_bytes')) if sz.get('adapter_bytes') is not None else 'none / not measured'}")
    else:
        L.append("- NOT MEASURED (pass --model-dir or pin MODEL_REVISION with the model in the HF cache)")
    L += ["", "## Not measured by this harness", "- Encode/denoise/decode split (engine does not expose stage timings); "
          "on-device phone numbers (P8); object-count and spatial-relation correctness (human review sheet).", ""]
    return "\n".join(L)


def write_raw_csv(results_dir: Path, out_path: Path) -> int:
    res = load_results(results_dir)
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RUN_FIELDS, extrasaction="ignore")
        w.writeheader()
        for vid, r in res.items():
            for x in r["runs"]:
                w.writerow({"variant": vid, **{k: ("" if x.get(k) is None else x.get(k)) for k in RUN_FIELDS[1:]}})
                n += 1
    return n


def write_review_sheet(results_dir: Path, out_path: Path, prompts: dict) -> int:
    """One row per (variant, prompt, seed) image for HUMAN review of count/relation/attribute/artifact (ADV-02).
    Review columns are left blank on purpose; nothing is pre-filled."""
    res = load_results(results_dir)
    cols = ["variant", "prompt_id", "category", "prompt", "seed", "image", "objects_and_counts_correct(y/n/partial)",
            "spatial_relations_correct(y/n/partial/na)", "attributes_present(y/n/partial)", "artifacts_seen",
            "cv_helped_hurt_neutral", "notes"]
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for vid, r in res.items():
            if r.get("synthetic"):
                continue
            for x in r["runs"]:
                if x["status"] == "ok" and x["repeat"] == 0:
                    w.writerow([vid, x["prompt_id"], x["category"], prompts.get(x["prompt_id"], ""), x["seed"],
                                x.get("image", ""), "", "", "", "", "", ""])
                    n += 1
    return n


FAILURE_TEMPLATE = """# P7B failure-case log (fill from the human review sheet; one entry per real case)
Required categories (docs/08 section 8.6): wrong object count; wrong spatial relation; missing attribute; anatomy/structure
artifact; over-smoothing or sharpening; colour shift from enhancement; CLIP score not matching human judgement;
OOM/timeout or slow fallback; mobile export/runtime incompatibility. Only log cases you actually observed.

## Case N
- Category:
- Variant / prompt id / seed / image path:
- What happened:
- How detected (metric, review sheet, error log):
- Corrected? (how) / Remaining unsolved:
"""


def write_plot(rep: dict, out_path: Path) -> bool:
    """Quality-vs-cost scatter (CLIP mean vs median end-to-end ms) for measured variants. False if nothing to plot."""
    pts = [(r["id"], r["end_to_end_ms"]["median"], r["clip"]["mean"]) for r in rep["rows"]
           if r.get("measured") and r.get("end_to_end_ms") and r.get("clip")]
    if len(pts) < 2:
        return False
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    for vid, x, y in pts:
        ax.scatter(x, y)
        ax.annotate(vid, (x, y), textcoords="offset points", xytext=(4, 4))
    ax.set_xlabel("median end-to-end latency (ms)")
    ax.set_ylabel("mean CLIP similarity")
    ax.set_title("Quality vs compute cost (measured variants only)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True
