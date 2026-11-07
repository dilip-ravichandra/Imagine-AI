# P7 evaluation report (mechanical)

Generated mechanically by ai_engine/evaluation/report.py from raw result files. It contains no interpretation and declares no winner. CLIP is a broad text-image alignment signal; it does not verify object counts or spatial relations (see the human review sheet). Memory is PyTorch GPU memory or process RAM as labelled, never nvidia-smi totals; VRAM and RAM are never mixed.

**P7 gate: MET**

## Environment and protocol
- GPU: NVIDIA GeForce RTX 5050 Laptop GPU (8151 MB VRAM); OS: Windows-11-10.0.26300-SP0; Python 3.12.10; torch 2.11.0+cu128; diffusers 0.42.1
- Model: stabilityai/sd-turbo @ b261bac6fd2cf515557d5d0707481eafa0485ec2; CLIP model: openai/clip-vit-base-patch32@3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268
- Prompts: 20 ({'version': '1.0', 'split': 'holdout', 'n_prompts': 20, 'per_category': None, 'limit': None, 'subset': False}); seeds: [1234, 5678, 9012]; timed repeats per (prompt, seed): 2; warm-up generations: 2
- Latency: generation_ms = wall time of engine.generate() (text encode + denoise + VAE decode + CUDA sync). cv_ms = wall time of the CV pipeline on that image (0 when CV is off; counted even when the pipeline bypasses). end_to_end_ms = generation_ms + cv_ms. Excludes model load, PNG save, CLIP scoring. Model load is reported separately (model_load_ms). Encode/denoise/decode split is recorded only if the engine result exposes `stage_ms`; otherwise null.
- Memory: peak_gpu_mb = per-generation torch.cuda peak allocated reported by the engine; peak_reserved_mb = torch.cuda peak reserved over the whole timed phase (after reset post warm-up); peak_process_ram_mb = peak working set / max RSS of THIS process since start (includes model load; system RAM, never mixed with VRAM)

## Results (median; n = timed generations)
| Variant | Status | n | CLIP mean | Median e2e ms | CV% | Peak alloc MB | Peak reserved MB | Peak RAM MB | Load ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 Baseline (fp32, 4 steps, 512, CV off) | measured | 120 | 0.327 | 856.1 | 0.3 | 6500 | 7670 | 4123 | 4596 |
| V1 Reduced precision: fp16 | measured | 120 | 0.330 | 413.8 | 0.8 | 3678 | 4228 | 2471 | 3643 |
| V2 Reduced steps: 2 | measured | 120 | 0.332 | 575.4 | 0.3 | 6500 | 7670 | 4124 | 5914 |
| V3 Reduced steps: 1 | measured | 120 | 0.336 | 432.5 | 0.3 | 6500 | 7670 | 4122 | 3767 |
| V4 COMBINED: fp16 + 2 steps | measured | 120 | 0.333 | 289.6 | 0.7 | 3678 | 4228 | 2470 | 3407 |
| V5 CV on (P5A auto_enhance) | measured | 120 | 0.326 | 874.1 | 0.6 | 6500 | 7670 | 4124 | 5707 |
| V6 Adapted model (LoRA) | NOT RUN — No approved adapter exists: P3A training was never run (code and a gated loader exist). Train and approve one, or declare the gap (DL-02 open). | | | | | | | | |
| V7 Adaptive controller modes across profiles | NOT RUN — Controller exists (P6) but is not wired into this harness and no MEASURED profile exists. Run the P6 profile sweep on the GPU first. | | | | | | | | |

Spread (stdev / p95 of end-to-end ms):
- V0: stdev 2.5, p95 860.2, min 852.1, max 874.7
- V1: stdev 3.4, p95 420.9, min 407.3, max 430.0
- V2: stdev 1.5, p95 577.4, min 570.8, max 583.7
- V3: stdev 1.5, p95 435.1, min 427.3, max 439.7
- V4: stdev 2.0, p95 293.7, min 285.2, max 297.0
- V5: stdev 5.1, p95 880.1, min 865.6, max 898.1

## CLIP: paired delta vs V0 (same prompts and seeds; bootstrap resamples prompts)
| Variant | n pairs | n prompts | mean Δ | 95% CI | share Δ>0 |
|---|---:|---:|---:|---|---:|
| V1 | 60 | 20 | 0.0031 | [-0.0015, 0.0075] | 0.53 |
| V2 | 60 | 20 | 0.0044 | [0.0015, 0.0078] | 0.62 |
| V3 | 60 | 20 | 0.0092 | [0.0050, 0.0133] | 0.68 |
| V4 | 60 | 20 | 0.0054 | [0.0016, 0.0092] | 0.60 |
| V5 | 60 | 20 | -0.0009 | [-0.0023, 0.0003] | 0.27 |

## CV off vs on (V5, same generated images before/after CV)
- mean CLIP Δ -0.0009, 95% CI [-0.0023, 0.0003], n=60; CV bypassed (dead band) on 38% of images; median cv_ms 17.9

## CLIP by prompt category (mean per category, one image per (prompt, seed))
- V0: unseen=0.327 (n=60)
- V1: unseen=0.330 (n=60)
- V2: unseen=0.332 (n=60)
- V3: unseen=0.336 (n=60)
- V4: unseen=0.333 (n=60)
- V5: unseen=0.326 (n=60)

## FID
- real reference images: 0; generated: 60
- decision: FID NOT computed. Justified alternative: paired CLIP deltas with prompt-cluster bootstrap CI + pixel fidelity vs V0 + human review sheet
- reason: no real reference images
- reason: generated sample count 60 <= feature dim 2048: covariance is singular

## Model size (file bytes on disk; not parameter count; app package size is separate)
- NOT MEASURED (pass --model-dir or pin MODEL_REVISION with the model in the HF cache)

## Not measured by this harness
- Encode/denoise/decode split (engine does not expose stage timings); on-device phone numbers (P8); object-count and spatial-relation correctness (human review sheet).
