import tempfile
import unittest
from pathlib import Path

from ragger.tui.commands import (
    parse_ingest_args,
    parse_list_args,
    parse_workspace_arg,
    render_clear_result,
    render_help_text,
    render_workspace_stats_text,
    render_workspace_file_list,
    render_workspaces_overview,
)


class ParseIngestArgsTests(unittest.TestCase):
    def test_render_help_text_mentions_supported_commands(self):
        output = render_help_text("default")

        self.assertIn("/ingest <path>", output)
        self.assertIn("/workspace <name>", output)
        self.assertIn("/list", output)
        self.assertIn("/workspaces", output)
        self.assertIn("/stats", output)
        self.assertIn("/clear", output)
        self.assertIn("/help", output)
        self.assertIn("Active workspace: `default`", output)

    def test_parse_list_args_uses_current_workspace_when_empty(self):
        self.assertEqual(parse_list_args("", "default"), "default")
        self.assertEqual(parse_list_args(" books ", "default"), "books")

    def test_parse_workspace_arg_uses_current_workspace_when_empty(self):
        self.assertEqual(parse_workspace_arg("", "default"), "default")
        self.assertEqual(parse_workspace_arg(" demo ", "default"), "demo")

    def test_render_workspace_file_list_includes_files(self):
        output = render_workspace_file_list(
            "default",
            [
                {"relative_path": "ragger/core/workspaces.py", "language": "python", "chunk_count": 6},
                {"relative_path": "README.md", "language": "markdown", "chunk_count": None},
            ],
        )

        self.assertIn("Indexed Files: `default`", output)
        self.assertIn("ragger/core/workspaces.py", output)
        self.assertIn("6 chunks", output)
        self.assertIn("chunk count unavailable", output)

    def test_render_workspace_stats_text_includes_core_fields(self):
        output = render_workspace_stats_text(
            "default",
            {
                "root_path": "/tmp/demo",
                "file_count": 10,
                "chunk_count": 22,
                "indexed_extensions": [".md", ".py"],
                "collection_name": "ragger_default",
                "last_indexed_at": "2026-04-22T10:00:00Z",
                "model": "gemma4:26b",
                "embedding_model": "nomic-embed-text",
            },
        )

        self.assertIn("Workspace Stats: `default`", output)
        self.assertIn("Files: **10**", output)
        self.assertIn("Collection: `ragger_default`", output)

    def test_render_workspaces_overview_lists_multiple_workspaces(self):
        output = render_workspaces_overview(
            [
                {
                    "workspace": "default",
                    "root_path": "/tmp/default",
                    "file_count": 10,
                    "chunk_count": 20,
                    "last_indexed_at": "2026-04-22T10:00:00Z",
                },
                {
                    "workspace": "docs",
                    "root_path": "/tmp/docs",
                    "file_count": 5,
                    "chunk_count": 11,
                    "last_indexed_at": "2026-04-22T10:05:00Z",
                },
            ]
        )

        self.assertIn("Indexed workspaces: **2**", output)
        self.assertIn("`default`", output)
        self.assertIn("`docs`", output)

    def test_render_clear_result_describes_outcome(self):
        deleted_output = render_clear_result("default", True)
        missing_output = render_clear_result("default", False)

        self.assertIn("Workspace removed from Chroma", deleted_output)
        self.assertIn("matching collection cleanup was attempted", missing_output)

    def test_uses_current_workspace_when_given_existing_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "my file.txt"
            file_path.write_text("hello\n")

            workspace, resolved = parse_ingest_args(str(file_path), "default")

            self.assertEqual(workspace, "default")
            self.assertEqual(resolved, file_path.resolve())

    def test_parses_explicit_workspace_and_relative_path(self):
        workspace, resolved = parse_ingest_args("book tmp/alice.txt", "default")

        self.assertEqual(workspace, "book")
        self.assertEqual(resolved.name, "alice.txt")
        self.assertTrue(str(resolved).endswith("tmp/alice.txt"))

    def test_empty_args_raise_helpful_error(self):
        with self.assertRaisesRegex(ValueError, "Usage: /ingest"):
            parse_ingest_args("   ", "default")


if __name__ == "__main__":
    unittest.main()
