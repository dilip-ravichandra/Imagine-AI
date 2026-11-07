# Imagine AI — Master Project Pack

**Tagline:** Your imagination. Our intelligence.  
**Problem statement:** P3 — Resource-Efficient Text-to-Image Generation for Mobile Devices.

This ZIP is the **master implementation blueprint and project scaffold** for building Imagine AI in controlled phases. It consolidates the requirements, architecture, feature specifications, ownership, AI-assisted ZIP handoff workflow, API contract, testing plan, evaluation methodology, mobile deployment checks, and final deliverables discussed by the team.

> **Important scope note:** This is not a finished text-to-image product and does not contain pretrained model weights, datasets, API keys, or a falsely “working” diffusion implementation. Those are selected, downloaded, trained/adapted, and tested during the relevant phases. The scaffold deliberately marks implementation points rather than pretending untested modules are complete.

## Product goal

Build an Android-facing text-to-image application backed by a resource-aware generation engine. It must:
- Understand prompts, including multi-object prompts, attributes, and spatial relationships.
- Generate images using a lightweight pretrained diffusion model with meaningful project adaptation.
- demonstrate at least two measured optimization strategies.
- Apply all five required classical computer-vision capabilities.
- Adapt generation settings to available compute resources and fall back safely.
- Report measured quality, latency, memory, and model-size results.
- Be honest about whether generation is on-device, hybrid, or cloud-hosted.

## Read this pack in order

1. `docs/01_PROJECT_CHARTER.md`
2. `docs/02_REQUIREMENTS_TRACEABILITY.md`
3. `docs/03_SYSTEM_ARCHITECTURE.md`
4. `docs/04_FEATURE_SPECIFICATION.md`
5. `docs/05_PHASED_IMPLEMENTATION_PLAN.md`
6. `docs/06_TEAM_AND_AI_WORKFLOW.md`
7. `docs/07_API_CONTRACT.md`
8. `docs/08_TEST_AND_EVALUATION_PLAN.md`
9. `docs/09_MOBILE_DEPLOYMENT.md`
10. `docs/10_DEMO_VIVA_AND_DELIVERABLES.md`
11. `docs/11_RISKS_AND_DECISIONS.md`
12. `ai_handoff/` for Claude and Antigravity task prompts.

## Recommended stack

- Android: Kotlin, Jetpack Compose, MVVM, Retrofit/OkHttp.
- Backend: Python, FastAPI, Pydantic.
- AI: PyTorch, Hugging Face Diffusers, Transformers, PEFT/LoRA where compatible.
- Computer vision: OpenCV.
- Evaluation: CLIP alignment, FID where the evaluation set is adequate, latency, peak memory, model size, and quality-cost comparisons.
- Collaboration: one GitHub repository, feature branches, pull requests, tests.
- Training / larger evaluations: Colab or another permitted GPU environment when needed.
- Local development target: NVIDIA RTX 5050 Laptop GPU (~8 GB VRAM) and 24 GB system RAM. Treat this as a constrained development GPU, not as proof of mobile deployment.

## First milestone

Make this end-to-end vertical slice work before building advanced features:

`Android prompt → FastAPI request → diffusion pipeline → generated image → Android display`

Then add adaptation, optimization, CV, adaptive routing, evaluation, and deployment.

## Status convention

Use `[ ]` not started, `[~]` in progress, `[x]` tested and accepted. A feature is not complete merely because code was generated. It must pass its acceptance tests and have evidence.
