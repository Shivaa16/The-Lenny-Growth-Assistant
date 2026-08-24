import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from lenny_api.knowledge.types import TranscriptDocument

FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class TranscriptParseError(ValueError):
    pass


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def parse_transcript(
    path: Path, *, repository_root: Path, repository_commit: str | None = None
) -> TranscriptDocument:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    match = FRONTMATTER_PATTERN.match(raw)
    if match is None:
        raise TranscriptParseError(f"Missing YAML frontmatter: {path}")

    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        raise TranscriptParseError(f"Invalid YAML frontmatter: {path}")
    content = raw[match.end() :].strip()
    if not content:
        raise TranscriptParseError(f"Transcript content is empty: {path}")

    relative_path = path.relative_to(repository_root).as_posix()
    source_key = path.parent.name
    guest = str(metadata.get("guest") or source_key.replace("-", " ").title()).strip()
    title = str(metadata.get("title") or f"Lenny's Podcast with {guest}").strip()
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    excluded_metadata = {"guest", "title", "youtube_url", "publish_date", "description"}
    safe_metadata = json.loads(
        json.dumps(
            {key: value for key, value in metadata.items() if key not in excluded_metadata},
            default=str,
        )
    )

    return TranscriptDocument(
        source_key=source_key,
        guest=guest,
        title=title,
        youtube_url=str(metadata["youtube_url"]).strip() if metadata.get("youtube_url") else None,
        publish_date=_parse_date(metadata.get("publish_date")),
        description=str(metadata["description"]).strip() if metadata.get("description") else None,
        repository_path=relative_path,
        repository_commit=repository_commit,
        content_checksum=checksum,
        content=content,
        metadata=safe_metadata,
        file_path=path,
    )


def discover_transcripts(repository_root: Path) -> list[Path]:
    episodes_dir = repository_root / "episodes"
    if not episodes_dir.is_dir():
        raise TranscriptParseError(f"Expected an episodes directory at {episodes_dir}")
    return sorted(episodes_dir.glob("*/transcript.md"))
