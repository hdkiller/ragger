# Plan - Local Codebase RAG with Gemma 4

## Objective
Create a lightweight, local RAG (Retrieval-Augmented Generation) stack in Python to experiment with the **Gemma 4 26B A4B-it** model. The system will ingest a local codebase into a vector database and provide a Terminal User Interface (TUI) for interaction.

## Proposed Stack
- **Language:** Python 3.12+
- **Package Manager:** `uv` (modern, fast replacement for pip)
- **LLM Engine:** Ollama (hosting Gemma 4 locally)
- **RAG Framework:** LangChain / LangGraph
- **Vector Database:** ChromaDB (local persistence)
- **Embeddings:** `nomic-embed-text` (via Ollama) or `HuggingFaceEmbeddings`
- **TUI Framework:** Textual

## Key Files & Context
- `pyproject.toml`: Project metadata and dependencies.
- `rag/`: Core RAG logic (ingestion, retrieval, chain).
- `tui/`: Textual interface implementation.
- `ingest.py`: CLI script for codebase indexing.
- `main.py`: Entry point for the TUI.

## Implementation Steps

### 1. Project Initialization
- Create `pyproject.toml` with dependencies: `langchain`, `langchain-community`, `chromadb`, `textual`, `ollama`, `beautifulsoup4` (for some loaders).
- Initialize git repository and `.gitignore`.
- Set up the virtual environment using `uv`.

### 2. Ollama Setup
- Verify Ollama installation.
- Pull or create `Modelfile` for `gemma-4-26b-a4b-it`.
- Pull `nomic-embed-text` for local embeddings.

### 3. Ingestion Engine (`rag/ingestor.py`)
- Implement `CodebaseIngestor` using LangChain's `LanguageParser`.
- Support language-aware splitting (Python, JS/TS, etc.).
- Store vectors in `./.chroma_db`.

### 4. RAG Chain (`rag/engine.py`)
- Setup Ollama LLM integration.
- Implement the retrieval chain with a custom prompt optimized for coding questions.
- Add "Thinking Mode" support if applicable to the model's performance.

### 5. TUI Development (`tui/app.py`)
- Create a `Textual` app with:
    - Input box for queries.
    - Markdown display for streaming responses.
    - Status bar/sidebar for ingestion progress.

## Verification & Testing
- **Ingestion Test:** Index a small repo and verify ChromaDB contents.
- **Retrieval Test:** Query the DB for a known function name and check if it's retrieved.
- **Inference Test:** Run a basic prompt through the Gemma 4 Ollama instance.
- **End-to-End:** Run the TUI and ask "How does the ingestion work?"
