# Prompt parser (P2) — `ai_engine/prompt/`

Deterministic, rule-based analysis of the prompt **text**. No ML, no LLM, no network. Parser `rules-1.0.0`, schema `1.0`.
It reports what the prompt *says*. It does **not** check what the generated image *shows*.

## Use
```python
from ai_engine.prompt import analyze_prompt
a = analyze_prompt("A red robot beside a blue submarine underwater")
a.model_dump(mode="json")      # stable JSON; a.objects, a.relations, a.environment, ...
```
HTTP (additive endpoint, no GPU/model needed): `POST /api/v1/prompt/analysis` with `{"prompt": "..."}`.
Full JSON Schema: `docs/prompt_analysis_schema_v1.json` (a test fails if it drifts from the code).

## Output schema (all keys always present)
| Field | Meaning |
|---|---|
| `raw_prompt` | The input, byte-for-byte (never trimmed or normalised). |
| `validation` | `valid`, `code` (`EMPTY_PROMPT` for empty/whitespace, `TOO_LONG` for >500 chars), `message`. Invalid prompts return no extraction. |
| `objects[]` | `id` (o1..), `name` (singular lemma), `surface`, `count` + `count_kind` (`exact` / `approximate` / `plural_unspecified` / `unspecified`), `quantifier`, `attributes[]` (`color`/`size`/`material`/`other`), `other_modifiers[]` (unclassified words, **not** claimed as attributes), `actions[]`, `frame_position`, `lexicon_match`, `evidence`, `span`. |
| `environment[]` | Places (`forest`, `kitchen`), weather (`snowy`, `rain`) and settings (`underwater`). ids `e1..` / `w1..`. |
| `relations[]` | `subject`, `relation`, `object` (ids; may be null when the prompt gives none), `spatial` (false for `with`), `evidence`, `span`. |
| `lighting[]`, `style[]` | `value`, `kind`, `evidence`, `span`. |
| `negations[]` | Things the prompt says are absent. Never turned into objects. |
| `ambiguities[]` | `code` + `detail` for anything the rules could not decide. |
| `complexity` | `object_count`, `relation_count`, `attribute_count`, `level` (simple/moderate/complex). Heuristic about prompt *structure*, not image difficulty or quality. |
| `notice` | Fixed limitation text (below). |

Every extracted item carries `span = [start, end)` into `raw_prompt` and `evidence = raw_prompt[start:end]`; tests check this for every suite prompt and 600 fuzzed inputs. That is how "never invent absent details" is enforced.

## Rules (summary)
- **Relations**: beside / next to / alongside / adjacent to -> `beside`; behind / in back of -> `behind`; in front of -> `in_front_of`; above / over -> `above`; below / beneath / underneath / under -> `below`; to the left of / on the left of / left of -> `left_of` (same for right); inside / within / in -> `inside`; on / on top of / atop -> `on`; near / close to / by -> `near`; with -> `with` (`spatial:false`). Longest phrase wins ("in front of" is never "in" + "of").
- **In/at/on + a scene noun** ("in a forest", "on a beach") is a *setting*: recorded in `environment`, no relation.
- **Counts**: `a/an/the` + singular = exactly 1; numerals/number words; `a pair of`=2, `a couple of`=2 (approximate), `a dozen`=12; `several/many/a few/a flock of ...` = approximate (count null); bare plural = `plural_unspecified`; bare singular or mass noun = `unspecified`. Counts are never guessed.
- **Coreference**: only "the X" (singular, no modifiers) after an earlier X reuses that object.
- **Negation**: `no / not / never / without` marks following noun phrases as absent; ", and ..." ends the scope; carry-over into an item with its own article is flagged `NEGATION_SCOPE`.
- **Time-of-day words** (night, morning...) count as lighting only after a preposition ("at night"). "a night owl" claims no lighting.
- **Ambiguity codes**: `ALTERNATIVES` (a or b), `VAGUE_NOUN`, `PRONOUN`, `UNSUPPORTED_RELATION` (between, around, into, "in the middle of"...), `RELATION_ATTACHMENT` (chained prepositions), `RELATION_SCOPE` (relation after "a and b"), `RELATION_MISSING_SUBJECT/OBJECT`, `OVER_AMBIGUOUS`, `BY_AMBIGUOUS`, `STYLE_OR_ATTRIBUTE`, `STYLE_REFERENCE_EMPTY`, `NUMBER_AMBIGUOUS` (sheep/fish), `FRAME_POSITION_NO_SUBJECT`, `NEGATION_SCOPE`, `NO_OBJECTS_FOUND`, `UNSUPPORTED_LANGUAGE`.

## Test suite — `evaluation/prompts/prompt_suite_v1.json` (87 prompts)
Categories: simple (5), multi_object (8), attributes (10), relations (17), scene_lighting (12), ambiguous (14), long (1) = **67 dev**, plus **20 hold-out** ("unseen").
Run: `python -m pytest -q` (every dev case is a test) or `python evaluation/scripts/run_prompt_suite.py [dev|holdout]`.
Gold annotations are author-written; the author is also the parser's author.

### Results (honest numbers)
- **Dev: 67/67.** The parser was tuned on these, so this shows regression safety, not accuracy.
- **Hold-out, FIRST run: 12/20 (60%).** Gold was written before the parser ever saw these prompts. Frozen in `evaluation/results/prompt_suite_v1_holdout_first_run.json`. The parser was **not** changed after this run. This 60% is the figure to quote for unseen prompts. Do not re-quote the hold-out after tuning; write new unseen prompts instead.

| Hold-out failure | Cause |
|---|---|
| unseen-01 wizard holding a glowing lantern beside a well | "glowing" read as a verb (-ing rule); preposition attached to nearest noun (lantern), not the wizard |
| unseen-04 city with flying cars | `with` + participle drops the relation |
| unseen-07 pencil sketch of an old man | "sketch of" matched as a medium before the phrase "pencil sketch" |
| unseen-08 four candles arranged in a row | past participle "arranged" taken as the noun |
| unseen-09 clock tower | compound noun not in the small compound list |
| unseen-12 a teapot and two cups on a tray | relation attaches to the nearest noun only (flagged `RELATION_SCOPE`) |
| unseen-15 hot air balloon | "hot" classified as adjective, breaking the compound |
| unseen-18 "black and white photo" | bare "photo" not in the style list |

## Limitations (read before relying on it)
1. **Not a guarantee of image correctness.** The parser describes the prompt; the image model may ignore counts, colours or relations. CLIP-style alignment scores measure broad text-image similarity and **do not prove** count or spatial-relation correctness. Evaluating those needs object-level checks or human review (P7).
2. English only; small lexicons (colours, sizes, materials, ~180 nouns, ~25 styles). Unknown words are kept as `other_modifiers` or flagged, never guessed into attributes.
3. No part-of-speech tagger: unknown adjective lists ("a fluffy, white cat"), past participles, and compounds outside the list can be mis-parsed.
4. Prepositional phrases attach to the nearest noun phrase (flagged where chained). Relations are binary; "between" is unsupported.
5. Words that are both colour and noun are handled only for "orange"; "golden retriever" reads "golden" as a colour.
6. `complexity.level` is a structural heuristic; it has not been shown to predict generation cost or quality.

## Integration hook (exact)
`backend/app/services/generation.py`, `GenerationService.generate`, the block marked `P2 INTEGRATION HOOK`: `analysis = self.analyze(req.prompt)`.
- The engine always receives the **raw prompt unchanged** (test: `test_engine_receives_raw_prompt_unchanged`). Feeding analysis-derived text to SD-Turbo is unproven and deliberately not done.
- `analysis` is logged (counts only, not the prompt text). A parser exception returns `None` and generation continues.
- The frozen `GenerateResponse` is unchanged (no analysis field, so Android's strict JSON parsing cannot break). Clients that want the analysis call `POST /api/v1/prompt/analysis`.
- Later phases may read `analysis.objects/relations/complexity` (P3B for per-category comparison, P6 as a controller input, P7 for count/relation test sets) **only with measured evidence** that it helps.
