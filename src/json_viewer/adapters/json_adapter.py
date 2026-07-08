from __future__ import annotations

import json
from typing import Any

from json_viewer.adapters.types import ParseError, ParseResult


def parse_json(text: str) -> ParseResult:
    errors: list[ParseError] = []
    try:
        data = json.loads(text)
        return ParseResult(data=data, errors=errors)
    except json.JSONDecodeError as exc:
        errors.append(
            ParseError(
                message=exc.msg,
                line=exc.lineno,
                column=exc.colno,
            )
        )
        return ParseResult(data={}, errors=errors)


def format_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
