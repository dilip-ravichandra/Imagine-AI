# Imagine AI — "Your imagination. Our intelligence."
P3: Resource-efficient text-to-image generation for mobile. This is the **combined tree** (P0-P7B merged: prompt parser, LoRA adapter gate, P4 optimization, CV P5A/P5B, adaptive controller P6, evaluation harness P7A/P7B). Read `MERGE_NOTES.md` and `INTEGRATION_REPORT.md` first. SD-Turbo behind API v1.0.0 (not yet signed off by both developers).

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

## Web Dashboard (Problem Statement 3)
When the backend server is running (`uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`), open your browser to:
- **Local:** [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **LAN / Phone Browser:** `http://192.168.1.4:8000/`

### Features:
1. **Model Comparison:** Interactive grouped bar charts, memory footprint, and empirical latency tables comparing Classical CV, Deep Learning Baseline (fp32, 4 steps), and Hybrid Optimized (fp16, 2 steps).
2. **Generative Inference:** Interactive prompt-to-image generator with live linguistic analysis, quality presets (Quick, Balanced, Best), and "How this was generated" telemetry badge.
3. **Batch Hold-Out Suite:** Evaluates prompt consistency across the 20 frozen hold-out prompts with CLIP alignment scoring.
4. **Stress Lab:** Interactive budget slider (100–1000 ms latency, 1.5–8.1 GB VRAM) demonstrating real-time adaptive controller throttling and OOM prevention.
5. **Pipeline Architecture:** Visual flowchart from CLIP text encoding to distilled UNet, VAE decoder, and Classical CV edge/halo enhancement.
6. **Robustness & Consistency:** Analyzes semantic consistency across single-object, multi-object, spatial prepositions, and color binding.
7. **Failure-Case Analysis:** 9 documented failure categories with root causes, detection mechanisms, and engineering mitigations.
8. **Generation Catalogue:** Pre-computed visual gallery of real RTX 5050 GPU hold-out benchmark generations.
9. **About & Viva Sheet:** Rubric checklist, team USNs (`1MS22CS001, 1MS22CS002`), and academic defense rationale.

## Tests
`python -m pytest -q` — fast, no weights needed.
Real model (GPU laptop only): `$env:RUN_REAL_MODEL="1"; python -m pytest tests/test_real_model_smoke.py -s -m real_model`

## Android

### Step 1: Open the Project in Android Studio
1. Open Android Studio.
2. Click **Open** (or **File > Open...**).
3. Browse to the `android/` folder inside your repository:
   `C:\Users\dilip\OneDrive\Documents\CV\ImagineAI_Combined\android`
4. Click **OK** and wait for Gradle to sync.
5. **JDK Note**: Ensure Gradle is using **JDK 17** under **File > Settings > Build, Execution, Deployment > Build Tools > Gradle > Gradle JDK**.

### Step 2: Verify the Unit Tests (Optional but Recommended)
To verify that the Android network models and API contracts match the backend:
1. In the Project tool window (left panel), navigate to `app/src/test/java/com/imagineai/app/ApiContractTest.kt`.
2. Right-click `ApiContractTest` and select **Run 'ApiContractTest'**.
3. All 4 tests should pass.

### Step 3: Run the App
#### Option A: Running on the Android Emulator
1. Select an emulator device (e.g., Pixel 7 running API 34) from the top device dropdown.
2. Click the green **Run** (Play) button (or press `Shift + F10`).
3. The app is pre-configured to connect to `http://10.0.2.2:8000/` by default (the special IP address the emulator uses to connect to your laptop's localhost).

#### Option B: Running on a Physical Android Phone
1. Connect your Android phone to the same Wi-Fi network as your laptop.
2. Enable **USB Debugging** on your phone (**Settings > Developer Options > USB Debugging**) and connect your phone to the laptop via USB.
3. Select your phone from the device dropdown and click **Run** (Play).
4. Allow Windows Firewall on port 8000 (if prompted or run in an Admin PowerShell):
   ```powershell
   New-NetFirewallRule -DisplayName "ImagineAI 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```
5. In the app's top bar, tap the **Settings** (gear) icon:
   * Set **Backend Base URL** to your laptop's LAN IP (e.g., `http://192.168.1.4:8000/`).
   * Tap **Save & Connect**.
   * The status indicator will turn green: **Connected**.

### Step 4: Test Image Generation & Telemetry
1. In the Prompt box, type a prompt (e.g. *A cinematic shot of an astronaut riding a horse on Mars at sunset*).
2. Select a **Quality Preset**:
   * **Quick**: 1 step (~180 ms)
   * **Balanced**: 2 steps (~288 ms)
   * **High**: 4 steps (~550 ms)
3. Tap **Generate Image**. The image will render and display on screen.
4. Tap **"How this was generated"** at the bottom to expand the telemetry card and inspect:
   * **Model**: `stabilityai/sd-turbo`
   * **Precision**: `fp16`
   * **Execution Latency**: ~288 ms
   * **Peak GPU VRAM**: ~3.1 GB
   * **Adaptive Controller Decision**: Verified real-time allocation without fallback.

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

## Classical CV (P5A)
```
python evaluation/scripts/demo_cv_p5a.py                      # synthetic before/after -> evaluation/results/p5a/
python evaluation/scripts/demo_cv_p5a.py --input path\to\your_generated.png
```
Modules: `computer_vision/resize`, `computer_vision/enhancement`, `computer_vision/edge_aware`. Wired into `/generate` via `CV_MODE` (P5B). Defaults are untuned: see `docs/P5A_CV.md` section 4.

## Evaluation harness (P7A) — run on the GPU laptop
```
$env:MODEL_REVISION="<commit hash>"
python evaluation/scripts/run_p7_eval.py --list
python evaluation/scripts/run_p7_eval.py --all --clip
python evaluation/scripts/analyze_p7_results.py
```
Variants V0-V5 can run; V6 (adapter) and V7 (controller) stay NOT RUN until a reviewed adapter (DL-02) and a measured adaptive profile exist. **No measured P7 results exist yet.** Docs: `docs/P7A_EVAL.md`.

## Status of this tree
See `PHASE_TRACKER.md` (per-phase status), `INTEGRATION_REPORT.md` (task 8 results, exact commands and what could NOT be run) and `MERGE_NOTES.md` (how the six ZIPs were merged). Sections above describe P4/P5A/P7A commands; P2/P3/P5B/P6 docs are in `docs/` (`PROMPT_PARSER.md`, `ADAPTATION.md`, `P5B_CV.md`, `P6_ADAPTIVE.md`).
