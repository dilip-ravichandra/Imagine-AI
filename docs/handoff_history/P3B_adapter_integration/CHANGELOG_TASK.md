# CHANGELOG P2
- Added `ai_engine/prompt/{schema,lexicon,parser,suite}.py`: rule-based analysis (objects, counts, attributes, relations, environment, lighting, style, negations, ambiguities, complexity) with span/evidence for every item.
- Added `evaluation/prompts/prompt_suite_v1.json` (67 dev + 20 hold-out), `evaluation/scripts/run_prompt_suite.py`, results + frozen hold-out first-run record.
- Added `POST /api/v1/prompt/analysis` and `backend/app/schemas/prompt.py` (additive).
- `GenerateRequest.prompt`: whitespace-only now rejected (422).
- `GenerationService`: analysis computed and logged (counts only); engine still receives the raw prompt; parser errors cannot break generation.
- Added `docs/PROMPT_PARSER.md`, `docs/prompt_analysis_schema_v1.json`; contract doc + README updated.
- Tests: +209 (parser, evidence integrity, fuzz, suite, API integration). Total 244 passed, 1 skipped.
