# HANDOFF_NEXT_CLAUDE.md
## Project
Imagine AI — P3 Resource-Efficient Text-to-Image Generation (SD-Turbo behind frozen API v1.0.0).
## Current phase
- **P3A Adaptation prep — PARTIAL** (code+tests; no training run). **P3B Adapter integration — PARTIAL** (code+tests+live-server checked; no real adapter exists). P2 COMPLETE. **P1A real SD-Turbo run still NOT RUN: this is now the critical path for everything.**
- Date: 2026-11-07
## Completed this session (P3B)
- `ai_engine/training/adapter.py`: shared validation + **approval gate** (rule: at each of 1 and 4 steps, >= 40 rated blind pairs and >= 70% adapted better-or-tie; zero adapted-only failures; human artefact confirmation). Approval is bound to the adapter's SHA-256 and re-evaluated against the current rule at load.
- `ai_engine/training/approve.py`: filled blind-review sheet -> `approval.json` (exit 0/1/2). `compare.py` now writes `compare_meta.json` so a review can't be applied to a different adapter.
- Backend: optional `ADAPTER_PATH`; `SDTurboEngine` loads an adapter only if approved AND `MODEL_REVISION` equals its base revision; any problem => base model (never a crash); failed load => clean base pipeline rebuilt; real OOM is reported, not hidden; pre-load verdict logged at startup.
- API: **additive** `GET /api/v1/model`; `generation.model_revision` becomes `<rev>+lora-<sha12>` only when the adapter made the image. Existing schemas unchanged (test asserts exact key sets). Android needs no change.
- Docs: `docs/ADAPTATION.md` (P3A+P3B), `docs/API_CONTRACT_v1.md` (P3B section), blank `docs/ADAPTATION_RESULT.md`.
## Tests actually executed
`python -m pytest -q`: **347 passed, 1 skipped** (244 P2 + 56 P3A + 47 P3B). 16 deliberate mutations of P3B code each caught. Live `uvicorn` under 5 adapter configs: OK, 0 tracebacks, no path leakage. **NOT RUN:** real `load_lora_weights` on a trained adapter, GPU memory with adapter, any training, Windows, Android.
## Known issues / risks
Fake torch/diffusers only prove OUR call logic; whether the real library accepts the upstream trainer's LoRA file is unproven until a real run. Approval is an integrity check, not security. Upstream trainer's scheduler load (`DDPMScheduler` on SD-Turbo's config) never exercised. LoRA served unfused (matches what was reviewed; fusing = P4 experiment needing its own comparison). Adapter likely won't help and may hurt: that is an acceptable, reportable result. COCO licences mixed: decide before redistributing an adapter.
## HUMAN STEPS (in priority order for a deadline day)
1. **P1A smoke test on the RTX 5050**: generate one image, pin `MODEL_REVISION` (40-char hash), note scheduler, read SD-Turbo licence. Nothing below works without this.
2. Start P4 (below). Its numbers are worth more than an adapter.
3. Optional, only if time: P3A smoke run -> small run -> `compare` -> blind review -> `approve`. If skipped or rejected, fill `docs/ADAPTATION_RESULT.md` honestly and keep base.
## Exact next task — **P4 Optimization (Person 1)**, independent of the adapter
**Goal:** the problem statement requires >= 2 optimization strategies, baseline-vs-optimized comparison, quality-degradation study, and resource numbers. Produce measured evidence, not claims.
**Profiles (change ONE variable at a time, fixed 512px, same prompts+seeds):**
`baseline_fp32_4step` | `fp16_4step` (precision only) | `fp32_1step` (steps only) | `fp16_1step` (combined) | `fp16_2step`. Optional extras only if time: attention/VAE slicing, tiny VAE, `torch.compile`, fused LoRA.
**Protocol:** run each profile in its **own process** (clean memory). Warm-up excluded. Use the 30 dev prompts to debug, **freeze settings, then run the 100 test prompts once**. Several seeds. Keep failures in the record.
**Record per profile:** warm latency median/p95 (excl. model load); cold load time; peak CUDA allocated *and* reserved; process RSS; model size on disk and loaded tensor bytes (fp32 vs fp16 variant); CLIP image-text cosine (offline, CPU) + small blind human sample for degradation; prompt-adherence notes for multi-object/attribute/spatial prompts.
**Outputs:** `evaluation/results/p4_*/` raw JSON + summary CSV; quality-vs-cost table; step-count degradation curve; written limitations. Feeds P6 (adaptive controller picks an *accepted* profile by free GPU memory / latency budget; one OOM fallback, already scaffolded in the first consolidated zip's `controller.py` for reference) and P7 (`eval_P3_<TeamID>.md`, USNs on the first line).
**Honesty rules:** warm vs cold labelled; "mobile" = server-side inference unless a phone really runs it (label "hybrid/cloud"); give a computed phone-budget estimate (weights bytes, fp16 activation estimate), clearly marked as an estimate; FID only if an adequate real-image reference set exists, else say so.
## After P4
P5 classical CV (resize/colour/edge-aware/IQA/artifact checks; the earlier consolidated zip has a working reference `computer_vision/pipeline.py` to adapt, thresholds untuned), P6 adaptive controller, P7 metrics harness + ablation + failure report, P8 deploy (GPU host; public URL must answer within ~10 s, so preload the model), P9 demo.
## Must NOT redo
Scaffold, API schema, engine/service, prompt parser/suite (don't tune on hold-out), data builder + leakage guards, vendored trainer (never edit), approval gate (don't loosen the rule after seeing results).
## Missing input
Smoke-test output + pinned revision; torch/CUDA versions; GPU memory actually free; repo URL; phone model; licence decision on COCO-trained adapters.
