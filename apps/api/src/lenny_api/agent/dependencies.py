from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lenny_api.agent.factory import create_chat_provider
from lenny_api.agent.repository import ConversationRepository
from lenny_api.agent.service import GroundedConversationService
from lenny_api.config import Settings, get_settings
from lenny_api.knowledge.embeddings import OllamaEmbeddingProvider
from lenny_api.knowledge.repository import KnowledgeRepository
from lenny_api.knowledge.service import RetrievalService
from lenny_api.persistence.database import get_db_session


def get_grounded_conversation_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GroundedConversationService:
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
    return GroundedConversationService(
        ConversationRepository(db),
        retrieval,
        create_chat_provider(settings),
        history_limit=settings.conversation_history_messages,
    )


GroundedConversationDependency = Annotated[
    GroundedConversationService, Depends(get_grounded_conversation_service)
]

