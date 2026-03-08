# Markdown TUI Documentation and UX Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add end-user documentation and polish the translation and status UX with progressive updates, persistent cache reuse, and clearer user messaging.

**Architecture:** Keep the existing Textual application and translator pipeline, but extend the translator with persistent cache and progress callbacks, then connect the app to background translation workers and clearer state/status transitions. Add a `README.md` as the primary user-facing document describing setup, usage, translation behavior, and cache behavior.

**Tech Stack:** Python 3.12+, Textual, deep-translator, platformdirs, pytest, pytest-asyncio

---

### Task 1: Add persistent translation cache coverage

**Files:**
- Modify: `src/md_man/translator.py`
- Modify: `tests/test_translator.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from md_man.translator import DeepTranslatorProvider


def test_deep_translator_provider_reuses_persistent_cache_across_instances(tmp_path):
    source_path = Path("/tmp/example.md")
    source = "hello world"
    first = DeepTranslatorProvider(
        translator=RecordingTranslator(),
        cache_dir=tmp_path,
        max_length=100,
    )

    translated = first.translate_document(source_path, source)

    second = DeepTranslatorProvider(
        translator=FailingTranslator(),
        cache_dir=tmp_path,
        max_length=100,
    )

    cached = second.translate_document(source_path, source)

    assert cached == translated
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_translator.py::test_deep_translator_provider_reuses_persistent_cache_across_instances -v`
Expected: FAIL because persistent cache support does not exist

**Step 3: Write minimal implementation**

```python
from hashlib import sha256
import json
from pathlib import Path

from platformdirs import user_cache_dir


class DeepTranslatorProvider:
    def __init__(..., cache_dir: Path | None = None):
        self._cache_dir = cache_dir or Path(user_cache_dir("md-man")) / "translations"

    def get_cached_translation(self, path: Path, text: str) -> str | None:
        ...

    def _write_cached_translation(self, path: Path, text: str, translated: str) -> None:
        ...
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_translator.py::test_deep_translator_provider_reuses_persistent_cache_across_instances -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/md_man/translator.py tests/test_translator.py
git commit -m "feat: add persistent translation cache"
```

### Task 2: Add progressive translation callback support

**Files:**
- Modify: `src/md_man/translator.py`
- Modify: `tests/test_translator.py`

**Step 1: Write the failing test**

```python
def test_translate_document_reports_progress_per_chunk():
    translator = RecordingTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=20)
    source = "first paragraph\n\nsecond paragraph"
    progress: list[tuple[str, int, int]] = []

    translated = provider.translate_document(
        Path("/tmp/example.md"),
        source,
        on_progress=lambda partial, completed, total: progress.append(
            (partial, completed, total)
        ),
    )

    assert translated.endswith("SECOND PARAGRAPH")
    assert progress[-1][1:] == (2, 2)
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_translator.py::test_translate_document_reports_progress_per_chunk -v`
Expected: FAIL because progress callbacks are not emitted

**Step 3: Write minimal implementation**

```python
def translate_document(..., on_progress=None) -> str:
    parts = []
    segments = self._build_translation_segments(text)
    total_chunks = ...
    for is_translatable, segment in segments:
        ...
        if on_progress is not None:
            on_progress("".join(parts), completed_chunks, total_chunks)
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_translator.py::test_translate_document_reports_progress_per_chunk -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/translator.py tests/test_translator.py
git commit -m "feat: add progressive translation callbacks"
```

### Task 3: Connect progressive translation updates to the UI

**Files:**
- Modify: `src/md_man/app.py`
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_translation_progressively_updates_the_viewer(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide\n\nbody", encoding="utf-8")

    app = MarkdownBrowserApp(
        root_path=str(tmp_path),
        translator=ProgressiveStubTranslator(),
    )

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("t")
        await pilot.pause(0.05)

        assert app.current_view_markdown == "# 1차 번역"
        assert "번역 중 1/2" in app.query_one("#status").content
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_app.py::test_translation_progressively_updates_the_viewer -v`
Expected: FAIL because translation is still synchronous / single-shot

**Step 3: Write minimal implementation**

```python
from textual import work


@work(thread=True, exclusive=True, group="translation", exit_on_error=False)
def run_translation_worker(...):
    translated = self.translator.translate_document(..., on_progress=...)
```

Update the viewer and status from the UI thread with request ID checks.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_app.py::test_translation_progressively_updates_the_viewer -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/app.py tests/test_app.py
git commit -m "feat: stream translation progress in the viewer"
```

### Task 4: Polish cache-hit and cancel behavior

**Files:**
- Modify: `src/md_man/app.py`
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_cached_translation_is_shown_immediately(tmp_path):
    ...


@pytest.mark.asyncio
async def test_pressing_t_again_restores_source_markdown(tmp_path):
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_app.py::test_cached_translation_is_shown_immediately tests/test_app.py::test_pressing_t_again_restores_source_markdown -v`
Expected: FAIL because cache-hit status and cancel behavior are not explicit enough

**Step 3: Write minimal implementation**

```python
if translated is not None:
    self.set_status("캐시된 번역 불러옴")
    ...

if self.show_translation:
    self.set_status("번역 취소됨")
    ...
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_app.py::test_cached_translation_is_shown_immediately tests/test_app.py::test_pressing_t_again_restores_source_markdown -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/app.py tests/test_app.py
git commit -m "fix: polish translation cache and cancel states"
```

### Task 5: Add README user documentation

**Files:**
- Create: `README.md`

**Step 1: Write the failing test**

Use a documentation checklist instead of an automated test:

- README explains setup with `uv`
- README explains `./md-man <path>`
- README lists main key bindings
- README explains translation progress and persistent cache
- README lists cache directory behavior and known limitations

**Step 2: Verify checklist is currently failing**

Run: `test -f README.md; echo $?`
Expected: `1`

**Step 3: Write minimal implementation**

Create `README.md` with:

```markdown
# md-man

Markdown TUI viewer with recursive file tree, live translation updates, and persistent translation cache.
```

Then add setup, usage, key bindings, translation and cache sections.

**Step 4: Verify checklist passes**

Run: `sed -n '1,240p' README.md`
Expected: required sections present

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add user guide"
```

### Task 6: Run full verification

**Files:**
- Review: `README.md`
- Review: `pyproject.toml`
- Review: `src/md_man/app.py`
- Review: `src/md_man/translator.py`
- Review: `tests/test_app.py`
- Review: `tests/test_translator.py`

**Step 1: Write the failing test**

If verification exposes a missing behavior, add one targeted regression test first.

**Step 2: Run test suite and CLI verification**

Run: `.venv/bin/pytest -q`
Expected: all tests PASS

Run: `./md-man --help`
Expected: usage output appears successfully

**Step 3: Review README coverage**

Run: `sed -n '1,240p' README.md`
Expected: setup, usage, key bindings, translation, cache, limitations all documented

**Step 4: Commit**

```bash
git add README.md pyproject.toml src/md_man/app.py src/md_man/translator.py tests/test_app.py tests/test_translator.py
git commit -m "feat: finalize documentation and ux polish"
```
