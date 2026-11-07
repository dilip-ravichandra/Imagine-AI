# P3A + P3B — Adapting SD-Turbo and (conditionally) serving the adapter (`ai_engine/training/`, `backend/`)

P3A: adapt SD-Turbo with a small LoRA **safely and reproducibly**, and judge the result. P3B: let the API use an adapter **only if it was approved**, with automatic fallback to the base model.
**Status: code and tests done for both; no training or review has been run, so no adapter exists and the API serves the base model.**

## Pipeline
```
COCO captions JSON + images --build_dataset--> training_data/<name>/{train,validation,manifest.json}
                            --train_lora-----> adapters/<name>/{pytorch_lora_weights.safetensors, adaptation.json}
                            --compare--------> evaluation/results/p3a_*/{blind/, review_sheet.csv, review_key.json}
                            --blind review---> fill review_sheet.csv
                            --approve--------> adapters/<name>/approval.json   (the ONLY way an adapter becomes usable)
                            --ADAPTER_PATH---> API serves it (P3B); anything wrong => base model
```

## Run it (Windows PowerShell, from repo root, GPU stack installed via requirements-training.txt)
```
# 0. Download COCO train2014 images + annotations yourself (cocodataset.org), accept its terms.
# 1. Tiny dataset to prove the pipeline (minutes):
python -m ai_engine.training.build_dataset --coco-annotations D:\coco\annotations\captions_train2014.json `
    --coco-images D:\coco\train2014 --out training_data\smoke --preset smoke
# 2. Check everything without a GPU (works anywhere):
python -m ai_engine.training.train_lora --data training_data\smoke --out adapters\smoke --revision <40-char hash> --preset smoke --dry-run
# 3. Real smoke run (5 optimizer steps; proves the stack, learns nothing):
python -m ai_engine.training.train_lora --data training_data\smoke --out adapters\smoke --revision <40-char hash> --preset smoke
# 4. First real adaptation (600 images, 150 updates; duration unmeasured):
python -m ai_engine.training.build_dataset ... --out training_data\small --preset small
python -m ai_engine.training.train_lora --data training_data\small --out adapters\small --revision <hash> --preset small
# 5. Compare on held-out prompts (blind):
python -m ai_engine.training.compare --data training_data\small --adapter adapters\small --revision <hash> --out evaluation\results\p3a_compare_small
```
`<hash>` = the full commit of `stabilityai/sd-turbo` you pinned as `MODEL_REVISION` after the P1A smoke test. Read the
model's licence page first (human step from the P2 handoff).

## Data policy
- Source: official COCO 2014 captions. Flickr30K is **not** used for training (access terms differ); it appears only in the evaluation prompts.
- **Leakage guard (two layers).** An image is dropped entirely if its id, file name, or *any* caption (case/punctuation-insensitive)
  matches `evaluation/prompts/dataset_prompts.json`, all splits (dev and test). The launcher re-runs this against the current eval
  file at launch, so prompts added after the dataset was built still block. By construction the 60 COCO *test* prompts come from `val2014`
  images, which are not in `captions_train2014.json` at all.
- Train and validation are split **by image** and share no identical bytes. One caption per image.
- **Mix.** `--complex-fraction` (default 0.5) of images come from those with a moderate/complex caption per the P2 parser; the rest are simple, so the
  adapter keeps seeing plain prompts. The parser scored **12/20 on unseen prompts**; this is a rough stratifier, not a measurement.
- `manifest.json` records annotation-file hash, seed, parameters, per-row ids/hashes/licence, rejects, counts. It contains no local paths.
- Licences: each row carries its COCO licence name. Many COCO images are non-commercial or no-derivatives. `--license-ids 4,5,7,8` restricts the
  pool. **Decide and document before redistributing images or an adapter.** Nothing here decides that for you.

## Known hazards (why the defaults are what they are)
| Hazard | What was done |
|---|---|
| Upstream `--lr_warmup_steps` defaults to **500**; a 150-step run would never reach its learning rate | Always passed explicitly; launcher rejects warm-up > steps/2 |
| `--random_flip` turns "left of" into "right of" and corrupts spatial captions | Not used (test enforces) |
| Upstream validation uses 30 steps and default guidance, wrong for SD-Turbo | `--validation_prompt` not used; `compare` does validation instead |
| SD-Turbo is already distilled for 1-4 steps; the upstream trainer samples **random timesteps 0-999** with plain denoising loss | Cannot be fixed here. Small rank/steps/LR, base kept as default, 1- and 4-step comparison. **Quality may degrade; that is a legitimate negative result.** |
| Upstream loads the scheduler **without `revision`** (line 501), so the scheduler config is not pinned | Disclosed. Check `scheduler/scheduler_config.json` at your pinned commit if reproducibility matters |
| Trainer drift | Vendored unmodified (diffusers v0.35.1, Apache-2.0), SHA-256 checked before every run |
| Silent preset fallback (`--steps 0` becoming the preset's value) | Fixed during this phase after a test caught it |
| Learning rate 5e-5, rank 4, 150 steps, 600 images | **Untuned guesses.** If the adapter is indistinguishable from base, try 1e-4 once; do not sweep on the held-out set |

## `adaptation.json` contract (consumed by P3B)
`base_model`, `base_revision` (40-hex), `settings`, `trainer_sha256`, `manifest_sha256`, `command`, `gpu`, `torch`, `warning`,
`status` ∈ `started | failed | training_completed_not_validated`, and on success `adapter_bytes`, `adapter_sha256`.
**There is no "validated" status in P3A.** Only the comparison plus human review can justify using an adapter.

## Acceptance rule (written before any result exists; change it only before looking at images)
The adapter is approved only if, on the blind review **at each of 1 and 4 steps separately**: (a) the adapted image is "better or tie" on **≥ 70%** of rated pairs, with **≥ 40 rated pairs at each step count** (80+ ratings in total; fewer is anecdote; clarified before any result existed); (b) no pair exists where the adapted run failed or was filtered but the base run succeeded (checked automatically); (c) you confirm you saw no systematic artefact (colour cast, texture collapse), via `--confirm-no-systematic-artifacts`. The 70% / 40 figures are judgement calls, not statistics. CLIP scoring
belongs to P7 and is not computed here. Otherwise: record the negative result, keep the base model, and move on to P4.

## Blind review
`compare` writes `blind/NNNN_A.png` / `_B.png` with random A/B order and a separate `review_key.json`. Open only `blind/` and
`review_sheet.csv` until finished. `summarize_review(rows, key)` then tallies adapted-better / base-better / tie and reports unrated rows.
Both models see identical prompts, seeds (CPU generator, same as `engine.py`), steps and 512px. Latency in this folder is **not** a benchmark (P4).

## What is verified vs not
Verified (sandbox, no GPU): data selection, leakage guards, determinism, split, manifest, launcher settings/preflight/command, adapter validation,
blind-review logic. 12 deliberate code mutations were each caught by the tests.
**Not verified:** any actual training run, memory fit on an 8 GB RTX 5050, training time, the dependency combination in `requirements-training.txt`,
`compare.run()` (needs GPU), whether the adapter helps, or whether the upstream script accepts SD-Turbo's scheduler config
(it loads it as `DDPMScheduler`; if that errors, that is the first thing to read). Only the 5-step smoke run answers these.

## Limitations
Near-duplicate images are not detected. SD-Turbo's pretraining data is undisclosed and may include COCO, so "unseen" means unseen by *this
adaptation*, not by the base model. Captions are human-written and imperfect. The parser stratification is approximate. The adapter, if any,
is bound to one exact base revision.

## P3B — serving an approved adapter
```
# after filling evaluation\results\p3a_compare_small\review_sheet.csv (blind):
python -m ai_engine.training.approve --adapter adapters\small --compare evaluation\results\p3a_compare_small --reviewer "Your Name" --confirm-no-systematic-artifacts
# exit 0 = approved (writes adapters\small\approval.json), 1 = rule not met (nothing written), 2 = bad input
$env:MODEL_REVISION="<the SAME 40-char hash used for training>"; $env:ADAPTER_PATH="adapters\small"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/api/v1/model      # shows active / not active and why
```
**The API uses the adapter only if all hold:** training completed for `stabilityai/sd-turbo`; `MODEL_REVISION` equals the adapter's base revision (an unpinned server is rejected); the weights still match the hash recorded at training; `approval.json` exists, is bound to that same hash, and its recorded tallies still satisfy the *current* rule. Otherwise: base model, reason logged at startup and shown by `/api/v1/model`. The server never fails because of an adapter.
- **Same weights as reviewed.** The adapter is loaded unfused with the same call `compare` used, so what is served is what was judged. Fusing it for speed is a P4 option that needs its own comparison.
- **Honest labelling.** Responses carry `model_revision = <rev>+lora-<sha12>` when the adapter made the image.
- **Clean fallback.** If loading fails midway the half-modified pipeline is discarded and a fresh base pipeline is built. A genuine out-of-memory error is reported, not hidden behind a fallback.
- **Not a security boundary.** Anyone who can write to the adapter folder can forge `approval.json`. It protects against accidents (wrong/edited/unreviewed adapter), not an attacker with disk access. Hosting an adapter publicly also needs the licence decision above.
- **A rejected adapter is a result, not a failure.** Record it in `docs/ADAPTATION_RESULT.md`, keep the base default, and move to P4.

## What is verified vs not (P3B)
Verified (fake torch/diffusers, no GPU): gate logic incl. exact thresholds, approval binding and re-evaluation, approve CLI, engine load/fallback/rebuild/OOM paths, honest labelling, API contracts unchanged, live `uvicorn` under 4 adapter configurations (zero tracebacks, no path leakage). 16 deliberate mutations of this code were each caught.
**Not verified:** that `load_lora_weights` accepts a real adapter produced by the upstream trainer on a real SD-Turbo pipeline (the fake only checks we call it correctly), actual GPU memory with an adapter attached, speed impact of an unfused adapter, and Windows.
