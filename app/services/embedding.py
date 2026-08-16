"""Hardware-independent embedding providers used by the API and data tools."""

from __future__ import annotations

import asyncio
import math
from collections import OrderedDict
from functools import lru_cache
from time import monotonic
from typing import Any, Protocol, Sequence

import httpx

from app.core.config import settings


class EmbeddingProviderError(RuntimeError):
    """The configured embedding provider is unavailable or returned invalid data."""


class EmbeddingProvider(Protocol):
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding per input text in the same order."""

    async def health(self) -> dict[str, Any]:
        """Return provider health information or raise EmbeddingProviderError."""

    async def close(self) -> None:
        """Release provider resources."""


class OllamaEmbeddingProvider:
    """Async client for Ollama's native batch embedding API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 30,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self._client.post(
                "/api/embed",
                json={"model": self.model, "input": list(texts)},
            )
            response.raise_for_status()
            payload = response.json()
            embeddings = payload.get("embeddings")
            if not isinstance(embeddings, list):
                raise EmbeddingProviderError(
                    "Ollama response does not contain an embeddings array."
                )
            return embeddings
        except EmbeddingProviderError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise EmbeddingProviderError(
                f"Could not generate embeddings with Ollama at {self.base_url}: {exc}"
            ) from exc

    async def health(self) -> dict[str, Any]:
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise EmbeddingProviderError(
                f"Could not reach Ollama at {self.base_url}: {exc}"
            ) from exc

        installed_models = {
            value
            for item in payload.get("models", [])
            if isinstance(item, dict)
            for value in (item.get("name"), item.get("model"))
            if isinstance(value, str)
        }
        return {
            "provider": "ollama",
            "base_url": self.base_url,
            "model": self.model,
            "model_installed": self.model in installed_models,
        }

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class EmbeddingService:
    """Adds batching, query instructions and strict vector validation."""

    def __init__(
        self,
        provider: EmbeddingProvider,
        *,
        model: str,
        dimensions: int,
        batch_size: int = 32,
        query_prefix: str = "",
        query_cache_size: int = 512,
        query_cache_ttl_seconds: float = 600,
    ) -> None:
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive.")
        if batch_size <= 0:
            raise ValueError("Embedding batch size must be positive.")
        self.provider = provider
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size
        self.query_prefix = query_prefix
        self.query_cache_size = max(0, query_cache_size)
        self.query_cache_ttl_seconds = max(0.0, query_cache_ttl_seconds)
        self._query_cache: OrderedDict[str, tuple[float, list[float]]] = OrderedDict()
        self._query_inflight: dict[str, asyncio.Task[list[list[float]]]] = {}
        self._query_cache_lock = asyncio.Lock()
        self._query_cache_hits = 0
        self._query_cache_misses = 0
        self._query_cache_evictions = 0
        self._query_cache_coalesced = 0

    async def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingProviderError("The embedding query cannot be empty.")
        prepared = f"{self.query_prefix}{text}" if self.query_prefix else text
        if self.query_cache_size == 0 or self.query_cache_ttl_seconds == 0:
            return (await self._embed_many([prepared]))[0]

        now = monotonic()
        async with self._query_cache_lock:
            cached = self._query_cache.get(prepared)
            if cached is not None:
                expires_at, vector = cached
                if expires_at > now:
                    self._query_cache.move_to_end(prepared)
                    self._query_cache_hits += 1
                    return list(vector)
                del self._query_cache[prepared]

            task = self._query_inflight.get(prepared)
            if task is None:
                task = asyncio.create_task(self._embed_many([prepared]))
                self._query_inflight[prepared] = task
                self._query_cache_misses += 1
            else:
                self._query_cache_coalesced += 1

        try:
            vector = (await task)[0]
        except BaseException:
            async with self._query_cache_lock:
                if self._query_inflight.get(prepared) is task:
                    del self._query_inflight[prepared]
            raise

        async with self._query_cache_lock:
            if prepared not in self._query_cache:
                self._query_cache[prepared] = (
                    monotonic() + self.query_cache_ttl_seconds,
                    list(vector),
                )
                while len(self._query_cache) > self.query_cache_size:
                    self._query_cache.popitem(last=False)
                    self._query_cache_evictions += 1
            if self._query_inflight.get(prepared) is task:
                del self._query_inflight[prepared]
        return list(vector)

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if any(not text.strip() for text in texts):
            raise EmbeddingProviderError("Embedding documents cannot be empty.")
        return await self._embed_many(list(texts))

    async def warmup(self) -> None:
        await self.embed_query("CineMate embedding service warmup")

    async def health(self) -> dict[str, Any]:
        result = await self.provider.health()
        result["embedding_dimensions"] = self.dimensions
        result["query_cache"] = self.query_cache_info()
        return result

    async def close(self) -> None:
        async with self._query_cache_lock:
            tasks = list(self._query_inflight.values())
            self._query_inflight.clear()
            self._query_cache.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.provider.close()

    def query_cache_info(self) -> dict[str, int | float]:
        return {
            "size": len(self._query_cache),
            "max_size": self.query_cache_size,
            "ttl_seconds": self.query_cache_ttl_seconds,
            "hits": self._query_cache_hits,
            "misses": self._query_cache_misses,
            "evictions": self._query_cache_evictions,
            "coalesced": self._query_cache_coalesced,
        }

    async def _embed_many(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            vectors = await self.provider.embed(batch)
            if len(vectors) != len(batch):
                raise EmbeddingProviderError(
                    f"Provider returned {len(vectors)} vectors for {len(batch)} texts."
                )
            results.extend(self._validate_vector(vector) for vector in vectors)
        return results

    def _validate_vector(self, vector: Any) -> list[float]:
        if not isinstance(vector, list) or len(vector) != self.dimensions:
            actual = len(vector) if isinstance(vector, list) else "non-list"
            raise EmbeddingProviderError(
                f"Embedding dimension mismatch: expected {self.dimensions}, got {actual}."
            )
        try:
            converted = [float(value) for value in vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingProviderError(
                "Embedding contains a non-numeric value."
            ) from exc
        if not all(math.isfinite(value) for value in converted):
            raise EmbeddingProviderError("Embedding contains a non-finite value.")
        return converted


def create_embedding_service() -> EmbeddingService:
    if settings.EMBEDDING_PROVIDER != "ollama":
        raise ValueError(
            f"Unsupported EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER!r}"
        )
    provider = OllamaEmbeddingProvider(
        base_url=settings.EMBEDDING_BASE_URL,
        model=settings.EMBEDDING_MODEL,
        timeout_seconds=settings.EMBEDDING_TIMEOUT_SECONDS,
    )
    return EmbeddingService(
        provider,
        model=settings.EMBEDDING_MODEL,
        dimensions=settings.EMBEDDING_DIMENSIONS,
        batch_size=settings.EMBEDDING_BATCH_SIZE,
        query_prefix=settings.EMBEDDING_QUERY_PREFIX,
        query_cache_size=settings.EMBEDDING_QUERY_CACHE_SIZE,
        query_cache_ttl_seconds=settings.EMBEDDING_QUERY_CACHE_TTL_SECONDS,
    )


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return create_embedding_service()


async def close_embedding_service() -> None:
    if get_embedding_service.cache_info().currsize:
        await get_embedding_service().close()
        get_embedding_service.cache_clear()
