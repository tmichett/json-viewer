from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from json_viewer.graph.models import JSONPath
from json_viewer.graph.schema import FieldSchema, infer_array_item_schema

TableKind = Literal["array_object", "array_scalar"]

PRIMARY_KEY_CANDIDATES = ("name", "id", "_id", "key", "uuid", "title", "label", "code")


@dataclass(frozen=True)
class TableTarget:
    label: str
    path: JSONPath
    kind: TableKind


@dataclass(frozen=True)
class TableColumn:
    header: str
    field_path: tuple[str, ...]
    value_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    read_only: bool = False


@dataclass
class TableSection:
    """One logical database table (main entity or related child table)."""

    label: str
    columns: list[TableColumn]
    rows: list[list[Any]]
    child_field: str | None = None
    foreign_key: str | None = None


@dataclass
class RelationalTableSet:
    target: TableTarget
    primary_key: str
    sections: list[TableSection]


# Legacy single-table shape (scalar arrays only).
@dataclass
class TableData:
    target: TableTarget
    columns: list[TableColumn]
    rows: list[list[Any]]


def path_label(path: JSONPath) -> str:
    if not path:
        return "[root]"
    parts: list[str] = []
    for segment in path:
        if isinstance(segment, int):
            parts[-1] = f"{parts[-1]}[{segment}]"
        else:
            parts.append(str(segment))
    return ".".join(parts)


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _scalar_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return "string"


def _list_kind(items: list[Any]) -> TableKind:
    if not items:
        return "array_object"
    if all(isinstance(item, dict) for item in items):
        return "array_object"
    if all(_is_scalar(item) for item in items):
        return "array_scalar"
    if any(isinstance(item, dict) for item in items):
        return "array_object"
    return "array_scalar"


def discover_table_targets(data: Any, path: JSONPath = ()) -> list[TableTarget]:
    targets: list[TableTarget] = []

    if isinstance(data, list):
        targets.append(TableTarget(path_label(path), path, _list_kind(data)))
        return targets

    if isinstance(data, dict):
        for key, value in data.items():
            child_path: JSONPath = (*path, key)
            if isinstance(value, list):
                targets.append(TableTarget(path_label(child_path), child_path, _list_kind(value)))
            elif isinstance(value, dict):
                targets.extend(discover_table_targets(value, child_path))

    return targets


def _items_at_path(data: Any, path: JSONPath) -> list[Any]:
    current = data
    for segment in path:
        current = current[segment]
    if not isinstance(current, list):
        raise TypeError(f"Expected list at {path_label(path)!r}")
    return current


def _detect_primary_key(items: list[dict[str, Any]]) -> str:
    if not items:
        return "name"

    keys_present: set[str] = set()
    for item in items:
        keys_present.update(item.keys())

    for candidate in PRIMARY_KEY_CANDIDATES:
        if candidate in keys_present:
            return candidate

    for item in items:
        for key, value in item.items():
            if _is_scalar(value) and isinstance(value, str):
                return key

    for item in items:
        for key, value in item.items():
            if _is_scalar(value):
                return key

    return "name"


def _collect_top_level_scalar_keys(items: list[dict[str, Any]], primary_key: str) -> list[str]:
    keys: set[str] = set()
    for item in items:
        for key, value in item.items():
            if key == primary_key:
                continue
            if _is_scalar(value):
                keys.add(key)
    return sorted(keys)


def _collect_nested_object_keys(items: list[dict[str, Any]]) -> list[str]:
    keys: set[str] = set()
    for item in items:
        for key, value in item.items():
            if isinstance(value, dict):
                keys.add(key)
    return sorted(keys)


def _nested_scalar_keys(nested: dict[str, Any]) -> list[str]:
    return sorted(key for key, value in nested.items() if _is_scalar(value))


def _column_for_field(key: str, sample: Any, *, primary_key: bool = False, foreign_key: bool = False) -> TableColumn:
    return TableColumn(
        header=key,
        field_path=(key,),
        value_type=_scalar_type(sample),
        is_primary_key=primary_key,
        is_foreign_key=foreign_key,
        read_only=foreign_key,
    )


def build_relational_tables(data: Any, target: TableTarget) -> RelationalTableSet | TableData:
    items = _items_at_path(data, target.path)

    if target.kind == "array_scalar":
        columns = [TableColumn("value", (), _scalar_type(items[0]) if items else "string")]
        rows = [[item] for item in items]
        return TableData(target, columns, rows)

    dict_items = [item for item in items if isinstance(item, dict)]
    primary_key = _detect_primary_key(dict_items)

    main_scalar_keys = _collect_top_level_scalar_keys(dict_items, primary_key)
    main_columns: list[TableColumn] = [
        _column_for_field(primary_key, _sample_value(dict_items, primary_key), primary_key=True)
    ]
    for key in main_scalar_keys:
        main_columns.append(_column_for_field(key, _sample_value(dict_items, key)))

    main_rows: list[list[Any]] = []
    for item in dict_items:
        main_rows.append([item.get(primary_key), *[item.get(key) for key in main_scalar_keys]])

    entity_label = path_label(target.path).split(".")[-1]
    sections: list[TableSection] = [
        TableSection(label=entity_label, columns=main_columns, rows=main_rows)
    ]

    for child_field in _collect_nested_object_keys(dict_items):
        child_columns: list[TableColumn] = [
            TableColumn(
                header=primary_key,
                field_path=(primary_key,),
                value_type=_scalar_type(_sample_value(dict_items, primary_key)),
                is_foreign_key=True,
                read_only=True,
            )
        ]
        child_scalar_keys: set[str] = set()
        for item in dict_items:
            nested = item.get(child_field)
            if isinstance(nested, dict):
                child_scalar_keys.update(_nested_scalar_keys(nested))

        for key in sorted(child_scalar_keys):
            sample = _sample_nested_value(dict_items, child_field, key)
            child_columns.append(
                TableColumn(
                    header=key,
                    field_path=(key,),
                    value_type=_scalar_type(sample),
                )
            )

        child_rows: list[list[Any]] = []
        for item in dict_items:
            nested = item.get(child_field) if isinstance(item.get(child_field), dict) else {}
            row = [item.get(primary_key)]
            row.extend(nested.get(key) if isinstance(nested, dict) else None for key in sorted(child_scalar_keys))
            child_rows.append(row)

        sections.append(
            TableSection(
                label=child_field,
                columns=child_columns,
                rows=child_rows,
                child_field=child_field,
                foreign_key=primary_key,
            )
        )

    return RelationalTableSet(target=target, primary_key=primary_key, sections=sections)


def build_table_data(data: Any, target: TableTarget) -> TableData:
    """Backward-compatible entry point; returns flat table for scalars only."""
    result = build_relational_tables(data, target)
    if isinstance(result, TableData):
        return result
    if not result.sections:
        return TableData(target, [], [])
    main = result.sections[0]
    return TableData(target, main.columns, main.rows)


def _sample_value(items: list[dict[str, Any]], key: str) -> Any:
    for item in items:
        if key in item:
            return item[key]
    return ""


def _sample_nested_value(items: list[dict[str, Any]], child_field: str, key: str) -> Any:
    for item in items:
        nested = item.get(child_field)
        if isinstance(nested, dict) and key in nested:
            return nested[key]
    return ""


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def cell_path(
    target: TableTarget,
    section: TableSection,
    row: int,
    column: TableColumn,
) -> JSONPath:
    if target.kind == "array_scalar":
        return (*target.path, row)

    if section.child_field:
        if column.is_foreign_key:
            return (*target.path, row, *column.field_path)
        return (*target.path, row, section.child_field, *column.field_path)

    return (*target.path, row, *column.field_path)


def parse_cell_text(raw: str, value_type: str) -> Any:
    from json_viewer.graph.data_edit import parse_typed_value

    if value_type == "string":
        return raw
    if not raw.strip() and value_type == "null":
        return None
    return parse_typed_value(raw, value_type)
