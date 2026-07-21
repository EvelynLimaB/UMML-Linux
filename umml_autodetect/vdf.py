"""Valve KeyValues parsing with an optional python-vdf fast path."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Mapping

from .model import VDFError


def _tokenize_vdf(text: str) -> Iterator[str]:
    i = 0
    length = len(text)
    while i < length:
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char == "/" and i + 1 < length and text[i + 1] == "/":
            i = text.find("\n", i + 2)
            if i < 0:
                return
            continue
        if char in "{}":
            yield char
            i += 1
            continue
        if char == '"':
            i += 1
            out: list[str] = []
            while i < length:
                char = text[i]
                if char == '"':
                    i += 1
                    break
                if char == "\\" and i + 1 < length:
                    next_char = text[i + 1]
                    if next_char in ('"', "\\"):
                        out.append(next_char)
                        i += 2
                        continue
                out.append(char)
                i += 1
            else:
                raise VDFError("unterminated quoted string")
            yield "".join(out)
            continue
        start = i
        while i < length and not text[i].isspace() and text[i] not in "{}":
            i += 1
        yield text[start:i]


def parse_vdf_text(text: str) -> dict:
    tokens = iter(_tokenize_vdf(text))

    def parse_object(stop_at_brace: bool) -> dict:
        result: dict[str, object] = {}
        while True:
            try:
                key = next(tokens)
            except StopIteration:
                if stop_at_brace:
                    raise VDFError("missing closing brace")
                return result
            if key == "}":
                if stop_at_brace:
                    return result
                raise VDFError("unexpected closing brace")
            if key == "{":
                raise VDFError("unexpected opening brace")
            try:
                value = next(tokens)
            except StopIteration as exc:
                raise VDFError(f"missing value for {key!r}") from exc
            if value == "{":
                result[key] = parse_object(True)
            elif value == "}":
                raise VDFError(f"missing value for {key!r}")
            else:
                result[key] = value

    return parse_object(False)


def load_vdf(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        import vdf  # type: ignore

        parsed = vdf.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return parse_vdf_text(text)


def get_casefold(mapping: Mapping[str, object], name: str, default=None):
    target = name.casefold()
    for key, value in mapping.items():
        if str(key).casefold() == target:
            return value
    return default


def walk_casefold_keys(value: object, prefix: str) -> Iterator[object]:
    if not isinstance(value, Mapping):
        return
    prefix = prefix.casefold()
    for key, child in value.items():
        if str(key).casefold().startswith(prefix):
            yield child
        yield from walk_casefold_keys(child, prefix)
