# pi-ragger

Pi extension for the local `ragger` FastAPI server.

## Expected server

Start the Python API locally:

```bash
python3 -m ragger_server
```

The extension expects the server at `http://127.0.0.1:8170` by default. Override with `RAGGER_BASE_URL`.

## Tools

- `ragger_index(workspace, path, replace?)`
- `ragger_search(workspace, query, k?)`
- `ragger_status(workspace?)`

## Auto-injection

Auto-injection is enabled by default. Before each agent turn, the extension searches the active workspace and prepends the top retrieved snippets to the system prompt.

Commands:

- `/ragger-workspace <name>`
- `/ragger-on`
- `/ragger-off`

## Example flow

1. Start the local API server.
2. Index a workspace with `ragger_index`.
3. Switch workspace with `/ragger-workspace <name>` if needed.
4. Let Pi use auto-injected retrieval context during normal coding turns.
