"""Request model for POST /api/v1/prompt/analysis (additive endpoint, see docs/API_CONTRACT_v1.md)."""
from pydantic import BaseModel, Field, field_validator

from ai_engine.prompt.schema import MAX_PROMPT_CHARS


class PromptAnalysisRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)

    @field_validator("prompt")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prompt must not be blank")
        return v
