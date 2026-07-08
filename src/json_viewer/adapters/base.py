from __future__ import annotations

from typing import Any

from json_viewer.adapters.json_adapter import format_json, parse_json
from json_viewer.adapters.types import DataFormat, ConvertResult, ParseError, ParseResult
from json_viewer.adapters.xml_adapter import format_xml, parse_xml, unwrap_xml_document
from json_viewer.adapters.yaml_adapter import format_yaml, parse_yaml


def parse_content(text: str, fmt: DataFormat) -> ParseResult:
    if not text.strip():
        return ParseResult(data={}, errors=[])

    if fmt == DataFormat.JSON:
        return parse_json(text)
    if fmt == DataFormat.YAML:
        return parse_yaml(text)
    if fmt == DataFormat.XML:
        result = parse_xml(text)
        if not result.errors:
            return ParseResult(data=unwrap_xml_document(result.data), errors=[])
        return result
    raise ValueError(f"Unsupported format: {fmt}")


def format_content(data: Any, fmt: DataFormat) -> str:
    if fmt == DataFormat.JSON:
        return format_json(data)
    if fmt == DataFormat.YAML:
        return format_yaml(data)
    if fmt == DataFormat.XML:
        return format_xml(data)
    raise ValueError(f"Unsupported format: {fmt}")


def convert_content(text: str, from_fmt: DataFormat, to_fmt: DataFormat) -> ConvertResult:
    """Parse text in one format and serialize it in another."""
    if from_fmt == to_fmt:
        parsed = parse_content(text, from_fmt)
        if parsed.errors:
            return ConvertResult(text=text, data=parsed.data, errors=parsed.errors)
        try:
            serialized = format_content(parsed.data, to_fmt)
        except (ValueError, TypeError) as exc:
            return ConvertResult(text=text, data=parsed.data, errors=[ParseError(message=str(exc))])
        return ConvertResult(text=serialized, data=parsed.data, errors=[])

    parsed = parse_content(text, from_fmt)
    if parsed.errors:
        return ConvertResult(text=text, data=parsed.data, errors=parsed.errors)

    data = parsed.data

    try:
        serialized = format_content(data, to_fmt)
    except (ValueError, TypeError) as exc:
        return ConvertResult(text=text, data=data, errors=[ParseError(message=str(exc))])

    return ConvertResult(text=serialized, data=data, errors=[])
