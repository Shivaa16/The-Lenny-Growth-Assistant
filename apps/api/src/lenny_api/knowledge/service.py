from pathlib import Path

import structlog

from lenny_api.knowledge.chunking import chunk_transcript
from lenny_api.knowledge.embeddings import EmbeddingProviderError, OllamaEmbeddingProvider
from lenny_api.knowledge.parser import discover_transcripts, parse_transcript
from lenny_api.knowledge.repository import KnowledgeRepository, RetrievedEvidence
from lenny_api.knowledge.types import IngestionResult
from lenny_api.sessions.exceptions import PersistenceUnavailableError

logger = structlog.get_logger()


class IngestionService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        embeddings: OllamaEmbeddingProvider,
        *,
        target_words: int,
        overlap_words: int,
        embedding_batch_size: int = 24,
    ) -> None:
        self.repository = repository
        self.embeddings = embeddings
        self.target_words = target_words
        self.overlap_words = overlap_words
        self.embedding_batch_size = embedding_batch_size

    async def ingest_repository(
        self,
        repository_root: Path,
        *,
        repository_commit: str | None,
        max_transcripts: int | None = None,
    ) -> IngestionResult:
        paths = discover_transcripts(repository_root)
        selected_paths = paths[:max_transcripts] if max_transcripts is not None else paths
        indexed = skipped = failed = chunk_count = 0
        for path in selected_paths:
            try:
                document = parse_transcript(
                    path,
                    repository_root=repository_root,
                    repository_commit=repository_commit,
                )
                existing_checksum = await self.repository.checksum_for(document.source_key)
                if existing_checksum == document.content_checksum:
                    skipped += 1
                    continue
                chunks = chunk_transcript(
                    document.content,
                    target_words=self.target_words,
                    overlap_words=self.overlap_words,
                )
                embeddings: list[list[float]] = []
                for offset in range(0, len(chunks), self.embedding_batch_size):
                    batch = chunks[offset : offset + self.embedding_batch_size]
                    batch_embeddings = await self.embeddings.embed(
                        [chunk.content for chunk in batch]
                    )
                    embeddings.extend(batch_embeddings)
                await self.repository.replace_source(document, chunks, embeddings)
                indexed += 1
                chunk_count += len(chunks)
                logger.info(
                    "transcript_indexed",
                    source_key=document.source_key,
                    chunks=len(chunks),
                    repository_commit=repository_commit,
                )
            except (EmbeddingProviderError, PersistenceUnavailableError):
                raise
            except Exception as exc:
                failed += 1
                logger.error(
                    "transcript_ingestion_failed",
                    path=str(path),
                    error_type=type(exc).__name__,
                )
        return IngestionResult(
            discovered=len(selected_paths),
            indexed=indexed,
            skipped=skipped,
            failed=failed,
            chunks=chunk_count,
        )


class RetrievalService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        embeddings: OllamaEmbeddingProvider,
        *,
        score_threshold: float,
    ) -> None:
        self.repository = repository
        self.embeddings = embeddings
        self.score_threshold = score_threshold

    async def search(self, query: str, *, limit: int) -> list[RetrievedEvidence]:
        query_embedding = (await self.embeddings.embed([query]))[0]
        evidence = await self.repository.search(query, query_embedding, limit=limit)
        return [item for item in evidence if item.score >= self.score_threshold]
