# 12. Master Project Checklist

## Foundation
- [ ] Repository created and protected.
- [ ] `main` and `develop` branches established.
- [ ] OS and toolchain versions recorded.
- [ ] API contract agreed.
- [ ] Android skeleton builds.
- [ ] FastAPI skeleton starts.
- [ ] Secrets and generated model/data files excluded from Git.

## Baseline
- [ ] One lightweight diffusion pipeline loads.
- [ ] API generates an actual image.
- [ ] Android sends prompt and displays image.
- [ ] Baseline latency and memory recorded.

## Prompt and adaptation
- [ ] Complex prompt suite created.
- [ ] Prompt parser implemented and tested.
- [ ] Dataset license recorded.
- [ ] Train/validation split created.
- [ ] Meaningful adaptation trained.
- [ ] Base/adapted comparison completed.

## Optimization
- [ ] Reduced precision implemented and benchmarked.
- [ ] Reduced steps implemented and benchmarked.
- [ ] Additional strategy evaluated if feasible.
- [ ] Baseline/optimized quality-cost comparison completed.

## Classical CV
- [ ] Resize/resolution optimization.
- [ ] Colour correction/enhancement.
- [ ] Edge-aware processing.
- [ ] Image quality assessment.
- [ ] Artifact detection/correction.
- [ ] Per-stage tests and ablation.

## Adaptive controller
- [ ] Resource monitor.
- [ ] Benchmark profiles.
- [ ] Quick/Balanced/Best mapping.
- [ ] Fallback sequence.
- [ ] Constrained-resource tests.
- [ ] UI explanation of decision.

## Evaluation
- [ ] CLIP protocol.
- [ ] FID or justified alternative.
- [ ] Latency.
- [ ] Peak memory.
- [ ] Model size.
- [ ] Ablation.
- [ ] Failure-case analysis.
- [ ] Unseen prompt evaluation.

## Mobile and final
- [ ] Deployment mode accurately labelled.
- [ ] Physical Android device tested.
- [ ] Full-pipeline mobile feasibility assessed.
- [ ] Hosted URL tested.
- [ ] Clean clone/setup tested.
- [ ] Architecture/design docs complete.
- [ ] `eval_P3_TeamID.md` first line contains all USNs.
- [ ] Demo rehearsed.
- [ ] Both members prepared for viva.
