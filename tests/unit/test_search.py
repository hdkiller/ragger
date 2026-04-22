import unittest
from unittest.mock import Mock

from ragger.core.search import RAGEngine


class RAGEngineTests(unittest.TestCase):
    def test_retrieve_delegates_to_manager_with_active_workspace(self):
        manager = Mock()
        manager.model_name = "gemma4:26b"
        manager.embedding_model = "nomic-embed-text"
        manager.persist_directory = "./.chroma_db"
        manager.retrieve_documents.return_value = ["doc1"]

        engine = RAGEngine(manager=manager, workspace="book")
        result = engine.retrieve("Who is Alice?")

        self.assertEqual(result, ["doc1"])
        manager.retrieve_documents.assert_called_once_with(
            workspace="book", query="Who is Alice?", k=5
        )

    def test_get_stats_adds_workspace_key(self):
        manager = Mock()
        manager.model_name = "gemma4:26b"
        manager.embedding_model = "nomic-embed-text"
        manager.persist_directory = "./.chroma_db"
        manager.get_workspace_stats.return_value = {"chunk_count": 10}

        engine = RAGEngine(manager=manager, workspace="book")
        result = engine.get_stats()

        self.assertEqual(result["workspace"], "book")
        self.assertEqual(result["chunk_count"], 10)

    def test_list_workspace_files_delegates_to_manager(self):
        manager = Mock()
        manager.model_name = "gemma4:26b"
        manager.embedding_model = "nomic-embed-text"
        manager.persist_directory = "./.chroma_db"
        manager.list_workspace_files.return_value = [{"relative_path": "alice.txt"}]

        engine = RAGEngine(manager=manager, workspace="book")
        result = engine.list_workspace_files()

        self.assertEqual(result, [{"relative_path": "alice.txt"}])
        manager.list_workspace_files.assert_called_once_with("book")


if __name__ == "__main__":
    unittest.main()
