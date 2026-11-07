"""P7A run harness. Engine-agnostic (duck-typed DiffusionEngine) so it is unit-tested with fake engines.

Per variant it writes <out>/<id>.json (raw per-run records + environment + protocol + summary) and one PNG per
(prompt, seed). It records measurements and draws NO conclusions. Run one variant per process (clean VRAM).
Missing measurements stay null. A failure (incl. OOM) is recorded as the result and stops that variant.
"""
import dataclasses
import json
import time
from pathlib import Path
from typing import Callable, Optional

from ai_engine.optimization.benchmark import gpu_snapshot, reset_gpu_peaks
from ai_engine.optimization.stats import pixel_fidelity, summarize

from .cv_pipelines import PIPELINES
from .variants import Variant

SCHEMA = "p7_variant_result/1"
LATENCY_DEFINITION = ("generation_ms = wall time of engine.generate() (text encode + denoise + VAE decode + CUDA sync). "
                      "cv_ms = wall time of the CV pipeline on that image (0 when CV is off; counted even when the "
                      "pipeline bypasses). end_to_end_ms = generation_ms + cv_ms. Excludes model load, PNG save, "
                      "CLIP scoring. Model load is reported separately (model_load_ms). Encode/denoise/decode split is "
                      "recorded only if the engine result exposes `stage_ms`; otherwise null.")
MEMORY_DEFINITION = ("peak_gpu_mb = per-generation torch.cuda peak allocated reported by the engine; "
                     "peak_reserved_mb = torch.cuda peak reserved over the whole timed phase (after reset post warm-up); "
                     "peak_process_ram_mb = peak working set / max RSS of THIS process since start (includes model "
                     "load; system RAM, never mixed with VRAM)")


def select_eval_prompts(suite: dict, split: str = "holdout", per_category: Optional[int] = None,
                        limit: Optional[int] = None) -> list[dict]:
    """Deterministic (file order). Default split is the frozen hold-out ('unseen') set reserved for P7 evaluation.
    per_category/limit exist for smoke runs; the CLI records them in the protocol so subsets are never hidden."""
    out, seen = [], {}
    for case in suite["cases"]:
        if case["split"] != split:
            continue
        if per_category is not None and seen.get(case["category"], 0) >= per_category:
            continue
        seen[case["category"]] = seen.get(case["category"], 0) + 1
        out.append({"id": case["id"], "category": case["category"], "prompt": case["prompt"]})
        if limit is not None and len(out) >= limit:
            break
    return out


def _fail_status(exc: BaseException) -> str:
    return "oom" if getattr(exc, "code", None) == "RESOURCE_EXHAUSTED" else "error"


def run_variant(variant: Variant, engine, prompts: list[dict], seeds: list[int], repeats: int, warmup: int,
                out_dir: Path, environment: dict, ram_fn: Callable[[], Optional[float]] = lambda: None,
                clip=None, clock: Callable[[], float] = time.perf_counter, suite_info: Optional[dict] = None) -> dict:
    if not variant.runnable:
        raise ValueError(f"{variant.id} is blocked: {variant.blocked_reason}")
    if repeats < 1 or not prompts or not seeds:
        raise ValueError("need >=1 prompt, >=1 seed, repeats>=1")
    cfg = variant.config
    cv_fn = PIPELINES[variant.cv] if variant.cv else None
    out_dir = Path(out_dir)
    img_dir = out_dir / "images" / variant.id
    img_dir.mkdir(parents=True, exist_ok=True)
    if cv_fn:
        (out_dir / "images" / f"{variant.id}_raw").mkdir(parents=True, exist_ok=True)

    result = {"schema": SCHEMA,
              "variant": {"id": variant.id, "title": variant.title, "hypothesis": variant.hypothesis,
                          "combined": variant.combined, "changed": list(variant.changed),
                          "config": dataclasses.asdict(cfg), "cv": variant.cv, "adapter": variant.adapter},
              "environment": environment,
              "protocol": {"prompt_ids": [p["id"] for p in prompts], "seeds": list(seeds), "repeats": repeats,
                           "warmup": warmup, "resolution": cfg.resolution, "steps": cfg.steps,
                           "suite": suite_info, "clip_model": getattr(clip, "model_id", None),
                           "latency_definition": LATENCY_DEFINITION, "memory_definition": MEMORY_DEFINITION},
              "synthetic": bool(getattr(engine, "is_synthetic", False)),
              "status": "ok", "error": None, "model_load_ms": None, "load_info": None, "generation_seen": None,
              "gpu_after_load_mb": None, "runs": [], "summary": None}

    def finish() -> dict:
        ok = [r for r in result["runs"] if r["status"] == "ok"]
        snap = gpu_snapshot()
        result["summary"] = {
            "n_ok": len(ok), "n_failed": len(result["runs"]) - len(ok),
            "generation_ms": summarize(r["generation_ms"] for r in ok),
            "cv_ms": summarize(r["cv_ms"] for r in ok),
            "end_to_end_ms": summarize(r["end_to_end_ms"] for r in ok),
            "peak_gpu_mb": summarize(r["peak_gpu_mb"] for r in ok),
            "peak_reserved_mb": snap["peak_reserved_mb"], "peak_process_ram_mb": ram_fn(),
            "clip_score": summarize(r.get("clip_score") for r in ok),
            "cv_applied_fraction": (sum(bool(r.get("cv_applied")) for r in ok) / len(ok)) if (ok and cv_fn) else None}
        (out_dir / f"{variant.id}.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
        return result

    try:
        result["model_load_ms"] = engine.ensure_loaded()
        result["load_info"] = getattr(engine, "load_info", None)
        result["gpu_after_load_mb"] = gpu_snapshot()["allocated_mb"]
        for _ in range(warmup):
            engine.generate(prompts[0]["prompt"], seeds[0], cfg.resolution, cfg.resolution, cfg.steps)
    except Exception as exc:  # noqa: BLE001
        result["status"], result["error"] = _fail_status(exc), type(exc).__name__ + ": " + str(exc)[:200]
        return finish()

    reset_gpu_peaks()
    for p in prompts:
        for seed in seeds:
            for rep in range(repeats):
                base_rec = {"prompt_id": p["id"], "category": p["category"], "seed": seed, "repeat": rep}
                try:
                    t0 = clock()
                    res = engine.generate(p["prompt"], seed, cfg.resolution, cfg.resolution, cfg.steps)
                    gen_ms = (clock() - t0) * 1000.0
                    cv_ms, final, applied, cv_notes = 0.0, res.image, None, []
                    if cv_fn:
                        t1 = clock()
                        final, applied, cv_notes = cv_fn(res.image)
                        cv_ms = (clock() - t1) * 1000.0
                except Exception as exc:  # noqa: BLE001
                    result["status"] = _fail_status(exc)
                    result["error"] = type(exc).__name__ + ": " + str(exc)[:200]
                    result["runs"].append({**base_rec, "status": result["status"]})
                    return finish()
                if result["generation_seen"] is None:
                    result["generation_seen"] = {k: getattr(res, k, None) for k in (
                        "model", "model_revision", "precision", "scheduler", "steps", "width", "height")}
                rec = {**base_rec, "status": "ok", "generation_ms": gen_ms, "cv_ms": cv_ms,
                       "end_to_end_ms": gen_ms + cv_ms, "peak_gpu_mb": getattr(res, "peak_gpu_mb", None),
                       "stage_ms": getattr(res, "stage_ms", None), "cv_applied": applied}
                if rep == 0:  # quality measured once per (prompt, seed), outside every timed region
                    name = f"{p['id']}_s{seed}.png"
                    final.save(img_dir / name)
                    rec["image"] = f"images/{variant.id}/{name}"
                    if cv_fn:
                        res.image.save(out_dir / "images" / f"{variant.id}_raw" / name)
                        rec["cv_notes"] = cv_notes
                        rec["cv_pixel_fidelity_vs_raw"] = pixel_fidelity(final, res.image)
                    if clip is not None:
                        rec["clip_score"] = clip.score(p["prompt"], final)
                        if cv_fn:
                            rec["clip_score_raw"] = clip.score(p["prompt"], res.image)
                result["runs"].append(rec)
    return finish()
