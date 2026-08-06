import unittest
from unittest.mock import patch

from app.services.vector_store_service import (
    query_similar_library,
    query_similar_task,
)


class FakeCollection:
    def __init__(self):
        self.query_kwargs = None

    def count(self):
        return 4

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return {
            "documents": [
                ["first-source-low", "first-source-medium"],
                ["second-source-high", "second-source-highest"],
            ],
            "metadatas": [
                [
                    {"report_id": "10", "block_id": "100", "start_char": "0", "end_char": "10"},
                    {"report_id": "11", "block_id": "110", "start_char": "0", "end_char": "10"},
                ],
                [
                    {"report_id": "40", "block_id": "400", "start_char": "0", "end_char": "10"},
                    {"report_id": "41", "block_id": "410", "start_char": "0", "end_char": "10"},
                ],
            ],
            "distances": [
                [0.3, 0.2],
                [0.1, 0.05],
            ],
        }


class VectorStoreGlobalTopKTest(unittest.TestCase):
    def assert_global_top_k(self, matches):
        self.assertEqual([match["similarity"] for match in matches], [0.95, 0.9])
        self.assertEqual([match["source_index"] for match in matches], [1, 1])
        self.assertEqual([match["target_report_id"] for match in matches], [41, 40])

    def test_task_query_ranks_candidates_globally(self):
        collection = FakeCollection()
        with patch(
            "app.services.vector_store_service._get_existing_collection",
            return_value=collection,
        ):
            matches = query_similar_task(
                query_vectors=[[0.0], [1.0]],
                task_id=1,
                top_k=2,
            )

        self.assert_global_top_k(matches)

    def test_library_query_ranks_candidates_globally(self):
        collection = FakeCollection()
        with patch(
            "app.services.vector_store_service._get_existing_library_collection",
            return_value=collection,
        ):
            matches = query_similar_library(
                query_vectors=[[0.0], [1.0]],
                user_id=7,
                top_k=2,
            )

        self.assert_global_top_k(matches)
        self.assertEqual(collection.query_kwargs["where"], {"user_id": "7"})

    def test_library_query_excludes_current_report(self):
        collection = FakeCollection()
        with patch(
            "app.services.vector_store_service._get_existing_library_collection",
            return_value=collection,
        ):
            matches = query_similar_library(
                query_vectors=[[0.0], [1.0]],
                user_id=7,
                top_k=4,
                exclude_report_ids={40, 41},
            )

        self.assertEqual([match["target_report_id"] for match in matches], [11, 10])
        self.assertEqual(
            collection.query_kwargs["where"],
            {
                "$and": [
                    {"user_id": "7"},
                    {"report_id": {"$nin": ["40", "41"]}},
                ]
            },
        )

    def test_task_query_excludes_current_report_before_search(self):
        collection = FakeCollection()
        with patch(
            "app.services.vector_store_service._get_existing_collection",
            return_value=collection,
        ):
            matches = query_similar_task(
                query_vectors=[[0.0], [1.0]],
                task_id=1,
                top_k=4,
                exclude_report_ids={40, 41},
            )

        self.assertEqual([match["target_report_id"] for match in matches], [11, 10])
        self.assertEqual(
            collection.query_kwargs["where"],
            {"report_id": {"$nin": ["40", "41"]}},
        )

    def test_task_query_can_keep_best_match_for_each_source(self):
        collection = FakeCollection()
        with patch(
            "app.services.vector_store_service._get_existing_collection",
            return_value=collection,
        ):
            matches = query_similar_task(
                query_vectors=[[0.0], [1.0]],
                task_id=1,
                top_k=1,
                per_source_limit=1,
            )

        self.assertEqual([match["source_index"] for match in matches], [1, 0])
        self.assertEqual([match["similarity"] for match in matches], [0.95, 0.8])


if __name__ == "__main__":
    unittest.main()
