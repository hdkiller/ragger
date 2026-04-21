import unittest
from types import SimpleNamespace

from ragger.tui.panels import render_retrieval_panel, render_stats_panel


class PanelRenderingTests(unittest.TestCase):
    def test_render_stats_panel_for_unindexed_workspace(self):
        output = render_stats_panel(
            current_workspace="default",
            health={"ollama": {"reachable": True}},
            stats=None,
            last_ingest_summary="No ingestion yet.",
        )

        self.assertIn("Status: not indexed yet", output)
        self.assertIn("Ollama: `up`", output)

    def test_render_stats_panel_for_indexed_workspace(self):
        output = render_stats_panel(
            current_workspace="book",
            health={"ollama": {"reachable": False}},
            stats={
                "root_path": "/tmp/alice",
                "file_count": 1,
                "chunk_count": 94,
                "indexed_extensions": [".txt"],
                "collection_name": "ragger_book",
                "last_indexed_at": "2026-04-21T00:00:00Z",
                "model": "gemma4:26b",
                "embedding_model": "nomic-embed-text",
            },
            last_ingest_summary="Last ingest: `book` with 1 files / 94 chunks",
        )

        self.assertIn("Active: `book`", output)
        self.assertIn("Chunks: **94**", output)
        self.assertIn("Ollama: `down`", output)

    def test_render_retrieval_panel_includes_hit_previews(self):
        docs = [
            SimpleNamespace(
                page_content="Alice follows the white rabbit into wonderland.",
                metadata={"relative_path": "alice.txt", "language": "text"},
            )
        ]

        output = render_retrieval_panel(docs, "book")

        self.assertIn("Using workspace `book`", output)
        self.assertIn("Source: `alice.txt`", output)
        self.assertIn("Alice follows the white rabbit", output)


if __name__ == "__main__":
    unittest.main()
