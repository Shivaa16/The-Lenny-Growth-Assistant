import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx

from lenny_api.agent.types import AgentMessage, GenerationProviderError, GenerationResult


class OllamaChatProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def generate(
        self, *, system_prompt: str, messages: list[AgentMessage]
    ) -> GenerationResult:
        payload_messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": message.role, "content": message.content} for message in messages],
        ]
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds, transport=self.transport
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": payload_messages,
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 1600},
                        "keep_alive": "5m",
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:
            raise GenerationProviderError(
                "ollama", f"Ollama model '{self.model}' is unavailable"
            ) from exc

        content = payload.get("message", {}).get("content", "").strip()
        if not content:
            raise GenerationProviderError("ollama", "Ollama returned an empty response")
        usage = {
            "prompt_tokens": payload.get("prompt_eval_count"),
            "completion_tokens": payload.get("eval_count"),
            "duration_ns": payload.get("total_duration"),
        }
        return GenerationResult(content=content, provider="ollama", model=self.model, usage=usage)


class ClaudeAgentProvider:
    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        max_budget_usd: float,
        timeout_seconds: float,
        query_factory: Callable[..., AsyncIterator[Any]] | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.max_budget_usd = max_budget_usd
        self.timeout_seconds = timeout_seconds
        self.query_factory = query_factory

    async def generate(
        self, *, system_prompt: str, messages: list[AgentMessage]
    ) -> GenerationResult:
        try:
            from claude_agent_sdk import (
                AssistantMessage,
                ClaudeAgentOptions,
                ResultMessage,
                TextBlock,
                query,
            )
        except ImportError as exc:
            raise GenerationProviderError("anthropic", "Claude Agent SDK is not installed") from exc

        prompt = "\n\n".join(f"{message.role.upper()}: {message.content}" for message in messages)
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=system_prompt,
            allowed_tools=[],
            max_turns=1,
            max_budget_usd=self.max_budget_usd,
            permission_mode="dontAsk",
            env={"ANTHROPIC_API_KEY": self.api_key},
        )
        texts: list[str] = []
        usage: dict[str, Any] = {}
        query_function = self.query_factory or query
        try:
            async with asyncio.timeout(self.timeout_seconds):
                async for message in query_function(prompt=prompt, options=options):
                    if isinstance(message, AssistantMessage):
                        texts.extend(
                            block.text for block in message.content if isinstance(block, TextBlock)
                        )
                    elif isinstance(message, ResultMessage):
                        usage = {
                            "cost_usd": message.total_cost_usd,
                            "duration_ms": message.duration_ms,
                            "turns": message.num_turns,
                        }
        except Exception as exc:
            raise GenerationProviderError("anthropic", "Claude Agent SDK request failed") from exc
        content = "\n".join(texts).strip()
        if not content:
            raise GenerationProviderError("anthropic", "Claude returned an empty response")
        return GenerationResult(
            content=content, provider="anthropic", model=self.model, usage=usage
        )
