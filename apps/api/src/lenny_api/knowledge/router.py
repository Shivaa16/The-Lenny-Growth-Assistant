from fastapi import APIRouter

from lenny_api.knowledge.dependencies import RetrievalServiceDependency
from lenny_api.knowledge.schemas import EvidenceResponse, RetrievalRequest, RetrievalResponse

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResponse)
async def search(
    request: RetrievalRequest, service: RetrievalServiceDependency
) -> RetrievalResponse:
    evidence = await service.search(request.query, limit=request.limit)
    return RetrievalResponse(
        query=request.query,
        evidence=[
            EvidenceResponse(
                chunk_id=item.chunk_id,
                source_id=item.source_id,
                content=item.content,
                title=item.title,
                guest=item.guest,
                youtube_url=item.youtube_url,
                repository_path=item.repository_path,
                ordinal=item.ordinal,
                score=item.score,
            )
            for item in evidence
        ],
        grounded=bool(evidence),
    )

