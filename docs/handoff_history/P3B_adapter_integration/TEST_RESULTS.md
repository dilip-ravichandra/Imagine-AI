# TEST_RESULTS (P3B on top of P3A and P2) — build sandbox: Ubuntu 24.04, Python 3.12.3, no GPU, no torch/diffusers, Hugging Face unreachable
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASS | 244 passed, 1 skipped (real-model smoke, skipped by design), 1 harmless Starlette/httpx deprecation warning. Includes the 35 P1A tests unchanged. |
| Same command in a fresh unzip of the final ZIP | PASS | see handoff for the exact count |
| Dev suite (67 prompts, `run_prompt_suite.py dev`) | PASS 67/67 | Parser was tuned on these: regression safety, NOT an accuracy figure |
| Hold-out suite (20 unseen prompts) | 12/20 (60%) | First run, parser untouched afterwards; frozen in `evaluation/results/prompt_suite_v1_holdout_first_run.json`; failure causes in `docs/PROMPT_PARSER.md`. Re-run on the final parser: still 12/20. |
| Evidence-integrity checks (all 87 suite prompts + 600 seeded fuzz inputs) | PASS | every span matches raw text; ids/relations consistent; parser never raised |
| Manual mutation checks (disable negators / drop "behind" / corrupt spans) | PASS (tests failed as they should) | One-off, not committed; parser restored and full suite re-run green |
| Live `uvicorn` + `POST /api/v1/prompt/analysis` (valid, blank) | PASS | 200 with expected JSON; blank -> 422 |
| Live `POST /api/v1/generate` without ML deps | PASS (expected 503) | stable error body, no traceback in server log |
| Real SD-Turbo smoke test | NOT RUN | unchanged from P1A: no GPU/torch/Hugging Face in sandbox |
| Run on Windows | NOT RUN | P2 code is pure Python (3.10+ syntax); `peak_wset` path from P1A still untested |
| Android Gradle build | NOT RUN | unchanged from P0 |

## P3A additions (same sandbox: Python 3.12.3, no GPU, no torch/diffusers)
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASS | 300 passed, 1 skipped (244 + 56 new in test_training_data / _launcher / _compare) |
| 12 manual mutation checks | PASS (each broke a test) | one-off; code restored and suite re-run green |
| CLI end-to-end (build_dataset, train_lora --dry-run, refusal paths) with 3 planted eval images | PASS | planted images rejected; overlap with eval set = none |
| Real LoRA training, `compare.run()`, 8 GB memory fit, dependency compatibility | NOT RUN | needs the GPU laptop |

## P3B additions (same sandbox: no GPU, no torch/diffusers)
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASS | 347 passed, 1 skipped (300 + 47 new: test_adapter_gate, test_approve_cli, test_adapter_engine) |
| 16 manual mutation checks on P3B code | PASS (each broke a test) | gate opens w/o approval, hash binding, 70%/40 boundaries, required steps, failures, stored-tally re-evaluation, half-loaded pipe reuse, OOM swallowed, missing label, wrong weight_name, crash-instead-of-fallback, approve CLI checks, unpinned revision. One-off, not committed |
| Live `uvicorn` with ADAPTER_PATH unset / unapproved / unpinned / missing / approved+pinned | PASS | server up, `/api/v1/model` truthful, generate 503 without ML deps (expected), 0 tracebacks, no paths in logs or responses |
| Real `load_lora_weights` on a trained adapter, GPU memory with adapter, Windows | NOT RUN | needs GPU laptop and a real adapter |
