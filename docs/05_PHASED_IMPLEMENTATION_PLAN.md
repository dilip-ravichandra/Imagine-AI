# 5. Phased Implementation Plan

Each phase has entry conditions, tasks, deliverables, and a gate. Do not begin broad parallel implementation before the previous integration gate passes.

## Phase 0 — Project foundation
**Tasks**
- Create one GitHub repository.
- Create `main` and `develop`.
- Add this master pack and issue/PR templates.
- Agree Python, Android Gradle, JDK, CUDA/PyTorch and API versions after checking the actual OS.
- Create Python virtual environment and Android Studio project.
- Create `.env.example`, `.gitignore`, dependency lock strategy.
- Agree API contract before Android integration.

**Gate:** clean clone can build the Android skeleton and import the FastAPI skeleton. Both developers can run their assigned setup.

## Phase 1 — Baseline end-to-end generation
**Person 1:** FastAPI health endpoint, model loader, one selected lightweight diffusion pipeline, generation endpoint, image output storage.
**Person 2:** Compose prompt screen, quality-mode selector, progress state, result image screen, Retrofit client.

**Gate:** Android prompt reaches backend and an actual generated image returns and displays. Record baseline latency and memory. If the GPU cannot support the selected pipeline, adjust candidate/resolution rather than hiding the failure.

## Phase 2 — Prompt intelligence and reproducibility
- Add prompt validation and structured prompt analysis.
- Support object/attribute/relation/scene extraction.
- Add seed and generation metadata.
- Build a fixed prompt evaluation suite and unseen prompt test protocol.

**Gate:** fixed prompts produce reproducible configurations; complex prompts are logged and evaluated.

## Phase 3 — Pretrained model adaptation
- Select a licensed dataset and document its terms.
- Create train/validation split and preprocessing.
- Train compatible LoRA or another meaningful adaptation.
- Compare base and adapted models on held-out prompts.

**Gate:** adapter and training metadata are reproducible; comparison includes actual results and limitations.

## Phase 4 — Inference optimization
- Establish baseline configuration.
- Implement reduced precision if supported.
- Implement reduced sampling steps using compatible scheduler/model.
- Consider quantization, compact model alternative, or memory offload if time and compatibility allow.
- Keep one variable changed at a time for ablation.

**Gate:** at least two strategies have actual measured results and a quality-cost analysis.

## Phase 5 — Classical CV pipeline
Implement and test all five:
1. Resize/resolution optimization.
2. Colour correction/enhancement.
3. Edge-aware processing.
4. Image quality assessment.
5. Artifact detection/correction.

**Gate:** every stage has unit/integration tests and before/after examples. Include no-op or bypass behavior when processing would degrade the image.

## Phase 6 — Adaptive controller and fallback
- Collect benchmark profiles.
- Implement Quick/Balanced/Best Quality mapping.
- Add resource monitoring.
- Implement fallback sequence.
- Add simulated constrained-resource tests and actual OOM/error handling.

**Gate:** controller decision is deterministic for a given profile/input, explainable, logged, and tested.

## Phase 7 — Evaluation and ablation
- Run fixed prompt set with fixed seeds where possible.
- Measure CLIP similarity, appropriate distribution metric, latency, memory and model size.
- Report mean/median and variability over repeated runs.
- Compare baseline, adapted, and optimized variants.
- Analyze degradation and failure cases.

**Gate:** all metrics have methodology, environment, sample count, and actual data. No fabricated numbers.

## Phase 8 — Mobile feasibility and deployment
- Decide and label deployment as on-device, hybrid, or cloud.
- Attempt export/runtime only if full pipeline compatibility can be tested.
- Measure actual Android device storage, memory, latency, startup, thermal/sustained behavior where possible.
- Deploy backend and test from phone and laptop.
- Verify error/loading states and network loss.

**Gate:** deployment claims match evidence. If on-device generation is not feasible, clearly present hybrid architecture and document the mobile feasibility experiment and limitations.

## Phase 9 — Final packaging, documentation and demo
- Complete architecture diagram and design document.
- Complete `eval_P3_TeamID.md` with first line containing all USNs comma-separated.
- Complete ablation and failure analysis.
- Check licenses and secrets.
- Test clean setup from README.
- Test live URL from phone and laptop.
- Rehearse 3-minute demo using an unseen prompt.
- Both members explain the entire system at a high level and their own modules in depth.

**Final gate:** source, hosted URL, documentation, evidence, and demo are all checked.
