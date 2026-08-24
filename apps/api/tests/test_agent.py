from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

from lenny_api.agent.providers import ClaudeAgentProvider, OllamaChatProvider
from lenny_api.agent.service import (
    GREETING_RESPONSE,
    INSUFFICIENT_EVIDENCE,
    GroundedConversationService,
)
from lenny_api.agent.types import AgentMessage, GenerationResult
from lenny_api.knowledge.repository import RetrievedEvidence


@pytest.mark.asyncio
async def test_ollama_provider_uses_bounded_deterministic_chat_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = __import__("json").loads(request.content)
        assert request.url.path == "/api/chat"
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0.2
        assert payload["messages"][0] == {"role": "system", "content": "Grounded only"}
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "Use a focused loop [1]."},
                "prompt_eval_count": 120,
                "eval_count": 9,
                "total_duration": 1000,
            },
        )

    provider = OllamaChatProvider(
        base_url="http://ollama",
        model="qwen-test",
        timeout_seconds=10,
        transport=httpx.MockTransport(handler),
    )

    result = await provider.generate(
        system_prompt="Grounded only",
        messages=[AgentMessage(role="user", content="How do loops work?")],
    )

    assert result.content == "Use a focused loop [1]."
    assert result.usage["prompt_tokens"] == 120


@pytest.mark.asyncio
async def test_claude_agent_sdk_provider_disables_tools_and_bounds_turns() -> None:
    captured = {}

    async def fake_query(*, prompt, options):
        captured["prompt"] = prompt
        captured["options"] = options
        yield AssistantMessage(content=[TextBlock("Use retention evidence [1].")], model="test")
        yield ResultMessage(
            subtype="success",
            duration_ms=12,
            duration_api_ms=10,
            is_error=False,
            num_turns=1,
            session_id="session",
            total_cost_usd=0.001,
        )

    provider = ClaudeAgentProvider(
        model="claude-test",
        api_key="test-key",
        max_budget_usd=0.05,
        timeout_seconds=10,
        query_factory=fake_query,
    )

    result = await provider.generate(
        system_prompt="Use transcript evidence only",
        messages=[AgentMessage(role="user", content="How should I improve retention?")],
    )

    assert result.content == "Use retention evidence [1]."
    assert captured["options"].allowed_tools == []
    assert captured["options"].max_turns == 1
    assert captured["options"].max_budget_usd == 0.05


def evidence(score: float = 0.8) -> RetrievedEvidence:
    return RetrievedEvidence(
        chunk_id=uuid4(),
        source_id=uuid4(),
        content="Each retained user creates an input for another user.",
        title="Building growth loops",
        guest="Test Guest",
        youtube_url="https://youtube.com/watch?v=test",
        repository_path="episodes/test/transcript.md",
        ordinal=3,
        semantic_score=score,
        keyword_score=0.2,
        score=score,
    )


class FakeConversationRepository:
    def __init__(self, messages=None) -> None:
        self.session = SimpleNamespace(id=uuid4(), messages=messages or [])
        self.persisted = None

    async def load_session(self, session_id):
        return self.session

    async def persist_turn(self, **kwargs):
        self.persisted = kwargs
        return "persisted-turn"


class FakeRetrieval:
    def __init__(self, items) -> None:
        self.items = items
        self.query = None

    async def search(self, query, *, limit):
        self.query = query
        return self.items[:limit]


class FakeProvider:
    def __init__(self) -> None:
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        return GenerationResult("Loops compound through retained inputs [1].", "ollama", "qwen")


@pytest.mark.asyncio
async def test_grounded_service_passes_evidence_and_persists_citations() -> None:
    repository = FakeConversationRepository(
        messages=[SimpleNamespace(role="user", content="Tell me about acquisition")]
    )
    retrieval = FakeRetrieval([evidence()])
    provider = FakeProvider()
    service = GroundedConversationService(
        repository, retrieval, provider, history_limit=8
    )

    turn, citations = await service.answer(repository.session.id, "How does it compound?")

    assert turn == "persisted-turn"
    assert citations[0].title == "Building growth loops"
    assert "Tell me about acquisition" in retrieval.query
    assert "TRANSCRIPT EVIDENCE" in provider.calls[0]["system_prompt"]
    assert repository.persisted["evidence"] == citations


@pytest.mark.asyncio
async def test_no_evidence_returns_deterministic_refusal_without_model_call() -> None:
    repository = FakeConversationRepository()
    retrieval = FakeRetrieval([])
    provider = FakeProvider()
    service = GroundedConversationService(repository, retrieval, provider, history_limit=8)

    await service.answer(repository.session.id, "Who won the football match?")

    assert provider.calls == []
    assert repository.persisted["generation"].content == INSUFFICIENT_EVIDENCE


@pytest.mark.asyncio
async def test_greeting_is_routed_without_retrieval_or_model() -> None:
    repository = FakeConversationRepository()
    retrieval = FakeRetrieval([evidence()])
    provider = FakeProvider()
    service = GroundedConversationService(repository, retrieval, provider, history_limit=8)

    _, citations = await service.answer(repository.session.id, "Hi!")

    assert retrieval.query is None
    assert provider.calls == []
    assert citations == []
    assert repository.persisted["generation"].content == GREETING_RESPONSE
