from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

JSONPath = tuple[str | int, ...]


@dataclass
class NodeRow:
    key: str | None
    value: str | int | float | bool | None
    type: str
    children_count: int | None = None
    to: list[str] | None = None


@dataclass
class NodeData:
    id: str
    text: list[NodeRow]
    width: float
    height: float
    path: JSONPath = field(default_factory=tuple)
    parent_key: str | None = None
    parent_type: str | None = None


@dataclass
class EdgeData:
    id: str
    from_id: str
    to_id: str
    text: str | None


@dataclass
class GraphData:
    nodes: list[NodeData]
    edges: list[EdgeData]


@dataclass
class ParseGraphResult:
    nodes: list[NodeData]
    edges: list[EdgeData]
    errors: list[Any] = field(default_factory=list)
