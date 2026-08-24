from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lenny_api.agent.factory import create_chat_provider
from lenny_api.artifacts.repository import ArtifactRepository
from lenny_api.artifacts.service import Ship30ArtifactService
from lenny_api.config import Settings, get_settings
from lenny_api.knowledge.embeddings import OllamaEmbeddingProvider
from lenny_api.knowledge.repository import KnowledgeRepository
from lenny_api.knowledge.service import RetrievalService
from lenny_api.persistence.database import get_db_session


def get_artifact_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Ship30ArtifactService:
    embeddings = OllamaEmbeddingProvider(
        base_url=str(settings.ollama_base_url),
        model=settings.ollama_embedding_model,
        expected_dimension=settings.embedding_dimension,
    )
    retrieval = RetrievalService(
        KnowledgeRepository(db),
        embeddings,
        score_threshold=settings.retrieval_score_threshold,
    )
    return Ship30ArtifactService(
        ArtifactRepository(db), retrieval, create_chat_provider(settings)
    )


def get_artifact_repository(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArtifactRepository:
    return ArtifactRepository(db)


ArtifactServiceDependency = Annotated[Ship30ArtifactService, Depends(get_artifact_service)]
ArtifactRepositoryDependency = Annotated[
    ArtifactRepository, Depends(get_artifact_repository)
]
