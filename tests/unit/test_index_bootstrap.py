import unittest
from unittest.mock import Mock, patch

from pymongo.errors import OperationFailure

from scripts.create_vector_indexes import search_indexes


class IndexBootstrapTests(unittest.TestCase):
    def test_search_service_startup_is_retried(self):
        collection = Mock()
        collection.list_search_indexes.side_effect = [
            OperationFailure(
                "Error connecting to Search Index Management service.", 125
            ),
            iter([{"name": "movie_vector_index"}]),
        ]
        with (
            patch("scripts.create_vector_indexes.time.monotonic", return_value=0),
            patch("scripts.create_vector_indexes.time.sleep"),
        ):
            self.assertEqual(
                search_indexes(collection, deadline=10, poll_interval=1),
                [{"name": "movie_vector_index"}],
            )
        self.assertEqual(collection.list_search_indexes.call_count, 2)

    def test_permission_errors_are_not_retried(self):
        collection = Mock()
        collection.list_search_indexes.side_effect = OperationFailure(
            "Unauthorized", 13
        )
        with self.assertRaises(OperationFailure):
            search_indexes(collection, deadline=10, poll_interval=1)
        self.assertEqual(collection.list_search_indexes.call_count, 1)

    def test_startup_timeout_is_bounded(self):
        collection = Mock()
        collection.list_search_indexes.side_effect = OperationFailure(
            "Error connecting to Search Index Management service.", 125
        )
        with patch("scripts.create_vector_indexes.time.monotonic", return_value=11):
            with self.assertRaises(TimeoutError):
                search_indexes(collection, deadline=10, poll_interval=1)
