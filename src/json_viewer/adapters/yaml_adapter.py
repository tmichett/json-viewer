from __future__ import annotations

from typing import Any

import yaml

from json_viewer.adapters.types import ParseError, ParseResult


def parse_yaml(text: str) -> ParseResult:
    errors: list[ParseError] = []
    try:
        data = yaml.safe_load(text)
        if data is None:
            data = {}
        return ParseResult(data=data, errors=errors)
    except yaml.YAMLError as exc:
        line = None
        column = None
        if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
            line = exc.problem_mark.line + 1
            column = exc.problem_mark.column + 1
        errors.append(ParseError(message=str(exc), line=line, column=column))
        return ParseResult(data={}, errors=errors)


def format_yaml(data: Any) -> str:
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
