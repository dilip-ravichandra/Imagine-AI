# 2. Requirements and Traceability

This checklist consolidates the P3 requirements and the additional product, evaluation, and delivery requirements discussed by the team.

| ID | Requirement | Planned implementation | Evidence / acceptance |
|---|---|---|---|
| CV-01 | Image resizing and resolution optimization | Resolution policy; interpolation choices such as Lanczos/bicubic; aspect-ratio handling | Unit tests and before/after examples |
| CV-02 | Colour correction and enhancement | Conditional brightness/contrast, gamma, white balance, HSV and CLAHE tools | Test images, parameter logs, visual comparison |
| CV-03 | Edge-aware post-processing | Bilateral/guided filtering, edge maps, edge-preserving sharpening | Edge preservation tests and visual comparison |
| CV-04 | Image quality assessment | Sharpness/blur, contrast, brightness, saturation, noise indicators; optional NIQE if compatible | Metric report and known-good/poor image tests |
| CV-05 | Artifact detection and correction | Heuristic detection; safe denoise/sharpen/colour correction; flag/regenerate semantic defects | Detection tests, correction tests, failure examples |
| DL-01 | Lightweight diffusion-based text-to-image architecture | Integrate a compact compatible pretrained diffusion pipeline | Reproducible generation test |
| DL-02 | Pretrained model with meaningful adaptation | Train a compatible LoRA or another documented adaptation on licensed data | Training config, split, adapter artifact, held-out comparison |
| DL-03 | Optimized inference pipeline | Inference mode, efficient attention if supported, controlled transfers, component reuse | Profiling report |
| DL-04 | Prompt encoding and conditional generation | Tokenizer/text encoder, conditioning embeddings, denoising, VAE decode | Prompt-to-image tests |
| OPT-01 | At least two optimization strategies | Minimum: reduced precision where supported and fewer sampling steps; consider quantization or compact model | Controlled benchmark and ablation |
| OPT-02 | Compare optimized and baseline performance | Same prompts/seeds/resolution where isolating variables | Comparison table/plots |
| OPT-03 | Demonstrate resource needs for mobile target | Full pipeline storage, memory, latency and compatibility analysis | Actual-device/export report |
| ADV-01 | Complex prompts | Multi-object, attributes, spatial relationships, environment and lighting | Fixed and unseen prompt suite |
| ADV-02 | Semantic consistency | CLIP alignment plus explicit relation/count review | Scores and human-reviewed failure cases |
| ADV-03 | Reduce latency and memory | Optimizations and adaptive controller | Measured latency/memory |
| ADV-04 | Analyze quality degradation | Change one optimization variable at a time | Ablation study |
| ADV-05 | Adaptive generation | Select settings using resource profile and quality mode | Decision logs and tests |
| ADV-06 | Fallback for constrained devices | Lower resolution/steps or supported smaller configuration; clear failure if no safe option | Simulated low-resource tests |
| EVAL-01 | CLIP similarity | Text/image embedding cosine similarity | Script, version, dataset/prompt details |
| EVAL-02 | FID or justified distribution metric | FID only with adequate, documented real/generated samples; otherwise justify a suitable alternative | Metric protocol and sample count |
| EVAL-03 | Generation latency | Model-load, encode, denoise, decode, CV, end-to-end timings | Repeated measurements and summary stats |
| EVAL-04 | Peak memory | GPU allocated/reserved and process/system memory | Method, hardware, peak values |
| EVAL-05 | Model size | Base weights, adapter, optimized weights, download size | File-size report |
| EVAL-06 | Quality vs compute cost | Compare quality, time, memory, size | Table and plots |
| APP-01 | Android user interface | Compose screens, prompt entry, quality mode, progress, results | Device/emulator demo |
| APP-02 | Backend integration | API request, image retrieval, error handling | Integration tests |
| APP-03 | User-visible resource explanation | Show selected configuration and fallback reason | UI/API test |
| DEL-01 | Live hosted app URL | Deploy backend/frontend as architecture permits | Publicly reachable URL tested on phone/laptop |
| DEL-02 | Complete GitHub source | One repository, setup instructions, no secrets | Clean clone setup |
| DEL-03 | Architecture diagram | Component and data-flow diagrams | `docs/diagrams/` |
| DEL-04 | Design document | Architecture, decisions, setup, models, data, limitations | Reviewed document |
| DEL-05 | `eval_P3_TeamID.md` | First line: all team USNs comma-separated | Final file checked |
| DEL-06 | Ablation and failure analysis | Controlled experiments and documented failure cases | Reports and example outputs |
| DEL-07 | 3-minute demo and viva | Unseen prompt, measured results, explanation by both members | Rehearsed demo |

## Definition of done
A row is complete only when implementation, test/evidence, and documentation exist. Mark the row `[x]` only after another team member has reviewed the evidence.
