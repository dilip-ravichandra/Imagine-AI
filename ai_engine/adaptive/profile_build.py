"""Turn raw benchmark result files (`p4_experiment_result/1`, written by ai_engine/optimization/benchmark.py)
into an adaptive profile. Pure Python. Reads only what was MEASURED; invents nothing.

Rules (all visible in the returned `skipped` list):
- status ok  + >= min_runs successful runs + measured on CUDA  -> entry with status "ok"
- status oom / error                                           -> entry kept as KNOWN-BAD (no metrics)
- status ok but too few runs, or not measured on a GPU          -> skipped (not proven for a GPU controller)
- one profile = one machine + one model: mixed gpu_name / model_id / model_revision raise ProfileError
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from .profiles import ProfileEntry, ProfileError, ProfileSet

RESULT_SCHEMA_PREFIX = "p4_experiment_result/"


def load_result_files(dirs: Iterable) -> list:
    out = []
    for d in dirs:
        for f in sorted(Path(d).glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and str(data.get("schema", "")).startswith(RESULT_SCHEMA_PREFIX):
                out.append((f, data))
    return out


def entry_from_result(data: dict, source: str, min_runs: int, require_gpu: bool) -> tuple:
    """(ProfileEntry | None, skip_reason | None)."""
    exp, env = data["experiment"], data.get("environment") or {}
    cfg, summary = exp["config"], data.get("summary") or {}
    info = data.get("load_info") or {}
    device = info.get("device") or ("cuda" if env.get("gpu_name") else "cpu")
    status = data.get("status", "error")
    n_ok = summary.get("n_ok", 0)
    base = dict(id=exp["id"], model_id=env.get("model_id") or "unknown", precision=cfg["precision"],
                steps=cfg["steps"], resolution=cfg["resolution"], device=device,
                attention_slicing=cfg.get("attention_slicing", False), vae_slicing=cfg.get("vae_slicing", False),
                offload=cfg.get("offload", "none"), source=source)
    if status in ("oom", "error"):
        return ProfileEntry(**base, status=status, n_runs=n_ok), None
    if status != "ok":
        return None, f"unknown status {status!r}"
    if require_gpu and device != "cuda":
        return None, "not measured on CUDA"
    if n_ok < min_runs:
        return None, f"only {n_ok} successful runs (< {min_runs})"
    lat, mem, clip = summary.get("latency_ms"), summary.get("peak_allocated_mb"), summary.get("clip_score")
    return ProfileEntry(**base, status="ok", n_runs=n_ok,
                        latency_ms_median=lat["median"] if lat else None, latency_ms_p95=lat["p95"] if lat else None,
                        peak_gpu_mb_max=mem["max"] if mem else None,
                        peak_gpu_mb_median=mem["median"] if mem else None,
                        peak_ram_mb=summary.get("peak_process_ram_mb"),
                        clip_mean=clip["mean"] if clip else None), None


def build_profile_set(dirs: Iterable, min_runs: int = 10, require_gpu: bool = True) -> tuple:
    """Returns (ProfileSet, skipped) where skipped = [(source, reason)]. Raises ProfileError if nothing usable
    or if the files come from different machines/models/revisions."""
    entries, skipped, envs = [], [], []
    for f, data in load_result_files(dirs):
        entry, why = entry_from_result(data, f.name, min_runs, require_gpu)
        if entry is None:
            skipped.append((f.name, why))
            continue
        entries.append(entry)
        envs.append(data.get("environment") or {})
    if not entries:
        raise ProfileError("no usable benchmark results found (run the benchmarks on the GPU laptop first)")
    for key in ("gpu_name", "model_id", "model_revision"):
        vals = {e.get(key) for e in envs}
        if len(vals) > 1:
            raise ProfileError(f"results mix several values of {key}: {sorted(map(str, vals))}; one profile = one setup")
    env = envs[0]
    hardware = {"gpu_name": env.get("gpu_name"), "gpu_total_vram_mb": env.get("gpu_total_vram_mb"),
                "python": env.get("python"), "os": env.get("os"), "torch": env.get("torch"),
                "diffusers": env.get("diffusers"), "cuda_runtime": env.get("cuda_runtime")}
    return ProfileSet(entries=tuple(entries), synthetic=False, hardware=hardware,
                      model_revision=env.get("model_revision"),
                      note=f"Built from {len(entries)} measured result file(s); min_runs={min_runs}."), skipped
