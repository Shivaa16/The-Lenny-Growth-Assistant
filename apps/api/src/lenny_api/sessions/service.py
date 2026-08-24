from collections.abc import Sequence
from uuid import UUID

from lenny_api.config import Settings
from lenny_api.persistence.models import MessageRecord, SessionRecord
from lenny_api.sessions.exceptions import SessionNotFoundError
from lenny_api.sessions.repository import SessionRepository
from lenny_api.sessions.schemas import CreateMessageRequest, CreateSessionRequest


class SessionService:
    def __init__(self, repository: SessionRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def create_session(self, request: CreateSessionRequest) -> SessionRecord:
        return await self.repository.create(
            SessionRecord(
                user_id=request.user_id,
                title=request.title,
                provider=self.settings.llm_provider,
                model=self.settings.active_model,
                user_metadata=request.metadata,
            )
        )

    async def list_sessions(
        self, user_id: str, *, limit: int, offset: int
    ) -> tuple[Sequence[SessionRecord], int]:
        return await self.repository.list_for_user(user_id, limit=limit, offset=offset)

    async def get_session(self, session_id: UUID) -> SessionRecord:
        record = await self.repository.get(session_id, include_messages=True)
        if record is None:
            raise SessionNotFoundError(session_id)
        record.messages.sort(key=lambda message: message.created_at)
        return record

    async def rename_session(self, session_id: UUID, title: str) -> SessionRecord:
        record = await self.repository.get(session_id)
        if record is None:
            raise SessionNotFoundError(session_id)
        record.title = title
        return await self.repository.save(record)

    async def delete_session(self, session_id: UUID) -> None:
        if not await self.repository.delete(session_id):
            raise SessionNotFoundError(session_id)

    async def add_user_message(
        self, session_id: UUID, request: CreateMessageRequest
    ) -> MessageRecord:
        if await self.repository.get(session_id) is None:
            raise SessionNotFoundError(session_id)
        return await self.repository.add_message(
            MessageRecord(
                session_id=session_id,
                role="user",
                content=request.content,
                status="completed",
                model_metadata={},
            )
        )

