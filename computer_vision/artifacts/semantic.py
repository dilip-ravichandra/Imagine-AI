"""Semantic defects (wrong objects, counts, relations, anatomy, rendered text) CANNOT be seen or fixed by classical
pixel filters. This module therefore does not look at pixels: it turns the PROMPT's structure into a
'human review / regeneration recommended' risk flag. It is a risk heuristic, not a detection of a defect.
Pure strings/ints in, so computer_vision stays independent of ai_engine and backend."""
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

SEMANTIC_FLAG = "semantic_review_recommended"
_RISKY_NOUNS = frozenset("""person people man men woman women child children kid kids baby boy girl human crowd
hand hands finger fingers face faces portrait body arm arms leg legs text sign letters words logo writing""".split())
# prompt words that ask for an intentionally dark / tinted look -> do not "correct" exposure or colour
_DARK_WORDS = frozenset("night nighttime midnight moonlight moonlit dark dim gloomy shadowy candlelight candlelit "
                        "dusk twilight blue_hour low_light silhouette".replace("_", " ").split())
_TINT_WORDS = frozenset("sunset sunrise dawn golden neon underwater sepia monochrome vintage foggy misty "
                        "warm cold".split())


@dataclass(frozen=True)
class SemanticReview:
    recommended: bool
    reasons: tuple[str, ...]
    note: str = ("Derived from the prompt text only; no pixels were examined. It says the prompt asks for things "
                 "diffusion models often get wrong, not that this image is wrong.")


def semantic_review(object_names: Sequence[str], counts: Sequence[Optional[int]], spatial_relations: int,
                    objects_with_attributes: int) -> SemanticReview:
    reasons = []
    multi = [(n, c) for n, c in zip(object_names, counts) if c is not None and c >= 2]
    if multi:
        reasons.append("count requested (" + ", ".join(f"{c} {n}" for n, c in multi) + "); generated counts are not verified")
    if spatial_relations >= 1:
        reasons.append("spatial relation requested; placement is not verified")
    if objects_with_attributes >= 2:
        reasons.append("several objects with their own attributes; attribute mix-ups are not verified")
    risky = sorted({n.lower() for n in object_names} & _RISKY_NOUNS)
    if risky:
        reasons.append("anatomy or rendered text requested (" + ", ".join(risky) + "); hands, faces and lettering are often malformed")
    return SemanticReview(bool(reasons), tuple(reasons))


def intent_suppressions(prompt: str, lighting: Iterable[str] = (), environment: Iterable[str] = ()) -> frozenset:
    """Flag names to leave alone because the prompt asked for that look: dark scenes -> dark/low_contrast/clipped_shadows,
    tinted scenes -> colour_cast. Word-level match on the prompt, lighting tags and environment names."""
    words = set()
    for text in (prompt, *lighting, *environment):
        words.update(w.strip(".,;:!?()\"'").lower() for w in text.split())
    out = set()
    if words & _DARK_WORDS:
        out |= {"dark", "low_contrast", "clipped_shadows", "colour_cast"}
    if words & _TINT_WORDS:
        out |= {"colour_cast"}
    return frozenset(out)
