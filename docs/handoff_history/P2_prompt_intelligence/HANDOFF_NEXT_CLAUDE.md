# HANDOFF_NEXT_CLAUDE.md
## Project
Imagine AI — P3 Resource-Efficient Text-to-Image Generation.
## Current phase
- Phase ID: P2 Prompt intelligence — Status: COMPLETE (code, tests, docs). P1A remains PARTIAL (real SD-Turbo run NOT RUN). P0/P1B Android unverified.
- Date: 2026-11-07
## Completed in this session
Rule-based prompt parser + schema, 87-prompt versioned suite (67 dev / 20 hold-out), suite runner, additive analysis endpoint, blank-prompt validation, logging-only generation hook, docs.
## Files added/changed
See FILES_CHANGED.txt. Key: `ai_engine/prompt/*`, `evaluation/prompts/prompt_suite_v1.json`, `evaluation/scripts/run_prompt_suite.py`, `backend/app/schemas/prompt.py`, `docs/PROMPT_PARSER.md`; edited `main.py`, `services/generation.py`, `schemas/v1.py`.
## Interfaces/contracts created or changed
New `POST /api/v1/prompt/analysis` (additive). `POST /api/v1/generate`: whitespace-only prompt now 422. `GenerateResponse` unchanged. Version still 1.0.0; both developers must confirm (Android must NOT expect analysis in the generate response). Python API: `ai_engine.prompt.analyze_prompt(str) -> PromptAnalysis` (schema 1.0, parser rules-1.0.0).
## Dependencies/environment
No new packages (pydantic/fastapi already present). Python 3.10+. Sandbox versions as in P1A.
## Tests actually executed
| Command | Status | Notes |
|---|---|---|
| python -m pytest -q | PASS | 244 passed, 1 skipped |
| dev suite | PASS 67/67 | tuned on these |
| hold-out suite | 12/20 | first run; frozen record |
| real SD-Turbo smoke / Windows run / Android build | NOT RUN | |
## Known issues/limitations
Parser limits and the 8 hold-out failures are in `docs/PROMPT_PARSER.md`. Parser does not prove image correctness; CLIP does not prove counts/relations. Gold labels are author-written. No lexicon/POS tagger.
## Decisions made (with reasons)
Engine gets the raw prompt (analysis-derived prompts unvalidated for SD-Turbo); no analysis in the frozen response (Android strict parsing); separate endpoint instead; coreference only for "the X"; negated nouns never become objects (over-negating is safer than inventing an excluded object); hold-out frozen after first run (no tuning on it).
## Exact next task
- Phase ID: **P3A** Adaptation data and training prep (Person 1). Card: `02_PHASE_TASKS/P3A_ADAPTATION_DATA_AND_TRAINING.md`.
- **Blocked on a human step first**: on the RTX 5050 laptop run the P1A smoke test, pin `MODEL_REVISION`, record the scheduler, and read the official SD-Turbo license page. P3A needs "P1A stable model choice".
- In parallel and unblocked: P1B Android vertical slice (Person 2).
- Optional P2.1 (small, only if wanted): fix the 8 failure causes, then add NEW unseen prompts (a second hold-out) before quoting any new accuracy.
## Next Claude must read
1. `01_SHARED_CONTEXT/PROJECT_BRIEF.md` 2. This handoff 3. The P3A card 4. `docs/API_CONTRACT_v1.md`, `README_TASK.md` of P1A (model record in P1A's README_TASK.md, if kept), `backend/app/services/engine.py`.
## Must NOT redo
Scaffold, API schema, engine/service, parser/suite (do not re-tune on the hold-out).
## Missing input
Laptop smoke-test output; torch/CUDA versions; repo URL; phone model; contract sign-off by both developers; whether to keep the new analysis endpoint.
