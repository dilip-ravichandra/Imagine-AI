# CHANGELOG
## P5B
- Added `computer_vision/quality/metrics.py` (QualityReport, noise/blur/halo/structure measures), `artifacts/{detect,correct,semantic}.py`, `pipeline.py`.
- Service: `Settings.cv_mode` / env `CV_MODE=off|assess|correct` (default off); `GenerationService._run_cv` fills `quality` and `performance.cv_ms`, failure-safe. No schema change.
- Added `evaluation/scripts/report_cv_p5b.py` + committed synthetic outputs `evaluation/results/p5b/`; `docs/P5B_CV.md`; README, API_CONTRACT note, PHASE_TRACKER, `.env.example` updated.
- Tests: +60 (quality, artifacts, pipeline, backend integration). Total 415 passed, 1 skipped.
- Found and fixed while building: thin blurred lines were misread as halos; noise hid blur in the blur ratio; luma-only noise estimate under-read per-channel noise by ~0.67; smooth skies would have been called blurry (structure guard added). Several first-draft test premises were corrected from measured behaviour; no P5A module changed.
## P5A
- Added `computer_vision/common.py` (CVResult, validation, PIL helpers), `resize/resize.py`, `enhancement/enhance.py`, `edge_aware/edges.py` (+ package `__init__`s).
- Added `evaluation/scripts/demo_cv_p5a.py` and committed synthetic demo outputs in `evaluation/results/p5a/`.
- Added `docs/P5A_CV.md`; README, PHASE_TRACKER, API_CONTRACT note updated; `requirements.txt` + numpy, opencv-python-headless.
- Tests: +61 (`test_cv_resize/enhance/edge/compose.py`). Total 355 passed, 1 skipped. No backend/API/engine change.
- During testing, 5 first-draft test premises were wrong (not the code) and were corrected from measured behaviour; no module code changed because of them.
## P4
- Added `ai_engine/optimization/{config,policy,experiments,stats,benchmark,report}.py`: validated `OptimizationConfig`, torch-free policy, 8-experiment grid (B0 baseline, E1-E6 single-variable, C1 labelled combined), stats + pixel fidelity, benchmark core, mechanical report/gate.
- `backend/app/config.py`: new `Settings` fields + env vars `PRECISION`, `ATTENTION_SLICING`, `VAE_SLICING`, `OFFLOAD`, `WEIGHTS_VARIANT` (invalid values raise at startup). Defaults reproduce P1A.
- `backend/app/services/engine.py`: precision resolution, weight-variant choice, offload (never preceded by `.to(device)`), attention/VAE slicing; `load_info` attribute recorded by benchmarks. Config errors map to the existing safe `INTERNAL_ERROR`.
- Added `evaluation/scripts/run_p4_benchmarks.py` (refuses unpinned `MODEL_REVISION`; one subprocess per experiment) and `analyze_p4_results.py` (gate exit code).
- Added `docs/P4_OPTIMIZATION.md`; API contract: "no API change" note. API version stays 1.0.0; `GenerateResponse` unchanged.
- Tests: +50 (core/policy/settings/stats, engine with fake torch, benchmark/report/CLI with synthetic data). Total 294 passed, 1 skipped.
