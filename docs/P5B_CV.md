# P5B — Classical CV: quality assessment, artifact detection, correction, pipeline

Status: **code + 60 new tests complete (415 total pass). Behaviour on real SD-Turbo output NOT evaluated.** With P5A this covers all five mandatory CV capabilities (resize, colour/enhancement, edge-aware, quality assessment, artifact detection) as implemented and tested on synthetic images. Optional NIQE was not implemented (no validated implementation available; it was optional).
Everything below defaults to **off**: `CV_MODE=off` leaves the service exactly as in P4.

## 1. Modules
| Piece | Where | What it does |
|---|---|---|
| Quality measurements | `computer_vision/quality/metrics.py` | `assess_quality(img) -> QualityReport`: sharpness (Laplacian variance), blur_ratio (re-blur on a denoised copy), brightness, contrast, saturation, noise_sigma (robust per-channel Immerkaer/MAD), clipped dark/bright fractions, colour_cast (gray-world), edge_density, gradient_p99 (structure), halo_score + halo_edges |
| Artifact flags | `computer_vision/artifacts/detect.py` | `detect_artifacts(img, thresholds, suppress) -> ArtifactReport` with flags `blur, noise, dark, bright, low_contrast, colour_cast, clipped_shadows, clipped_highlights, halo`; each flag carries value, threshold, `correctable`, note |
| Correction | `computer_vision/artifacts/correct.py` | `correct_artifacts(img, thresholds, suppress)`: order denoise -> white balance -> exposure -> contrast -> sharpen; each step kept only if its target measurement improves by >= 10 % AND no new flag appears (denoise may not be blamed for `blur`, the sharpen step is judged on its own); every step logged with accept/reject reason; before/after reports returned |
| Semantic review | `computer_vision/artifacts/semantic.py` | `semantic_review(...)` and `intent_suppressions(...)`: prompt-derived risk flag and look-protecting suppressions. **Never looks at pixels** |
| Pipeline | `computer_vision/pipeline.py` | `run_pipeline(img, CVPipelineConfig, semantic)`: resize -> enhance -> smooth -> sharpen -> correct, each toggleable; default = measure only |
| Service hook | `backend/app/services/generation.py`, `config.py` | `CV_MODE=off\|assess\|correct` |

## 2. Service behaviour (`CV_MODE`)
- `off` (default): nothing runs; `quality` and `performance.cv_ms` stay null.
- `assess`: image untouched; `quality = {sharpness, brightness, contrast, artifact_flags}`, `cv_ms` filled. `sharpness` = Laplacian variance (0..255 scale, unbounded, content- and resolution-dependent, inflated by noise). `brightness`/`contrast` = mean/std of luma in 0..1. `clip_score` stays null.
- `correct`: as `assess` plus guarded correction; **the saved/served PNG is the corrected image and the original is not kept**; `quality` describes the final image.
- `artifact_flags` = pixel flags of the final image, plus `semantic_review_recommended` when the prompt asks for counts, spatial relations (any one, e.g. "on a cliff"), several objects with attributes, or anatomy/text. That flag is a prompt-risk heuristic, fires often, and means "a human should look", not "this image is wrong".
- Prompt intent: night/dark words suppress `dark, low_contrast, clipped_shadows, colour_cast`; tint words (sunset, neon, underwater, sepia...) suppress `colour_cast`. Suppressed flags are hidden from the response and not corrected.
- A CV failure never breaks generation: the original image is served and `quality`/`cv_ms` are null (logged server-side). `end_to_end_ms` includes CV time.
- API schema unchanged (v1.0.0). Needs numpy + opencv at runtime only when `CV_MODE != off` (lazy import).

## 3. What is NOT handled (by design)
Semantic defects (wrong object, count, relation, anatomy, garbled text) are flagged for review/regeneration, never "fixed" by filters. Clipped shadows/highlights and halos are flagged but not corrected (information lost / no deconvolution implemented). Flags are not a quality score.

## 4. Evidence and limits (synthetic only; see `evaluation/results/p5b/report.md`, `cases.png`)
- **All thresholds are provisional and were set while looking at synthetic images like the test cases.** "Flag raised on its own degradation" is a sanity check, not a detection rate.
- Noise estimate tracks true sigma on synthetic noise (4 -> 4.0, 8 -> 8.2, 15 -> 15.1) but dense fine texture or intended film grain reads as noise (report case "INTENDED fine grain": denoise was accepted).
- `blur_ratio` separates sharp (<= 0.26) from soft (>= 0.40) on synthetic images, also with noise up to sigma 15; the margin is small. Smooth skies are not called blurry (structure guard `gradient_p99 >= 4`).
- Halo detection only judges hard, roughly axis-aligned edges with flat plateaus; thin lines, soft/textured/noisy edges are skipped (a first version mistook blurred thin lines for halos; fixed and tested). With heavy noise it returns "no evidence" (0.0).
- Correction results on the synthetic set: denoise accepted and clearly lowers noise; white balance and exposure accepted where flagged; **conservative sharpening never repaired blur** (rejected: not enough gain) so blur stays flagged; contrast (CLAHE) often rejected. Looking at `cases.png`: exposure on the dark image gave a lifted, greyish result; on the dark+noisy case the accepted contrast step left visible grain; the overexposed case became more saturated while still clipped. Accepted means "the target number moved without creating a new flag", not "looks better".
- Prompt-aware suppression works for the synthetic night/underwater cases; without the hint the same images are brightened / white-balanced even though the look may be intended.
- Timing in the 1-core sandbox, 512x512: assess ~65 ms, correct ~300-330 ms. Not representative of the laptop; `cv_ms` will tell.
- OpenCV tested on 5.0.0 only.

## 5. Run
```
python -m pytest -q
python evaluation/scripts/report_cv_p5b.py        # writes evaluation/results/p5b/{report.md,report.json,cases.png}
$env:CV_MODE="assess"; uvicorn backend.app.main:app --port 8000     # or "correct"
```
Recommended order of use once real images exist: run with `CV_MODE=assess` first, look at the flags on real generations, then decide thresholds and whether `correct` should ever be on.
