from __future__ import annotations

import copy
from typing import Any

from json_viewer.graph.models import JSONPath


def get_at_path(data: Any, path: JSONPath) -> Any:
    current = data
    for segment in path:
        current = current[segment]
    return current


def _default_array_item(existing: list[Any]) -> Any:
    if not existing:
        return {}
    sample = existing[0]
    if isinstance(sample, dict):
        return {}
    if isinstance(sample, list):
        return []
    if isinstance(sample, str):
        return ""
    if isinstance(sample, bool):
        return False
    if isinstance(sample, (int, float)):
        return 0
    return {}


def add_array_item(data: Any, path: JSONPath, item: Any | None = None) -> Any:
    updated = copy.deepcopy(data)
    target = get_at_path(updated, path)
    if not isinstance(target, list):
        raise TypeError(f"Expected list at path {path!r}, got {type(target).__name__}")
    target.append(item if item is not None else _default_array_item(target))
    return updated


def add_object_key(data: Any, path: JSONPath, key: str, value: Any) -> Any | None:
    updated = copy.deepcopy(data)
    target = get_at_path(updated, path)
    if not isinstance(target, dict):
        raise TypeError(f"Expected dict at path {path!r}, got {type(target).__name__}")
    if key in target:
        return None
    target[key] = value
    return updated


def set_value_at_path(data: Any, path: JSONPath, value: Any) -> Any:
    updated = copy.deepcopy(data)
    if not path:
        raise ValueError("Cannot set root value")
    parent_path, key = path[:-1], path[-1]
    parent = get_at_path(updated, parent_path) if parent_path else updated
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        parent[int(key)] = value
    else:
        raise TypeError(f"Cannot set value on {type(parent).__name__}")
    return updated


def parse_typed_value(raw: str, value_type: str) -> Any:
    if value_type == "null":
        return None
    if value_type == "boolean":
        lowered = raw.strip().lower()
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no"):
            return False
        raise ValueError("Boolean value must be true or false")
    if value_type == "number":
        if "." in raw:
            return float(raw)
        return int(raw)
    if value_type == "object":
        return {}
    if value_type == "array":
        return []
    return raw
