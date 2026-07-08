from __future__ import annotations

import json
from typing import Any

from json_viewer.graph.models import EdgeData, GraphData, JSONPath, NodeData, NodeRow, ParseGraphResult
from json_viewer.graph.sizing import measure_node


def _value_type(value: Any) -> str:
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


def parse_graph_from_data(data: Any) -> ParseGraphResult:
    nodes: list[NodeData] = []
    edges: list[EdgeData] = []
    counter = {"node": 1, "edge": 1}

    def nid() -> str:
        value = str(counter["node"])
        counter["node"] += 1
        return value

    def eid() -> str:
        value = str(counter["edge"])
        counter["edge"] += 1
        return value

    def parent_meta(path: JSONPath, parent_is_array: bool) -> tuple[str | None, str | None]:
        if not path:
            return None, None
        if parent_is_array:
            return str(path[-1]), "array"
        return str(path[-1]), "object"

    def traverse(
        value: Any,
        path: JSONPath = (),
        parent_id: str | None = None,
        parent_is_array: bool = False,
    ) -> str | None:
        node_id = nid()

        if parent_id is not None and parent_is_array:
            edges.append(EdgeData(id=eid(), from_id=parent_id, to_id=node_id, text=""))

        # Root-level array
        if isinstance(value, list) and not path:
            count = len(value)
            node = NodeData(
                id=node_id,
                text=[
                    NodeRow(
                        key=None,
                        value=f"[{count} items]",
                        type="array",
                        children_count=count,
                    )
                ],
                width=0,
                height=0,
                path=path,
            )
            measure_node(node)
            nodes.append(node)
            for index, child in enumerate(value):
                traverse(child, (index,), parent_id=node_id, parent_is_array=True)
            return node_id

        if isinstance(value, dict):
            rows: list[NodeRow] = []

            for key, child in value.items():
                child_path: JSONPath = (*path, key)
                child_type = _value_type(child)

                if child_type == "array" and isinstance(child, list):
                    target_ids: list[str] = []
                    for index, item in enumerate(child):
                        child_node_id = traverse(item, (*child_path, index))
                        if child_node_id:
                            target_ids.append(child_node_id)

                    rows.append(
                        NodeRow(
                            key=key,
                            value=f"[{len(child)} items]",
                            type="array",
                            children_count=len(child),
                            to=target_ids or None,
                        )
                    )
                    for target in target_ids:
                        edges.append(EdgeData(id=eid(), from_id=node_id, to_id=target, text=key))

                elif child_type == "object" and isinstance(child, dict):
                    object_id = traverse(child, child_path, parent_id=node_id)
                    row = NodeRow(
                        key=key,
                        value=f"{{{len(child)} keys}}",
                        type="object",
                        children_count=len(child),
                    )
                    if object_id:
                        row.to = [object_id]
                        edges.append(EdgeData(id=eid(), from_id=node_id, to_id=object_id, text=key))
                    rows.append(row)
                else:
                    rows.append(NodeRow(key=key, value=child, type=child_type))

            if parent_is_array and not rows:
                rows.append(NodeRow(key=None, value="{0 keys}", type="object", children_count=0))

            pkey, ptype = parent_meta(path, parent_is_array)
            node = NodeData(
                id=node_id,
                text=rows,
                width=0,
                height=0,
                path=path,
                parent_key=pkey,
                parent_type=ptype,
            )
            measure_node(node)
            nodes.append(node)
            return node_id

        # Scalars
        pkey, ptype = parent_meta(path, parent_is_array)
        node = NodeData(
            id=node_id,
            text=[NodeRow(key=None, value=value, type=_value_type(value))],
            width=0,
            height=0,
            path=path,
            parent_key=pkey,
            parent_type=ptype,
        )
        measure_node(node)
        nodes.append(node)
        return node_id

    if data is None or data == "":
        return ParseGraphResult(nodes=[], edges=[])

    if isinstance(data, list) and len(data) == 0:
        return ParseGraphResult(nodes=[], edges=[])

    traverse(data)
    return ParseGraphResult(nodes=nodes, edges=edges)


def parse_graph(json_text: str) -> ParseGraphResult:
    errors: list[Any] = []
    if not json_text.strip():
        return ParseGraphResult(nodes=[], edges=[], errors=errors)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        errors.append(exc)
        return ParseGraphResult(nodes=[], edges=errors)

    result = parse_graph_from_data(data)
    result.errors = errors
    return result


def graph_data_from_result(result: ParseGraphResult) -> GraphData:
    return GraphData(nodes=result.nodes, edges=result.edges)
