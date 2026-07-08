from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldSchema:
    value_type: str
    children: dict[str, FieldSchema] = field(default_factory=dict)


def _scalar_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def _merge_types(left: str, right: str) -> str:
    if left == right:
        return left
    if "object" in (left, right):
        return "object"
    if "array" in (left, right):
        return "array"
    if {left, right} <= {"number", "integer"}:
        return "number"
    return "string"


def infer_field_schema(samples: list[Any]) -> FieldSchema:
    values = [sample for sample in samples if sample is not None]
    if not values:
        return FieldSchema("string")

    if all(isinstance(value, dict) for value in values):
        children: dict[str, list[Any]] = {}
        for value in values:
            for key, child in value.items():
                children.setdefault(key, []).append(child)
        return FieldSchema(
            "object",
            {
                key: infer_field_schema(child_samples)
                for key, child_samples in children.items()
            },
        )

    if all(isinstance(value, list) for value in values):
        nested: list[Any] = []
        for value in values:
            nested.extend(value)
        return FieldSchema("array")

    value_type = _scalar_type(values[0])
    for value in values[1:]:
        value_type = _merge_types(value_type, _scalar_type(value))
    return FieldSchema(value_type)


def infer_array_item_schema(items: list[Any]) -> FieldSchema | None:
    if not items:
        return None
    dict_items = [item for item in items if isinstance(item, dict) and item]
    if dict_items:
        return infer_field_schema(dict_items)
    return infer_field_schema(items)


def build_object_from_fields(
    schema: FieldSchema,
    values: dict[tuple[str, ...], str],
    prefix: tuple[str, ...] = (),
) -> Any:
    if schema.value_type != "object":
        return _parse_scalar(values.get(prefix, ""), schema.value_type)

    result: dict[str, Any] = {}
    for key, child in schema.children.items():
        child_prefix = (*prefix, key)
        if child.value_type == "object":
            result[key] = build_object_from_fields(child, values, child_prefix)
        else:
            result[key] = _parse_scalar(values.get(child_prefix, ""), child.value_type)
    return result


def _parse_scalar(raw: str, value_type: str) -> Any:
    if value_type == "null":
        return None
    if value_type == "boolean":
        if not raw.strip():
            return False
        lowered = raw.strip().lower()
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no"):
            return False
        raise ValueError("Boolean value must be true or false")
    if value_type == "number":
        if not raw.strip():
            return 0
        return float(raw) if "." in raw else int(raw)
    if value_type == "array":
        return []
    return raw
