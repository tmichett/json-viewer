from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DataFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"
    XML = "xml"

    @classmethod
    def from_extension(cls, path: str) -> DataFormat:
        lower = path.lower()
        if lower.endswith((".yaml", ".yml")):
            return cls.YAML
        if lower.endswith(".xml"):
            return cls.XML
        return cls.JSON

    @property
    def label(self) -> str:
        return self.value.upper()


@dataclass
class ParseError:
    message: str
    line: int | None = None
    column: int | None = None


@dataclass
class ParseResult:
    data: Any
    errors: list[ParseError]


@dataclass
class ConvertResult:
    text: str
    data: Any
    errors: list[ParseError]
