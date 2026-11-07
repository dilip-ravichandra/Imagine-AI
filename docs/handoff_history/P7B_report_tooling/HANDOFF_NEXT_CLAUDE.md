# HANDOFF_NEXT_CLAUDE.md
## Project
Imagine AI — P3 Resource-Efficient Text-to-Image Generation (hybrid/cloud inference).
## Current phase
- P7B — **generators done, report CONTENT NOT WRITTEN** (no real results exist). `python evaluation/scripts/build_p7b_report.py --usns U1,U2` writes `eval_P3_<TeamID>.md`, `ablation_study.md`, `failure_analysis.md` into `evaluation/reports/`; exit 1 until no `TODO(team)` remains and the P7 gate is met. Order: real P7A run -> analyze -> fill `p7_human_review.csv` by eye -> build_p7b_report -> team writes interpretations/failure explanations.
- P7A Metrics harness — **COMPLETE for code + tests; NO real measurements.** Still open from before: P4 measured results NOT RUN, P1A real SD-Turbo run NOT RUN, P0/P1B Android unverified, P3A/P3B/P6 skipped (DL-02 still open), P5B (CV quality metrics + artifact detection) NOT done (P5A modules only).
- Date: 2026-11-07
## Completed
`ai_engine/evaluation/` (variants V0-V7, harness, metrics incl. FID gate + prompt-cluster bootstrap, sizes, report, dry-run engine), `run_p7_eval.py`, `analyze_p7_results.py`, `docs/P7A_EVAL.md`, 40 tests. 395 pass, 1 skipped.
## Files
Key: `ai_engine/evaluation/*.py`, `evaluation/scripts/{run,analyze}_p7_*.py`, `docs/P7A_EVAL.md`, `tests/test_p7_*.py`, `tests/p7_helpers.py`.
## Interfaces
`run_variant(variant, engine, prompts, seeds, repeats, warmup, out_dir, environment, ram_fn, clip, clock, suite_info)`; result schema `p7_variant_result/1`. Report: `build_report/render_markdown`. Details: `docs/P7A_EVAL.md`. API v1.0.0 and backend unchanged.
## Dependencies
New: `matplotlib` (plot only, lazy import). CLIP needs `transformers` + weights (requirements-ml.txt), untested in sandbox.
## Tests
| Command | Status | Notes |
|---|---|---|
| python -m pytest -q | PASS | 395 passed, 1 skipped |
| run_p7_eval.py --all --dry-run ... then analyze | PASS (plumbing) | synthetic, gate correctly NOT MET |
| Real GPU run, real CLIP, model size, Windows | NOT RUN | |
## Known issues
No stage-level latency (engine exposes none; stored null). FID not computable (no real reference set, no Inception extractor; gate refuses). Default sample (20 prompts x 3 seeds x 2 repeats) is small, CIs will be wide. V5 tests P5A auto_enhance only. The 20 hold-out prompts are frozen but now seen: demo needs NEW unseen prompts.
## Decisions
Hold-out split is the default eval set; CLIP once per (prompt, seed) from repeat 0; CV effect measured against the same images pre-CV; bootstrap resamples prompts; synthetic results can never satisfy the gate; blocked variants stay listed as NOT RUN; report is mechanical (no verdicts).
## Exact next task
Human step first (laptop): pin `MODEL_REVISION`, run P1A smoke test, then `run_p7_eval.py --only V0 --clip --prompts-per-category 1 --repeats 1 --warmup 1`, then the full `--all --clip` and `analyze_p7_results.py`; also run P4 (`run_p4_benchmarks.py`) since V1-V4 mirror it. Then P7B (Both): fill `eval_P3_TeamID.md` from `evaluation/reports/p7_report.md`, ablation table (docs/08 section 8.5), failure cases from `p7_human_review.csv`; explicitly declare the V6/V7 gaps (DL-02). Optionally P5B first (CV-04/CV-05 still open).
## Next Claude must read
PROJECT_BRIEF.md, this handoff, `docs/P7A_EVAL.md`, `docs/08_TEST_AND_EVALUATION_PLAN.md`, `evaluation/reports/p7_report.md` (once real).
## Must NOT redo
Scaffold, API schema, engine/service, prompt parser, P4 harness, P5A modules, P7A harness (extend, do not rewrite).
## Missing input
Real SD-Turbo images, GPU results, MODEL_REVISION, real FID reference set (if FID is wanted), repo URL, phone model, contract sign-off, team USNs.
