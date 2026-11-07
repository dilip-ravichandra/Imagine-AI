USN_1,USN_2
<!-- TODO(team): replace line 1 with ALL team USNs, comma-separated. Rename this file to eval_P3_<TeamID>.md. The generator `evaluation/scripts/build_p7b_report.py --usns ...` produces the results sections from real P7A data. -->

# Imagine AI — P3 Evaluation Report (DRAFT, no results)

## Team and problem statement
TODO(team): team id, members, exact problem statement ("P3 Resource-Efficient Text-to-Image Generation for Mobile Devices").

## Environment
TODO(team): OS, CPU, GPU (RTX 5050 Laptop ~8 GB per docs), RAM, Android device, Python/PyTorch/Diffusers/OpenCV versions, Android/JDK/Gradle versions. **NOT RECORDED.**

## Model and adaptation
- Base model: `stabilityai/sd-turbo`; exact revision: **NOT PINNED**; licence: TODO(team).
- Adaptation: LoRA tooling exists; **no adapter trained (DL-02 open)**. Dataset/split/settings: NOT RUN.

## Prompt benchmark
Prompt suite v1 (87 prompts, dev + 20 frozen hold-out; hold-out now seen). Unseen evaluation prompts: TODO(team).

## Quantitative results
CLIP, FID, latency, memory, model size: **NOT RUN / NOT MEASURED.** FID is not computable without a real reference set.

## Ablation study
Variants V0-V5 defined; V6 (adapter) and V7 (controller) blocked. Table: NOT RUN.

## Failure analysis
NOT WRITTEN (needs `p7_human_review.csv`).

## Mobile deployment result
Android app is a skeleton; no phone test. Mode today: none demonstrated (hybrid at best once P8 is done).

## Limitations and reproducibility
See `docs/P9_FINAL/DESIGN_DOCUMENT.md` section 10. Commands: `python -m pytest -q`; `python evaluation/scripts/run_p7_eval.py --all --clip`; `python evaluation/scripts/analyze_p7_results.py`; `python evaluation/scripts/build_p7b_report.py --usns <USNs>`.
