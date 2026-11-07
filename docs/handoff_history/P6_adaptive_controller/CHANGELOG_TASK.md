# CHANGELOG
## P6
- Added `ai_engine/adaptive/{profiles,policy,resources,controller,executor,profile_build}.py`: measured-profile schema (`adaptive_profile/1`), external policy, resource monitors (system/static/capped), deterministic controller with scale-free quality guardrail, fallback ladder (resolution -> precision -> steps -> model -> remote), `ResourceError`, OOM fallback executor, structured decision log (`adaptive_decision/1`).
- Backend (opt-in, default OFF): `Settings` + env `ADAPTIVE_PROFILE/POLICY/ALLOW_SYNTHETIC/DECISION_LOG`; `services/adaptive.py` (builder + JSONL sink); `GenerationService(controller, monitor)`; `errors.no_safe_configuration`; `create_app(controller=, monitor=)`. Without a profile the old fixed mapping runs unchanged.
- Scripts: `build_adaptive_profile.py`, `run_p6_profile_sweep.py`, `demo_p6_controller.py`. Fixture `tests/fixtures/adaptive_profile_synthetic.json` (INVENTED numbers).
- Docs: `docs/P6_ADAPTIVE.md`; API contract note (no schema change).
- Tests: +95 run via shim, +2 API tests not run.
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
