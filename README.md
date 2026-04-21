# ragger

Local multi-workspace RAG for codebases and docs, built around Chroma, Ollama, a FastAPI server, and a terminal-first TUI.

`ragger` gives you three ways to work with the same local retrieval stack:

- a Textual TUI for indexing repos and exploring results interactively
- a FastAPI server for external clients and editor tooling
- a CLI for indexing, stats, and search from scripts or the terminal

## Highlights

- Run everything locally with Ollama-backed chat and embeddings
- Index multiple workspaces and query them independently
- Inspect retrieval hits directly in the TUI
- Expose the same functionality over HTTP for other tools
- Connect Pi through the bundled `pi-ragger` extension

## Project layout

- `ragger/core/`: ingestion, workspace management, search, and health helpers
- `ragger/server/`: FastAPI app and routes
- `ragger/tui/`: Textual app plus UI helpers
- `ragger/cli/`: CLI entrypoint
- `pi-ragger/`: Pi extension for the local API server

## Quick start

Create a virtual environment and install the project:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Start Ollama and make sure the models you want are available:

```bash
ollama pull gemma4:26b
ollama pull nomic-embed-text
```

Launch the TUI:

```bash
python3 -m ragger.tui
```

Inside the TUI, index a workspace:

```text
/ingest default /path/to/repo
```

You can also omit the workspace name:

```text
/ingest /path/to/repo
```

After indexing completes, ask questions normally.

## Running the server

Start the local API server before using external clients:

```bash
python3 -m ragger.server
```

Default base URL:

```text
http://127.0.0.1:8170
```

Interactive docs:

- Swagger UI: `http://127.0.0.1:8170/docs`
- ReDoc: `http://127.0.0.1:8170/redoc`
- OpenAPI JSON: `http://127.0.0.1:8170/openapi.json`

The checked-in exported spec lives at [docs/openapi.json](docs/openapi.json).

## CLI usage

Run commands directly with Python:

```bash
python3 -m ragger.cli index default /path/to/repo
python3 -m ragger.cli stats default
python3 -m ragger.cli search default "Where is auth configured?"
```

If installed in your environment, console scripts are also available:

```bash
ragger-tui
ragger-server
ragger-cli search default "Where is auth configured?"
```

## Pi extension

Before starting Pi with `pi-ragger`, make sure the local server is already running:

```bash
python3 -m ragger.server
```

Then start Pi with the extension:

```bash
pi -e ./pi-ragger/index.ts
```

More extension details are in [`pi-ragger/README.md`](./pi-ragger/README.md).

## API examples

Index a workspace:

```bash
curl -sS http://127.0.0.1:8170/workspaces/index \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace": "book",
    "path": "/absolute/path/to/alice.txt",
    "replace": true
  }'
```

Fetch workspace status:

```bash
curl -sS http://127.0.0.1:8170/workspaces/book/status | jq
```

The legacy stats endpoint is still available:

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

## Indexed file types

`ragger` currently indexes:

- `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`
- `.md`, `.txt`
- `.json`, `.yaml`, `.yml`, `.toml`
- `.html`, `.css`, `.scss`

Common generated folders such as `node_modules`, `.nuxt`, `.next`, `dist`, and `coverage` are skipped by default.

## Development

Run the unit test suite:

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache .venv/bin/python -m unittest discover -s tests/unit -v
```

Format Python code:

```bash
.venv/bin/black ragger tests/unit scripts
```

Current test coverage includes:

- ingestion and file filtering
- workspace and search delegation
- TUI command and panel helpers
- FastAPI route contracts

## Commit convention

This repo uses semantic commit messages:

```text
type(scope): short summary
```

Examples:

```text
feat(server): add workspace status endpoint
fix(tui): show retrieval hits for active workspace
docs(readme): improve setup and screenshot sections
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

## Screenshots

Workspace indexing and monitoring in the TUI:

<img src="./docs/index.jpg" alt="Index workspace" width="100%" />

Querying the RAG engine and inspecting retrieval hits:

<img src="./docs/query.jpg" alt="Query workspace" width="100%" />
