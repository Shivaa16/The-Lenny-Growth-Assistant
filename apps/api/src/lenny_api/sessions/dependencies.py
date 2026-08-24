from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lenny_api.config import Settings, get_settings
from lenny_api.persistence.database import get_db_session
from lenny_api.sessions.repository import SqlAlchemySessionRepository
from lenny_api.sessions.service import SessionService


def get_session_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionService:
    return SessionService(SqlAlchemySessionRepository(db), settings)


SessionServiceDependency = Annotated[SessionService, Depends(get_session_service)]

