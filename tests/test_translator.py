from pathlib import Path

from md_man.translator import DeepTranslatorProvider, DocumentTranslationState


def test_translation_state_toggles_to_cached_korean_text():
    state = DocumentTranslationState()
    state.cache_translation("/tmp/a.md", "# 안녕하세요")

    translated, show_translation = state.toggle("/tmp/a.md")

    assert translated == "# 안녕하세요"
    assert show_translation is True


class RecordingTranslator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        return text.upper()


class NoneReturningTranslator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, text: str) -> str | None:
        self.calls.append(text)
        if len(self.calls) == 1:
            return None
        return text.upper()


class FailingTranslator:
    def translate(self, text: str) -> str:
        raise AssertionError("persistent cache should have been used")


def test_deep_translator_provider_splits_long_text_into_chunks():
    translator = RecordingTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=40)
    source = ("first paragraph\n\nsecond paragraph\n\n" * 4).strip()

    translated = provider.translate(source)

    assert translated == source.upper()
    assert len(translator.calls) > 1
    assert all(len(call) <= 40 for call in translator.calls)


def test_deep_translator_provider_preserves_code_blocks_and_inline_code():
    translator = RecordingTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=200)
    source = (
        "hello `code_sample()` world\n\n"
        "```python\n"
        "print('keep me')\n"
        "```\n\n"
        "bye"
    )

    translated = provider.translate(source)

    assert translated == (
        "HELLO `code_sample()` WORLD\n\n"
        "```python\n"
        "print('keep me')\n"
        "```\n\n"
        "BYE"
    )


def test_deep_translator_provider_falls_back_to_original_chunk_on_none_response():
    translator = NoneReturningTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=20)
    source = "first paragraph\n\nsecond paragraph"

    translated = provider.translate(source)

    assert translated == "first paragraph\n\nSECOND PARAGRAPH"


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

    assert translated == "HELLO WORLD"
    assert cached == translated
