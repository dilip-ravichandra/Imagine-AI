# P2 — Prompt intelligence (task README)
Adds a deterministic prompt parser (`ai_engine/prompt/`), a versioned 87-prompt suite, an additive `POST /api/v1/prompt/analysis` endpoint, blank-prompt validation, and a logging-only hook in `GenerationService`.
Full rules, schema, results and limitations: `docs/PROMPT_PARSER.md`.

## Run / test (Windows PowerShell, from repo root; Python 3.10+)
```
python -m pytest -q
python evaluation/scripts/run_prompt_suite.py
```
## Integration
Unzip over the P1A repo (it contains the full P1A tree). Changed P1A files: `backend/app/main.py`, `backend/app/services/generation.py`, `backend/app/schemas/v1.py`, `docs/API_CONTRACT_v1.md`, `README.md`, `PHASE_TRACKER.md`. If you changed those locally, merge by hand (small diffs; see FILES_CHANGED.txt).
