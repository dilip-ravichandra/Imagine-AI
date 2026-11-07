# 4. Complete Feature Specification

## 4.1 Prompt input and guided prompt understanding
**User capability:** Enter a natural-language prompt.

**Required engine behavior:**
- Accept ordinary and complex prompts.
- Identify multiple objects, attributes, approximate counts, spatial relations, setting, lighting, and style.
- Preserve important wording and avoid silently changing the user's intent.
- Use text tokenizer/encoder embeddings for conditional generation.
- Provide validation for empty, excessively long, or unsupported prompts.
- Optionally provide prompt suggestions/examples; do not make an additional large LLM a dependency unless measured benefit justifies it.

**Tests:** simple prompt; multiple objects; colour/material attributes; left/right/above/below/behind relations; scene and lighting; long prompt; unseen prompt; ambiguous relation.

**Limitation:** CLIP similarity alone does not prove correct object counts or spatial relationships. Add explicit human review or a suitable relation/count evaluation protocol.

## 4.2 Lightweight diffusion generation
- Integrate a compact pretrained diffusion model.
- Use a documented compatible tokenizer, text encoder, denoiser/UNet or architecture, scheduler, and VAE as applicable.
- Expose deterministic seed for reproducibility.
- Keep model revision and license in a model card.
- Handle model download, cache, load errors, GPU OOM, and request cancellation safely.
- Avoid loading several large models simultaneously on the development GPU.

Candidate models to benchmark:
1. **SD-Turbo** — practical first candidate for a fast working pipeline; validate exact supported scheduler and steps.
2. **BK-SDM-Tiny** — compact candidate; measure actual latency, quality and memory.
3. **SD 1.5 + LCM-LoRA** — possible few-step alternative; validate adapter/scheduler compatibility.
4. **SSD-1B** — deprioritize initially due to likely heavier resource demands; only reconsider if profiling supports it.

These are candidates, not guaranteed winners. Select based on measured results, licensing, compatibility, and target-device feasibility.

## 4.3 Meaningful pretrained-model adaptation
Recommended first adaptation: train a compatible LoRA adapter on a licensed image-caption dataset subset.
- Choose dataset (e.g., MS COCO or Flickr30K where license/terms allow intended use).
- Document source, license, preprocessing, number of examples, and filtering.
- Split train/validation before training.
- Avoid leakage between train and validation.
- Save base model revision, LoRA config, training hyperparameters, random seed, and logs.
- Compare base vs adapted model on held-out prompts with fixed generation settings.
- Do not describe downloading an existing adapter as your own training/adaptation.

## 4.4 Inference optimization
Minimum two strategies must be implemented and measured. Recommended starting pair:
1. Reduced precision (FP16 or another supported reduced precision) compared with a suitable baseline.
2. Reduced sampling steps with a compatible scheduler/model configuration.

Additional strategies if compatible and useful:
- Quantization.
- Pruning or knowledge distillation.
- Compact architecture selection.
- Latent-space optimization.
- Efficient attention / memory-efficient attention.
- CPU offload or sequential offload where appropriate, noting it may reduce VRAM but increase latency.

Do not assume every strategy works with every model, GPU, or mobile runtime. Record compatibility and actual result.

## 4.5 Resolution and image sizing
- Provide supported resolution profiles.
- Preserve aspect ratio where possible.
- Use model-compatible dimensions.
- Select resolution based on measured resource profile.
- Use Lanczos/bicubic or other suitable interpolation for resizing.
- Do not upscale low-detail images and claim new semantic detail.

## 4.6 Colour correction and enhancement
Implement conservative options such as:
- Brightness/contrast adjustment.
- Gamma correction.
- White-balance/colour cast adjustment.
- RGB/HSV-based adjustments.
- CLAHE for local contrast where appropriate.

Apply only when quality checks or user choice indicate benefit. Test on images where enhancement is and is not needed.

## 4.7 Edge-aware post-processing
Implement at least one edge-aware method, preferably with a comparison:
- Bilateral filter.
- Guided filter if available.
- Edge-map-guided sharpening or edge-preserving smoothing.
- Sobel/Canny for edge analysis.

Avoid aggressive smoothing that removes texture or fine detail.

## 4.8 Image quality assessment
Use measurable no-reference indicators:
- Sharpness/blur (e.g., variance of Laplacian, with known limitations).
- Contrast.
- Brightness/exposure.
- Saturation/colour distribution.
- Noise indicators.
- Optional NIQE/other no-reference metric only if dependency and validity are established.
- CLIP prompt-image alignment as a separate semantic alignment measure.

Report individual indicators; do not collapse them into an unexplained “AI quality score.”

## 4.9 Artifact detection and correction
Detect or flag:
- Blur/over-smoothing.
- Excessive noise/grain.
- Colour anomalies.
- Edge discontinuities or halos.
- Obvious local image defects where a defensible heuristic exists.

Correction:
- Conservative denoising, sharpening, contrast/colour correction.
- Re-run quality checks after correction.
- If a semantic defect exists (wrong number of objects, extra limbs, incorrect spatial relation), flag it and optionally regenerate with a controlled prompt/seed/configuration. Classical filters cannot reliably repair semantic mistakes.

## 4.10 Resource-Adaptive Quality Controller
Quality modes:
- **Quick:** lowest measured latency/resource configuration that meets a minimum quality guardrail.
- **Balanced:** default trade-off.
- **Best Quality:** highest measured quality configuration within resource limits.

Controller policy:
1. Read available resource indicators and target profile.
2. Find compatible configurations from benchmark profile.
3. Filter configurations that exceed safe memory/storage limits.
4. Rank remaining choices according to quality mode and user constraints.
5. Select configuration and log rationale.
6. Monitor execution; handle OOM/timeouts.
7. Apply fallback sequence and record every change.

Suggested fallback order (must be validated per model):
- Reduce requested output resolution.
- Switch to supported reduced precision.
- Reduce steps only when compatible and quality guardrail permits.
- Switch to a smaller benchmarked model.
- Use a remote backend only if the app explicitly discloses hybrid/cloud processing and network/consent rules are met.
- If no safe option remains, return a clear error rather than crashing.

Do not treat arbitrary thresholds as universal. Calibrate thresholds from actual profiles.

## 4.11 User experience features
Core:
- Prompt entry.
- Quick/Balanced/Best Quality modes.
- Generate action and progress/loading state.
- Result image display.
- Retry and actionable error states.
- Display generation configuration and resource decision.
- Save/share result where platform permissions allow.

Optional enhancements (do not substitute for mandatory P3 work):
- Prompt examples and guided prompt helper.
- Gallery/history.
- Mascot/branding.
- Voice input.
- Indian-language prompts.
- Additional visual themes.

## 4.12 Privacy and reliability
- Do not log secrets or unnecessary personal prompt content.
- Define image retention and deletion behavior.
- Validate file type/size and generated paths.
- Limit request concurrency and rate as appropriate.
- Return safe errors; never expose server stack traces to users.
- Use environment variables/secrets manager for credentials.
