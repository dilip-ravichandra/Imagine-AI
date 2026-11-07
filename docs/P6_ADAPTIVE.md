# P6 — Resource-Adaptive Quality Controller and fallback

Status: **code + 95 tests complete; NO measured profile exists yet** (needs the GPU laptop). Covers ADV-05, ADV-06, APP-03 (explanation text) and part of ADV-03. Until a real profile is built, every demo uses the **synthetic fixture** (invented numbers, labelled as such everywhere).
Pure Python in `ai_engine/adaptive/` (no torch, no pydantic). Backend wiring is **opt-in**: without `ADAPTIVE_PROFILE` the server behaves exactly as in P5A (fixed quick 1 / balanced 2 / best 4 steps). API v1.0.0 is unchanged.

## 1. Pieces
| File | Role |
|---|---|
| `profiles.py` | `ProfileEntry` / `ProfileSet`: the measured facts (latency median/p95, GPU peak max/median, RAM peak, optional CLIP, benchmark status). JSON schema `adaptive_profile/1`; `synthetic` must be stated explicitly. |
| `policy.py` | `ControllerPolicy`: every tunable number (headroom, quality tolerances, fallback order, ...). External JSON possible. **Defaults are uncalibrated.** |
| `resources.py` | `ResourceSnapshot`, `SystemMonitor` (torch.cuda + psutil, lazily imported, unknown = `None`), `StaticMonitor`, `CappedMonitor` (simulated constraint). |
| `controller.py` | `AdaptiveController.decide()` and `.fallback()`; `ResourceError` when nothing is safe. |
| `executor.py` | `run_with_fallback()`: runs the engine call, classifies failures, applies the fallback sequence. |
| `profile_build.py` | Measured result files -> profile. |
| `backend/app/services/adaptive.py`, `generation.py` | Opt-in wiring, JSONL decision log, error mapping. |

## 2. Decision algorithm (deterministic; no randomness, clock or network)
Inputs: quality mode, requested resolution, resource snapshot, profile, policy, optional prompt-complexity level, locked runtime, remote consent.
1. **Screen** each profiled entry: known-bad benchmark (oom/error), remote without consent, resolution above the request, missing latency, runtime locked by the loaded engine (precision/model/offload need a reload), CUDA entry on a machine without CUDA.
2. **Ideal** = best entry for the mode *as if resources were unlimited*, at the highest profiled resolution <= the request (local entries only; remote is never a first pick).
3. **Ranking rule (all modes):** quality guardrail, then lowest measured median latency. Guardrail: `quality >= best - tol*(best-worst)` over the candidate set (scale-free). Defaults: quick tol 0.8, balanced 0.4, best 0.0 (= highest quality). Quality = measured `clip_mean` if **every** candidate has it, otherwise the **steps proxy, labelled `steps_proxy_UNMEASURED`** in the log and the explanation.
4. **Safety:** an entry fits if `measured GPU peak * (1 + headroom) <= snapshot.gpu_budget_mb`. Budget = free GPU memory + memory this process already reserved. Memory statistic default = worst observed run (`max`). Missing metric or unknown budget => rejected (policy `unknown_memory=allow` lets it through, flagged `UNVERIFIED_*`). CPU-only entries and (opt-in) GPU entries are also checked against RAM.
5. If the ideal is safe, use it. Otherwise walk the **fallback ladder** from the ideal: resolution -> precision/memory option -> steps -> smaller model -> remote (consented) (`policy.fallback_order`, docs/04 §4.10). A candidate sits on its deepest rung (resolution + precision change = "precision" rung); never raises resolution or local steps; changes involving steps must still pass the quality guardrail, so **Best mode returns a clear error instead of silently degrading**.
6. Nothing safe => `ResourceError` (code `NO_SAFE_CONFIGURATION`, full log). The service maps it to the existing frozen error shape: 503 `RESOURCE_EXHAUSTED`, retryable, with a suggested action.

Requested resolution is honoured whenever a safe profiled config exists at it. A resolution with no profile (e.g. 640 when only 256/384/512 were measured) is **never extrapolated**: the closest profiled size is used and flagged `RESOLUTION_NOT_PROFILED`.

## 3. Runtime fallback (actual OOM)
`run_with_fallback` calls the engine; on a failure classified as `oom` (engine's 503 `RESOURCE_EXHAUSTED`, torch `OutOfMemoryError`, "out of memory" RuntimeError) it re-reads the snapshot and calls `fallback()`: next entry on the ladder that is safe now, not yet attempted, and strictly lighter in the failed resource. The 429 "busy" error and every non-resource exception propagate unchanged (bugs are never masked). `timeout` fallback exists but is **off by default** (`fallback_on`); there is no preemptive timeout, only a `TimeoutError` raised by the caller's run function is classified. Attempts are capped by `max_fallback_attempts`.

## 4. Outputs and logging
`Decision`: selected entry (model, precision, resolution, steps, expected measured band), `fallback_used`, stable `reason` code, human `explanation`, and a structured `log` (`adaptive_decision/1`): inputs (request, snapshot, profile id + `synthetic`, policy incl. `calibrated`), an evaluation for **every** profile entry (selected / accepted / rejected + code + numbers), guardrail values, `input_hash`. Logged via `imagineai.adaptive` and, if `ADAPTIVE_DECISION_LOG` is set, one JSON line per decision. No prompt text is logged. API: `resource_decision{fallback_used, reason, explanation}` is filled from the decision (chain of hops after runtime fallbacks).

## 5. Run it
```
python evaluation/scripts/demo_p6_controller.py                    # synthetic fixture; table + simulated OOM
python -m pytest -q tests/test_adaptive_*.py
```
Enable in the server (after building a real profile): `$env:ADAPTIVE_PROFILE="evaluation\profiles\profile_<gpu>.json"` (add `ADAPTIVE_POLICY`, `ADAPTIVE_DECISION_LOG` as needed). A synthetic profile is refused at startup unless `ADAPTIVE_ALLOW_SYNTHETIC=true`. A bad profile/policy fails startup loudly (never a silent fallback to fixed steps).
**Integration limit:** the loaded engine cannot change precision/model/offload without a reload, so the service passes a *locked runtime*; only configs matching it (differing in resolution/steps) are selectable. Switching precision or model at run time is a future extension (engine reload).

## 6. How measured profiles are collected (GPU laptop, PowerShell)
```
$env:MODEL_REVISION="<commit hash>"
python evaluation/scripts/run_p4_benchmarks.py --all                    # B0, E1..E6, C1 (512 only)
python evaluation/scripts/run_p6_profile_sweep.py --all                 # resolution x precision x steps; one subprocess each
python evaluation/scripts/build_adaptive_profile.py                     # -> evaluation/profiles/profile_<gpu>.json
```
Use `--clip` in the benchmarks so quality is measured, not the steps proxy. The builder keeps OOM/error runs as known-bad entries, skips results with < 10 successful runs or not on CUDA, and refuses to mix GPUs/models/revisions. **Calibration:** compare the controller's choices with `nvidia-smi` and real OOMs, tune `headroom_fraction`/tolerances in a policy file, then set `calibrated: true`. Sweep size: 30 configs x (44 timed + warm-up runs) by default; narrow with `--resolutions/--precisions/--steps`.

## 7. Known limitations
- No measured profile, no real-GPU run, no Windows run, no Android check: everything above is verified only with synthetic data and fakes.
- Headroom 10 % and the quick/balanced tolerances are provisional guesses. The steps proxy assumes more steps = higher quality, which P4/P7 must confirm.
- Latency/memory only transfer to the profiled machine; a GPU-name mismatch is not checked (planned: warn). Peak RAM includes already-resident weights, hence the RAM check is opt-in for GPU entries.
- Complexity input (from P2) is plumbed but has **no effect by default** (no evidence yet).
- Remote/hybrid fallback is implemented in the controller but not reachable from the API: it needs a consent UI and a remote endpoint (neither exists).
- Not covered: pixel-level quality of fallback outputs (P7), CV stages in the decision (the controller does not consider CV).
