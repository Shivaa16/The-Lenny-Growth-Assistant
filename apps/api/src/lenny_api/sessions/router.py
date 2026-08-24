from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from lenny_api.sessions.dependencies import SessionServiceDependency
from lenny_api.sessions.schemas import (
    CreateMessageRequest,
    CreateSessionRequest,
    MessageResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummaryResponse,
    UpdateSessionRequest,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest, service: SessionServiceDependency
) -> SessionSummaryResponse:
    return SessionSummaryResponse.model_validate(await service.create_session(request))


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    service: SessionServiceDependency,
    user_id: Annotated[str, Query(min_length=1, max_length=128)] = "local-evaluator",
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SessionListResponse:
    records, total = await service.list_sessions(user_id, limit=limit, offset=offset)
    return SessionListResponse(
        items=[SessionSummaryResponse.model_validate(record) for record in records], total=total
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID, service: SessionServiceDependency
) -> SessionDetailResponse:
    return SessionDetailResponse.model_validate(await service.get_session(session_id))


@router.patch("/{session_id}", response_model=SessionSummaryResponse)
async def rename_session(
    session_id: UUID, request: UpdateSessionRequest, service: SessionServiceDependency
) -> SessionSummaryResponse:
    return SessionSummaryResponse.model_validate(
        await service.rename_session(session_id, request.title)
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, service: SessionServiceDependency) -> Response:
    await service.delete_session(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    session_id: UUID, request: CreateMessageRequest, service: SessionServiceDependency
) -> MessageResponse:
    return MessageResponse.model_validate(await service.add_user_message(session_id, request))

