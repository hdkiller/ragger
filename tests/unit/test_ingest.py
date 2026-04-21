import tempfile
import unittest
from pathlib import Path

from ragger.core.ingest import CodebaseIngestor


class CodebaseIngestorTests(unittest.TestCase):
    def test_prepare_documents_indexes_supported_files_and_skips_excluded_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "node_modules").mkdir()
            (root / ".nuxt").mkdir()
            (root / ".hidden").mkdir()
            (root / "src" / "app.ts").write_text(
                "export const greet = (name: string) => `hi ${name}`;\n"
            )
            (root / "src" / "App.vue").write_text(
                "<template><div>{{ title }}</div></template>\n<script setup lang=\"ts\">const title = 'hi'</script>\n"
            )
            (root / "docs" / "guide.md").write_text("# Guide\n\nThe app greets Alice.\n")
            (root / "notes.txt").write_text("Alice uses the greet helper.\n")
            (root / "package.json").write_text('{"name":"demo"}\n')
            (root / "node_modules" / "ignored.ts").write_text("export const nope = true;\n")
            (root / ".nuxt" / "generated.ts").write_text("export const generated = true;\n")
            (root / ".hidden" / "secret.ts").write_text("export const secret = true;\n")

            ingestor = CodebaseIngestor(chunk_size=80, chunk_overlap=0)
            prepared = ingestor.prepare_documents(str(root), workspace="demo")

            self.assertEqual(prepared.file_count, 5)
            self.assertEqual(prepared.indexed_extensions, [".json", ".md", ".ts", ".txt", ".vue"])
            self.assertGreaterEqual(prepared.chunk_count, 5)
            self.assertTrue(
                all("node_modules" not in doc.metadata["source"] for doc in prepared.documents)
            )
            self.assertTrue(
                all(".nuxt" not in doc.metadata["source"] for doc in prepared.documents)
            )
            self.assertTrue(
                all("/.hidden/" not in doc.metadata["source"] for doc in prepared.documents)
            )

    def test_prepare_documents_populates_workspace_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "alice.txt"
            file_path.write_text("Alice falls down the rabbit hole.\n")

            ingestor = CodebaseIngestor(chunk_size=50, chunk_overlap=0)
            prepared = ingestor.prepare_documents(str(file_path), workspace="book")

            self.assertEqual(prepared.file_count, 1)
            self.assertEqual(Path(prepared.root_path), Path(tmp).resolve())
            self.assertEqual(len(prepared.documents), 1)
            metadata = prepared.documents[0].metadata
            self.assertEqual(metadata["workspace"], "book")
            self.assertEqual(metadata["relative_path"], "alice.txt")
            self.assertEqual(metadata["extension"], ".txt")
            self.assertEqual(metadata["language"], "text")


if __name__ == "__main__":
    unittest.main()
