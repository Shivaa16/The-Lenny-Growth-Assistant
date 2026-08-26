import argparse
import asyncio
import subprocess
from pathlib import Path

from lenny_api.config import get_settings
from lenny_api.knowledge.embeddings import OllamaEmbeddingProvider
from lenny_api.knowledge.repository import KnowledgeRepository
from lenny_api.knowledge.service import IngestionService
from lenny_api.persistence.database import dispose_engine, session_factory


def repository_commit(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


async def ingest(source_dir: Path, *, max_transcripts: int | None = None) -> int:
    settings = get_settings()
    embeddings = OllamaEmbeddingProvider(
        base_url=str(settings.ollama_base_url),
        model=settings.ollama_embedding_model,
        expected_dimension=settings.embedding_dimension,
    )
    try:
        async with session_factory() as db:
            service = IngestionService(
                KnowledgeRepository(db),
                embeddings,
                target_words=settings.chunk_target_words,
                overlap_words=settings.chunk_overlap_words,
            )
            result = await service.ingest_repository(
                source_dir.resolve(),
                repository_commit=repository_commit(source_dir),
                max_transcripts=max_transcripts,
            )
    finally:
        await dispose_engine()
    print(
        f"discovered={result.discovered} indexed={result.indexed} "
        f"skipped={result.skipped} failed={result.failed} chunks={result.chunks}"
    )
    return 1 if result.failed else 0


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Index Lenny's Podcast transcripts")
    parser.add_argument("--source-dir", type=Path, default=Path(settings.transcript_source_dir))
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Index only the first N transcripts for a fast low-storage demo bootstrap",
    )
    arguments = parser.parse_args()
    if arguments.limit is not None and arguments.limit < 1:
        parser.error("--limit must be greater than zero")
    raise SystemExit(
        asyncio.run(ingest(arguments.source_dir, max_transcripts=arguments.limit))
    )


if __name__ == "__main__":
    main()
