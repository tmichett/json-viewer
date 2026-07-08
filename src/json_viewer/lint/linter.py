from __future__ import annotations

from json_viewer.adapters.base import parse_content
from json_viewer.adapters.types import DataFormat, ParseError, ParseResult


def lint_content(text: str, fmt: DataFormat) -> ParseResult:
    """Validate editor text and return parse errors with line/column positions."""
    if not text.strip():
        return ParseResult(data={}, errors=[])
    return parse_content(text, fmt)
