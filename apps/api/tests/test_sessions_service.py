from collections.abc import Sequence
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from lenny_api.config import Settings
from lenny_api.persistence.models import MessageRecord, SessionRecord
from lenny_api.sessions.exceptions import PersistenceUnavailableError, SessionNotFoundError
from lenny_api.sessions.repository import SqlAlchemySessionRepository
from lenny_api.sessions.schemas import CreateMessageRequest, CreateSessionRequest
from lenny_api.sessions.service import SessionService


class InMemorySessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[UUID, SessionRecord] = {}
        self.messages: dict[UUID, list[MessageRecord]] = {}

    @staticmethod
    def stamp(record: SessionRecord | MessageRecord) -> None:
        now = datetime.now(UTC)
        if not getattr(record, "id", None):
            record.id = uuid4()
        if not getattr(record, "created_at", None):
            record.created_at = now
        if isinstance(record, SessionRecord) and not getattr(record, "updated_at", None):
            record.updated_at = now

    async def create(self, record: SessionRecord) -> SessionRecord:
        self.stamp(record)
        record.messages = []
        self.sessions[record.id] = record
        self.messages[record.id] = []
        return record
    async def list_for_user(
        self, user_id: str, *, limit: int, offset: int
    ) -> tuple[Sequence[SessionRecord], int]:
        records = [record for record in self.sessions.values() if record.user_id == user_id]
        records.sort(key=lambda record: record.updated_at, reverse=True)
        return records[offset : offset + limit], len(records)

    async def get(
        self, session_id: UUID, *, include_messages: bool = False
    ) -> SessionRecord | None:
        record = self.sessions.get(session_id)
        if record is not None and include_messages:
            record.messages = list(self.messages[session_id])
        return record

    async def save(self, record: SessionRecord) -> SessionRecord:
        record.updated_at = datetime.now(UTC)
        self.sessions[record.id] = record
        return record

    async def delete(self, session_id: UUID) -> bool:
        record = self.sessions.pop(session_id, None)
        self.messages.pop(session_id, None)
        return record is not None

    async def add_message(self, record: MessageRecord) -> MessageRecord:
        self.stamp(record)
        self.messages[record.session_id].append(record)
        return record


@pytest.mark.asyncio
async def test_raw_driver_connection_failure_is_normalized() -> None:
    db = AsyncMock()
    db.scalars.side_effect = ConnectionRefusedError("database is offline")
    repository = SqlAlchemySessionRepository(db)

    with pytest.raises(PersistenceUnavailableError):
        await repository.list_for_user("local-evaluator", limit=30, offset=0)


@pytest.fixture
def repository() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def service(repository: InMemorySessionRepository) -> SessionService:
    return SessionService(repository, Settings())


@pytest.mark.asyncio
async def test_sessions_are_isolated_by_user(
    service: SessionService, repository: InMemorySessionRepository
) -> None:
    alice = await service.create_session(CreateSessionRequest(user_id="alice", title="Alice chat"))
    await service.create_session(CreateSessionRequest(user_id="bob", title="Bob chat"))

    records, total = await service.list_sessions("alice", limit=30, offset=0)

    assert total == 1
    assert [record.id for record in records] == [alice.id]
    assert len(repository.sessions) == 2


@pytest.mark.asyncio
async def test_message_is_persisted_in_its_session(service: SessionService) -> None:
    session = await service.create_session(CreateSessionRequest(title="Growth loop"))

    created = await service.add_user_message(
        session.id, CreateMessageRequest(content="How do growth loops compound?")
    )
    loaded = await service.get_session(session.id)

    assert created.role == "user"
    assert [message.content for message in loaded.messages] == ["How do growth loops compound?"]


@pytest.mark.asyncio
async def test_missing_session_raises_domain_error(service: SessionService) -> None:
    missing_id = uuid4()

    with pytest.raises(SessionNotFoundError) as error:
        await service.get_session(missing_id)

    assert error.value.session_id == missing_id


@pytest.mark.asyncio
async def test_rename_and_delete_session(service: SessionService) -> None:
    session = await service.create_session(CreateSessionRequest(title="Initial title"))

    renamed = await service.rename_session(session.id, "Retention research")
    await service.delete_session(session.id)

    assert renamed.title == "Retention research"
    with pytest.raises(SessionNotFoundError):
        await service.get_session(session.id)
