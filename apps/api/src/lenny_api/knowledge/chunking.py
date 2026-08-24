import re

from lenny_api.knowledge.types import TranscriptChunk

WORD_PATTERN = re.compile(r"\S+")


def chunk_transcript(
    content: str, *, target_words: int = 220, overlap_words: int = 40
) -> list[TranscriptChunk]:
    if target_words < 1:
        raise ValueError("target_words must be positive")
    if overlap_words < 0 or overlap_words >= target_words:
        raise ValueError("overlap_words must be between 0 and target_words - 1")

    words = WORD_PATTERN.findall(content)
    chunks: list[TranscriptChunk] = []
    start = 0
    ordinal = 0
    while start < len(words):
        end = min(start + target_words, len(words))
        chunk_words = words[start:end]
        chunks.append(
            TranscriptChunk(
                ordinal=ordinal,
                content=" ".join(chunk_words),
                word_count=len(chunk_words),
                start_word=start,
                end_word=end,
            )
        )
        if end == len(words):
            break
        start = end - overlap_words
        ordinal += 1
    return chunks

