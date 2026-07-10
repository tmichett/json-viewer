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
    sample = next((item for item in existing if isinstance(item, dict) and item), None)
    if isinstance(sample, dict):
        return template_object_from_sample(sample)
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


def template_object_from_sample(sample: dict[str, Any]) -> dict[str, Any]:
    """Build an empty object with the same nested shape as an existing item."""
    result: dict[str, Any] = {}
    for key, value in sample.items():
        if isinstance(value, dict):
            result[key] = {}
        elif isinstance(value, list):
            result[key] = []
        elif value is None:
            result[key] = None
        elif isinstance(value, bool):
            result[key] = False
        elif isinstance(value, (int, float)):
            result[key] = 0
        elif isinstance(value, str):
            result[key] = ""
        else:
            result[key] = {}
    return result


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


def add_key_to_nested_objects_in_array(
    data: Any,
    array_path: JSONPath,
    child_field: str,
    key: str,
    value: Any,
) -> Any | None:
    """Add a scalar key to a nested object field on every item in an array."""
    updated = copy.deepcopy(data)
    items = get_at_path(updated, array_path)
    if not isinstance(items, list):
        raise TypeError(f"Expected list at path {array_path!r}, got {type(items).__name__}")

    for item in items:
        if not isinstance(item, dict):
            continue
        nested = item.get(child_field)
        if isinstance(nested, dict) and key in nested:
            return None

    for item in items:
        if not isinstance(item, dict):
            continue
        nested = item.get(child_field)
        if not isinstance(nested, dict):
            item[child_field] = {}
            nested = item[child_field]
        nested[key] = copy.deepcopy(value) if isinstance(value, (dict, list)) else value

    return updated


def set_nested_value(root: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    if not path:
        raise ValueError("Path is required")
    current: Any = root
    for key in path[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[path[-1]] = value


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
