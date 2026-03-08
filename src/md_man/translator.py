from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Protocol

from deep_translator import GoogleTranslator


class Translator(Protocol):
    def translate(self, text: str) -> str: ...


class DeepTranslatorProvider:
    def __init__(
        self,
        translator: Translator | None = None,
        max_length: int = 4000,
    ) -> None:
        self._translator = translator or GoogleTranslator(source="auto", target="ko")
        self._max_length = max_length

    def translate(self, text: str) -> str:
        parts: list[str] = []
        for is_translatable, segment in self._tokenize(text):
            if not is_translatable or not segment.strip():
                parts.append(segment)
                continue

            translated_chunks = [
                self._translate_chunk(chunk)
                for chunk in self._split_translatable_segment(segment)
            ]
            parts.append("".join(translated_chunks))

        return "".join(parts)

    def _translate_chunk(self, chunk: str) -> str:
        translated = self._translator.translate(chunk)
        if translated is None:
            return chunk
        return translated

    def _tokenize(self, text: str) -> list[tuple[bool, str]]:
        tokens: list[tuple[bool, str]] = []
        fence_pattern = re.compile(r"(```.*?```)", re.DOTALL)
        inline_code_pattern = re.compile(r"(`[^`\n]+`)")

        for fenced_segment in fence_pattern.split(text):
            if not fenced_segment:
                continue

            if fence_pattern.fullmatch(fenced_segment):
                tokens.append((False, fenced_segment))
                continue

            for inline_segment in inline_code_pattern.split(fenced_segment):
                if not inline_segment:
                    continue

                if inline_code_pattern.fullmatch(inline_segment):
                    tokens.append((False, inline_segment))
                else:
                    tokens.append((True, inline_segment))

        return tokens

    def _split_translatable_segment(self, text: str) -> list[str]:
        if len(text) <= self._max_length:
            return [text]

        blocks = re.split(r"(\n\s*\n)", text)
        return self._merge_segments(blocks)

    def _merge_segments(self, segments: list[str]) -> list[str]:
        chunks: list[str] = []
        current = ""

        for segment in segments:
            if not segment:
                continue

            if len(segment) > self._max_length:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_large_segment(segment))
                continue

            if current and len(current) + len(segment) > self._max_length:
                chunks.append(current)
                current = segment
                continue

            current += segment

        if current:
            chunks.append(current)

        return chunks

    def _split_large_segment(self, segment: str) -> list[str]:
        sentence_parts = re.split(r"(?<=[.!?])(\s+)", segment)
        sentence_chunks = self._merge_segments(sentence_parts)
        if all(len(chunk) <= self._max_length for chunk in sentence_chunks):
            return sentence_chunks

        line_parts = re.split(r"(\n)", segment)
        line_chunks = self._merge_segments(line_parts)
        if all(len(chunk) <= self._max_length for chunk in line_chunks):
            return line_chunks

        return [
            segment[index : index + self._max_length]
            for index in range(0, len(segment), self._max_length)
        ]


@dataclass
class DocumentTranslationState:
    cache: dict[str, str] = field(default_factory=dict)
    visible_paths: set[str] = field(default_factory=set)

    def cache_translation(self, path: str, content: str) -> None:
        self.cache[path] = content

    def toggle(self, path: str) -> tuple[str | None, bool]:
        if path in self.visible_paths:
            self.visible_paths.remove(path)
            return None, False

        self.visible_paths.add(path)
        return self.cache.get(path), True
