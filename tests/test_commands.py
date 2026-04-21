import tempfile
import unittest
from pathlib import Path

from ragger.tui.commands import parse_ingest_args


class ParseIngestArgsTests(unittest.TestCase):
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
