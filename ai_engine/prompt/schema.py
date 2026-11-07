"""Stable output schema for prompt analysis (schema_version 1.0).

Every key is always present (empty list / null instead of omitted). Every extracted item carries
`span` = [start, end) character offsets into `raw_prompt`, so nothing can be claimed without evidence.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"
PARSER_VERSION = "rules-1.0.0"
MAX_PROMPT_CHARS = 500  # must equal GenerateRequest.prompt max_length (checked by a test)

NOTICE = ("Rule-based, English-only analysis of the prompt TEXT. It does not verify what the generated image "
          "contains. Counts and relations are what the prompt says, not what the image shows. CLIP-style "
          "alignment scores do not prove count or spatial-relation correctness.")

CountKind = Literal["exact", "approximate", "plural_unspecified", "unspecified"]
AttrType = Literal["color", "size", "material", "other"]


class Validation(BaseModel):
    valid: bool = True
    code: Optional[Literal["EMPTY_PROMPT", "TOO_LONG"]] = None
    message: Optional[str] = None


class Attribute(BaseModel):
    type: AttrType
    value: str
    evidence: str
    span: list[int]


class SceneObject(BaseModel):
    id: str
    name: str                       # singular best-effort lemma of the head noun
    surface: str                    # head as written (lower-cased)
    count: Optional[int] = None     # only when the prompt states/implies it
    count_kind: CountKind = "unspecified"
    quantifier: Optional[str] = None  # e.g. "three", "a flock of", "several"
    attributes: list[Attribute] = Field(default_factory=list)
    other_modifiers: list[str] = Field(default_factory=list)  # unclassified words before the head; NOT claimed as attributes
    actions: list[str] = Field(default_factory=list)          # -ing/verb words attached to this object
    frame_position: Optional[str] = None  # left|right|top|bottom|center|background|foreground (position in the frame)
    lexicon_match: bool = False     # head noun is in the built-in lexicon (False = guessed from position)
    evidence: str
    span: list[int]


class EnvironmentItem(BaseModel):
    id: str
    name: str
    category: Literal["place", "weather", "setting"]
    attributes: list[Attribute] = Field(default_factory=list)
    evidence: str
    span: list[int]


class Relation(BaseModel):
    subject: Optional[str] = None   # object/environment id, or null if the prompt gives none
    relation: str                   # beside|behind|in_front_of|above|below|left_of|right_of|inside|on|near|with
    object: Optional[str] = None
    spatial: bool = True            # False for "with"
    evidence: str
    span: list[int]


class Tagged(BaseModel):
    value: str
    kind: Optional[str] = None
    evidence: str
    span: list[int]


class Negation(BaseModel):
    text: str                       # what the prompt says is absent; never turned into an object
    evidence: str
    span: list[int]


class Ambiguity(BaseModel):
    code: str
    detail: str
    span: Optional[list[int]] = None


class Complexity(BaseModel):
    """Heuristic about the PROMPT's structure (for later resource decisions). Not a quality or difficulty measure."""
    object_count: int
    relation_count: int
    attribute_count: int
    level: Literal["simple", "moderate", "complex"]


class PromptAnalysis(BaseModel):
    schema_version: str = SCHEMA_VERSION
    parser_version: str = PARSER_VERSION
    raw_prompt: str                 # byte-for-byte the input; never trimmed or normalised
    validation: Validation
    objects: list[SceneObject] = Field(default_factory=list)
    environment: list[EnvironmentItem] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    lighting: list[Tagged] = Field(default_factory=list)
    style: list[Tagged] = Field(default_factory=list)
    negations: list[Negation] = Field(default_factory=list)
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    complexity: Complexity
    notice: str = NOTICE
