from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str


class ProviderInfo(BaseModel):
    provider: Literal["ollama", "anthropic"]
    model: str
    local_model: str
    embedding_model: str
    cloud_configured: bool


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

