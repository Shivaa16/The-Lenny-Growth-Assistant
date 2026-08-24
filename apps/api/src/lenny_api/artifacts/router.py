from uuid import UUID

from fastapi import APIRouter, status

from lenny_api.artifacts.dependencies import (
    ArtifactRepositoryDependency,
    ArtifactServiceDependency,
)
from lenny_api.artifacts.exceptions import ArtifactNotFoundError
from lenny_api.artifacts.schemas import (
    ArtifactListResponse,
    ArtifactResponse,
    CreateArtifactRequest,
)

router = APIRouter(prefix="/api/v1", tags=["artifacts"])


@router.post(
    "/sessions/{session_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact(
    session_id: UUID,
    request: CreateArtifactRequest,
    service: ArtifactServiceDependency,
) -> ArtifactResponse:
    return ArtifactResponse.model_validate(
        await service.create(session_id, request.topic, request.kind)
    )


@router.get("/sessions/{session_id}/artifacts", response_model=ArtifactListResponse)
async def list_artifacts(
    session_id: UUID, repository: ArtifactRepositoryDependency
) -> ArtifactListResponse:
    records = await repository.list_for_session(session_id)
    return ArtifactListResponse(
        items=[ArtifactResponse.model_validate(record) for record in records]
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID, repository: ArtifactRepositoryDependency
) -> ArtifactResponse:
    artifact = await repository.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(artifact_id)
    return ArtifactResponse.model_validate(artifact)
