# Claude task — Classical computer vision pipeline

## Objective
Implement the five required CV capabilities as separate, testable modules.

## Allowed files
`computer_vision/`, tests, module documentation.

## Required modules
1. Resize/resolution optimization.
2. Colour correction/enhancement.
3. Edge-aware post-processing.
4. Image quality assessment.
5. Artifact detection/correction.

## Requirements
- Use OpenCV where appropriate.
- Keep functions composable and parameters explicit.
- Provide safe bypass/no-op behavior.
- Do not use aggressive defaults.
- Separate semantic defects (wrong object/count/relation) from low-level visual artifacts.
- Report before/after indicators; do not promise that filters fix semantic generation errors.

## Acceptance
- Unit tests with synthetic and sample images.
- Verify image dimensions, dtype, channels, and output validity.
- Tests show that processing does not unexpectedly destroy edges/colour.
- Include a small demo script and documented outputs.

## Return
ZIP-ready module, tests, README, changelog, requirements and limitations.
