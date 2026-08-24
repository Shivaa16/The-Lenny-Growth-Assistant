from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lenny_api.persistence.models import MessageRecord, SessionRecord
from lenny_api.sessions.exceptions import PersistenceUnavailableError


class SessionRepository(Protocol):
    async def create(self, record: SessionRecord) -> SessionRecord: ...

    async def list_for_user(
        self, user_id: str, *, limit: int, offset: int
    ) -> tuple[Sequence[SessionRecord], int]: ...

    async def get(
        self, session_id: UUID, *, include_messages: bool = False
    ) -> SessionRecord | None: ...

    async def save(self, record: SessionRecord) -> SessionRecord: ...

    async def delete(self, session_id: UUID) -> bool: ...

    async def add_message(self, record: MessageRecord) -> MessageRecord: ...


class SqlAlchemySessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, record: SessionRecord) -> SessionRecord:
        try:
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc

    async def list_for_user(
        self, user_id: str, *, limit: int, offset: int
    ) -> tuple[Sequence[SessionRecord], int]:
        try:
            records = await self.db.scalars(
                select(SessionRecord)
                .where(SessionRecord.user_id == user_id)
                .order_by(SessionRecord.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            total = await self.db.scalar(
                select(func.count())
                .select_from(SessionRecord)
                .where(SessionRecord.user_id == user_id)
            )
            return records.all(), int(total or 0)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError from exc

    async def get(
        self, session_id: UUID, *, include_messages: bool = False
    ) -> SessionRecord | None:
        query = select(SessionRecord).where(SessionRecord.id == session_id)
        if include_messages:
            query = query.options(selectinload(SessionRecord.messages))
        try:
            return await self.db.scalar(query)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError from exc

    async def save(self, record: SessionRecord) -> SessionRecord:
        try:
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc

    async def delete(self, session_id: UUID) -> bool:
        try:
            result = await self.db.execute(
                delete(SessionRecord).where(SessionRecord.id == session_id)
            )
            await self.db.commit()
            return bool(result.rowcount)
        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc

    async def add_message(self, record: MessageRecord) -> MessageRecord:
        try:
            self.db.add(record)
            session = await self.db.get(SessionRecord, record.session_id)
            if session is not None:
                session.updated_at = func.now()
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc
