# P4 — Inference optimization

Status: **code + tests complete; measured results NOT RUN** (build sandbox has no GPU). The P4 gate needs real numbers from the RTX 5050 laptop.
Requirements covered by the *method*: OPT-01, OPT-02, ADV-04 (and part of ADV-03). They are satisfied only once the benchmark has actually been run and the table filled from real data.

## 1. Decision: Phase 3 (adaptation) was skipped
> Update (combined tree, safety audit): P3A/P3B code (training tooling, gated adapter loader) was later delivered, but **no adapter has been trained or approved**, so the consequences below still hold.
P4 depends on a measured **baseline**, not on an adapter, so it can proceed. Consequences, stated plainly:
- **DL-02 (meaningful adaptation) and the "base vs adapted" experiment (docs/08 §8.4) are still OPEN.** P3A/P3B must be done before submission, or the gap must be declared in the final report.
- P4 profiles are adapter-agnostic (they only touch precision/steps/memory), so a LoRA from P3B can later be benchmarked with the same harness.
- P4 still needs the P1A human step: real SD-Turbo run on the laptop and a **pinned `MODEL_REVISION`** (the runner refuses to run without it).

## 2. What was added
| Piece | Where |
|---|---|
| Validated config + one-variable-at-a-time experiment registry | `ai_engine/optimization/{config,experiments}.py` |
| Torch-free decisions (precision resolve, weight variant, offload rules) | `ai_engine/optimization/policy.py` |
| Engine applies optimizations (env-driven; defaults = P1A behaviour) | `backend/app/services/engine.py`, `backend/app/config.py` |
| Benchmark core (per-run records, OOM-as-result, optional CLIP) | `ai_engine/optimization/benchmark.py`, `evaluation/scripts/run_p4_benchmarks.py` |
| Mechanical quality-cost table + gate check | `ai_engine/optimization/report.py`, `evaluation/scripts/analyze_p4_results.py` |

**API v1.0.0 is unchanged.** `MODE_STEPS` (quick 1 / balanced 2 / best 4) is still the provisional P1A mapping; P6 will replace it using measured profiles.

## 3. Settings (environment variables; defaults reproduce P1A exactly)
`PRECISION=auto|fp32|fp16|bf16` (auto = fp16 on CUDA, fp32 on CPU) · `ATTENTION_SLICING` · `VAE_SLICING` · `OFFLOAD=none|model|sequential` · `WEIGHTS_VARIANT=auto|fp16|none`.
Rules enforced at model load (errors are logged server-side; clients get the usual safe `INTERNAL_ERROR`): fp16/bf16 only on CUDA; bf16 only if the device reports support; offload only on CUDA; offload is applied *without* a prior `.to(device)` (diffusers requirement).
`WEIGHTS_VARIANT=auto`: with `PRECISION=auto` the `fp16` file variant is loaded exactly as in P1A; with an explicit precision, `fp16` loads the fp16 files and `fp32`/`bf16` load the full-precision files. **Unverified:** whether the pinned SD-Turbo revision ships full-precision component files (no Hugging Face access in the sandbox). If B0 fails to load for that reason, set `WEIGHTS_VARIANT=fp16` (fp16 weights upcast to fp32) and **label the baseline accordingly** in the report.

## 4. Experiment grid (one variable at a time; `python evaluation/scripts/run_p4_benchmarks.py --list`)
| ID | Changes vs B0 | Note |
|---|---|---|
| B0 | — | fp32, 4 steps, 512, no memory options |
| E1 | precision → fp16 | |
| E2 / E3 | steps → 2 / 1 | |
| E4 | attention slicing on | |
| E5 | VAE slicing on | |
| E6 | model CPU offload | expect big latency cost |
| C1 | **COMBINED** fp16 + 2 steps | not a single-variable result; never counted toward the gate |
Registry rule (tested): every non-combined experiment differs from B0 in exactly one field.
Not implemented (optional per plan, compatibility unverified): quantization, `torch.compile`, compact-model alternative (BK-SDM-Tiny / LCM-LoRA). Resolution policy belongs to P5A/P6.

## 5. Run it (Windows PowerShell, repo root, GPU torch installed per `requirements-ml.txt`)
```
$env:MODEL_REVISION="<commit hash from the P1A smoke test>"
python evaluation/scripts/run_p4_benchmarks.py --all          # one subprocess per experiment => clean VRAM
python evaluation/scripts/analyze_p4_results.py               # writes evaluation/reports/p4_quality_cost_table.{md,json}
```
Optional: `--clip` (adds CLIP-B/32 cosine similarity; downloads a CLIP model; **this code path was not executed in the sandbox**). Defaults: 11 dev prompts × seeds 1234,5678 × 2 timed repeats + 2 warm-ups per experiment. The hold-out split is never used.
Raw output: `evaluation/results/p4/<ID>.json`; images: `evaluation/results/p4/images/<ID>/` (git-ignored).

## 6. If B0 (fp32) runs out of memory
That is a finding, not a failure: keep `B0.json` (status `oom`). Then re-run with `WEIGHTS_VARIANT`/baseline decision documented: make fp16 the baseline for steps/slicing/offload experiments, and report precision as "fp32 does not fit in 8 GB at 512" with the recorded error. Edit `BASELINE` in `experiments.py` in a reviewed commit (the registry test will tell you which experiments must change).

## 7. Measurement definitions
- **Latency** = wall time of `engine.generate()` (text encode + denoise + VAE decode + CUDA sync). Excludes PNG save, model load, CLIP. Per-stage split (encode/denoise/decode) is **not** measured here; that is P7A.
- **Memory** = PyTorch peak *allocated* per run and peak *reserved* per experiment (reset after warm-up), plus allocated-after-load. Process RAM = peak working set since process start. nvidia-smi totals are not recorded. VRAM and RAM are never mixed.
- **Statistics**: n, mean, median, sample stdev, min, max, p95 (nearest-rank). Repeats share (prompt, seed), so latency spread is measurement noise; across prompts it also includes content variation.
- **Fidelity** = pixel PSNR of an image vs B0's image for the same prompt+seed. It measures *deviation*, not quality: an optimized image may differ and still be good. Identical images are counted separately (PSNR would be infinite). Judge quality with CLIP (broad alignment only; not object counts or relations) plus human review of the saved images.
- Failure policy: an OOM/error stops that experiment, is stored in its JSON, and appears in the table. Nothing is retried silently.

## 8. Gate check (`analyze_p4_results.py`, exit code 0/1)
Met only if B0 and **at least two single-variable strategies** have status `ok`, were measured on CUDA, and have ≥ `--min-runs` (default 10) successful runs. The script also warns on: differing scheduler/model revision/protocol across experiments, and an unpinned revision. It writes **no conclusions**; the quality-cost interpretation and plots are for the report (use the ablation template below).

## 9. Ablation record template (docs/08 §8.5) — fill from real data only
Hypothesis · Changed variable · Fixed variables · Prompt subset · Hardware/software (copy `environment` from the JSON) · Runs/samples · Quality/alignment result · Latency & memory · Interpretation · Failure/limitation.

## 10. Known limitations
No measured results exist yet. Gold-standard quality is unmeasured (CLIP optional, FID is P7). `fp32` full-precision file availability, `pipe.vae.enable_slicing()` behaviour on the pinned diffusers version, offload behaviour on RTX 50-series, and the CLIP scorer are unverified outside fakes. Windows run NOT RUN.
