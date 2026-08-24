from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lenny_api.config import Settings, get_settings
from lenny_api.knowledge.embeddings import OllamaEmbeddingProvider
from lenny_api.knowledge.repository import KnowledgeRepository
from lenny_api.knowledge.service import RetrievalService
from lenny_api.persistence.database import get_db_session


def get_retrieval_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RetrievalService:
    embeddings = OllamaEmbeddingProvider(
        base_url=str(settings.ollama_base_url),
        model=settings.ollama_embedding_model,
        expected_dimension=settings.embedding_dimension,
    )
    return RetrievalService(
        KnowledgeRepository(db),
        embeddings,
        score_threshold=settings.retrieval_score_threshold,
    )


RetrievalServiceDependency = Annotated[RetrievalService, Depends(get_retrieval_service)]

