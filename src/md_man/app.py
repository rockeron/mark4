from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static


class MarkdownBrowserApp(App[None]):
    CSS_PATH = "app.tcss"

    def __init__(self, root_path: str) -> None:
        super().__init__()
        self.root_path = root_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield Static("tree", id="tree")
            yield Static("왼쪽 트리에서 Markdown 파일을 선택하세요", id="viewer")
        yield Footer()
