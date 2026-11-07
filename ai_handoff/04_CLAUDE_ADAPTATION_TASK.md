# Claude task — Pretrained-model adaptation plan and training code

## Objective
Prepare a reproducible, resource-conscious LoRA adaptation workflow for the selected compatible diffusion model.

## Requirements
- First verify the exact model/adapter training compatibility and license.
- Use a licensed image-caption dataset and document terms.
- Split train/validation before training.
- Provide dataset manifest and preprocessing; do not bundle restricted dataset files.
- Provide configurable training parameters and deterministic seed.
- Save adapter, training config, logs and base model revision.
- Provide inference comparison script using fixed prompts/seeds/settings.
- Do not claim training succeeded unless actually run.

## Acceptance
- Dataset preparation tests.
- Training command and environment documented.
- Validation is held out.
- Base-versus-adapted evaluation is reproducible.
- GPU memory estimate is clearly labelled as estimate unless measured.

## Return
Training scripts, config, README, tests, changelog and known limitations. Do not include large model weights or datasets in the ZIP.
