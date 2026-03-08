from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer, Header, Markdown, Static

from md_man.translator import DeepTranslatorProvider, DocumentTranslationState, Translator
from md_man.widgets import MarkdownTree


class MarkdownBrowserApp(App[None]):
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("t", "toggle_translation", "Translate"),
        ("r", "refresh_tree", "Refresh"),
        ("question_mark", "show_help", "Help"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, root_path: str, translator: Translator | None = None) -> None:
        super().__init__()
        self.root_path = Path(root_path)
        self.current_file: Path | None = None
        self.current_markdown: str | None = None
        self.current_view_markdown: str | None = None
        self.show_translation = False
        self.last_error: str | None = None
        self.translator = translator or DeepTranslatorProvider()
        self.translation_state = DocumentTranslationState()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield MarkdownTree(self.root_path)
            with ContentSwitcher(initial="viewer", id="viewer-switcher"):
                yield Static("왼쪽 트리에서 Markdown 파일을 선택하세요", id="viewer")
                yield Markdown(id="markdown-view")
        yield Static(str(self.root_path), id="status")
        yield Footer()

    def on_mount(self) -> None:
        if not self.root_path.exists():
            self.last_error = "경로를 열 수 없습니다"
            self.query_one("#viewer", Static).update(self.last_error)
            self.set_status(self.last_error)
            return

        tree = self.query_one(MarkdownTree)
        tree.focus()
        if tree.first_file_node is not None:
            tree.select_node(tree.first_file_node)
            self.set_status(str(tree.first_file_node.data))
        else:
            self.set_status("이 경로 아래에 markdown 파일이 없습니다")

    def on_tree_node_selected(self, event: MarkdownTree.NodeSelected[Path]) -> None:
        path = event.node.data
        if path.is_file() and path.suffix.lower() == ".md":
            self.open_markdown(path)

    def open_markdown(self, path: Path) -> None:
        markdown = path.read_text(encoding="utf-8")
        self.current_file = path
        self.current_markdown = markdown
        self.current_view_markdown = markdown
        self.show_translation = False
        self.query_one("#markdown-view", Markdown).update(markdown)
        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
        self.set_status(str(path))

    def action_toggle_translation(self) -> None:
        if self.current_file is None or self.current_markdown is None:
            return

        path_key = str(self.current_file)
        translated = self.translation_state.cache.get(path_key)
        if translated is None:
            translated = self.translator.translate(self.current_markdown)
            self.translation_state.cache_translation(path_key, translated)

        _, is_showing_translation = self.translation_state.toggle(path_key)
        self.show_translation = is_showing_translation
        self.current_view_markdown = (
            translated if self.show_translation else self.current_markdown
        )
        self.query_one("#markdown-view", Markdown).update(self.current_view_markdown)
        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
        self.set_status("한국어 번역 보기" if self.show_translation else str(self.current_file))

    def action_refresh_tree(self) -> None:
        if not self.root_path.exists():
            self.last_error = "경로를 열 수 없습니다"
            self.query_one("#viewer", Static).update(self.last_error)
            self.set_status(self.last_error)
            return

        tree = self.query_one(MarkdownTree)
        tree.reload_tree()
        if tree.first_file_node is not None:
            tree.select_node(tree.first_file_node)
            self.set_status("경로를 다시 스캔했습니다")
        else:
            self.query_one("#viewer", Static).update(
                "이 경로 아래에 markdown 파일이 없습니다"
            )
            self.query_one("#viewer-switcher", ContentSwitcher).current = "viewer"
            self.set_status("이 경로 아래에 markdown 파일이 없습니다")

    def action_show_help(self) -> None:
        self.set_status(
            "단축키: Enter 열기, t 번역, r 재스캔, ? 도움말, q 종료"
        )

    def set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)
