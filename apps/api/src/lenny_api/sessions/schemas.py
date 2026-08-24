from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CreateSessionRequest(BaseModel):
    user_id: str = Field(default="local-evaluator", min_length=1, max_length=128)
    title: str = Field(default="New conversation", min_length=1, max_length=160)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_id", "title")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class UpdateSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    status: Literal["pending", "completed", "failed"]
    model_metadata: dict[str, Any]
    created_at: datetime


class SessionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    title: str
    provider: str
    model: str
    user_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(SessionSummaryResponse):
    messages: list[MessageResponse] = Field(default_factory=list)


class SessionListResponse(BaseModel):
    items: list[SessionSummaryResponse]
    total: int


class CitationResponse(BaseModel):
    position: int
    chunk_id: UUID
    title: str
    guest: str
    youtube_url: HttpUrl | None
    repository_path: str
    quoted_text: str
    relevance_score: float


class ConversationTurnResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    citations: list[CitationResponse]
    grounded: bool
