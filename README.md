# ragger

Local multi-workspace RAG for codebases and docs, backed by Chroma + Ollama.

## What it includes

- `python3 main.py`: Textual TUI for ingesting repos, inspecting retrieval hits, and chatting with Gemma through Ollama
- `python3 -m ragger_server`: local FastAPI server for external clients such as Pi extensions
- `python3 -m ragger_cli ...`: helper CLI for indexing, stats, and search
- `./pi-ragger/`: Pi extension that talks to the local FastAPI server

## Project layout

The main Python package now lives under `./ragger/`:

- `ragger/core/`: ingestion, workspace management, search, and health helpers
- `ragger/server/`: FastAPI app and routes
- `ragger/tui/`: Textual app plus UI helpers
- `ragger/cli/`: CLI entrypoint

Compatibility wrappers are still kept at the repo root:

- `main.py`
- `ragger_server.py`
- `ragger_cli.py`
- legacy import shims under `rag/` and `tui/`

## Basic usage

Start Ollama first and make sure the models you want are available, for example:

```bash
ollama run gemma4:26b
ollama pull nomic-embed-text
```

Run the TUI:

```bash
python3 main.py
```

Inside the TUI:

```text
/ingest default /path/to/repo
```

or:

```text
/ingest /path/to/repo
```

Then ask questions normally.

Run the API server:

```bash
python3 -m ragger_server
```

You can also use the package-native entrypoint:

```bash
python3 -m ragger.server.app
```

The default API base URL is:

```bash
http://127.0.0.1:8170
```

Swagger UI and ReDoc are available when the server is running:

```bash
http://127.0.0.1:8170/docs
http://127.0.0.1:8170/redoc
http://127.0.0.1:8170/openapi.json
```

Run the CLI:

```bash
python3 -m ragger_cli index default /path/to/repo
python3 -m ragger_cli stats default
python3 -m ragger_cli search default "Where is auth configured?"
```

Or the package-native CLI:

```bash
python3 -m ragger.cli.main index default /path/to/repo
```

## API curl examples

Index a workspace:

```bash
curl -sS http://127.0.0.1:8170/workspaces/index \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace": "book",
    "path": "/Users/hdkiller/Develop/pets/ragger/tmp/alice.txt",
    "replace": true
  }'
```

Fetch workspace status:

```bash
curl -sS http://127.0.0.1:8170/workspaces/book/status | jq
```

The older stats endpoint is still available too:

```bash
curl -sS http://127.0.0.1:8170/workspaces/book/stats | jq
```

Query a workspace:

```bash
curl -sS http://127.0.0.1:8170/workspaces/search \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace": "book",
    "query": "Who is Alice?",
    "k": 5
  }' | jq
```

List workspaces:

```bash
curl -sS http://127.0.0.1:8170/workspaces | jq
```

Check server health:

```bash
curl -sS http://127.0.0.1:8170/health | jq
```

Export the checked-in OpenAPI spec:

```bash
.venv/bin/python scripts/export_openapi.py
```

## Tests

Run the unit test suite with:

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache .venv/bin/python -m unittest discover -s tests -v
```

Current test coverage includes:

- ingestion and file filtering
- workspace/search delegation
- TUI command and panel helpers
- FastAPI route contracts

## Commit convention

This repo uses **semantic commit messages** as a convention.

Preferred format:

```text
type(scope): short summary
```

Examples:

```text
feat(server): add workspace status endpoint
fix(tui): show retrieval hits for active workspace
docs(readme): add curl examples for the local API
test(core): cover mixed file ingestion and exclusions
refactor(core): move workspace logic into package modules
```

Common types:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `chore`

## Indexed file types

`ragger` currently indexes:

- `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`
- `.md`, `.txt`
- `.json`, `.yaml`, `.yml`, `.toml`
- `.html`, `.css`, `.scss`

Common generated folders such as `node_modules`, `.nuxt`, `.next`, `dist`, and `coverage` are skipped by default.
