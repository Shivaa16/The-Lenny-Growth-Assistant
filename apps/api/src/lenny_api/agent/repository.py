from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lenny_api.agent.types import GenerationResult
from lenny_api.knowledge.repository import RetrievedEvidence
from lenny_api.persistence.errors import DATABASE_OPERATION_ERRORS
from lenny_api.persistence.models import CitationRecord, MessageRecord, SessionRecord
from lenny_api.sessions.exceptions import PersistenceUnavailableError, SessionNotFoundError


@dataclass(frozen=True, slots=True)
class PersistedTurn:
    user_message: MessageRecord
    assistant_message: MessageRecord


class ConversationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def load_session(self, session_id: UUID) -> SessionRecord:
        try:
            session = await self.db.scalar(
                select(SessionRecord)
                .where(SessionRecord.id == session_id)
                .options(selectinload(SessionRecord.messages))
            )
        except DATABASE_OPERATION_ERRORS as exc:
            raise PersistenceUnavailableError from exc
        if session is None:
            raise SessionNotFoundError(session_id)
        session.messages.sort(key=lambda message: message.created_at)
        return session

    async def persist_turn(
        self,
        *,
        session: SessionRecord,
        user_content: str,
        generation: GenerationResult,
        evidence: list[RetrievedEvidence],
    ) -> PersistedTurn:
        user_message = MessageRecord(
            session_id=session.id,
            role="user",
            content=user_content,
            status="completed",
            model_metadata={},
        )
        assistant_message = MessageRecord(
            session_id=session.id,
            role="assistant",
            content=generation.content,
            status="completed",
            model_metadata={
                "provider": generation.provider,
                "model": generation.model,
                "usage": generation.usage,
            },
        )
        try:
            self.db.add_all([user_message, assistant_message])
            await self.db.flush()
            self.db.add_all(
                [
                    CitationRecord(
                        message_id=assistant_message.id,
                        chunk_id=item.chunk_id,
                        position=index,
                        quoted_text=item.content,
                        relevance_score=item.score,
                    )
                    for index, item in enumerate(evidence, start=1)
                ]
            )
            session.updated_at = func.now()
            if session.title == "New conversation":
                session.title = _title_from(user_content)
            await self.db.commit()
            await self.db.refresh(user_message)
            await self.db.refresh(assistant_message)
            return PersistedTurn(user_message=user_message, assistant_message=assistant_message)
        except DATABASE_OPERATION_ERRORS as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc


def _title_from(content: str, limit: int = 64) -> str:
    normalized = " ".join(content.split())
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 1].rstrip()}…"
