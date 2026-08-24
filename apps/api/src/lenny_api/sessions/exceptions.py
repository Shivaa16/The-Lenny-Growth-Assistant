from uuid import UUID


class SessionNotFoundError(Exception):
    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} was not found")


class PersistenceUnavailableError(Exception):
    """Raised when the persistence layer cannot complete an operation."""

