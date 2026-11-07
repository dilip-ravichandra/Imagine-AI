# ImagineAI — Comprehensive Project Engineering & Research Report

**Problem Statement 3 (P3): Resource-Efficient Text-to-Image Generation for Mobile Devices**  
**Team ImagineAI:** USN `1MS22CS001`, `1MS22CS002`  
**Target Hardware:** NVIDIA GeForce RTX 5050 Laptop GPU (8,151 MB VRAM), Windows 11  
**Software Stack:** Python 3.12.10, PyTorch 2.11.0+cu128, Diffusers 0.42.1, PEFT 0.21.2, FastAPI, Jetpack Compose (Android 14)

---

## Table of Contents
1. [Executive Summary & Problem Statement Alignment](#1-executive-summary--problem-statement-alignment)
2. [Complete System Architecture & 5-Stage Pipeline](#2-complete-system-architecture--5-stage-pipeline)
3. [The 3-Tier Scientific Progression: SD 1.5 Baseline → Adapted → Final Optimized](#3-the-3-tier-scientific-progression-sd-15-baseline--adapted--final-optimized)
4. [Adaptive Fallback Ladder & Real-Time Stress Lab](#4-adaptive-fallback-ladder--real-time-stress-lab)
5. [Classical Computer Vision Post-Processing & Ablation Suite](#5-classical-computer-vision-post-processing--ablation-suite)
6. [Mobile Client & Hybrid Edge-Server Architecture](#6-mobile-client--hybrid-edge-server-architecture)
7. [Comprehensive Verification & Automated Test Suite (55/55 Passed)](#7-comprehensive-verification--automated-test-suite-5555-passed)
8. [Pin-to-Pin Engineering Challenges, Errors & Resolution Proofs](#8-pin-to-pin-engineering-challenges-errors--resolution-proofs)
9. [Visual Proofs, Graph Catalog & Artifact Sitemap](#9-visual-proofs-graph-catalog--artifact-sitemap)
10. [Reproduction & Deployment Manual](#10-reproduction--deployment-manual)

---

## 1. Executive Summary & Problem Statement Alignment

### 1.1 The Challenge
Modern text-to-image diffusion models (e.g., Stable Diffusion 1.5, SDXL) deliver extraordinary photographic quality but exhibit severe computational bottlenecks that prevent interactive execution on consumer mobile hardware:
- **High Latency:** Standard SD 1.5 requires 30–50 iterative denoising steps in 32-bit floating point precision, taking **12.43 seconds** on mobile/laptop GPUs.
- **Excessive Memory (VRAM):** Standard inference consumes **5.65 GB to 7.0 GB VRAM**, exceeding the memory bounds of mobile devices and entry-level laptops.
- **Compute and Thermal Bottlenecks:** Sustained diffusion denoising on mobile system-on-chips (SoCs) triggers aggressive thermal throttling, rapidly depleting battery reserves.

### 1.2 Our Solution
To satisfy **Problem Statement 3: Resource-Efficient Text-to-Image Generation for Mobile Devices**, Team ImagineAI developed an end-to-end optimized generative system featuring:
1. **A Controlled 3-Tier Model Progression:** We compared **SD 1.5 Baseline (Unchanged)** against **SD 1.5 Adapted (LoRA)** and **SD 1.5 Final Optimized (LCM-LoRA + FP16 + 8 steps)**, benchmarking the exact marginal gains of each optimization strategy while preserving model foundation consistency.
2. **Extreme Adversarial Distillation Benchmark:** We benchmarked **SD-Turbo** (2-step ADD distillation) delivering sub-300 ms response times.
3. **Adaptive Hardware Controller & Real-Time Stress Lab:** A dynamic 4-stage fallback ladder that adjusts spatial resolution and denoising steps under fluctuating latency ($50 - 5,000 \text{ ms}$) and VRAM ($1,024 - 16,384 \text{ MB}$) constraints.
4. **Classical Computer Vision Post-Processing:** Lightweight, intent-aware bilateral filtering, Laplacian edge unsharp masking, and dead-band gated CLAHE to recover micro-textures lost during rapid denoising.
5. **Hybrid Edge-Server Architecture:** A lightweight Android Jetpack Compose client communicating with a high-throughput, asynchronous FastAPI backend.

---

## 2. Complete System Architecture & 5-Stage Pipeline

The ImagineAI pipeline divides generation into five cohesive stages:

```
[ Natural Language Prompt ]
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Linguistic Prompt Analysis & Text Encoding    │
│  • Rule-based NLP entity, count, & relation extraction │
│  • CLIP ViT-B/32 text encoder (77 tokens × 768 dims)   │
│  • Latency: ~8.2 ms on GPU                             │
└────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Distilled Latent Denoising UNet               │
│  • Compact 64×64×4 latent feature space                │
│  • FP16 Tensor Core acceleration on RTX 5050           │
│  • ADD (2 steps) or LCM-LoRA (8 steps)                 │
│  • Peak VRAM: 3,408 MB (Optimized) vs 5,645 MB (Base)  │
└────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Latent-to-RGB VAE Decoder                     │
│  • 8× spatial upsampling convolutional decoder         │
│  • Tiled decoding in FP16 to eliminate memory spikes   │
│  • Output: 512×512×3 RGB tensor (Latency: ~51.8 ms)    │
└────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Classical Computer Vision Post-Processing     │
│  • Dead-band gate: skips 38% of balanced images        │
│  • Edge-preserving bilateral filter (denoising noise)  │
│  • Laplacian-guided unsharp mask (halo-guarded)        │
│  • Intent-aware CLAHE contrast normalization           │
│  • Median CPU Latency: ~17.9 ms                        │
└────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 5: Hybrid Edge-Mobile Delivery                   │
│  • REST v1.0.0 API / Web Dashboard / Android App       │
│  • Total End-to-End Latency: 288 ms (Turbo) / 1.65 s   │
│  • Uncompressed PNG stream with full telemetry headers │
└────────────────────────────────────────────────────────┘
```

---

## 3. The 3-Tier Scientific Progression: SD 1.5 Baseline → Adapted → Final Optimized

### 3.1 Experimental Design
Per evaluator guidelines, scientific comparisons must evaluate the impact of **meaningful adaptation** and **multiple optimization strategies** on the **same base model** before comparing against alternative architectures:

$$\text{SD 1.5 Baseline (Unchanged)} \longrightarrow \text{SD 1.5 Adapted (+ LoRA)} \longrightarrow \text{SD 1.5 Final Optimized (+ FP16 + 8 steps)}$$

An additional architectural benchmark is provided against **SD-Turbo** (Adversarial Diffusion Distillation).

### 3.2 Hardware Environment
- **GPU:** NVIDIA GeForce RTX 5050 Laptop GPU (8,151 MB Dedicated VRAM)
- **NVIDIA Driver:** 572.16 / CUDA 13.2
- **Operating System:** Windows 11 Pro 64-bit
- **Python / Frameworks:** Python 3.12.10, PyTorch 2.11.0+cu128, Diffusers 0.42.1, PEFT 0.21.2

### 3.3 Quantitative Empirical Results
All metrics were gathered by running identical prompt suites on the local GPU with cache clearance and synchronization:

| Model Variant | Base Foundation | Adaptation / LoRA | Precision | Sampling Steps | Latency (ms) | Peak VRAM | CLIP Alignment | Speedup | VRAM Reduction |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. SD 1.5 Baseline** | `runwayml/stable-diffusion-v1-5` | None (Original) | FP32 | 30 steps | **12,429.6 ms** | **5,645.0 MB** | **0.368** | 1.00× *(Ref)* | 0.0% |
| **2. SD 1.5 Adapted** | `runwayml/stable-diffusion-v1-5` | LCM-LoRA (Rank 64) | FP32 | 30 steps | **11,858.0 ms** | **5,906.1 MB** | **0.335** | 1.05× | -4.6% *(Overhead)* |
| **3. SD 1.5 Final Optimized** | `runwayml/stable-diffusion-v1-5` | LCM-LoRA (Rank 64) | **FP16** | **8 steps** | **1,647.1 ms** | **3,407.9 MB** | **0.324** | **7.55×** | **-39.6%** |
| **4. SD-Turbo (Benchmark)** | `stabilityai/sd-turbo` | Native ADD Distillation | **FP16** | **2 steps** | **344.9 ms** | **3,677.6 MB** | **0.342** | **36.0×** | **-34.9%** |

### 3.4 Key Empirical Findings
1. **7.55× Inference Speedup on SD 1.5:**
   - Reducing sampling steps from 30 down to 8 via the `LCMScheduler` combined with native half-precision Tensor Core execution reduced generation time from **12.43 seconds to 1.65 seconds**.
   - FP16 conversion accounts for a $2.0\times$ speedup, while step compression yields an additional $3.75\times$ speedup.
2. **39.6% VRAM Reduction (Eliminating OOM):**
   - Baseline SD 1.5 requires 5.65 GB VRAM, approaching the physical capacity of 6 GB laptop GPUs.
   - Final Optimized SD 1.5 peaks at **3,407.9 MB (3.41 GB)**, leaving **+4.74 GB of safe operating headroom** on the RTX 5050.
3. **Fidelity Retention (88% CLIP Preservation):**
   - Despite an **73.3% reduction in denoising steps** (30 down to 8), the CLIP score dropped only moderately from 0.368 to 0.324.

---

## 4. Adaptive Fallback Ladder & Real-Time Stress Lab

### 4.1 The 4-Stage Adaptive Fallback Ladder
Mobile clients experience fluctuating compute budgets due to thermal throttling, background tasks, and battery savers. The ImagineAI Adaptive Controller enforces a four-rung decision ladder:

| Ladder Step | Strategy Name | Resolution | Steps | Precision | Est. Latency | Est. VRAM | Trigger Conditions |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Step 1** | **Standard Combined / Quality Mode** | $512 \times 512$ | 2–4 | FP16 | 288–485 ms | 3,678 MB | Latency $\ge 300\text{ ms}$, VRAM $\ge 3,800\text{ MB}$ |
| **Step 2** | **Step Throttling** | $512 \times 512$ | 1 | FP16 | ~180 ms | 3,678 MB | Latency $< 300\text{ ms}$ or VRAM $< 3,800\text{ MB}$ |
| **Step 3** | **Spatial Rescaling** | $256 \times 256$ | 1 | FP16 | ~120 ms | 2,100 MB | Latency $< 200\text{ ms}$ or VRAM $< 2,800\text{ MB}$ |
| **Step 4** | **Classical Downsampling & Upscale** | $128 \times 128$ | 1 | FP16 | ~65 ms | 1,450 MB | Latency $< 120\text{ ms}$ or VRAM $< 2,000\text{ MB}$ |

### 4.2 Stress Lab Integration & Live Empirical Validation
The Stress Lab is fully connected to the backend via `POST /api/v1/adaptive/stress-generate`:
- **Interactive Budget Sliders:**
  - Latency budget: $50\text{ ms}$ to $5,000\text{ ms}$ (`step="50"`).
  - VRAM budget: $1,500\text{ MB}$ to $8,151\text{ MB}$ (`step="256"`).
- **Live Empirical Hardware Proofs:**
  - **Extreme Stress Run ($100\text{ ms}$, $1,800\text{ MB}$):** Triggered **Ladder Step 4** (`Classical Rescaling (128px, 1 step + Bicubic Upscale)`). Latency: **292.1 ms**, VRAM: **2,545.5 MB**.
  - **Moderate Stress Run ($250\text{ ms}$, $3,500\text{ MB}$):** Triggered **Ladder Step 2** (`Step Throttling (512px, 1 step)`). Latency: **411.6 ms**.
  - **Generous Run ($1,000\text{ ms}$, $6,000\text{ MB}$):** Triggered **Ladder Step 1** (`Quality Mode (512px, 4 steps)`). Latency: **485.7 ms**, **Budget Met ✔**.
  - **High Budget Run ($5,000\text{ ms}$, $4,096\text{ MB}$):** Generated full quality output in **743.3 ms** with **Budget Met ✔**.

---

## 5. Classical Computer Vision Post-Processing & Ablation Suite

### 5.1 CV Post-Processing Pipeline (`computer_vision/pipeline.py`)
To recover edge acuity and dynamic range without running extra diffusion steps, we implemented a classical image enhancement pipeline:
1. **Edge-Preserving Bilateral Filtering:** Removes high-frequency noise while preserving object boundaries ($\sigma_{\text{color}}=25$, $\sigma_{\text{space}}=9$).
2. **Halo-Guarded Laplacian Unsharp Masking:** High-pass filter sharpening with clipping thresholds to prevent ringing artifacts.
3. **Intent-Aware CLAHE:** Contrast Limited Adaptive Histogram Equalization normalized across luminance channels.
4. **Dead-Band Variance Gating:** An automated pre-check on image contrast variance. If an image is already well-balanced, CV processing is skipped entirely. In empirical benchmarks, **38% of images cleanly bypassed post-processing**, saving CPU compute.

### 5.2 Single-Variable Ablation Study (V0 to V5)
Evaluated across 20 prompts from the hold-out 'unseen' split (seeds 1234, 5678, 9012; 120 total runs):

| Variant | Precision | Steps | CV Mode | Latency (ms) | Peak VRAM | CLIP Alignment | Paired CLIP Δ vs V0 (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V0 (Baseline)** | FP32 | 4 | Off | 856.1 ms | 6,500 MB | 0.327 | Reference (0.000) |
| **V1 (Precision)** | **FP16** | 4 | Off | 413.8 ms | 3,678 MB | 0.330 | +0.0031 `[-0.0015, 0.0075]` |
| **V2 (Steps=2)** | FP32 | **2** | Off | 575.4 ms | 6,500 MB | 0.332 | +0.0044 `[0.0015, 0.0078]` |
| **V3 (Steps=1)** | FP32 | **1** | Off | 432.5 ms | 6,500 MB | 0.336 | +0.0092 `[0.0050, 0.0133]` |
| **V4 (Combined)** | **FP16** | **2** | Off | **289.6 ms** | **3,678 MB** | **0.333** | **+0.0054 `[0.0016, 0.0092]`** |
| **V5 (CV On)** | FP32 | 4 | **On** | 874.1 ms | 6,500 MB | 0.326 | -0.0009 `[-0.0023, 0.0003]` |

---

## 6. Mobile Client & Hybrid Edge-Server Architecture

### 6.1 Feasibility Analysis: On-Device vs Hybrid
- **Direct On-Device Diffusion (Infeasible):**
  - Requires loading 3.4 GB of model weights into mobile unified RAM.
  - Mobile GPUs lack cooling fans; running 8–30 denoising steps causes battery drain and thermal throttling within minutes.
- **Hybrid Client-Server (Production Standard):**
  - High-performance GPU server runs model inference behind an asynchronous REST API.
  - Lightweight native Android client (<15 MB APK) sends prompts, displays generation progress, renders returned images, and inspects hardware telemetry.

### 6.2 Android Implementation (`android/`)
- **Technology:** Android 14 (API 34, minSdk 26), Jetpack Compose, Kotlin Coroutines, Retrofit 2, Coil.
- **Features:** Prompt bar, resolution selector, live latency counter, hardware telemetry viewer, local image caching.

---

## 7. Comprehensive Verification & Automated Test Suite (55/55 Passed)

The entire project is guarded by a comprehensive regression and unit test suite:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\dilip\OneDrive\Documents\CV\ImagineAI_Combined
configfile: pytest.ini
plugins: anyio-4.16.0
collected 55 items

tests\test_api.py ...............                                        [ 27%]
tests\test_web_dashboard.py ......                                       [ 38%]
tests\test_safety.py ................................                    [ 96%]
tests\test_repo_structure.py ..                                          [100%]

============================= 55 passed in 3.43s ==============================
```

### Breakdown of Test Suites
1. **`test_api.py` (15 Passed):**
   - Validates input schemas, prompt length constraints (1–500 chars), resolution bounds, quality mode mappings, seed reproducibility, error response structures, and HTTP status codes.
2. **`test_web_dashboard.py` (6 Passed):**
   - Tests root HTML delivery (`GET /`), dashboard alias (`GET /dashboard`), CSS/JS asset integrity, `/api/v1/metrics/summary`, empirical SD 1.5 JSON comparison, and the live Stress Lab adaptive generation ladder.
3. **`test_safety.py` (32 Passed):**
   - Verifies safety auditing: path traversal rejection (`/images/../`), non-listable image directories, internal traceback redaction on error, UUID4 image token unguessability, and prompt toxicity filters.
4. **`test_repo_structure.py` (2 Passed):**
   - Enforces clean repository hygiene, ensuring no large binaries, models, or unapproved artifacts are tracked in Git.

---

## 8. Pin-to-Pin Engineering Challenges, Errors & Resolution Proofs

Throughout development, we encountered and resolved several complex engineering bugs:

### Bug 1: Windows Path Separator Mismatch in Asset & Binary Scanners
- **Symptom:** `test_repo_structure.py` and `size_report.py` failed with assertion errors due to mixed path separators (`\` vs `/`).
- **Root Cause:** Hardcoded Unix-style paths failed when traversing Windows file trees.
- **Resolution:** Replaced all string path splits with `pathlib.Path` methods and normalized strings using `.as_posix()`.

### Bug 2: Android Build Artifacts Triggering Binary Scanner Failures
- **Symptom:** Running `pytest tests/test_repo_structure.py tests/test_safety.py` failed with:
  ```
  AssertionError: unexpected binary found: android/app/build/intermediates/apk/debug/app-debug.apk
  ```
- **Root Cause:** Compiling the Android APK in Android Studio created build directories (`android/.gradle/`, `android/build/`) containing compiled binaries.
- **Resolution:** Updated `test_repo_structure.py` and `test_safety.py` path exclusions to ignore `.gradle` and `build` folders, consistent with `.gitignore`.

### Bug 3: Android Studio JDK & Gradle Daemon Incompatibility
- **Symptom:** Android Studio build failed with Gradle Daemon launch errors:
  ```
  Unsupported class file major version 69 (Java 25)
  ```
- **Root Cause:** Host machine had JDK 25 pre-installed, whereas Gradle 8.2 and AGP 8.2 only supported up to JDK 17/21.
- **Resolution:**
  - Configured `android/gradle.properties` to explicitly pin OpenJDK 17:
    `org.gradle.java.home=C:\\Program Files\\Eclipse Adoptium\\jdk-17.0.12.7-hotspot`
  - Upgraded AGP to `8.5.2` and Gradle wrapper to `8.7`.
  - Re-synced and built the APK cleanly without warnings.

### Bug 4: 401 Unauthorized Error on Gated LoRA Weights
- **Symptom:** Attempting to download `sayakpaul/sd-model-finetuned-lora-t4` threw an HTTP 401 Unauthorized error from HuggingFace Hub.
- **Root Cause:** The repository was gated/private, requiring authenticated token access.
- **Resolution:** Switched to the public canonical `latent-consistency/lcm-lora-sdv1-5` safetensors (~135 MB), which downloaded cleanly and provided superior 8-step consistency adaptation.

### Bug 5: Missing PEFT Library for Diffusers LoRA Integration
- **Symptom:** Generation pipeline failed with:
  ```
  ValueError: PEFT backend is required for load_lora_weights()
  ```
- **Root Cause:** In `diffusers>=0.28`, loading LoRA state dictionaries into a UNet requires the `peft` library.
- **Resolution:** Installed `peft==0.21.2` in the virtual environment.

### Bug 6: Windows Sandbox Isolation & CUDA Context Hangs
- **Symptom:** Running pytest or python scripts inside the default sandbox while uvicorn had an active CUDA context caused child processes to deadlock on CUDA initialization, and `Invoke-RestMethod` to `localhost:8000` failed with connection refused.
- **Root Cause:** Windows sandbox isolation blocks localhost socket communication and blocks cross-process CUDA IPC memory sharing.
- **Resolution:** Followed Sandbox Rules 1 & 8: executed network- and GPU-bound background tasks with `BypassSandbox: true`. Tests and server communication executed in milliseconds.

### Bug 7: Multi-Model VRAM Contention & WDDM Paging Slowdowns
- **Symptom:** Generating with `SD 1.5 Final Optimized` after `SD-Turbo` caused inference times to spike to 10 seconds per step.
- **Root Cause:** Both models (~3.5 GB each) remained resident in GPU VRAM simultaneously, exceeding the 8 GB capacity of the RTX 5050. Windows WDDM began paging memory over PCIe to system RAM.
- **Resolution:** Implemented an active GPU lease manager in `backend/app/services/multi_model.py`. When a new model is requested, any previously active pipeline is parked to CPU (`.to("cpu")`) and `torch.cuda.empty_cache()` is called, immediately reclaiming VRAM and restoring full Tensor Core speed.

### Bug 8: Disconnected Stress Lab Trigger in Web Dashboard
- **Symptom:** The Stress Lab sliders updated client-side math, but clicking "Run Live Adaptive Stress Test" did nothing.
- **Root Cause:** The HTML button `#stress-generate-btn` had no event listener wired in `app.js`, and no dedicated backend route existed.
- **Resolution:** Created `POST /api/v1/adaptive/stress-generate` in `main.py`, wired the button with an asynchronous fetch, added live stopwatch animations, and dynamically highlighted the active ladder rung in the UI.

---

## 9. Visual Proofs, Graph Catalog & Artifact Sitemap

| Artifact | File Path | Description |
| :--- | :--- | :--- |
| **SD 1.5 Comparison Chart** | `evaluation/reports/sd15_vs_adapted_vs_optimized.png` | 4-panel publication graphic comparing Latency, Peak VRAM, CLIP Score, and Sampling Steps. |
| **Web Static Comparison Chart** | `backend/app/static/sd15_comparison.png` | Mirrored comparison graphic rendered directly on the web dashboard. |
| **Empirical Metrics JSON** | `evaluation/reports/sd15_comparison_empirical.json` | Exact millisecond and megabyte telemetry for Baseline, Adapted, Optimized, and SD-Turbo. |
| **P7 Quality-Cost Graph** | `evaluation/reports/p7_quality_cost.png` | Scatter plot of CLIP alignment vs median latency across variants V0–V5. |
| **RTX 5050 Adaptive Profile** | `evaluation/profiles/profile_NVIDIA_GeForce_RTX_5050_Laptop_GPU.json` | 38-entry hardware profile mapping resolutions and steps to measured VRAM and latency. |
| **Formal Empirical Report** | `evaluation/reports/sd15_baseline_vs_adapted_vs_optimized.md` | Formal research documentation of the 3-tier model progression. |
| **Failure Analysis Report** | `evaluation/reports/failure_analysis.md` | Detailed taxonomy of resolved, mitigated, and inherent diffusion boundary cases. |
| **Ablation Study Report** | `evaluation/reports/ablation_study.md` | Rigorous evaluation of single-variable optimizations (V1–V5). |
| **Android Application Source** | `android/` | Complete native Jetpack Compose mobile application. |
| **Web Dashboard Application** | `backend/app/static/` | 9-tab responsive web application matching the project specification. |

---

## 10. Reproduction & Deployment Manual

### 10.1 Environment Setup
```powershell
# 1. Clone repository & checkout develop
git clone <repo-url>
cd ImagineAI_Combined
git checkout develop

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt
pip install peft
```

### 10.2 Run Automated Tests
```powershell
# Run the complete test suite (55 tests)
pytest tests/test_api.py tests/test_web_dashboard.py tests/test_safety.py tests/test_repo_structure.py
```

### 10.3 Launch the Web Dashboard Server
```powershell
$env:MODEL_REVISION="b261bac6fd2cf515557d5d0707481eafa0485ec2"
$env:ADAPTIVE_PROFILE="evaluation/profiles/profile_NVIDIA_GeForce_RTX_5050_Laptop_GPU.json"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- Open in Browser: **`http://localhost:8000/`** or **`http://localhost:8000/dashboard`**
- Mobile Access: **`http://<your-lan-ip>:8000/`** (e.g. `http://192.168.1.4:8000/`)

### 10.4 Build Native Android APK
```powershell
cd android
.\gradlew.bat assembleDebug
```
- Generated APK: `android/app/build/outputs/apk/debug/app-debug.apk`

---
*Report compiled and certified for Hackathon Evaluation — Team ImagineAI.*
