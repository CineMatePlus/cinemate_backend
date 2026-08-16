import unittest

from app.db.mongodb import (
    VectorSearchIndexNotReadyError,
    inspect_vector_search_indexes,
    verify_vector_search_indexes_ready,
)
from app.services.movie import MovieService
from app.services.vector_search import (
    VectorSearchMetrics,
    build_vector_search_stage,
    calculate_num_candidates,
)


class VectorSearchBuilderTests(unittest.TestCase):
    def test_candidates_scale_with_limit_and_respect_bounds(self):
        self.assertEqual(calculate_num_candidates(1), 100)
        self.assertEqual(calculate_num_candidates(10), 200)
        self.assertEqual(calculate_num_candidates(100), 1000)
        self.assertEqual(calculate_num_candidates(2000), 2000)

    def test_stage_uses_shared_dynamic_candidate_policy(self):
        stage = build_vector_search_stage(
            index="movies", query_vector=[1.0, 2.0], limit=10
        )
        self.assertEqual(stage["$vectorSearch"]["numCandidates"], 200)
        self.assertEqual(stage["$vectorSearch"]["limit"], 10)

    def test_movie_response_projection_excludes_embedding(self):
        pipeline = MovieService._movie_response_pipeline()
        self.assertIn({"$project": {"embedding": 0}}, pipeline)


class VectorSearchMetricsTests(unittest.TestCase):
    def test_reports_latency_and_similarity_distribution(self):
        metrics = VectorSearchMetrics(window_size=2)
        metrics.record("movies", 0.01, [{"score": 0.5}, {"score": 0.9}], "score")
        metrics.record("movies", 0.02, [{"score": 0.7}], "score")

        result = metrics.snapshot()["operations"]["movies"]

        self.assertEqual(result["query_count"], 2)
        self.assertEqual(result["latency_ms"]["mean"], 15.0)
        self.assertEqual(result["similarity"]["count"], 3)
        self.assertAlmostEqual(result["similarity"]["mean"], 0.7)


class FakeSearchIndexCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, length=None):
        return self.documents


class FakeCollection:
    def __init__(self, indexes):
        self.indexes = indexes

    def list_search_indexes(self):
        return FakeSearchIndexCursor(self.indexes)


class FakeDatabase:
    def __init__(self, movies, users):
        self.collections = {
            "movies": FakeCollection(movies),
            "users": FakeCollection(users),
        }

    def __getitem__(self, name):
        return self.collections[name]


class VectorSearchReadinessTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_required_ready_indexes(self):
        database = FakeDatabase(
            [{"name": "movie_vector_index", "status": "READY", "queryable": True}],
            [{"name": "user_vector_index", "status": "READY", "queryable": True}],
        )

        statuses = await inspect_vector_search_indexes(database)
        await verify_vector_search_indexes_ready(database)

        self.assertTrue(all(item["ready"] for item in statuses))

    async def test_rejects_missing_or_building_index(self):
        database = FakeDatabase(
            [{"name": "movie_vector_index", "status": "BUILDING"}],
            [],
        )

        with self.assertRaisesRegex(VectorSearchIndexNotReadyError, "not READY"):
            await verify_vector_search_indexes_ready(database)


if __name__ == "__main__":
    unittest.main()
