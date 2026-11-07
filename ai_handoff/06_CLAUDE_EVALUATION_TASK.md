# Claude task — Evaluation and benchmark harness

## Objective
Create reproducible evaluation scripts for CLIP similarity, FID or a justified alternative, latency, memory and model size.

## Requirements
- Fixed, versioned prompt list and seeds.
- Record model revision, scheduler, steps, resolution, precision, environment and sample count.
- Separate model loading from generation latency.
- Warm up and repeat runs; report median/mean and spread.
- Measure GPU peak allocated/reserved memory when supported and process RAM separately.
- Report model/adapter file sizes.
- FID must be dataset-level with documented real/generated samples; do not compute or present a misleading tiny-sample score.
- Never fabricate data. Missing measurements remain null/blank.

## Acceptance
- Unit tests for aggregation and report generation.
- Reproducible command.
- CSV/JSON raw output and Markdown summary.
- Clear limitations.

## Return
ZIP-ready scripts, tests, prompt manifest template, README and report template.
