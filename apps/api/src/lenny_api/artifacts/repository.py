from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lenny_api.persistence.models import ArtifactRecord, SessionRecord
from lenny_api.sessions.exceptions import PersistenceUnavailableError, SessionNotFoundError


class ArtifactRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def require_session(self, session_id: UUID) -> SessionRecord:
        try:
            session = await self.db.get(SessionRecord, session_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError from exc
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    async def save(self, artifact: ArtifactRecord) -> ArtifactRecord:
        try:
            self.db.add(artifact)
            await self.db.commit()
            await self.db.refresh(artifact)
            return artifact
        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc

    async def get(self, artifact_id: UUID) -> ArtifactRecord | None:
        try:
            return await self.db.get(ArtifactRecord, artifact_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError from exc

    async def list_for_session(self, session_id: UUID) -> list[ArtifactRecord]:
        await self.require_session(session_id)
        try:
            result = await self.db.scalars(
                select(ArtifactRecord)
                .where(ArtifactRecord.session_id == session_id)
                .order_by(ArtifactRecord.updated_at.desc())
            )
            return list(result)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError from exc
