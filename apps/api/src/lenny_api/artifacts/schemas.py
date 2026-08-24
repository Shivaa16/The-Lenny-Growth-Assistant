from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateArtifactRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=20_000)
    kind: Literal["markdown", "html"] = "markdown"

    @field_validator("topic")
    @classmethod
    def strip_topic(cls, value: str) -> str:
        return value.strip()


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    message_id: UUID | None
    kind: Literal["markdown", "html"]
    title: str
    content: str
    sanitized_content: str
    artifact_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ArtifactListResponse(BaseModel):
    items: list[ArtifactResponse]
