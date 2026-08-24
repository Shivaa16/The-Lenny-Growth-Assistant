from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lenny_api.config import get_settings
from lenny_api.logging import configure_logging
from lenny_api.schemas import ErrorResponse, HealthResponse, ProviderInfo

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


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.exception("unhandled_exception", error_type=type(exc).__name__)
    payload = ErrorResponse.model_validate(
        {
            "error": {
                "code": "internal_error",
                "message": "The service encountered an unexpected error.",
                "request_id": request_id,
            }
        }
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok", service="lenny-growth-api", version=app.version)


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def readiness() -> HealthResponse:
    # Dependency-specific checks are added with persistence and model adapters.
    return HealthResponse(status="ok", service="lenny-growth-api", version=app.version)


@app.get("/api/v1/config", response_model=ProviderInfo, tags=["configuration"])
async def provider_config() -> ProviderInfo:
    return ProviderInfo(
        provider=settings.llm_provider,
        model=settings.active_model,
        local_model=settings.ollama_chat_model,
        embedding_model=settings.ollama_embedding_model,
        cloud_configured=settings.cloud_configured,
    )

