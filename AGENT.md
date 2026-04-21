# AGENT.md

## Overview

`ragger` is a local multi-workspace RAG service for codebases and docs. It uses:

- Chroma for persistent local vector storage
- Ollama for embeddings and local answer generation
- FastAPI for the local HTTP server
- Textual for the local TUI
- a separate `pi-ragger/` TypeScript extension for Pi integration

## Important paths

- `ragger/core/`: canonical Python business logic
- `ragger/server/`: HTTP server
- `ragger/tui/`: TUI app and UI helpers
- `ragger/cli/`: CLI entrypoint
- `pi-ragger/`: Pi extension
- `tests/unit/`: stdlib `unittest` suite

`ragger/` is the only source of truth for Python application code.

## Local commands

Run the TUI:

```bash
python3 -m ragger.tui
```

Run the API server:

```bash
python3 -m ragger.server
```

Run the CLI:

```bash
python3 -m ragger.cli search default "Where is auth configured?"
```

Export OpenAPI:

```bash
.venv/bin/python scripts/export_openapi.py
```

The checked-in exported spec lives at `docs/openapi.json`.

Run tests:

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache .venv/bin/python -m unittest discover -s tests/unit -v
```

Format Python code:

```bash
.venv/bin/black ragger tests/unit scripts
```

## Notes for changes

- Default server port is `8170`.
- Default workspace is `default`.
- FastAPI is local-only by default.
- Reindexing a workspace replaces the previous collection by default.
- TUI and FastAPI should share the same core services, not call each other over HTTP.
- Keep Pi-facing server behavior retrieval-focused; Pi does final answer generation.

## Commit convention

This repo uses **semantic commit messages** as our convention.

Format:

```text
type(scope): short summary
```

Examples:

```text
feat(server): add OpenAPI export script
fix(core): normalize workspace stats for missing collections
docs(agent): document local commands and repo structure
test(server): cover workspace search endpoint
refactor(tui): split panel rendering helpers
```
