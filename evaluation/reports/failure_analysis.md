# Failure-case analysis (P7B)

Source: Evaluation suite across hold-out prompts and classical CV degradations.
Each category documents observed behaviors, detection mechanism, mitigation/correction, and current status.

## Required categories (docs/08 section 8.6)

### 1. Wrong object count
- **Observed Case:** In prompt `unseen-08` ("four candles arranged in a row on a dark table"), seeds 5678 and 9012 rendered 3 and 5 candles respectively instead of exactly four.
- **Detection:** Human visual review sheet; CLIP similarity does not penalize count mismatch (CLIP scored 0.334 despite count error).
- **Correction / Mitigation:** Increasing steps from 1 to 4 improves object separation; full count precision requires layout conditioning (e.g. bounding boxes or ControlNet).
- **Status:** Unsolved in single-pass text-only diffusion models without spatial layout guidance.

### 2. Incorrect spatial relationship
- **Observed Case:** In prompt `unseen-01` ("a wizard holding a glowing lantern beside an old stone well"), seed 1234 rendered the lantern floating between the wizard and the well rather than being held.
- **Detection:** Human inspection of spatial relations column in review sheet.
- **Correction / Mitigation:** The prompt parser extracts spatial tokens ("beside", "holding"), allowing the server to recommend higher step counts (balanced/best mode).
- **Status:** Inherent limitation of cross-attention in single-stage distilled text-to-image architectures.

### 3. Missing prompt attribute
- **Observed Case:** In prompt `unseen-07` ("a pencil sketch of an old man with a long beard"), seed 9012 produced a sepia photographic texture rather than a pure monochrome pencil sketch.
- **Detection:** Visual review and low style adherence.
- **Correction / Mitigation:** Weighting style keywords or prefixing style tokens in the prompt analyzer.
- **Status:** Partially mitigated by prompt structure; distilled models prioritize semantic subject over subtle style modifiers.

### 4. Anatomy and structure artifacts
- **Observed Case:** In prompt `unseen-06` ("an astronaut riding a horse on the moon"), the rider's legs and saddle interface show blended structural geometry at 1 step (V3).
- **Detection:** Visual inspection and artifact flagging.
- **Correction / Mitigation:** Increasing denoising steps to 2 (V4) or 4 (V0) cleanly delineates rider anatomy and horse harness.
- **Status:** Resolved by setting recommended quality mode to `balanced` (2 steps) or `best` (4 steps).

### 5. Over-smoothing or sharpening
- **Observed Case:** Aggressive unsharp masking without halo suppression produced ringing artifacts around high-contrast edges (e.g., lamp posts and silhouettes in P5B test case).
- **Detection:** Laplacian edge gradient variance and halo detector in `computer_vision/edge_aware.py`.
- **Correction / Mitigation:** Added `halo_guard=True` and bilateral filtering with edge-preserving clamping.
- **Status:** Resolved in classical CV post-processing pipeline.

### 6. Colour shifts from enhancement
- **Observed Case:** In dark nighttime scenes (`unseen-04`) and underwater prompts (`unseen-10`), naive global histogram equalization or gray-world white balance stripped the intentional blue/dark color cast.
- **Detection:** Measured mean saturation and color cast shift in `computer_vision/quality.py`.
- **Correction / Mitigation:** Implemented prompt intent suppression (`intent_suppressions`) in `computer_vision/artifacts.py`: when keywords like "night", "underwater", "dusk" are detected, color cast and low-contrast flags are suppressed.
- **Status:** Resolved.

### 7. CLIP score not matching human judgement
- **Observed Case:** In prompt `unseen-02` ("two penguins standing on an iceberg under a pink sky"), an image with 3 penguins scored higher CLIP cosine similarity (0.342) than an image with exactly 2 penguins (0.329).
- **Detection:** Comparison of paired CLIP metrics against human review sheet ground truth.
- **Correction / Mitigation:** Acknowledged in project documentation: CLIP is used strictly as a broad text-image alignment indicator, not a definitive verification of counts or spatial logic.
- **Status:** Documented known limitation of contrastive vision-language embeddings.

### 8. OOM, timeout, or slow fallback
- **Observed Case:** Requesting 768x768 resolution at fp32 with 4 steps consumes 7.11 GB VRAM (87% of laptop GPU capacity) and 3,723 ms latency.
- **Detection:** GPU allocation tracking in `ai_engine/adaptive/resources.py`.
- **Correction / Mitigation:** The P6 adaptive controller automatically detects resource constraints and steps down resolution (e.g. 768px -> 640px or 512px) or switches precision to fp16, keeping latency under 300 ms and VRAM under 3.7 GB.
- **Status:** Resolved via adaptive controller and fallback ladder.

### 9. Mobile export and runtime incompatibility
- **Observed Case:** Running the full SD-Turbo diffusion pipeline (UNet, text encoder, VAE, scheduler) directly on a mobile Android device crashes due to RAM limits (requiring >3.5 GB VRAM/RAM) and missing float16 NPU acceleration.
- **Detection:** Mobile feasibility analysis (P8).
- **Correction / Mitigation:** Adopted a hybrid client-server deployment model: the mobile device runs a lightweight Jetpack Compose client that handles UI, user input, and image display, while the GPU laptop executes FastAPI inference.
- **Status:** Resolved by architectural design.
