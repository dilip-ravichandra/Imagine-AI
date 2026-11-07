# P6 — Resource-Adaptive Quality Controller (task README)
Adds a deterministic, explainable, profile-driven controller + fallback runner (`ai_engine/adaptive/`), opt-in backend wiring, profile build/sweep scripts, a synthetic demo and 95 tests. **No measured profile exists; defaults are uncalibrated; nothing ran on a GPU.** Full design, limits and the measured-profile collection procedure: `docs/P6_ADAPTIVE.md`.
## Run / test (Windows PowerShell, repo root)
```
python -m pytest -q
python evaluation/scripts/demo_p6_controller.py
```
