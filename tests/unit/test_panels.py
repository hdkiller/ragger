import unittest
from types import SimpleNamespace

from ragger.tui.panels import (
    render_ingest_progress,
    render_retrieval_panel,
    render_stats_panel,
    render_workspace_browser,
)


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

    def test_render_workspace_browser_includes_workspaces_and_files(self):
        output = render_workspace_browser(
            workspaces=[
                {"workspace": "book", "file_count": 2, "chunk_count": 8},
                {"workspace": "notes", "file_count": 1, "chunk_count": 3},
            ],
            current_workspace="book",
            files=[
                {"relative_path": "alice.txt", "language": "text", "chunk_count": 4},
                {"relative_path": "chapter1.md", "language": "markdown", "chunk_count": 4},
            ],
        )

        self.assertIn("`book` (active): 2 files / 8 chunks", output)
        self.assertIn("`notes`: 1 files / 3 chunks", output)
        self.assertIn("`alice.txt` [text, 4 chunks]", output)

    def test_render_workspace_browser_handles_empty_state(self):
        output = render_workspace_browser(
            workspaces=[],
            current_workspace="default",
            files=[],
        )

        self.assertIn("No indexed workspaces yet.", output)
        self.assertIn("Use `/ingest <path>` to add one.", output)

    def test_render_ingest_progress_shows_bar_and_file(self):
        output = render_ingest_progress(
            workspace="default",
            current_file=3,
            total_files=6,
            current_path="ragger/core/workspaces.py",
            active=True,
        )

        self.assertIn("Workspace: `default`", output)
        self.assertIn("3/6", output)
        self.assertIn("ragger/core/workspaces.py", output)

    def test_render_ingest_progress_idle_state(self):
        output = render_ingest_progress(
            workspace="default",
            current_file=None,
            total_files=None,
            current_path=None,
            active=False,
        )

        self.assertIn("Idle.", output)


if __name__ == "__main__":
    unittest.main()
