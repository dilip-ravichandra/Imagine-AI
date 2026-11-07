# HANDOFF_NEXT_CLAUDE.md
## Project
Imagine AI — P3 Resource-Efficient Text-to-Image Generation (hybrid/cloud inference).
## Current phase
- P5B Classical CV (quality, artifacts, correction, pipeline) — **COMPLETE for code + tests; behaviour on real SD-Turbo output NOT evaluated; all thresholds provisional.** With P5A all five mandatory CV capabilities exist. Still open: P4 measured results, P1A real model run, P0/P1B Android, P3A/P3B skipped (DL-02 open).
- Date: 2026-11-07
## Completed
`computer_vision/quality`, `artifacts` (detect/correct/semantic), `pipeline.py`; service hook `CV_MODE=off|assess|correct` (default off); 60 tests; synthetic before/after report; `docs/P5B_CV.md`.
## Files
Key: `computer_vision/{quality/metrics.py,artifacts/*.py,pipeline.py}`, `backend/app/services/generation.py` (`_run_cv`), `backend/app/config.py`, `tests/test_cv_{quality,artifacts,pipeline,backend_integration}.py`, `evaluation/scripts/report_cv_p5b.py`.
## Interfaces
Schema unchanged. `quality` = {sharpness (Laplacian var), brightness, contrast (0..1), artifact_flags}; `performance.cv_ms`; flag `semantic_review_recommended` is prompt-derived. `correct` mode serves the corrected PNG and does NOT keep the original.
## Dependencies
numpy, opencv-python-headless (OpenCV 5.0.0 tested), lazy-imported only when CV_MODE != off.
## Tests
| Command | Status | Notes |
|---|---|---|
| python -m pytest -q | PASS | 415 passed, 1 skipped |
| report_cv_p5b.py | PASS | synthetic |
| Real images, laptop cv_ms, GPU, Windows, Android | NOT RUN | |
## Known issues
Conservative sharpen never fixed blur; CLAHE often rejected or leaves grain; intended grain/dark/tint look like defects unless the prompt says so; halo only on hard axis-aligned edges; clipping/halo flagged not fixed; semantic flag fires on any spatial relation (frequent); `sharpness` is noise-inflated; single-colour scenes fool gray-world.
## Decisions
CV off by default; accept a correction step only if its target number improves >=10 % with no new flag; semantic defects flagged never filtered; suppress flags the prompt asked for; failure falls back to original.
## Exact next task
Human (priority): P1A smoke test on the laptop, then run with `CV_MODE=assess` on real generations, look at flags and `cv_ms`, paste into docs. Next Claude: P6 adaptive controller needs P4 measured profiles first (card `P6_...`); if those are still missing, say so and do not invent them. Alternatives: P3A/P3B (DL-02) or P7A metrics harness.
## Next Claude must read
PROJECT_BRIEF.md, this handoff, `docs/P5B_CV.md`, `docs/P4_OPTIMIZATION.md`, the next phase card.
## Must NOT redo
Scaffold, API schema, engine/service, prompt parser, P4 harness, P5A/P5B modules (extend, do not rewrite).
## Missing input
Real SD-Turbo images, GPU benchmark results, MODEL_REVISION, repo URL, phone model, contract sign-off.
