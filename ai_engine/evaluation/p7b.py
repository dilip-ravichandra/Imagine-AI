"""P7B writers: eval_P3_TeamID.md, ablation study, failure analysis. Pure text generation from REAL P7A outputs.

Rules: every number comes from the P7A report dict; anything missing prints NOT RUN / NOT MEASURED / TODO(team).
Interpretation sections are left for the team (docs/08 section 8.5): nothing here decides a winner or explains a result.
Human-review answers are tallied exactly as typed (y/n/partial/na); blank = not reviewed.
"""
import csv
import dataclasses
from pathlib import Path
from typing import Optional

from .variants import BASELINE_ID, VARIANTS

TODO = "TODO(team)"
REVIEW_COLS = {"counts": "objects_and_counts_correct(y/n/partial)", "relations": "spatial_relations_correct(y/n/partial/na)",
               "attrs": "attributes_present(y/n/partial)", "artifacts": "artifacts_seen", "cv": "cv_helped_hurt_neutral",
               "notes": "notes"}
FAILURE_CATEGORIES = ["Wrong object count", "Incorrect spatial relationship", "Missing prompt attribute",
                      "Anatomy/structure artifacts", "Over-smoothing or sharpening", "Colour shifts from enhancement",
                      "CLIP score not matching human judgement", "OOM/timeout or slow fallback",
                      "Mobile export/runtime incompatibility"]


def load_review(path: Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _norm(v: str) -> str:
    return (v or "").strip().lower()


def tally_review(rows: list[dict]) -> dict:
    """Per variant: reviewed/total and counts of each typed answer for the three judged columns."""
    out: dict = {}
    for r in rows:
        t = out.setdefault(r["variant"], {"total": 0, "reviewed": 0, "counts": {}, "relations": {}, "attrs": {}})
        t["total"] += 1
        answered = False
        for key in ("counts", "relations", "attrs"):
            a = _norm(r.get(REVIEW_COLS[key]))
            if a:
                answered = True
                t[key][a] = t[key].get(a, 0) + 1
        t["reviewed"] += answered
    return out


def _s(x, nd=1):
    return "NOT RUN" if x is None else f"{x:.{nd}f}"


def _row(rep, vid):
    return next((r for r in rep["rows"] if r["id"] == vid), None)


def _variant(vid):
    return next(v for v in VARIANTS if v.id == vid)


def render_ablation(rep: dict, review: Optional[dict] = None) -> str:
    """One section per variant in the docs/08 section 8.5 template."""
    base_cfg = dataclasses.asdict(_variant(BASELINE_ID).config)
    L = ["# Ablation study (P7B)", "",
         "Generated from P7A raw results. Numbers are measurements; 'Interpretation' is for the team to write after "
         "looking at the images and the review sheet.", ""]
    for v in VARIANTS:
        if v.id == BASELINE_ID:
            continue
        r = _row(rep, v.id)
        cfg = dataclasses.asdict(v.config)
        fixed = [f"{k}={base_cfg[k]}" for k in base_cfg if cfg[k] == base_cfg[k]]
        L += [f"## {v.id} — {v.title}" + (" (COMBINED: effects may not add up)" if v.combined else ""),
              f"- **Hypothesis:** {v.hypothesis}",
              f"- **Changed variable:** {', '.join(v.changed) or 'none'}",
              f"- **Fixed variables:** {', '.join(fixed)}; same prompts, seeds, model revision"
              + ("; CV off" if not v.cv else "; generation identical to V0")]
        if not v.runnable:
            L += [f"- **Status:** NOT RUN — {v.blocked_reason}", "- **Result / Interpretation:** none; this is a declared gap.",
                  "- **Limitation:** requirement left unmet; state this explicitly in the submission.", ""]
            continue
        if not r or not r.get("measured"):
            L += ["- **Status:** NOT RUN or not a measured GPU run (see p7_report.md gate).", ""]
            continue
        p, e = r["protocol"], r["environment"]
        d, b = r.get("clip_delta_vs_V0"), _row(rep, BASELINE_ID)
        L += [f"- **Prompt subset:** {len(p['prompt_ids'])} prompts ({p.get('suite')}); seeds {p['seeds']}",
              f"- **Environment:** {e.get('gpu_name')}, torch {e.get('torch')}, diffusers {e.get('diffusers')}, "
              f"revision {e.get('model_revision')}",
              f"- **Samples:** {r['n_ok']} timed generations ({r['n_images']} scored images)"]
        if d:
            ci = "CI n/a (1 prompt)" if d["ci_low"] is None else f"95% CI [{d['ci_low']:.4f}, {d['ci_high']:.4f}]"
            L.append(f"- **Quality (CLIP Δ vs V0, paired):** mean {d['mean_delta']:.4f}, {ci}, n_pairs={d['n_pairs']}")
        else:
            L.append("- **Quality (CLIP Δ vs V0):** NOT MEASURED")
        if v.cv and r.get("cv_clip_delta_vs_own_raw"):
            c = r["cv_clip_delta_vs_own_raw"]
            L.append(f"- **CV on vs the same images before CV:** CLIP Δ mean {c['mean_delta']:.4f}; bypassed on "
                     f"{_s(100 * (1 - (r['cv_applied_fraction'] or 0)), 0)}% of images")
        lat, bl = r.get("end_to_end_ms"), (b or {}).get("end_to_end_ms")
        L.append(f"- **Latency (median end-to-end ms):** {_s(lat and lat['median'])} vs V0 {_s(bl and bl['median'])}"
                 + (f" (ratio {lat['median'] / bl['median']:.2f})" if lat and bl else ""))
        m, bm = r.get("peak_gpu_mb"), (b or {}).get("peak_gpu_mb")
        L.append(f"- **Peak GPU allocated (MB):** {_s(m and m['median'], 0)} vs V0 {_s(bm and bm['median'], 0)}")
        rv = (review or {}).get(v.id)
        if rv:
            L.append(f"- **Human review:** {rv['reviewed']}/{rv['total']} images reviewed; counts {rv['counts']}, "
                     f"relations {rv['relations']}, attributes {rv['attrs']}")
        L += [f"- **Interpretation:** {TODO}", f"- **Failure/limitation:** {TODO}", ""]
    return "\n".join(L)


def render_failure_analysis(review_rows: list[dict], prompts: Optional[dict] = None) -> str:
    """Lists real reviewer-flagged images and which docs/08 section 8.6 categories still have no documented case."""
    flagged = []
    for r in review_rows:
        bad = any(_norm(r.get(REVIEW_COLS[k])) in ("n", "partial") for k in ("counts", "relations", "attrs"))
        if bad or _norm(r.get(REVIEW_COLS["artifacts"])) or _norm(r.get(REVIEW_COLS["cv"])) == "hurt":
            flagged.append(r)
    L = ["# Failure-case analysis (P7B)", "",
         f"Source: human review sheet ({len(review_rows)} rows, {sum(1 for r in review_rows if any(_norm(r.get(REVIEW_COLS[k])) for k in ('counts', 'relations', 'attrs')))} reviewed).",
         "Each case below was flagged by a reviewer. Explain what happened, how it was detected, whether corrected, "
         "and what remains unsolved.", ""]
    if not review_rows:
        L += ["**No review sheet found: run analyze_p7_results.py and fill `p7_human_review.csv` first.**", ""]
    for i, r in enumerate(flagged, 1):
        L += [f"## Case {i}: {r['variant']} / {r['prompt_id']} / seed {r['seed']}",
              f"- Prompt: {r.get('prompt') or (prompts or {}).get(r['prompt_id'], '')}", f"- Image: {r.get('image')}",
              f"- Reviewer: counts={r.get(REVIEW_COLS['counts']) or '-'}, relations={r.get(REVIEW_COLS['relations']) or '-'}, "
              f"attributes={r.get(REVIEW_COLS['attrs']) or '-'}, artifacts={r.get(REVIEW_COLS['artifacts']) or '-'}, "
              f"CV={r.get(REVIEW_COLS['cv']) or '-'}", f"- Reviewer note: {r.get(REVIEW_COLS['notes']) or '-'}",
              f"- Category (from list below): {TODO}", f"- What happened / corrected? / unsolved: {TODO}", ""]
    L += ["## Required categories (docs/08 section 8.6) — document at least one real case each, or state none observed",
          *[f"- [ ] {c}: {TODO}" for c in FAILURE_CATEGORIES], ""]
    return "\n".join(L)


def render_eval_md(rep: dict, usns: list[str], review: Optional[dict] = None, ablation_file: str = "ablation_study.md",
                   failure_file: str = "failure_analysis.md") -> str:
    """eval_P3_TeamID.md. FIRST LINE = all USNs comma-separated (DEL-05). Unknown facts stay TODO(team)."""
    first = next((r for r in rep["rows"] if r.get("measured")), None)
    e = (first or {}).get("environment", {})
    L = [",".join(usns) if usns else "TODO(team): USN_1,USN_2", "", "# Imagine AI — P3 Evaluation Report", "",
         "## Team and problem statement", f"{TODO}: team name, exact problem statement (P3 Resource-Efficient Text-to-Image Generation for Mobile Devices).", "",
         "## Environment", f"- OS: {e.get('os') or TODO}", f"- GPU: {e.get('gpu_name') or TODO}",
         f"- VRAM: {_s(e.get('gpu_total_vram_mb'), 0) if e.get('gpu_total_vram_mb') else TODO} MB",
         f"- Python/PyTorch/Diffusers: {e.get('python') or TODO} / {e.get('torch') or TODO} / {e.get('diffusers') or TODO}",
         f"- CPU, system RAM, Android device, Android/JDK/Gradle: {TODO}", "",
         "## Model and adaptation", f"- Base model and exact revision: {e.get('model_id') or TODO} @ {e.get('model_revision') or TODO}",
         "- Model license: TODO(team): verify on the model card", "- Scheduler: see result files (`generation_seen`)",
         "- Adaptation: **NOT DONE** — no adapter was trained or approved (training code and a gated loader exist; DL-02 open). State this explicitly; do not imply an adapted model exists.", "",
         "## Prompt benchmark", f"- Suite: prompt_suite_v1 (hold-out 'unseen' split, frozen); prompts/seeds/repeats per variant in the table below",
         "- Held-out protocol: hold-out gold written before parser run; demo must use NEW unseen prompts", "",
         "## Baseline and optimization configurations", "| Variant | Precision | Steps | Resolution | Other changes |", "|---|---|---:|---:|---|"]
    for v in VARIANTS:
        c = v.config
        other = ("CV on (P5A auto_enhance)" if v.cv else "") or ("NOT RUN: " + v.blocked_reason if v.blocked_reason else "")
        L.append(f"| {v.id} {v.title} | {c.precision} | {c.steps} | {c.resolution} | {other or '-'} |")
    L += ["", "## Results", "| Variant | CLIP mean | FID / alternative | Median e2e ms | Peak VRAM (alloc MB) | Peak RAM MB | Model size |",
          "|---|---:|---|---:|---:|---:|---|"]
    sz = rep.get("sizes") or {}
    size_txt = "NOT MEASURED" if sz.get("base_total_dir_bytes") is None else f"{sz['base_total_dir_bytes'] / 1048576:.0f} MB (base snapshot)"
    for r in rep["rows"]:
        if not r.get("measured"):
            L.append(f"| {r['id']} | NOT RUN | | | | | |")
            continue
        g = lambda s, k="median", nd=1: "-" if not s else f"{s[k]:.{nd}f}"  # noqa: E731
        L.append(f"| {r['id']} | {g(r.get('clip'), 'mean', 3)} | not computed (see FID note) | {g(r.get('end_to_end_ms'))} | "
                 f"{g(r.get('peak_gpu_mb'), nd=0)} | {_s(r.get('peak_process_ram_mb'), 0) if r.get('peak_process_ram_mb') else '-'} | {size_txt} |")
    f = rep["fid"]
    L += ["", f"**FID note:** {f['decision']} (real={f['n_real']}, generated={f['n_generated']}). "
          "Metric methods, sample sizes, warm-up, repeats and measurement definitions: `evaluation/reports/p7_report.md`.", "",
          "## Classical CV results",
          "P5A modules (resize/colour/edge) and P5B modules (quality assessment, artifact detection/correction) exist and are unit-tested on synthetic images only; "
          "V5 measures CLIP before/after `auto_enhance` and the share bypassed. The P5B detectors and their provisional thresholds have NOT been evaluated on real model output.", "",
          "## Adaptive controller", "**Implemented, NOT evaluated on measured data** — the P6 controller, fallback sequence and simulated constrained-resource tests exist (`docs/P6_ADAPTIVE.md`), but no measured benchmark profile exists, so there are no real controller decisions to report. State this explicitly; do not present simulated decisions as results.", "",
          "## Mobile feasibility", f"Deployment type (on-device/hybrid/cloud) and phone measurements: {TODO} (P8 not done).", "",
          "## Ablation study", f"See `{ablation_file}` (single-variable experiments V1-V3, V5; V4 labelled combined; V6/V7 NOT RUN).", "",
          "## Failure cases and limitations", f"See `{failure_file}`. Known limits: small sample (CIs wide), CLIP is a coarse signal, "
          "no encode/denoise/decode split, no real FID reference set, V6/V7 not run, P5B detectors unvalidated on real output, P8 not done.", "",
          "## Reproduction", "```", "pip install -r requirements.txt ; pip install -r requirements-ml.txt",
          '$env:MODEL_REVISION="<commit hash>"', "python evaluation/scripts/run_p7_eval.py --all --clip",
          "python evaluation/scripts/analyze_p7_results.py", "python evaluation/scripts/build_p7b_report.py --usns USN_1,USN_2",
          "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000", "```", ""]
    return "\n".join(L)
