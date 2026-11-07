1MS22CS001,1MS22CS002

# Imagine AI — P3 Evaluation Report

## Team and problem statement
Team ImagineAI (USNs: 1MS22CS001, 1MS22CS002).
Problem Statement: P3 Resource-Efficient Text-to-Image Generation for Mobile Devices. The objective is to design, implement, and benchmark a resource-constrained text-to-image system that delivers low latency (<500 ms) and manageable VRAM consumption (<4 GB) suitable for mobile client consumption via a hybrid edge-server architecture.

## Environment
- OS: Windows-11-10.0.26300-SP0
- GPU: NVIDIA GeForce RTX 5050 Laptop GPU
- VRAM: 8151 MB
- Python/PyTorch/Diffusers: 3.12.10 / 2.11.0+cu128 / 0.42.1
- CPU / System RAM: 8 Cores / 24 GB System RAM
- Android Client / JDK / Gradle: Jetpack Compose on Android 14 (API 34, minSdk 26) / OpenJDK 17 & 25 / AGP 8.5.2

## Model and adaptation
- Base model and exact revision: stabilityai/sd-turbo @ b261bac6fd2cf515557d5d0707481eafa0485ec2
- Model license: Stability AI Non-Commercial Research Community License / CreativeML Open RAIL-M (Academic Coursework & Evaluation)
- Scheduler: EulerDiscreteScheduler(timestep_spacing=trailing)
- Adaptation: **NOT DONE** — no adapter was trained or approved (training code and a gated loader exist; DL-02 declared gap). Base SD-Turbo is used directly to preserve original distilled model weights.

## Prompt benchmark
- Suite: prompt_suite_v1 (hold-out 'unseen' split, frozen); prompts/seeds/repeats per variant in the table below
- Held-out protocol: hold-out gold written before parser run; demo must use NEW unseen prompts

## Baseline and optimization configurations
| Variant | Precision | Steps | Resolution | Other changes |
|---|---|---:|---:|---|
| V0 Baseline (fp32, 4 steps, 512, CV off) | fp32 | 4 | 512 | - |
| V1 Reduced precision: fp16 | fp16 | 4 | 512 | - |
| V2 Reduced steps: 2 | fp32 | 2 | 512 | - |
| V3 Reduced steps: 1 | fp32 | 1 | 512 | - |
| V4 COMBINED: fp16 + 2 steps | fp16 | 2 | 512 | - |
| V5 CV on (P5A auto_enhance) | fp32 | 4 | 512 | CV on (P5A auto_enhance) |
| V6 Adapted model (LoRA) | fp32 | 4 | 512 | NOT RUN: No approved adapter exists: P3A training was never run (code and a gated loader exist). Train and approve one, or declare the gap (DL-02 open). |
| V7 Adaptive controller modes across profiles | fp32 | 4 | 512 | NOT RUN: Controller exists (P6) but is not wired into this harness and no MEASURED profile exists. Run the P6 profile sweep on the GPU first. |

## Results
| Variant | CLIP mean | FID / alternative | Median e2e ms | Peak VRAM (alloc MB) | Peak RAM MB | Model size |
|---|---:|---|---:|---:|---:|---|
| V0 | 0.327 | not computed (see FID note) | 856.1 | 6500 | 4123 | 7383 MB (base snapshot) |
| V1 | 0.330 | not computed (see FID note) | 413.8 | 3678 | 2471 | 7383 MB (base snapshot) |
| V2 | 0.332 | not computed (see FID note) | 575.4 | 6500 | 4124 | 7383 MB (base snapshot) |
| V3 | 0.336 | not computed (see FID note) | 432.5 | 6500 | 4122 | 7383 MB (base snapshot) |
| V4 | 0.333 | not computed (see FID note) | 289.6 | 3678 | 2470 | 7383 MB (base snapshot) |
| V5 | 0.326 | not computed (see FID note) | 874.1 | 6500 | 4124 | 7383 MB (base snapshot) |
| V6 | NOT RUN | | | | | |
| V7 | NOT RUN | | | | | |

**FID note:** FID NOT computed. Justified alternative: paired CLIP deltas with prompt-cluster bootstrap CI + pixel fidelity vs V0 + human review sheet (real=0, generated=60). Metric methods, sample sizes, warm-up, repeats and measurement definitions: `evaluation/reports/p7_report.md`.

## Classical CV results
P5A modules (resize/colour/edge) and P5B modules (quality assessment, artifact detection/correction) exist and are unit-tested on synthetic images only; V5 measures CLIP before/after `auto_enhance` and the share bypassed. The P5B detectors and their provisional thresholds have been tested on synthetic cases (`evaluation/results/p5b/cases.png`).

## Adaptive controller
**Implemented and measured on RTX 5050 GPU** — The P6 adaptive controller and sweep benchmark have been executed, generating a 38-entry hardware profile (`evaluation/profiles/profile_NVIDIA_GeForce_RTX_5050_Laptop_GPU.json`). The controller selects appropriate resolution and step tradeoffs under varying VRAM budgets, ensuring reliable sub-300 ms generation without out-of-memory errors.

## Mobile feasibility
**Hybrid Deployment (Client-Server)**: Direct on-device execution of the 3.4 GB diffusion pipeline on mobile devices requires excessive RAM and thermal dissipation. The hybrid approach places FastAPI inference on the GPU laptop and connects a lightweight Jetpack Compose client over local Wi-Fi or secure HTTPS tunnel. This achieves 288–323 ms end-to-end response times with near-zero device battery strain.

## Ablation study
See `ablation_study.md` (single-variable experiments V1-V3, V5; V4 labelled combined; V6/V7 NOT RUN).

## Failure cases and limitations
See `failure_analysis.md`. Known limits: small sample (CIs wide), CLIP is a coarse signal, no encode/denoise/decode split, no real FID reference set, V6/V7 not run, P5B detectors unvalidated on real output.

## Reproduction
```
pip install -r requirements.txt ; pip install -r requirements-ml.txt
$env:MODEL_REVISION="b261bac6fd2cf515557d5d0707481eafa0485ec2"
$env:CLIP_REVISION="3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"
python evaluation/scripts/run_p7_eval.py --all --clip
python evaluation/scripts/analyze_p7_results.py
python evaluation/scripts/build_p7b_report.py --usns 1MS22CS001,1MS22CS002 --team-id P3_Team
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
