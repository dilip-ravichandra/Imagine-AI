# Imagine AI — "Your imagination. Our intelligence."
P3: Resource-efficient text-to-image generation for mobile. Phase: **P6 Adaptive controller** (on top of P5A Classical CV) on top of P4/P2/P1A (P3 adaptation skipped by decision — see docs/P4_OPTIMIZATION.md) (SD-Turbo behind the frozen API v1.0.0).

## Run the backend (Windows PowerShell)
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# GPU torch first (see requirements-ml.txt header), then:
pip install -r requirements-ml.txt
$env:PRELOAD_MODEL="true"        # optional: load model at startup
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Without `requirements-ml.txt` the server still starts: `/health` and `/api/v1/capabilities` work and `generate` returns a stable 503.
Phone on the same Wi-Fi: use `http://<laptop-LAN-IP>:8000` (allow Python through Windows Firewall). Android emulator: `http://10.0.2.2:8000`.
First start downloads the model (several GB) from Hugging Face.

## Tests
`python -m pytest -q` — fast, no weights needed.
Real model (GPU laptop only): `$env:RUN_REAL_MODEL="1"; python -m pytest tests/test_real_model_smoke.py -s -m real_model`

## Android
Open `android/` in Android Studio (not built yet — see TEST_RESULTS.md). Docs: `docs/`.

## Prompt analysis (P2) — Windows PowerShell
```
python evaluation/scripts/run_prompt_suite.py          # dev + hold-out report
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/prompt/analysis -ContentType "application/json" -Body '{"prompt":"A red robot beside a blue submarine underwater"}'
```
Docs: `docs/PROMPT_PARSER.md`. Needs Python 3.10+.

## Inference optimization (P4) — run on the GPU laptop, Windows PowerShell
```
$env:MODEL_REVISION="<commit hash>"
python evaluation/scripts/run_p4_benchmarks.py --list
python evaluation/scripts/run_p4_benchmarks.py --all
python evaluation/scripts/analyze_p4_results.py
```
Server knobs: `PRECISION`, `ATTENTION_SLICING`, `VAE_SLICING`, `OFFLOAD`, `WEIGHTS_VARIANT` (defaults = unchanged P1A behaviour). Docs: `docs/P4_OPTIMIZATION.md`. **No measured P4 results exist yet.**

## Adaptive controller (P6)
```
python evaluation/scripts/demo_p6_controller.py     # SYNTHETIC profile: invented numbers, simulated budgets + OOM
$env:ADAPTIVE_PROFILE="evaluation\profiles\profile_<gpu>.json"   # opt-in; see docs/P6_ADAPTIVE.md
```
No measured profile exists yet (needs the GPU laptop). Default behaviour is unchanged when `ADAPTIVE_PROFILE` is unset.

## Classical CV (P5A)
```
python evaluation/scripts/demo_cv_p5a.py                      # synthetic before/after -> evaluation/results/p5a/
python evaluation/scripts/demo_cv_p5a.py --input path\to\your_generated.png
```
Modules: `computer_vision/{resize,enhancement,edge_aware}`. Not wired into `/generate` yet (P5B). Defaults are untuned: see `docs/P5A_CV.md` section 4.
