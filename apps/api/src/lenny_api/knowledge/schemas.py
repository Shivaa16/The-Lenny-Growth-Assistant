from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2_000)
    limit: int = Field(default=6, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 2:
            raise ValueError("query must contain at least two non-whitespace characters")
        return stripped


class EvidenceResponse(BaseModel):
    chunk_id: UUID
    source_id: UUID
    content: str
    title: str
    guest: str
    youtube_url: HttpUrl | None
    repository_path: str
    ordinal: int
    score: float


class RetrievalResponse(BaseModel):
    query: str
    evidence: list[EvidenceResponse]
    grounded: bool

