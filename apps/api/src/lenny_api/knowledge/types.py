from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TranscriptDocument:
    source_key: str
    guest: str
    title: str
    youtube_url: str | None
    publish_date: date | None
    description: str | None
    repository_path: str
    repository_commit: str | None
    content_checksum: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    file_path: Path | None = None


@dataclass(frozen=True, slots=True)
class TranscriptChunk:
    ordinal: int
    content: str
    word_count: int
    start_word: int
    end_word: int


@dataclass(frozen=True, slots=True)
class IngestionResult:
    discovered: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    chunks: int = 0

