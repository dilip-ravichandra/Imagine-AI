# TEST_RESULTS (GPU Laptop Run, 2026-11-07) — Windows 11, Python 3.12.10, NVIDIA GeForce RTX 5050 Laptop GPU (8GB VRAM), CUDA 12.8 / Driver 595.95
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASSED | **698 passed, 1 skipped** in 15.74s (all unit, integration, and safety tests passed on Windows) |
| `python -m pytest tests/test_real_model_smoke.py -s -m real_model` | PASSED | **1 passed** in 316.89s (model download + load + 2 generation runs) |

### P1A Real SD-Turbo Generation Output (512x512, 2 steps, fp16, seed 42)
```json
{
  "status": "success",
  "request_id": "d40d7d32d94e48fcb84ab0cfcf19aff1",
  "image_url": "http://testserver/images/d40d7d32d94e48fcb84ab0cfcf19aff1.png",
  "generation": {
    "model": "stabilityai/sd-turbo",
    "model_revision": "b261bac6fd2cf515557d5d0707481eafa0485ec2",
    "precision": "fp16",
    "scheduler": "EulerDiscreteScheduler(timestep_spacing=trailing)",
    "steps": 2,
    "width": 512,
    "height": 512,
    "seed": 42
  },
  "performance": {
    "model_load_ms": 306163.8821000088,
    "prompt_encode_ms": null,
    "denoise_ms": null,
    "decode_ms": null,
    "cv_ms": null,
    "end_to_end_ms": 1050.583699994604,
    "peak_gpu_mb": 3097.60986328125,
    "peak_process_ram_mb": 2547.3828125
  },
  "quality": null,
  "resource_decision": {
    "fallback_used": false,
    "reason": null,
    "explanation": "balanced mode -> 2 step(s) at 512x512. No adaptive controller yet (P6); no fallback applied."
  }
}
```
**Warm inference latency (second call):** `323.82 ms` end-to-end.
**Peak GPU VRAM:** `3,097.61 MB` (~3.1 GB / 8 GB).
**Peak System RAM:** `2,547.38 MB`.

---
# TEST_RESULTS (safety audit, 2026-11-07) — sandbox: Ubuntu 24.04, Python 3.12.3, no GPU/torch/Docker/Android
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` (before changes) | PASSED | 666 passed, 1 skipped — the earlier merge-session figure, now actually observed |
| `python -m pytest -q` (after changes) | PASSED | **698 passed, 1 skipped**; +32 in `tests/test_safety.py`; 2 existing assertions updated for corrected wording |
| Mutation checks (6 one-off breakages of auth route, key compare, static dir, key repr, CLIP pin, Docker USER) | PASSED | a test failed each time; code restored; not committed |
| Real `uvicorn` start + curl, auth off/on | PASSED | see `docs/SAFETY_AND_PHASE_AUDIT.md` §1 |
| `pip-audit -r requirements.txt` | PASSED | no known vulnerabilities (API/CV set only; ML deps NOT audited) |
| `bandit -r` (excl. vendored trainer) | 0 High, 2 Medium (fixed: unpinned CLIP), 10 Low (reviewed, accepted) | |
| P7 dry-run + analyzer; P5A/P5B/P6 demos regenerated | PASSED (plumbing) | outputs identical to committed synthetic files; gate NOT MET |
| Real SD-Turbo / GPU / CLIP / Windows / Android / Docker build / hosted URL | NOT RUN | |

---
# TEST_RESULTS (P7A) — build sandbox: Ubuntu 24.04, Python 3.12.3, OpenCV 5.0.0, numpy 2.5.4, no GPU, no torch/diffusers
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASSED | 401 passed, 1 skipped (real-model smoke, skipped by design); 355 earlier tests unchanged and green, +40 P7A and +6 P7B tests |
| P7A tests: metric maths (cosine, Frechet incl. closed-form cases, FID gate, paired deltas, clustered bootstrap), variant registry rules, size report, harness protocol (counts, warm-up, clock-injected latency, CV separate, OOM recorded, blocked refused), report gate/synthetic exclusion/CSV/sheet/plot, CLI | PASSED | fakes and stub CLIP only; fixture values are not results |
| `run_p7_eval.py --all --dry-run --split dev --limit 4` then `analyze_p7_results.py` | PASSED (plumbing) | synthetic engine; report says SYNTHETIC and gate NOT MET, as designed |
| Real SD-Turbo run, real CLIP scoring (`ClipScorer`), GPU memory, model size on a real snapshot | NOT RUN | no GPU/weights in sandbox |
| Any measured latency/memory/CLIP/FID number | NONE EXIST | nothing in this ZIP may be cited as a result |
| Windows/PowerShell run | NOT RUN | commands written for it, unverified |
| P4 benchmarks, P1A smoke test, Android build | NOT RUN | unchanged from earlier phases |
| `build_p7b_report.py` on empty results | PASSED (skeleton) | all results NOT RUN, TODO markers present, exit 1 as designed |
| Real P7B report content | NOT WRITTEN | depends on real measurements and human review |


# Task 08 integration session (2026-11-07) - sandbox: Ubuntu 24.04, Python 3.12.3, NO network, no pytest/fastapi/pydantic
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | NOT RUN | pytest could not be installed offline. The 666 passed / 1 skipped figure is from the earlier merge session, NOT re-confirmed |
| `python -m compileall -q .` | PASSED | no syntax errors |
| AST check of internal imports | PASSED | 125 modules, 0 unresolved |
| CLIs (`run_p7_eval.py` etc.) | NOT RUN | import `ai_engine.prompt` -> pydantic missing |
| Real model / GPU / Windows / Android / Docker build | NOT RUN | |
