from collections.abc import Sequence

import httpx


class EmbeddingProviderError(RuntimeError):
    pass


class OllamaEmbeddingProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        expected_dimension: int,
        timeout_seconds: float = 60,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.expected_dimension = expected_dimension
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds, transport=self.transport
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": list(texts), "truncate": True},
                )
                response.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            raise EmbeddingProviderError(
                f"Ollama embedding model '{self.model}' is unavailable"
            ) from exc

        embeddings = response.json().get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingProviderError("Ollama returned an invalid embedding response")
        if any(len(vector) != self.expected_dimension for vector in embeddings):
            raise EmbeddingProviderError(
                f"Embedding dimension did not match expected {self.expected_dimension}"
            )
        return embeddings
