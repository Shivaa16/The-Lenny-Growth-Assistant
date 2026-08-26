from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from lenny_api.knowledge.types import TranscriptChunk, TranscriptDocument
from lenny_api.persistence.errors import DATABASE_OPERATION_ERRORS
from lenny_api.persistence.models import ChunkRecord, SourceRecord
from lenny_api.sessions.exceptions import PersistenceUnavailableError


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    chunk_id: UUID
    source_id: UUID
    content: str
    title: str
    guest: str
    youtube_url: str | None
    repository_path: str
    ordinal: int
    semantic_score: float
    keyword_score: float
    score: float


class KnowledgeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def checksum_for(self, source_key: str) -> str | None:
        try:
            return await self.db.scalar(
                select(SourceRecord.content_checksum).where(SourceRecord.source_key == source_key)
            )
        except DATABASE_OPERATION_ERRORS as exc:
            raise PersistenceUnavailableError from exc

    async def replace_source(
        self,
        document: TranscriptDocument,
        chunks: Sequence[TranscriptChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have one embedding")
        try:
            statement = (
                insert(SourceRecord)
                .values(
                    source_key=document.source_key,
                    guest=document.guest,
                    title=document.title,
                    youtube_url=document.youtube_url,
                    publish_date=document.publish_date,
                    description=document.description,
                    repository_path=document.repository_path,
                    repository_commit=document.repository_commit,
                    content_checksum=document.content_checksum,
                    source_metadata=document.metadata,
                )
                .on_conflict_do_update(
                    constraint="uq_sources_source_key",
                    set_={
                        "guest": document.guest,
                        "title": document.title,
                        "youtube_url": document.youtube_url,
                        "publish_date": document.publish_date,
                        "description": document.description,
                        "repository_path": document.repository_path,
                        "repository_commit": document.repository_commit,
                        "content_checksum": document.content_checksum,
                        "source_metadata": document.metadata,
                        "updated_at": func.now(),
                    },
                )
                .returning(SourceRecord.id)
            )
            source_id = await self.db.scalar(statement)
            if source_id is None:
                raise PersistenceUnavailableError

            await self.db.execute(delete(ChunkRecord).where(ChunkRecord.source_id == source_id))
            self.db.add_all(
                [
                    ChunkRecord(
                        source_id=source_id,
                        ordinal=chunk.ordinal,
                        content=chunk.content,
                        word_count=chunk.word_count,
                        start_word=chunk.start_word,
                        end_word=chunk.end_word,
                        embedding=list(embedding),
                        chunk_metadata={},
                    )
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ]
            )
            await self.db.commit()
        except DATABASE_OPERATION_ERRORS as exc:
            await self.db.rollback()
            raise PersistenceUnavailableError from exc

    async def search(
        self, query: str, query_embedding: Sequence[float], *, limit: int
    ) -> list[RetrievedEvidence]:
        semantic = 1 - ChunkRecord.embedding.cosine_distance(list(query_embedding))
        keyword = func.ts_rank_cd(
            ChunkRecord.search_vector, func.websearch_to_tsquery("english", query)
        )
        combined = semantic * 0.75 + func.least(keyword, 1.0) * 0.25
        statement = (
            select(
                ChunkRecord.id.label("chunk_id"),
                ChunkRecord.source_id,
                ChunkRecord.content,
                ChunkRecord.ordinal,
                SourceRecord.title,
                SourceRecord.guest,
                SourceRecord.youtube_url,
                SourceRecord.repository_path,
                semantic.label("semantic_score"),
                keyword.label("keyword_score"),
                combined.label("score"),
            )
            .join(SourceRecord, SourceRecord.id == ChunkRecord.source_id)
            .where(ChunkRecord.embedding.is_not(None))
            .order_by(combined.desc())
            .limit(limit)
        )
        try:
            rows = (await self.db.execute(statement)).all()
        except DATABASE_OPERATION_ERRORS as exc:
            raise PersistenceUnavailableError from exc
        return [RetrievedEvidence(**row._mapping) for row in rows]
