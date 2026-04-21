import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from ragger.server.app import app


class ServerRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_returns_manager_status(self):
        fake_health = {
            "status": "ok",
            "persist_directory": "./.chroma_db",
            "workspace_count": 1,
            "embedding_model": "nomic-embed-text",
            "model": "gemma4:26b",
            "ollama": {
                "reachable": True,
                "base_url": "http://localhost:11434",
                "models": ["gemma4:26b"],
            },
        }
        with patch("ragger.server.app.manager.get_health", return_value=fake_health):
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_health)

    def test_index_endpoint_returns_duration_and_stats(self):
        fake_stats = {
            "workspace": "book",
            "root_path": "/tmp/alice.txt",
            "collection_name": "ragger_book",
            "file_count": 1,
            "chunk_count": 94,
            "indexed_extensions": [".txt"],
            "last_indexed_at": "2026-04-21T00:00:00Z",
            "embedding_model": "nomic-embed-text",
            "model": "gemma4:26b",
        }
        with patch("ragger.server.app.manager.ingest_workspace", return_value=fake_stats):
            response = self.client.post(
                "/workspaces/index",
                json={"workspace": "book", "path": "/tmp/alice.txt", "replace": True},
            )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["workspace"], "book")
        self.assertIn("duration_seconds", body)

    def test_search_endpoint_returns_results(self):
        fake_results = [
            {
                "source": "/tmp/alice.txt",
                "relative_path": "alice.txt",
                "workspace": "book",
                "extension": ".txt",
                "language": "text",
                "score": 0.1,
                "content_preview": "Alice was beginning to get very tired...",
                "content": "Alice was beginning to get very tired of sitting by her sister on the bank.",
            }
        ]
        with patch("ragger.server.app.manager.search_workspace", return_value=fake_results):
            response = self.client.post(
                "/workspaces/search",
                json={"workspace": "book", "query": "Who is Alice?", "k": 5},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], fake_results)

    def test_status_alias_uses_same_workspace_stats(self):
        fake_stats = {
            "workspace": "book",
            "root_path": "/tmp/alice.txt",
            "collection_name": "ragger_book",
            "file_count": 1,
            "chunk_count": 94,
            "indexed_extensions": [".txt"],
            "last_indexed_at": "2026-04-21T00:00:00Z",
            "embedding_model": "nomic-embed-text",
            "model": "gemma4:26b",
        }
        with patch("ragger.server.app.manager.get_workspace_stats", return_value=fake_stats):
            response = self.client.get("/workspaces/book/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workspace"], "book")


if __name__ == "__main__":
    unittest.main()
