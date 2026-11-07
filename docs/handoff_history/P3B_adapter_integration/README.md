# Imagine AI — "Your imagination. Our intelligence."
P3: Resource-efficient text-to-image generation for mobile. Phase: **P3B Adapter integration** (after P3A) on top of P2 prompt intelligence and P1A (SD-Turbo behind the frozen API v1.0.0).

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

## Adaptation (P3A) — GPU laptop / Colab only
Code and tests are complete; **no training has been run**. Full runbook, hazards and the acceptance rule: `docs/ADAPTATION.md`.
```
pip install -r requirements-training.txt     # after the CUDA build of torch
python -m ai_engine.training.build_dataset --coco-annotations <captions_train2014.json> --coco-images <train2014 dir> --out training_data\smoke --preset smoke
python -m ai_engine.training.train_lora --data training_data\smoke --out adapters\smoke --revision <40-char sd-turbo hash> --preset smoke --dry-run
```

## Using an adapter (P3B) — optional, default off
The API serves the base model unless `ADAPTER_PATH` points at an adapter that passed `ai_engine.training.approve` **and** `MODEL_REVISION` matches its base revision. Anything else falls back to base; check `GET /api/v1/model`. Details: `docs/ADAPTATION.md`.
