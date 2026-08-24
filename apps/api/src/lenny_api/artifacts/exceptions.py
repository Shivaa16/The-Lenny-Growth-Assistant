from uuid import UUID


class ArtifactNotFoundError(Exception):
    def __init__(self, artifact_id: UUID) -> None:
        self.artifact_id = artifact_id
        super().__init__(f"Artifact {artifact_id} was not found")
