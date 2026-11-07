# TEST_RESULTS (P2) — build sandbox: Ubuntu 24.04, Python 3.12.3, no GPU, no torch/diffusers, Hugging Face unreachable
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
