# P7A — Metrics harness (CLIP, FID gate, latency, memory, size, paired comparison)

Status: **code + 40 unit tests complete. NO real measurements exist yet.** The harness has only been run with fake engines
(tests) and the synthetic dry-run engine (plumbing check, flagged `synthetic=true`, rejected by the report gate).
Every number in a real report must come from a GPU-laptop run. Covers EVAL-01..EVAL-06 mechanics; P7B (ablation write-up,
failure analysis) needs the real results first. API v1.0.0 unchanged; nothing in `backend/` was modified.

## 1. What was added
| Path | Purpose |
|---|---|
| `ai_engine/evaluation/variants.py` | Fixed variant grid V0-V7, one-variable-at-a-time check, blocked variants kept with a reason |
| `ai_engine/evaluation/harness.py` | `run_variant()` + `select_eval_prompts()`; reuses P4 `gpu_snapshot`, `summarize`, `pixel_fidelity` |
| `ai_engine/evaluation/metrics.py` | cosine similarity, Frechet distance, **FID gate**, paired deltas, prompt-cluster bootstrap CI |
| `ai_engine/evaluation/sizes.py` | file-size report (base snapshot, weight files, adapter) |
| `ai_engine/evaluation/cv_pipelines.py` | CV-on pipeline = P5A `auto_enhance` (P5B registers its pipeline here) |
| `ai_engine/evaluation/report.py` | Markdown/JSON/CSV report, human review sheet, failure-log template, quality-vs-cost plot |
| `ai_engine/evaluation/dryrun.py` | synthetic engine for plumbing checks only |
| `evaluation/scripts/run_p7_eval.py`, `analyze_p7_results.py` | runner and analyzer CLIs |
| `tests/test_p7_*.py`, `tests/p7_helpers.py` | 40 tests |

## 2. Variants (docs/08 section 8.4)
| ID | Changes vs V0 | Runnable |
|---|---|---|
| V0 | baseline: fp32, 4 steps, 512, CV off | yes |
| V1 | precision fp16 | yes |
| V2 / V3 | steps 2 / steps 1 | yes |
| V4 | **COMBINED** fp16 + 2 steps | yes |
| V5 | CV on (P5A `auto_enhance`), generation identical to V0 | yes |
| V6 | adapted model (LoRA) | **NO** — no approved adapter exists (P3A training never run; code + gated loader exist); DL-02 open |
| V7 | adaptive controller across resource profiles | **NO** — controller exists (P6) but is not wired into this harness and no measured profile exists |

V6/V7 appear in every report as `NOT RUN` with the reason. Requirement gaps this leaves (must be declared in the final
report): base-vs-adapted comparison, adaptive modes across profiles, fallback under constrained resources.

## 3. Protocol
- **Prompts:** frozen hold-out split of `prompt_suite_v1.json` (20 `unseen` cases) by default; `--split dev` for smoke runs.
  `--prompts-per-category` / `--limit` create subsets and are recorded in the result (`suite.subset=true`).
  Those 20 prompts are frozen but now *seen by the team*: for the live demo, write NEW unseen prompts.
- **Seeds** identical for every variant (default 1234,5678,9012). **Repeats** per (prompt, seed) default 2; **warm-up** 2.
- **Latency:** `generation_ms` (engine.generate: encode + denoise + decode + sync), `cv_ms`, `end_to_end_ms` = sum; model load
  separate (`model_load_ms`). Excludes PNG save and CLIP scoring. Encode/denoise/decode split is stored only if the engine
  result has a `stage_ms` dict — the current engine has none, so it is **null** (known gap, see section 6).
- **Memory:** `peak_gpu_mb` = per-generation PyTorch peak *allocated* (from the engine); `peak_reserved_mb` = peak reserved over
  the timed phase (reset after warm-up); `peak_process_ram_mb` = process peak working set / max RSS. VRAM and RAM never mixed.
- **CLIP:** `openai/clip-vit-base-patch32` (P4 `ClipScorer`), normalised embeddings, cosine similarity, one score per
  (prompt, seed) from the repeat-0 image (so repeats do not inflate n). For V5 the score is taken on the CV output **and** on the
  raw image, so the CV effect is isolated from generation noise (`clip_score_raw`).
- **Paired comparison:** deltas per (prompt, seed) vs V0; mean, median, share>0, and a 95% percentile bootstrap that resamples
  **prompts** (seeds of one prompt are correlated). With 1 prompt the CI is reported as null.
- **FID:** `fid_gate()` refuses unless both sets exceed the feature dimension (2048 for Inception) and labels n<10,000 as not
  citable. No real reference set and no Inception extractor exist in this repo, so FID is **not computed**; the report states the
  justified alternative (paired CLIP deltas + bootstrap CI, pixel fidelity vs V0, human review sheet).
- **Model size:** bytes on disk of the HF snapshot (auto-found from `MODEL_ID` + exact `MODEL_REVISION`, or `--model-dir`), listing
  weight files so fp16/fp32 variants are visible; adapter via `--adapter`. App package size is separate and not measured here.
- **Gate (`analyze_p7_results.py` exit code):** measured GPU baseline V0, >=1 measured optimized variant, measured CLIP scores,
  >= `--min-runs` timed runs each, no synthetic files counted. Failures/OOM are recorded as results, not hidden.

## 4. Run on the GPU laptop (Windows PowerShell, repo root)
```
$env:MODEL_REVISION="<commit hash of stabilityai/sd-turbo>"
python evaluation/scripts/run_p7_eval.py --list
python evaluation/scripts/run_p7_eval.py --only V0 --clip --prompts-per-category 1 --repeats 1 --warmup 1   # quick check first
python evaluation/scripts/run_p7_eval.py --all --clip           # full hold-out run, one subprocess per variant
python evaluation/scripts/analyze_p7_results.py                  # add --adapter <path> once an adapter exists
```
Plumbing check without GPU (synthetic, never citable): `python evaluation/scripts/run_p7_eval.py --all --dry-run --split dev --limit 4`.
Outputs in `evaluation/reports/`: `p7_report.md/.json`, `p7_runs.csv` (raw), `p7_human_review.csv`, `p7_failure_cases_TEMPLATE.md`,
`p7_quality_cost.png` (only with >=2 measured variants).

## 5. Human review (ADV-02)
CLIP does not verify object count or spatial relations. `p7_human_review.csv` has one row per image with blank columns
(counts, relations, attributes, artifacts, CV helped/hurt) for the team to fill in by looking at the images. Nothing is pre-filled.

## 6. Known limitations
- Never run on a real model or GPU; real CLIP scoring (`ClipScorer`) is untested in the build sandbox (it needs weights).
- Stage-level latency split is not captured (needs engine instrumentation, a P1A-owned file; not changed here).
- Default sample size (20 prompts x 3 seeds x 2 repeats) is small; CIs will be wide. Increase seeds if time allows.
- CLIP-B/32 is a coarse signal; differences of a few thousandths are not meaningful without the CI.
- Run-to-run GPU clocks/thermals vary; keep the laptop plugged in and the same power plan across variants.
- CV-on tests the P5A auto-enhance only. P5B (quality metrics, artifact detection/correction) now exists as code + tests on synthetic images, but its thresholds are provisional and unvalidated on real output, so CV-04/CV-05 are not yet evidenced.
- No real-image FID reference dataset exists; license and sourcing of one is a separate decision.
