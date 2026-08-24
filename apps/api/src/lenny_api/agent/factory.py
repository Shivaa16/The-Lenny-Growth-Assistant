from lenny_api.agent.providers import ClaudeAgentProvider, OllamaChatProvider
from lenny_api.agent.types import ChatProvider, GenerationProviderError
from lenny_api.config import Settings


def create_chat_provider(settings: Settings) -> ChatProvider:
    if settings.llm_provider == "ollama":
        return OllamaChatProvider(
            base_url=str(settings.ollama_base_url),
            model=settings.ollama_chat_model,
            timeout_seconds=settings.generation_timeout_seconds,
        )
    if not settings.anthropic_api_key or not settings.anthropic_model:
        raise GenerationProviderError(
            "anthropic", "Anthropic is selected but its key or model is not configured"
        )
    return ClaudeAgentProvider(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key.get_secret_value(),
        max_budget_usd=settings.anthropic_max_budget_usd,
        timeout_seconds=settings.generation_timeout_seconds,
    )

