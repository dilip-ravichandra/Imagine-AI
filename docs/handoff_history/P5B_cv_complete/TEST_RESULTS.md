# TEST_RESULTS (P5B) — build sandbox: Ubuntu 24.04, Python 3.12.3, OpenCV 5.0.0, numpy 2.5.4, 1 CPU core, no GPU, no torch/diffusers
| Command | Status | Notes |
|---|---|---|
| `python -m pytest -q` | PASSED | 415 passed, 1 skipped (real-model smoke, skipped by design); 355 earlier tests unchanged and green, +60 new |
| Same command in a fresh unzip of this ZIP | PASSED | 415 passed, 1 skipped |
| Quality metrics tests (noise estimate vs true sigma within 15 %, blur ratio with/without noise, halo cases, structure guard) | PASSED | synthetic images only |
| Artifact detection / correction tests (each degradation -> its flag; clean -> none; accept/reject logic incl. a harmful step; suppression; unfixable flags stay flagged) | PASSED | synthetic |
| Pipeline tests (default measure-only, bypass identity, stage order, semantic flag never pixel-fixed) | PASSED | |
| Backend integration with a fake engine (`CV_MODE` off / assess / correct, prompt-derived semantic flag, intent suppression, CV failure falls back to the original) | PASSED | fake engine, not real SD-Turbo |
| `python evaluation/scripts/report_cv_p5b.py` | PASSED | ran; table + `cases.png` committed. Visual check: mixed (see docs/P5B_CV.md section 4) |
| Timing, 512x512, 1 core | MEASURED (sandbox only) | assess ~65 ms, correct ~300-330 ms; not representative of the laptop |
| CV behaviour/thresholds on real SD-Turbo images | NOT RUN | no real generation exists yet |
| `cv_ms` on the laptop, Windows run, Android build, P4 benchmarks, real smoke test | NOT RUN | unchanged from earlier phases |
| OpenCV 4.9-4.x compatibility | NOT RUN | tested on 5.0.0 only |
