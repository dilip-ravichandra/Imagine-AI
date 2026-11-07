# Claude task — Resource-Adaptive Quality Controller

## Objective
Implement an explainable, deterministic controller that selects supported generation configurations using measured benchmark profiles.

## Inputs
- Quality mode: quick/balanced/best.
- Available resource profile.
- Requested resolution.
- Supported model/configuration profiles.
- Optional prompt complexity indicator.

## Outputs
- Selected model/configuration.
- Precision, resolution, steps.
- Fallback-used flag.
- Human-readable reason.
- Structured decision log.

## Requirements
- Do not hardcode universal hardware thresholds without calibration.
- Reject configurations that exceed the provided safe profile.
- Fallback only to configurations proven compatible.
- If none are safe, return a clear resource error.
- Keep profile data external/configurable.

## Acceptance
- Unit tests for all modes, no-fit, fallback, missing metrics and deterministic decisions.
- Example benchmark profile fixture.
- Explain how measured profiles are collected.

## Return
ZIP-ready module, tests, README, changelog and integration instructions.
