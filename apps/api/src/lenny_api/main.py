from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lenny_api.agent.types import GenerationProviderError
from lenny_api.artifacts.exceptions import ArtifactNotFoundError
from lenny_api.artifacts.router import router as artifacts_router
from lenny_api.config import get_settings
from lenny_api.knowledge.embeddings import EmbeddingProviderError
from lenny_api.knowledge.router import router as knowledge_router
from lenny_api.logging import configure_logging
from lenny_api.persistence.database import database_is_ready, dispose_engine
from lenny_api.schemas import ErrorResponse, HealthResponse, ProviderInfo
from lenny_api.sessions.exceptions import PersistenceUnavailableError, SessionNotFoundError
from lenny_api.sessions.router import router as sessions_router

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "application_started",
        environment=settings.app_env,
        provider=settings.llm_provider,
        model=settings.active_model,
    )
    yield
    await dispose_engine()
    logger.info("application_stopped")


app = FastAPI(
    title="Lenny Growth Assistant API",
    version="0.1.0",
    description="Grounded product and growth intelligence from Lenny's Podcast transcripts.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)
app.include_router(sessions_router)
app.include_router(knowledge_router)
app.include_router(artifacts_router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def error_response(request: Request, *, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    payload = ErrorResponse.model_validate(
        {"error": {"code": code, "message": message, "request_id": request_id}}
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found(request: Request, exc: SessionNotFoundError) -> JSONResponse:
    return error_response(
        request,
        status_code=status.HTTP_404_NOT_FOUND,
        code="session_not_found",
        message=f"Session {exc.session_id} was not found.",
    )


@app.exception_handler(ArtifactNotFoundError)
async def artifact_not_found(request: Request, exc: ArtifactNotFoundError) -> JSONResponse:
    return error_response(
        request,
        status_code=status.HTTP_404_NOT_FOUND,
        code="artifact_not_found",
        message=f"Artifact {exc.artifact_id} was not found.",
    )


@app.exception_handler(PersistenceUnavailableError)
async def persistence_unavailable(
    request: Request, _: PersistenceUnavailableError
) -> JSONResponse:
    logger.warning("persistence_unavailable")
    return error_response(
        request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="persistence_unavailable",
        message="Conversation storage is temporarily unavailable. Please retry shortly.",
    )


@app.exception_handler(EmbeddingProviderError)
async def embedding_unavailable(request: Request, _: EmbeddingProviderError) -> JSONResponse:
    logger.warning("embedding_provider_unavailable")
    return error_response(
        request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="embedding_provider_unavailable",
        message="The local embedding model is unavailable. Start Ollama and retry.",
    )


@app.exception_handler(GenerationProviderError)
async def generation_unavailable(
    request: Request, exc: GenerationProviderError
) -> JSONResponse:
    logger.warning("generation_provider_unavailable", provider=exc.provider)
    return error_response(
        request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="generation_provider_unavailable",
        message=f"The selected {exc.provider} generation provider is unavailable. Please retry.",
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
    detail = first_error.get("msg", "Invalid request")
    message = f"{location}: {detail}" if location else detail
    return error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="validation_error",
        message=message,
    )


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", error_type=type(exc).__name__)
    return error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_error",
        message="The service encountered an unexpected error.",
    )


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok", service="lenny-growth-api", version=app.version)


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def readiness(response: Response) -> HealthResponse:
    ready = await database_is_ready()
    response_status = "ok" if ready else "degraded"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status=response_status, service="lenny-growth-api", version=app.version)


@app.get("/api/v1/config", response_model=ProviderInfo, tags=["configuration"])
async def provider_config() -> ProviderInfo:
    return ProviderInfo(
        provider=settings.llm_provider,
        model=settings.active_model,
        local_model=settings.ollama_chat_model,
        embedding_model=settings.ollama_embedding_model,
        cloud_configured=settings.cloud_configured,
    )
