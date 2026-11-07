# P5B — Classical CV: quality, artifacts, correction, pipeline (task README)
Adds `computer_vision/quality` (measurements), `computer_vision/artifacts` (flags, guarded re-assessed correction, prompt-derived semantic review), `computer_vision/pipeline.py` (per-stage toggles), a `CV_MODE=off|assess|correct` hook in the service (default off), 60 tests and a synthetic before/after report. API schema unchanged. **Behaviour on real SD-Turbo output is not evaluated; every threshold is provisional.** Details, evidence and limits: `docs/P5B_CV.md`.

## Run / test (Windows PowerShell, repo root; Python 3.10+)
```
python -m pytest -q
python evaluation/scripts/report_cv_p5b.py
$env:CV_MODE="assess"; uvicorn backend.app.main:app --port 8000
```
## Integration
`CV_MODE=assess` fills `quality` + `performance.cv_ms`, image untouched. `CV_MODE=correct` also serves the corrected PNG (original not kept).
