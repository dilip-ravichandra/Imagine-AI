# Claude task — Prompt intelligence

## Objective
Build a lightweight prompt-analysis module for objects, attributes, relations, environment, lighting and style.

## Allowed files
`ai_engine/prompt/`, tests, module documentation.

## Requirements
- Preserve original prompt.
- Return a structured, serializable representation.
- Handle multi-object prompts and common relations: beside, behind, above, below, left/right, in front of, inside.
- Include confidence/unknown handling; do not invent missing attributes.
- Begin with deterministic/rule-based parsing or a small dependency. Do not introduce a large LLM without a measured rationale.
- Do not claim that parsing guarantees the diffusion model will render relations correctly.

## Acceptance
- Tests cover simple, multi-object, attribute, relation, ambiguous, empty, and long prompts.
- Stable output schema and example JSON.
- Explain parser limitations.

## Return
ZIP-ready module, tests, README, changelog, dependency list, integration instructions.
