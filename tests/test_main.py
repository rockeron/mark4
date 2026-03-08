from md_man.main import parse_args


def test_parse_args_reads_root_path():
    args = parse_args(["/tmp/docs"])
    assert str(args.root_path) == "/tmp/docs"


def test_main_runs_app_with_root_path(tmp_path):
    calls: list[str] = []

    class StubApp:
        def __init__(self, root_path: str) -> None:
            calls.append(root_path)

        def run(self) -> None:
            calls.append("run")

    from md_man.main import main

    exit_code = main([str(tmp_path)], app_factory=StubApp)

    assert exit_code == 0
    assert calls == [str(tmp_path), "run"]
