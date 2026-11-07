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
