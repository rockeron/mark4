from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Callable, Protocol

from md_man.app import MarkdownBrowserApp


class RunnableApp(Protocol):
    def run(self) -> object: ...


def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(prog="md-man")
    parser.add_argument("root_path", type=Path)
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    app_factory: Callable[[str], RunnableApp] = MarkdownBrowserApp,
) -> int:
    args = parse_args(argv)
    app = app_factory(str(args.root_path))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
