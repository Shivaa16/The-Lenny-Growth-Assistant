from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from lenny_api.knowledge.chunking import chunk_transcript
from lenny_api.knowledge.embeddings import EmbeddingProviderError, OllamaEmbeddingProvider
from lenny_api.knowledge.parser import TranscriptParseError, discover_transcripts, parse_transcript
from lenny_api.knowledge.repository import RetrievedEvidence
from lenny_api.knowledge.service import RetrievalService
from lenny_api.knowledge.sync import TranscriptSyncError, sync


def write_transcript(root: Path, guest: str = "test-guest") -> Path:
    directory = root / "episodes" / guest
    directory.mkdir(parents=True)
    path = directory / "transcript.md"
    path.write_text(
        "---\n"
        "guest: Test Guest\n"
        "title: Building durable growth loops\n"
        "youtube_url: https://www.youtube.com/watch?v=test\n"
        "publish_date: 2025-01-02\n"
        "---\n"
        "Growth loops compound when each user action creates an input for the next user.\n",
        encoding="utf-8",
    )
    return path


def test_parser_preserves_source_traceability(tmp_path: Path) -> None:
    path = write_transcript(tmp_path)

    document = parse_transcript(path, repository_root=tmp_path, repository_commit="abc123")

    assert document.source_key == "test-guest"
    assert document.guest == "Test Guest"
    assert document.repository_path == "episodes/test-guest/transcript.md"
    assert document.repository_commit == "abc123"
    assert len(document.content_checksum) == 64


def test_discovery_is_deterministic(tmp_path: Path) -> None:
    second = write_transcript(tmp_path, "z-guest")
    first = write_transcript(tmp_path, "a-guest")

    assert discover_transcripts(tmp_path) == [first, second]


def test_parser_rejects_untraceable_document(tmp_path: Path) -> None:
    path = tmp_path / "transcript.md"
    path.write_text("No frontmatter", encoding="utf-8")

    with pytest.raises(TranscriptParseError):
        parse_transcript(path, repository_root=tmp_path)


def test_chunking_is_deterministic_and_overlapping() -> None:
    content = " ".join(f"word-{index}" for index in range(12))

    chunks = chunk_transcript(content, target_words=5, overlap_words=2)

    assert [(chunk.start_word, chunk.end_word) for chunk in chunks] == [
        (0, 5),
        (3, 8),
        (6, 11),
        (9, 12),
    ]
    assert chunks[0].content.split()[-2:] == chunks[1].content.split()[:2]


@pytest.mark.asyncio
async def test_ollama_embedding_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})

    provider = OllamaEmbeddingProvider(
        base_url="http://ollama",
        model="test-embedding",
        expected_dimension=3,
        transport=httpx.MockTransport(handler),
    )

    assert await provider.embed(["growth loop"]) == [[0.1, 0.2, 0.3]]


@pytest.mark.asyncio
async def test_ollama_dimension_mismatch_is_actionable() -> None:
    provider = OllamaEmbeddingProvider(
        base_url="http://ollama",
        model="test-embedding",
        expected_dimension=3,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})
        ),
    )

    with pytest.raises(EmbeddingProviderError, match="dimension"):
        await provider.embed(["growth loop"])


class FakeEmbeddings:
    async def embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeKnowledgeRepository:
    async def search(self, query, query_embedding, *, limit):
        return [
            RetrievedEvidence(
                chunk_id=uuid4(),
                source_id=uuid4(),
                content="Evidence",
                title="Episode",
                guest="Guest",
                youtube_url=None,
                repository_path="episodes/guest/transcript.md",
                ordinal=0,
                semantic_score=0.7,
                keyword_score=0.2,
                score=0.6,
            ),
            RetrievedEvidence(
                chunk_id=uuid4(),
                source_id=uuid4(),
                content="Weak evidence",
                title="Episode 2",
                guest="Guest 2",
                youtube_url=None,
                repository_path="episodes/guest-2/transcript.md",
                ordinal=0,
                semantic_score=0.2,
                keyword_score=0.1,
                score=0.2,
            ),
        ][:limit]


@pytest.mark.asyncio
async def test_retrieval_applies_grounding_threshold() -> None:
    service = RetrievalService(FakeKnowledgeRepository(), FakeEmbeddings(), score_threshold=0.35)

    evidence = await service.search("How do loops compound?", limit=6)

    assert [item.content for item in evidence] == ["Evidence"]


def test_sync_refuses_to_overwrite_non_git_directory(tmp_path: Path) -> None:
    destination = tmp_path / "transcripts"
    destination.mkdir()
    (destination / "personal-file.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(TranscriptSyncError, match="Refusing to overwrite"):
        sync("https://github.com/ChatPRD/lennys-podcast-transcripts.git", destination)

    assert (destination / "personal-file.txt").read_text(encoding="utf-8") == "keep me"
