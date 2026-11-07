"""P4 benchmark core. Engine-agnostic (duck-typed DiffusionEngine) so it is unit-tested with a fake engine.

Writes one JSON per experiment (raw per-run records + summary) and the first-repeat image of every
(prompt, seed). It records measurements; it draws NO conclusions. Run one experiment per process so VRAM is clean.
"""
import dataclasses
import importlib
import importlib.metadata
import platform
import time
from pathlib import Path
from typing import Callable, Optional

from .experiments import BASELINE_ID, Experiment
from .stats import summarize

SCHEMA = "p4_experiment_result/1"
DEFAULT_CATEGORIES = ("simple", "multi_object", "attributes", "relations", "scene_lighting", "long")


def select_prompts(suite: dict, per_category: int = 2, categories=DEFAULT_CATEGORIES, split: str = "dev") -> list[dict]:
    """Deterministic: first `per_category` cases per category (file order) from the dev split.
    The hold-out split is never used here; it stays reserved for the final evaluation (P7)."""
    out, seen = [], {c: 0 for c in categories}
    for case in suite["cases"]:
        c = case["category"]
        if case["split"] == split and c in seen and seen[c] < per_category:
            seen[c] += 1
            out.append({"id": case["id"], "category": c, "prompt": case["prompt"]})
    return out


def _torch_cuda():
    try:
        torch = importlib.import_module("torch")
        return torch if torch.cuda.is_available() else None
    except Exception:  # noqa: BLE001 - torch missing or broken: no GPU numbers, never a crash
        return None


def gpu_snapshot() -> dict:
    """Allocated/reserved GPU memory in MB right now (peak_* since the last reset). None values if no CUDA."""
    t = _torch_cuda()
    if t is None:
        return {"allocated_mb": None, "peak_allocated_mb": None, "peak_reserved_mb": None}
    mb = 1048576
    return {"allocated_mb": t.cuda.memory_allocated() / mb, "peak_allocated_mb": t.cuda.max_memory_allocated() / mb,
            "peak_reserved_mb": t.cuda.max_memory_reserved() / mb}


def reset_gpu_peaks() -> None:
    t = _torch_cuda()
    if t is not None:
        t.cuda.reset_peak_memory_stats()


def _version(name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def collect_environment(model_id: Optional[str], model_revision: Optional[str]) -> dict:
    env = {"python": platform.python_version(), "os": platform.platform(), "torch": _version("torch"),
           "diffusers": _version("diffusers"), "transformers": _version("transformers"),
           "cuda_runtime": None, "gpu_name": None, "gpu_total_vram_mb": None,
           "model_id": model_id, "model_revision": model_revision}
    t = _torch_cuda()
    if t is not None:
        env["cuda_runtime"] = t.version.cuda
        env["gpu_name"] = t.cuda.get_device_name(0)
        env["gpu_total_vram_mb"] = t.cuda.get_device_properties(0).total_memory / 1048576
    return env


def _failure_status(exc: BaseException) -> str:
    return "oom" if getattr(exc, "code", None) == "RESOURCE_EXHAUSTED" else "error"


def run_experiment(exp: Experiment, engine, prompts: list[dict], seeds: list[int], repeats: int, warmup: int,
                   out_dir: Path, environment: dict, ram_fn: Callable[[], Optional[float]] = lambda: None,
                   clip=None, clock: Callable[[], float] = time.perf_counter) -> dict:
    """Run one experiment end to end and write <out_dir>/<id>.json. Returns the result dict.
    Stops at the first failure (OOM is recorded as a result, not hidden)."""
    cfg = exp.config
    out_dir = Path(out_dir)
    img_dir = out_dir / "images" / exp.id
    img_dir.mkdir(parents=True, exist_ok=True)
    result = {"schema": SCHEMA, "experiment": {"id": exp.id, "title": exp.title, "hypothesis": exp.hypothesis,
                                               "combined": exp.combined, "changed_fields": list(exp.changed),
                                               "config": dataclasses.asdict(cfg)},
              "environment": environment,
              "protocol": {"prompt_ids": [p["id"] for p in prompts], "seeds": list(seeds), "repeats": repeats,
                           "warmup": warmup, "resolution": cfg.resolution, "steps": cfg.steps,
                           "latency_definition": "wall time of engine.generate() incl. text encode, denoise, VAE "
                                                 "decode, CUDA sync; excludes PNG save, model load, CLIP scoring",
                           "memory_definition": "torch.cuda peak allocated/reserved since reset after warm-up; "
                                                "process RAM = peak working set since process start"},
              "status": "ok", "error": None, "model_load_ms": None, "load_info": None, "generation_seen": None,
              "gpu_after_load": None, "runs": [], "summary": None}

    def finish() -> dict:
        ok = [r for r in result["runs"] if r["status"] == "ok"]
        snap = gpu_snapshot()
        result["summary"] = {
            "n_ok": len(ok), "n_failed": len(result["runs"]) - len(ok),
            "latency_ms": summarize(r["total_ms"] for r in ok),
            "peak_allocated_mb": summarize(r["peak_gpu_mb"] for r in ok),
            "peak_reserved_mb_experiment": snap["peak_reserved_mb"],
            "peak_process_ram_mb": ram_fn(),
            "clip_score": summarize(r.get("clip_score") for r in ok)}
        import json
        (out_dir / f"{exp.id}.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
        return result

    try:
        result["model_load_ms"] = engine.ensure_loaded()
        result["load_info"] = getattr(engine, "load_info", None)
        result["gpu_after_load"] = gpu_snapshot()["allocated_mb"]
        for _ in range(warmup):
            engine.generate(prompts[0]["prompt"], seeds[0], cfg.resolution, cfg.resolution, cfg.steps)
    except Exception as exc:  # noqa: BLE001
        result["status"], result["error"] = _failure_status(exc), type(exc).__name__ + ": " + str(exc)[:200]
        return finish()

    reset_gpu_peaks()
    for p in prompts:
        for seed in seeds:
            for rep in range(repeats):
                try:
                    t0 = clock()
                    res = engine.generate(p["prompt"], seed, cfg.resolution, cfg.resolution, cfg.steps)
                    ms = (clock() - t0) * 1000.0
                except Exception as exc:  # noqa: BLE001
                    result["status"] = _failure_status(exc)
                    result["error"] = type(exc).__name__ + ": " + str(exc)[:200]
                    result["runs"].append({"prompt_id": p["id"], "seed": seed, "repeat": rep,
                                           "status": result["status"]})
                    return finish()
                if result["generation_seen"] is None:
                    result["generation_seen"] = {"model": res.model, "model_revision": res.model_revision,
                                                 "precision": res.precision, "scheduler": res.scheduler,
                                                 "steps": res.steps, "width": res.width, "height": res.height}
                rec = {"prompt_id": p["id"], "seed": seed, "repeat": rep, "status": "ok", "total_ms": ms,
                       "peak_gpu_mb": res.peak_gpu_mb}
                if rep == 0:  # outside the timed region
                    res.image.save(img_dir / f"{p['id']}_s{seed}.png")
                    if clip is not None:
                        rec["clip_score"] = clip.score(p["prompt"], res.image)
                result["runs"].append(rec)
    return finish()


class ClipScorer:
    """Optional CLIP text-image cosine similarity. NOT exercised in the build sandbox (needs weights).
    Reports a broad alignment signal only; it does not verify counts or spatial relations.

    The CLIP revision must be pinned (env CLIP_REVISION or `revision=`), like MODEL_REVISION: downloading an
    unpinned model means a later upstream change can silently alter the metric (and is a supply-chain risk).
    `model_id` is the label written into result files and includes the revision."""

    def __init__(self, model_id: str = "openai/clip-vit-base-patch32", device: str = "cpu",
                 revision: Optional[str] = None, allow_unpinned: bool = False):
        import os
        revision = revision or os.getenv("CLIP_REVISION") or None
        if revision is None and not allow_unpinned:  # checked before any heavy import so it is unit-testable
            raise ValueError("CLIP_REVISION is not set: pin the CLIP model revision (commit hash), "
                             "or pass --allow-unpinned for a throwaway run")
        import torch
        from transformers import CLIPModel, CLIPProcessor
        self.repo_id, self.revision, self.device, self._torch = model_id, revision, device, torch
        self.model_id = f"{model_id}@{revision or 'unpinned'}"
        self.model = CLIPModel.from_pretrained(model_id, revision=revision).to(device).eval()
        self.processor = CLIPProcessor.from_pretrained(model_id, revision=revision)

    def score(self, prompt: str, image) -> float:
        torch = self._torch
        inputs = self.processor(text=[prompt], images=image, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model(**inputs)
        t = out.text_embeds / out.text_embeds.norm(dim=-1, keepdim=True)
        i = out.image_embeds / out.image_embeds.norm(dim=-1, keepdim=True)
        return float((t * i).sum(-1).item())


__all__ = ["select_prompts", "collect_environment", "run_experiment", "ClipScorer", "gpu_snapshot",
           "BASELINE_ID", "SCHEMA"]
