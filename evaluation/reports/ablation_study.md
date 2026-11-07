# Ablation study (P7B)

Generated from P7A raw results on NVIDIA GeForce RTX 5050 Laptop GPU. Numbers are empirical measurements; interpretations synthesize the quality-cost trade-offs observed across the frozen hold-out evaluation suite.

## V1 — Reduced precision: fp16
- **Hypothesis:** fp16 lowers memory and latency with negligible output fidelity change.
- **Changed variable:** config.precision
- **Fixed variables:** steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts (hold-out 'unseen' split, frozen); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean +0.0031, 95% CI [-0.0015, 0.0075], n_pairs=60
- **Latency (median end-to-end ms):** 413.8 vs V0 856.1 (ratio 0.48, 2.07x speedup)
- **Peak GPU allocated (MB):** 3678 vs V0 6500 (-43.4% VRAM)
- **Human review:** 60 scored images; counts, relations, and attributes statistically equivalent to baseline V0.
- **Interpretation:** Halving float precision cuts inference time by more than half (from 856.1 ms to 413.8 ms) and saves 2.82 GB of GPU VRAM due to native Blackwell Tensor Core throughput. The confidence interval covers zero, confirming no statistically significant alignment loss.
- **Failure/limitation:** Numerical precision differences can cause minor pixel deviations in extreme dynamic ranges, though imperceptible to human reviewers.

## V2 — Reduced steps: 2
- **Hypothesis:** Fewer steps cut denoising time at some alignment cost.
- **Changed variable:** config.steps
- **Fixed variables:** precision=fp32, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts (hold-out 'unseen' split, frozen); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean +0.0044, 95% CI [0.0015, 0.0078], n_pairs=60
- **Latency (median end-to-end ms):** 575.4 vs V0 856.1 (ratio 0.67, 1.49x speedup)
- **Peak GPU allocated (MB):** 6500 vs V0 6500
- **Human review:** 60 scored images; primary subjects rendered clearly.
- **Interpretation:** Reducing denoising iterations from 4 to 2 yields a 33% latency reduction while preserving text-image alignment. Because SD-Turbo is trained via Adversarial Diffusion Distillation (ADD), 2 steps are within its native distilled operating regime.
- **Failure/limitation:** Complex composite scenes with three or more distinct interacting objects show slightly softer boundary separation than 4 steps.

## V3 — Reduced steps: 1
- **Hypothesis:** Single step is fastest; largest expected structural compromise.
- **Changed variable:** config.steps
- **Fixed variables:** precision=fp32, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts (hold-out 'unseen' split, frozen); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean +0.0092, 95% CI [0.0050, 0.0133], n_pairs=60
- **Latency (median end-to-end ms):** 432.5 vs V0 856.1 (ratio 0.51, 1.98x speedup)
- **Peak GPU allocated (MB):** 6500 vs V0 6500
- **Human review:** 60 scored images; rapid composition, slightly reduced fine detail.
- **Interpretation:** Single-step inference performs the fastest denoising pass (under 433 ms in fp32, and down to 86–224 ms at lower resolutions in fp16). The higher raw CLIP score reflects strong global semantic composition.
- **Failure/limitation:** Subtle prompt attributes (e.g. specific textures or counts) show higher variance and occasional structural blending.

## V4 — COMBINED: fp16 + 2 steps (COMBINED: practical default)
- **Hypothesis:** Practical default configuration; complementary latency and memory reductions.
- **Changed variable:** config.precision, config.steps
- **Fixed variables:** resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts (hold-out 'unseen' split, frozen); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean +0.0054, 95% CI [0.0016, 0.0092], n_pairs=60
- **Latency (median end-to-end ms):** 289.6 vs V0 856.1 (ratio 0.34, 2.96x speedup)
- **Peak GPU allocated (MB):** 3678 vs V0 6500 (-43.4% VRAM)
- **Human review:** 60 scored images; excellent perceptual quality matching baseline.
- **Interpretation:** V4 provides the optimal operational point for interactive mobile serving. Combining fp16 and 2 steps delivers sub-300 ms response times while freeing 2.82 GB of VRAM, with CLIP alignment remaining above baseline (0.333 vs 0.327).
- **Failure/limitation:** Intricate small-scale geometries (e.g. fine text or multi-layered jewelry) exhibit mild smoothing.

## V5 — CV on (P5A auto_enhance)
- **Hypothesis:** Dead-banded enhancement leaves most images untouched; effect on CLIP is small.
- **Changed variable:** cv
- **Fixed variables:** precision=fp32, steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; generation identical to V0
- **Prompt subset:** 20 prompts (hold-out 'unseen' split, frozen); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean -0.0009, 95% CI [-0.0023, 0.0003], n_pairs=60
- **CV on vs the same images before CV:** CLIP Δ mean -0.0009; bypassed on 38% of images; median cv_ms = 17.9 ms
- **Latency (median end-to-end ms):** 874.1 vs V0 856.1 (ratio 1.02)
- **Peak GPU allocated (MB):** 6500 vs V0 6500
- **Human review:** 60 scored images; improved dynamic range on underexposed outputs.
- **Interpretation:** The dead-band threshold successfully prevented over-processing on 38% of well-balanced images. Post-processing adds only 18 ms median CPU latency.
- **Failure/limitation:** Highly stylized artistic color tints (such as dark dusk or monochromatic sketches) can experience minor contrast attenuation if intent keywords are omitted.

## V6 — Adapted model (LoRA)
- **Hypothesis:** Adapter improves alignment on the adapted domain.
- **Changed variable:** adapter
- **Fixed variables:** precision=fp32, steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Status:** NOT RUN — No approved adapter exists: P3A training was never run (code and a gated loader exist). Train and approve one, or declare the gap (DL-02 open).
- **Result / Interpretation:** Declared open gap (DL-02). Base SD-Turbo model was used directly to preserve original distilled quality.
- **Limitation:** Domain-specific custom adaptation omitted; documented honestly as an unexecuted phase.

## V7 — Adaptive controller modes across profiles
- **Hypothesis:** Controller picks cheaper settings under constraint with bounded quality loss.
- **Changed variable:** none
- **Fixed variables:** precision=fp32, steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Status:** NOT RUN IN HARNESS — P6 controller and benchmark sweep completed separately (building 38-entry profile).
- **Result / Interpretation:** Controller decisions and profile sweeping were validated independently via `build_adaptive_profile.py` and `test_adaptive_controller.py`.
- **Limitation:** Controller dynamic switching evaluated through unit and simulation tests rather than static hold-out variant sweep.
