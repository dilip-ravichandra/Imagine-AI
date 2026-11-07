# TEST_RESULTS (P7A) — build sandbox: Ubuntu 24.04, Python 3.12.3, OpenCV 5.0.0, numpy 2.5.4, no GPU, no torch/diffusers
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASSED | 401 passed, 1 skipped (real-model smoke, skipped by design); 355 earlier tests unchanged and green, +40 P7A and +6 P7B tests |
| P7A tests: metric maths (cosine, Frechet incl. closed-form cases, FID gate, paired deltas, clustered bootstrap), variant registry rules, size report, harness protocol (counts, warm-up, clock-injected latency, CV separate, OOM recorded, blocked refused), report gate/synthetic exclusion/CSV/sheet/plot, CLI | PASSED | fakes and stub CLIP only; fixture values are not results |
| `run_p7_eval.py --all --dry-run --split dev --limit 4` then `analyze_p7_results.py` | PASSED (plumbing) | synthetic engine; report says SYNTHETIC and gate NOT MET, as designed |
| Real SD-Turbo run, real CLIP scoring (`ClipScorer`), GPU memory, model size on a real snapshot | NOT RUN | no GPU/weights in sandbox |
| Any measured latency/memory/CLIP/FID number | NONE EXIST | nothing in this ZIP may be cited as a result |
| Windows/PowerShell run | NOT RUN | commands written for it, unverified |
| P4 benchmarks, P1A smoke test, Android build | NOT RUN | unchanged from earlier phases |
| `build_p7b_report.py` on empty results | PASSED (skeleton) | all results NOT RUN, TODO markers present, exit 1 as designed |
| Real P7B report content | NOT WRITTEN | depends on real measurements and human review |
