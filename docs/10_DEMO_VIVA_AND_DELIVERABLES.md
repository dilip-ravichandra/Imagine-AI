# 10. Deliverables, Demo, and Viva

## 10.1 Required project deliverables
- Live hosted application URL.
- GitHub repository with complete source code.
- Architecture diagram.
- Design document.
- `eval_P3_TeamID.md`, with first line containing all team USNs comma-separated.
- Ablation study.
- Failure-case analysis.
- Quantitative evaluation evidence.
- Reproducible setup/run instructions.
- Dataset and model license notes.

## 10.2 Suggested 3-minute demo
1. **0:00–0:25 — Problem and product:** introduce Imagine AI and resource constraints.
2. **0:25–1:05 — Live prompt:** enter an unseen complex prompt with multiple objects and spatial relations.
3. **1:05–1:40 — Generation:** show actual selected model, resolution, precision, steps, and resource decision.
4. **1:40–2:10 — CV and quality:** show quality indicators and a post-processing comparison.
5. **2:10–2:40 — Evidence:** show baseline vs optimized latency/memory/alignment.
6. **2:40–3:00 — Mobile and limitations:** show phone UI and honestly explain whether inference is on-device, hybrid, or cloud.

Rehearse a backup recording or locally cached output in case network/model loading fails, but distinguish backup evidence from the live generation.

## 10.3 Viva preparation
Both members should be able to explain:
- Diffusion process and conditional text embeddings.
- Why the selected lightweight model was chosen.
- What was adapted and how.
- The two or more optimization strategies and their trade-offs.
- Each of the five CV modules.
- Resource controller inputs, decisions, and fallback.
- CLIP versus FID and their limitations.
- Latency/memory measurement methods.
- Why deployment is on-device, hybrid, or cloud.
- One real failure case and what remains unresolved.

## 10.4 `eval_P3_TeamID.md` starter
The first line must be replaced with all USNs separated by commas. Then include:
- Team/project identification.
- Hardware/software environment.
- Model and revision.
- Dataset and license.
- Prompt set and seeds.
- Baseline and optimized configurations.
- CLIP/FID or justified alternative.
- Latency/memory/model size.
- Ablation table.
- Failure analysis.
- Mobile deployment result.
- Limitations and reproducibility commands.
