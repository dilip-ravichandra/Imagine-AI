# Design document — Imagine AI (P3 resource-efficient text-to-image)

Every statement below is about **design and code**. No latency, memory, CLIP, FID or size figure appears because none has been measured.

## 1. Problem and constraints
Generate images from complex prompts under limited resources (target dev machine: RTX 5050 Laptop ~8 GB VRAM, 24 GB RAM; phone client). See `docs/01_PROJECT_CHARTER.md`, `docs/02_REQUIREMENTS_TRACEABILITY.md`.

## 2. Model choice (`docs/11_RISKS_AND_DECISIONS.md`)
SD-Turbo (`stabilityai/sd-turbo`) as the first lightweight candidate, 1-4 step sampling. **Not benchmarked against alternatives** (BK-SDM-Tiny, SD1.5+LCM-LoRA were not tried). Revision unpinned in code defaults; the benchmark CLIs refuse to run unpinned. Licence: TODO(team) read the model card before any redistribution/hosting.

## 3. Prompt intelligence (P2)
Deterministic lexicon/rule parser (`ai_engine/prompt/`), output schema `docs/prompt_analysis_schema_v1.json`, endpoint `/api/v1/prompt/analysis`. Rationale: reproducible, no extra model memory. Limit: hold-out result was 12/20 on the first run, frozen; those 20 prompts are now seen, so the demo needs new prompts (`docs/PROMPT_PARSER.md`).

## 4. Adaptation (P3A/P3B)
LoRA data prep, training launcher and compare tooling exist, plus a loader gated on an `approval.json` (`docs/ADAPTATION.md`). **No adapter was trained or approved; DL-02 is open.** The gate is an accident guard, not a security boundary.

## 5. Optimization (P4)
Configurable precision, attention/VAE slicing, CPU offload, weight variant, step count; 8-experiment grid (B0, E1-E6, C1) and stats/report code (`docs/P4_OPTIMIZATION.md`). Trade-offs are documented qualitatively; **quality-cost numbers do not exist**.

## 6. Classical CV (P5A/P5B) — the five modules
1. Resize (`computer_vision/resize`), 2. colour/enhancement, 3. edge-aware smoothing/sharpening, 4. quality assessment (`quality/metrics.py`), 5. artifact detection + guarded correction (`artifacts/`). Thresholds are provisional, set on synthetic images (`docs/P5B_CV.md` section 4). Conservative sharpening did not repair blur on the synthetic set. Not evaluated on real SD-Turbo output.

## 7. Resource-adaptive controller (P6)
Deterministic profile-driven controller with quick/balanced/best, headroom check on measured GPU peak, fallback ladder (resolution -> precision -> steps -> model -> consented remote), runtime OOM fallback, JSONL decision log, human-readable explanation (`docs/P6_ADAPTIVE.md`). Because the engine cannot change precision/model without a reload, only resolution/steps vary at run time. **No measured profile exists**; the synthetic fixture is refused unless `ADAPTIVE_ALLOW_SYNTHETIC=true`. Defaults are uncalibrated.

## 8. Evaluation design (P7A/P7B)
Variants V0-V7, prompt-cluster bootstrap CIs, FID gate that refuses small samples, mechanical report, human-review sheet (`docs/P7A_EVAL.md`). V6/V7 blocked. Synthetic output can never satisfy the gate.

## 9. Mobile and deployment (P8)
Not delivered. `android/` is a Compose skeleton (`MainActivity.kt`, 14 lines, no Retrofit, no INTERNET permission). Honest labels per `docs/09_MOBILE_DEPLOYMENT.md`: on-device = full path on phone; hybrid = phone + laptop server; cloud = hosted. Current best case after P8 would be **hybrid**. A full-pipeline on-device feasibility experiment was not run.

## 10. Known limitations (carry into the viva)
No real results; FID not computable (no reference set / Inception extractor); stage-level latency not exposed by the engine; default sample is small so CIs will be wide; CV thresholds provisional; API contract unsigned; Windows/Docker/Android never built.
