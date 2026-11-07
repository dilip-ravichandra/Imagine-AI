# Claude task — Diffusion engine baseline

## Objective
Implement the first minimal, reproducible lightweight diffusion inference module for Imagine AI.

## Read first
- `docs/03_SYSTEM_ARCHITECTURE.md`
- `docs/04_FEATURE_SPECIFICATION.md` sections 4.2–4.4
- `docs/07_API_CONTRACT.md`

## Allowed files
`ai_engine/models/`, related tests, module README, dependency notes.

## Requirements
- Use Hugging Face Diffusers and a selected compatible pretrained lightweight model.
- Make model ID/revision configurable; do not silently substitute another model.
- Support prompt, seed, width/height, steps, and precision only where supported.
- Include model load and generation timing separately.
- Include clear CPU/GPU selection and CUDA/OOM error handling.
- Avoid loading multiple large pipelines.
- Add a small smoke test that can be run only when model access/hardware is available, plus unit tests that do not download weights.
- Document model license and expected memory caveats; do not invent benchmark values.

## Acceptance
- Module imports in a clean environment.
- Unit tests pass.
- Smoke-test command is documented.
- A real output can be generated when the selected model is available.
- Output includes actual configuration and seed.

## Return
ZIP-ready folder, README, tests, requirements, CHANGELOG, known limitations, files changed, and actual test log or explicit statement that execution was not possible.
