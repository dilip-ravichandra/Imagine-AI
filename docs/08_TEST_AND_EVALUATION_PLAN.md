# 8. Testing and Evaluation Plan

## 8.1 Test layers
1. Unit tests: prompt parsing, controller rules, CV functions, schema validation.
2. Component tests: model loading, generation, post-processing, metric calculation.
3. Integration tests: Android → API → inference → image response.
4. System tests: complete user flow, error states, low-resource fallback.
5. Acceptance tests: every requirement ID in `02_REQUIREMENTS_TRACEABILITY.md`.
6. Demo tests: unseen prompt, clean startup, live URL from phone/laptop.

## 8.2 Prompt benchmark set
Create and version a fixed set containing:
- Simple single-object prompts.
- Two-object prompts with distinct colours/materials.
- Three-or-more object prompts.
- Spatial relations: left/right, above/below, in front/behind, beside/inside.
- Environment/background and lighting.
- Style and texture.
- Long/complex prompts.
- Ambiguous prompts.
- Unseen prompts reserved for final evaluation.

Record exact prompt text, seed, model revision, scheduler, resolution, precision, and steps. Use the same prompts/seeds/settings when comparing variants, except for the variable intentionally changed.

## 8.3 Metrics

### CLIP text-image similarity
Use normalized text and image embeddings and cosine similarity:

`similarity = (T · I) / (||T|| × ||I||)`

Higher generally indicates stronger broad text-image alignment. It is not proof of correct object count or spatial relation. State the CLIP model/version and preprocessing.

### FID
FID compares feature distributions of real and generated image sets; lower is generally better. It requires an adequately sized and representative set. Report real/generated sample counts, dataset, feature extractor, and implementation. If sample size is too small or assumptions are unsuitable, do not overclaim FID; use a justified alternative and explain why.

### Latency
Measure separately:
- Model loading/startup.
- Prompt encoding.
- Denoising.
- VAE decode.
- CV post-processing.
- End-to-end request.

Use warm-up runs, repeated measurements, and report median/mean plus spread (e.g. standard deviation or percentiles). State whether model load is included.

### Peak memory
Record:
- GPU allocated and reserved peak memory where available.
- Process/system RAM peak.
- Device/runtime context.
State measurement method and hardware. Do not mix VRAM and system RAM.

### Model size
Report:
- Base model download/storage size.
- Adapter size.
- Optimized/quantized artifact size.
- Total application package size separately.
Do not confuse parameter count with actual download or runtime memory.

### Quality vs compute cost
Compare quality/alignment, latency, peak memory and size. Include a graph/table and discuss trade-offs rather than declaring a winner using one metric.

## 8.4 Required controlled experiments
At minimum:
- Baseline model/configuration.
- Reduced precision versus baseline.
- Reduced steps versus baseline.
- Base versus adapted model.
- CV pipeline off versus on.
- Adaptive modes across resource profiles.
- Fallback under simulated constrained resources.

Change one variable at a time where possible. If two changes are combined, label the combined experiment clearly.

## 8.5 Ablation study template
For every experiment record:
- Hypothesis.
- Changed variable.
- Fixed variables.
- Dataset/prompt subset.
- Hardware/software environment.
- Number of runs/samples.
- Quality/alignment result.
- Latency and memory.
- Interpretation.
- Failure/limitation.

## 8.6 Failure-case analysis
Include examples of:
- Wrong object count.
- Incorrect spatial relationship.
- Missing prompt attribute.
- Anatomy/structure artifacts.
- Over-smoothing or sharpening.
- Colour shifts from enhancement.
- CLIP score not matching human judgement.
- OOM/timeout or slow fallback.
- Mobile export/runtime incompatibility.

Explain what happened, how it was detected, whether corrected, and what remains unsolved.
