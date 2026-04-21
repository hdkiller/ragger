# Usage Guide

This guide covers advanced usage of `ragger`, including direct API interaction and CLI commands.

## API Examples

The `ragger` server must be running (`ragger-server`) to use these endpoints. Default base URL is `http://127.0.0.1:8170`.

### Index a Workspace
Index a local directory into a specific workspace.
```bash
curl -sS http://127.0.0.1:8170/workspaces/index \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace": "book",
    "path": "/absolute/path/to/alice.txt",
    "replace": true
  }'
```

### Fetch Workspace Status
Check if a workspace is currently indexing or ready.
```bash
curl -sS http://127.0.0.1:8170/workspaces/book/status | jq
```

### Query a Workspace
Perform a RAG search against a specific workspace.
```bash
curl -sS http://127.0.0.1:8170/workspaces/search \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace": "book",
    "query": "Who is Alice?",
    "k": 5
  }' | jq
```

### List Workspaces
List all available workspaces and their collection names.
```bash
curl -sS http://127.0.0.1:8170/workspaces | jq
```

### Server Health
```bash
curl -sS http://127.0.0.1:8170/health | jq
```

---

## CLI Usage

If installed in your environment, use the `ragger-cli` command. Otherwise, use `python3 -m ragger.cli`.

### Indexing
```bash
ragger-cli index <workspace_name> <path_to_repo>
```

### Search
```bash
ragger-cli search <workspace_name> "your query here"
```

### Statistics
```bash
ragger-cli stats <workspace_name>
```

---

## Documentation & Specs

### OpenAPI Export
To export the latest OpenAPI specification:
```bash
python3 scripts/export_openapi.py
```
The spec will be saved to `docs/openapi.json`.

### Interactive API Docs
- **Swagger UI**: `http://127.0.0.1:8170/docs`
- **ReDoc**: `http://127.0.0.1:8170/redoc`
