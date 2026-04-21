import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Log, Markdown, Static

from ragger.config import DEFAULT_WORKSPACE
from ragger.core.search import RAGEngine
from ragger.core.workspaces import RAGWorkspaceManager
from ragger.tui.commands import parse_ingest_args
from ragger.tui.panels import render_retrieval_panel, render_stats_panel


class RaggerApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    #main-container {
        height: 1fr;
        padding: 1;
    }
    #chat-area {
        height: 1fr;
        border: solid $primary;
        overflow-y: auto;
        padding: 1;
        margin-bottom: 1;
    }
    Input {
        dock: bottom;
        margin-top: 1;
    }
    #status-sidebar {
        width: 52;
        dock: right;
        border-left: solid $accent;
        padding: 1;
        background: $surface-darken-1;
    }
    .panel-title {
        margin-bottom: 1;
    }
    #stats-panel {
        height: 13;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }
    #retrieval-panel {
        height: 16;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
    }
    #status-log {
        height: 1fr;
        border: solid $success;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=True),
    ]

    def on_mount(self):
        self.manager = RAGWorkspaceManager()
        self.current_workspace = DEFAULT_WORKSPACE
        self.engine = RAGEngine(manager=self.manager, workspace=self.current_workspace)
        self.chat_history = (
            "## Ragger\n\n"
            "Use `/ingest <path>` or `/ingest <workspace> <path>` to index a repo.\n\n"
            "Use `/workspace <name>` to switch the active workspace."
        )
        self.last_ingest_summary = "No ingestion yet."
        self.log_widget = self.query_one("#status-log", Log)
        self.chat_area = self.query_one("#chat-area", Markdown)
        self.stats_area = self.query_one("#stats-panel", Markdown)
        self.retrieval_area = self.query_one("#retrieval-panel", Markdown)
        self.chat_area.update(self.chat_history)
        self.retrieval_area.update("## Retrieval\n\nNo query yet.")
        self.update_stats_panel()
        self.log_widget.write_line("System ready.")
        self.log_widget.write_line("Try: /ingest default tmp/alice.txt")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="main-container"):
                yield Markdown(id="chat-area")
                yield Input(placeholder="Ask a question or run /ingest ...", id="query-input")
            with Vertical(id="status-sidebar"):
                yield Static("Workspace + Chroma", classes="panel-title")
                yield Markdown(id="stats-panel")
                yield Static("RAG Retrieval", classes="panel-title")
                yield Markdown(id="retrieval-panel")
                yield Static("Engine Log", classes="panel-title")
                yield Log(id="status-log")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted):
        query = event.value.strip()
        if not query:
            return

        input_widget = self.query_one("#query-input", Input)
        input_widget.value = ""

        if query.startswith("/ingest "):
            await self.run_ingestion(query.removeprefix("/ingest ").strip())
        elif query.startswith("/workspace "):
            self.switch_workspace(query.removeprefix("/workspace ").strip())
        else:
            await self.run_query(query)

    async def run_ingestion(self, raw_args: str):
        workspace, resolved_path = parse_ingest_args(raw_args, self.current_workspace)
        self.log_widget.write_line(f"Ingesting into `{workspace}`: {resolved_path}")
        try:
            loop = asyncio.get_running_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: self.manager.ingest_workspace(
                    workspace=workspace,
                    path=str(resolved_path),
                    replace=True,
                ),
            )
            self.current_workspace = workspace
            self.engine.set_workspace(workspace)
            self.last_ingest_summary = (
                f"Last ingest: `{workspace}` with {stats['file_count']} files / {stats['chunk_count']} chunks"
            )
            self.log_widget.write_line(
                f"Indexed {stats['file_count']} files and {stats['chunk_count']} chunks into `{workspace}`."
            )
            self.update_stats_panel()
        except Exception as exc:
            self.log_widget.write_line(f"Ingest error: {exc}")

    async def run_query(self, query: str):
        self.chat_history += f"\n\n**You:** {query}\n\n**Gemma:** "
        self.chat_area.update(self.chat_history)
        self.retrieval_area.update("## Retrieval\n\nSearching Chroma...")
        self.log_widget.write_line(f"Retrieving from `{self.current_workspace}` for: {query}")

        full_response = ""
        try:
            loop = asyncio.get_running_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.engine.retrieve(query, workspace=self.current_workspace),
            )
            self.retrieval_area.update(render_retrieval_panel(docs, self.current_workspace))
            if not docs:
                self.log_widget.write_line("No retrieval hits found.")
            else:
                self.log_widget.write_line(f"Retrieved {len(docs)} chunks from Chroma.")
            for chunk in self.engine.stream_answer(query, docs):
                full_response += chunk
                self.chat_area.update(self.chat_history + full_response)
                await asyncio.sleep(0)
            self.chat_history += full_response
            self.log_widget.write_line("Response complete.")
            self.update_stats_panel()
        except Exception as exc:
            self.log_widget.write_line(f"Query error: {exc}")

    def switch_workspace(self, workspace: str):
        if not workspace:
            self.log_widget.write_line("Workspace name cannot be empty.")
            return
        self.current_workspace = workspace
        self.engine.set_workspace(workspace)
        self.log_widget.write_line(f"Switched workspace to `{workspace}`.")
        self.update_stats_panel()

    def action_clear_chat(self):
        self.chat_history = (
            "## Ragger\n\n"
            "Use `/ingest <path>` or `/ingest <workspace> <path>` to index a repo.\n\n"
            "Use `/workspace <name>` to switch the active workspace."
        )
        self.chat_area.update(self.chat_history)

    def update_stats_panel(self):
        health = self.engine.get_health()
        try:
            stats = self.engine.get_stats(self.current_workspace)
        except Exception:
            stats = None
        self.stats_area.update(
            render_stats_panel(
                current_workspace=self.current_workspace,
                health=health,
                stats=stats,
                last_ingest_summary=self.last_ingest_summary,
            )
        )


def main() -> None:
    app = RaggerApp()
    app.run()


if __name__ == "__main__":
    main()
