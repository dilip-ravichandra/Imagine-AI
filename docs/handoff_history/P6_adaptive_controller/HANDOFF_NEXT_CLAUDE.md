# HANDOFF_NEXT_CLAUDE.md
## Project
Imagine AI — P3 Resource-Efficient Text-to-Image Generation (hybrid/cloud inference).
## Current phase
- P6 Adaptive controller — **COMPLETE for code + tests; NO measured profile; nothing run on the GPU laptop.** Date: 2026-11-07.
- Still open from before: P5B (quality metrics + artifact detection) **not present in the uploaded ZIPs**; P4 measured results NOT RUN; P1A real SD-Turbo run NOT RUN; P0/P1B Android unverified; P3A/P3B skipped (DL-02 open).
## Completed
`ai_engine/adaptive/`: profiles, policy, resource monitors, deterministic controller (`decide`, `fallback`), fallback executor, profile builder. Opt-in backend wiring (`ADAPTIVE_PROFILE`). Scripts: `build_adaptive_profile.py`, `run_p6_profile_sweep.py`, `demo_p6_controller.py`. 95 new tests. `docs/P6_ADAPTIVE.md`.
## Interfaces
`docs/P6_ADAPTIVE.md` sections 2-5. API v1.0.0 unchanged (`resource_decision` filled when the controller is on; new 503 RESOURCE_EXHAUSTED case).
## Tests
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q tests/test_adaptive_*.py` | see TEST_RESULTS.md | 95 passed in the sandbox through a throwaway pytest shim; real pytest NOT available there |
| `tests/test_adaptive_api.py` (2 tests) | NOT RUN | needs fastapi/pydantic |
| Full suite (earlier 355 + new) with real pytest | NOT RUN | run on the laptop first |
## Known issues
Defaults (headroom 10 %, tolerances 0.8/0.4/0.0) are uncalibrated guesses. Steps-as-quality proxy is unmeasured. Engine cannot change precision/model at run time (locked runtime). No preemptive timeout. GPU-name mismatch between profile and machine is not warned about. Remote fallback unreachable from the API.
## Decisions
Profile-only reasoning (no extrapolation); resolution honoured if any safe profiled config exists; ladder order resolution -> precision -> steps -> model -> remote; Best mode errors instead of degrading steps; synthetic profile refused unless explicitly allowed; controller OFF by default.
## Exact next task (human first)
1. On the GPU laptop: `python -m pytest -q` (real pytest, whole suite). 2. Pin MODEL_REVISION; run P1A smoke test, then `run_p4_benchmarks.py --all --clip`, then `run_p6_profile_sweep.py --all --clip`, then `build_adaptive_profile.py`. 3. Start the server with `ADAPTIVE_PROFILE` and try Quick/Balanced/Best plus a forced low-VRAM case; keep `ADAPTIVE_DECISION_LOG`. 4. Then P5B (CV quality/artifacts) or P7A (metrics harness).
## Must NOT redo
Scaffold, API schema, engine/service, prompt parser, P4 harness, P5A modules, P6 controller (extend, do not rewrite).
## Missing input
Real SD-Turbo images, GPU results, MODEL_REVISION, repo URL, phone model, P5B code, contract sign-off.
