# Ablation study (P7B)

Generated from P7A raw results. Numbers are measurements; 'Interpretation' is for the team to write after looking at the images and the review sheet.

## V1 — Reduced precision: fp16
- **Hypothesis:** fp16 lowers memory/latency with small output change.
- **Changed variable:** config.precision
- **Fixed variables:** steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts ({'version': '1.0', 'split': 'holdout', 'n_prompts': 20, 'per_category': None, 'limit': None, 'subset': False}); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean 0.0031, 95% CI [-0.0015, 0.0075], n_pairs=60
- **Latency (median end-to-end ms):** 413.8 vs V0 856.1 (ratio 0.48)
- **Peak GPU allocated (MB):** 3678 vs V0 6500
- **Human review:** 0/60 images reviewed; counts {}, relations {}, attributes {}
- **Interpretation:** TODO(team)
- **Failure/limitation:** TODO(team)

## V2 — Reduced steps: 2
- **Hypothesis:** Fewer steps cut denoising time at some alignment cost.
- **Changed variable:** config.steps
- **Fixed variables:** precision=fp32, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts ({'version': '1.0', 'split': 'holdout', 'n_prompts': 20, 'per_category': None, 'limit': None, 'subset': False}); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean 0.0044, 95% CI [0.0015, 0.0078], n_pairs=60
- **Latency (median end-to-end ms):** 575.4 vs V0 856.1 (ratio 0.67)
- **Peak GPU allocated (MB):** 6500 vs V0 6500
- **Human review:** 0/60 images reviewed; counts {}, relations {}, attributes {}
- **Interpretation:** TODO(team)
- **Failure/limitation:** TODO(team)

## V3 — Reduced steps: 1
- **Hypothesis:** Single step is fastest; largest expected drop.
- **Changed variable:** config.steps
- **Fixed variables:** precision=fp32, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts ({'version': '1.0', 'split': 'holdout', 'n_prompts': 20, 'per_category': None, 'limit': None, 'subset': False}); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean 0.0092, 95% CI [0.0050, 0.0133], n_pairs=60
- **Latency (median end-to-end ms):** 432.5 vs V0 856.1 (ratio 0.51)
- **Peak GPU allocated (MB):** 6500 vs V0 6500
- **Human review:** 0/60 images reviewed; counts {}, relations {}, attributes {}
- **Interpretation:** TODO(team)
- **Failure/limitation:** TODO(team)

## V4 — COMBINED: fp16 + 2 steps (COMBINED: effects may not add up)
- **Hypothesis:** Likely practical default; effects may not add up.
- **Changed variable:** config.precision, config.steps
- **Fixed variables:** resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Prompt subset:** 20 prompts ({'version': '1.0', 'split': 'holdout', 'n_prompts': 20, 'per_category': None, 'limit': None, 'subset': False}); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean 0.0054, 95% CI [0.0016, 0.0092], n_pairs=60
- **Latency (median end-to-end ms):** 289.6 vs V0 856.1 (ratio 0.34)
- **Peak GPU allocated (MB):** 3678 vs V0 6500
- **Human review:** 0/60 images reviewed; counts {}, relations {}, attributes {}
- **Interpretation:** TODO(team)
- **Failure/limitation:** TODO(team)

## V5 — CV on (P5A auto_enhance)
- **Hypothesis:** Dead-banded enhancement leaves most images untouched; effect on CLIP is small. Untuned thresholds: may help or hurt.
- **Changed variable:** cv
- **Fixed variables:** precision=fp32, steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; generation identical to V0
- **Prompt subset:** 20 prompts ({'version': '1.0', 'split': 'holdout', 'n_prompts': 20, 'per_category': None, 'limit': None, 'subset': False}); seeds [1234, 5678, 9012]
- **Environment:** NVIDIA GeForce RTX 5050 Laptop GPU, torch 2.11.0+cu128, diffusers 0.42.1, revision b261bac6fd2cf515557d5d0707481eafa0485ec2
- **Samples:** 120 timed generations (60 scored images)
- **Quality (CLIP Δ vs V0, paired):** mean -0.0009, 95% CI [-0.0023, 0.0003], n_pairs=60
- **CV on vs the same images before CV:** CLIP Δ mean -0.0009; bypassed on 38% of images
- **Latency (median end-to-end ms):** 874.1 vs V0 856.1 (ratio 1.02)
- **Peak GPU allocated (MB):** 6500 vs V0 6500
- **Human review:** 0/60 images reviewed; counts {}, relations {}, attributes {}
- **Interpretation:** TODO(team)
- **Failure/limitation:** TODO(team)

## V6 — Adapted model (LoRA)
- **Hypothesis:** Adapter improves alignment on the adapted domain.
- **Changed variable:** adapter
- **Fixed variables:** precision=fp32, steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Status:** NOT RUN — No approved adapter exists: P3A training was never run (code and a gated loader exist). Train and approve one, or declare the gap (DL-02 open).
- **Result / Interpretation:** none; this is a declared gap.
- **Limitation:** requirement left unmet; state this explicitly in the submission.

## V7 — Adaptive controller modes across profiles
- **Hypothesis:** Controller picks cheaper settings under constraint with bounded quality loss.
- **Changed variable:** none
- **Fixed variables:** precision=fp32, steps=4, resolution=512, attention_slicing=False, vae_slicing=False, offload=none; same prompts, seeds, model revision; CV off
- **Status:** NOT RUN — Controller exists (P6) but is not wired into this harness and no MEASURED profile exists. Run the P6 profile sweep on the GPU first.
- **Result / Interpretation:** none; this is a declared gap.
- **Limitation:** requirement left unmet; state this explicitly in the submission.
