import pytest

from md_man.app import MarkdownBrowserApp


@pytest.mark.asyncio
async def test_app_shows_initial_guidance_when_no_file_is_selected():
    app = MarkdownBrowserApp(root_path="/tmp/docs")

    async with app.run_test():
        viewer = app.query_one("#viewer")
        assert "왼쪽 트리에서 Markdown 파일을 선택하세요" in viewer.content
