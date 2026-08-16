import asyncio
import unittest
from datetime import datetime

import httpx

from app.services.embedding import (
    EmbeddingProviderError,
    EmbeddingService,
    OllamaEmbeddingProvider,
)
from app.services.vector_math import average_vectors
from scripts.seed_movies import (
    _embed_with_retry,
    embedding_is_current,
    embedding_text,
    embedding_text_hash,
    parse_list,
)


class RecordingProvider:
    def __init__(self, dimensions: int = 3) -> None:
        self.dimensions = dimensions
        self.calls: list[list[str]] = []
        self.closed = False

    async def embed(self, texts):
        self.calls.append(list(texts))
        return [[float(index)] * self.dimensions for index, _ in enumerate(texts)]

    async def health(self):
        return {"provider": "recording"}

    async def close(self):
        self.closed = True


class EmbeddingServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_batches_documents_and_preserves_order(self):
        provider = RecordingProvider()
        service = EmbeddingService(
            provider,
            model="test-model",
            dimensions=3,
            batch_size=2,
        )

        result = await service.embed_documents(["one", "two", "three"])

        self.assertEqual(provider.calls, [["one", "two"], ["three"]])
        self.assertEqual(result, [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]])

    async def test_query_prefix_is_applied_only_to_queries(self):
        provider = RecordingProvider()
        service = EmbeddingService(
            provider,
            model="test-model",
            dimensions=3,
            query_prefix="Query: ",
        )

        await service.embed_query("science fiction")
        await service.embed_documents(["A movie overview"])

        self.assertEqual(
            provider.calls,
            [["Query: science fiction"], ["A movie overview"]],
        )

    async def test_rejects_dimension_mismatch(self):
        provider = RecordingProvider(dimensions=2)
        service = EmbeddingService(
            provider,
            model="test-model",
            dimensions=3,
        )

        with self.assertRaisesRegex(EmbeddingProviderError, "dimension mismatch"):
            await service.embed_query("query")

    async def test_reuses_cached_query_embedding_and_returns_a_copy(self):
        provider = RecordingProvider()
        service = EmbeddingService(
            provider,
            model="test-model",
            dimensions=3,
            query_cache_size=2,
            query_cache_ttl_seconds=60,
        )

        first = await service.embed_query("science fiction")
        first[0] = 999
        second = await service.embed_query("science fiction")

        self.assertEqual(provider.calls, [["science fiction"]])
        self.assertEqual(second, [0.0, 0.0, 0.0])
        self.assertEqual(service.query_cache_info()["hits"], 1)

    async def test_evicts_least_recent_query_when_cache_is_full(self):
        provider = RecordingProvider()
        service = EmbeddingService(
            provider,
            model="test-model",
            dimensions=3,
            query_cache_size=1,
            query_cache_ttl_seconds=60,
        )

        await service.embed_query("first")
        await service.embed_query("second")
        await service.embed_query("first")

        self.assertEqual(len(provider.calls), 3)
        self.assertEqual(service.query_cache_info()["evictions"], 2)

    async def test_refreshes_query_after_cache_ttl_expires(self):
        provider = RecordingProvider()
        service = EmbeddingService(
            provider,
            model="test-model",
            dimensions=3,
            query_cache_size=2,
            query_cache_ttl_seconds=0.01,
        )

        await service.embed_query("short lived")
        await asyncio.sleep(0.02)
        await service.embed_query("short lived")

        self.assertEqual(len(provider.calls), 2)


class OllamaProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_batch_embed_endpoint_and_reports_health(self):
        requests = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/api/embed":
                return httpx.Response(200, json={"embeddings": [[1, 2], [3, 4]]})
            return httpx.Response(
                200,
                json={"models": [{"name": "qwen3-embedding:0.6b"}]},
            )

        client = httpx.AsyncClient(
            base_url="http://ollama.test",
            transport=httpx.MockTransport(handler),
        )
        provider = OllamaEmbeddingProvider(
            "http://ollama.test",
            "qwen3-embedding:0.6b",
            client=client,
        )
        try:
            vectors = await provider.embed(["one", "two"])
            health = await provider.health()
        finally:
            await client.aclose()

        self.assertEqual(vectors, [[1, 2], [3, 4]])
        self.assertTrue(health["model_installed"])
        self.assertEqual(
            [request.url.path for request in requests], ["/api/embed", "/api/tags"]
        )
        self.assertEqual(requests[0].read().decode().count('"keep_alive":"30m"'), 1)


class VectorMathTests(unittest.TestCase):
    def test_averages_vectors_without_numpy(self):
        self.assertEqual(average_vectors([[1, 2], [3, 6]]), [2.0, 4.0])

    def test_rejects_mixed_dimensions(self):
        with self.assertRaisesRegex(ValueError, "same dimensions"):
            average_vectors([[1, 2], [3]])


class MovieImportTests(unittest.TestCase):
    def test_parses_pipe_and_comma_separated_list_formats(self):
        self.assertEqual(parse_list("Drama|Thriller"), ["Drama", "Thriller"])
        self.assertEqual(
            parse_list("Action, Science Fiction, Adventure"),
            ["Action", "Science Fiction", "Adventure"],
        )

    def test_builds_labeled_embedding_text_like_the_old_migration(self):
        text = embedding_text(
            {
                "title": "Inception",
                "original_title": "Inception",
                "overview": "A dream heist.",
                "genres": ["Action", "Science Fiction"],
                "keywords": ["dream", "heist"],
                "tagline": "Your mind is the scene of the crime.",
                "release_date": datetime(2010, 7, 15),
                "adult": False,
            }
        )

        self.assertIn("Original Title: Inception", text)
        self.assertIn("Genres: Action, Science Fiction", text)
        self.assertIn("Keywords: dream, heist", text)
        self.assertIn("Released in 2010", text)
        self.assertNotIn("Adult Content", text)

    def test_embedding_hash_is_stable_and_changes_with_text(self):
        first = embedding_text_hash("movie text  \n")
        self.assertEqual(first, embedding_text_hash("movie text"))
        self.assertNotEqual(first, embedding_text_hash("changed movie text"))

    def test_embedding_is_current_requires_matching_metadata_and_dimensions(self):
        text_hash = embedding_text_hash("movie")
        existing = {
            "embedding": [1.0, 2.0],
            "embedding_model": "model-a",
            "embedding_dimensions": 2,
            "embedding_text_hash": text_hash,
        }
        self.assertTrue(
            embedding_is_current(
                existing, model="model-a", dimensions=2, text_hash=text_hash
            )
        )
        self.assertFalse(
            embedding_is_current(
                existing, model="model-b", dimensions=2, text_hash=text_hash
            )
        )


class FlakyBatchService:
    def __init__(self):
        self.calls = []

    async def embed_documents(self, texts):
        self.calls.append(list(texts))
        if "bad" in texts:
            raise EmbeddingProviderError("bad input")
        return [[float(len(text))] for text in texts]


class MovieEmbeddingRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_splits_failed_batch_and_can_skip_one_bad_movie(self):
        service = FlakyBatchService()
        result = await _embed_with_retry(
            service,
            ["good", "bad", "also good"],
            max_retries=0,
            continue_on_error=True,
        )
        self.assertEqual(result, [[4.0], None, [9.0]])
        self.assertIn(["bad"], service.calls)


if __name__ == "__main__":
    unittest.main()
