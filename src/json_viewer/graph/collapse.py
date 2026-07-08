from __future__ import annotations

import json
from typing import Any

from json_viewer.graph.models import EdgeData, GraphData, JSONPath, NodeData


def path_key(path: JSONPath) -> str:
    return json.dumps(list(path))


def is_path_collapsed(collapsed: set[str], path: JSONPath) -> bool:
    return path_key(path) in collapsed


def is_node_hidden(collapsed_prefixes: list[JSONPath], node_path: JSONPath | tuple) -> bool:
    if not node_path or not collapsed_prefixes:
        return False
    for prefix in collapsed_prefixes:
        if len(prefix) > len(node_path):
            continue
        if all(prefix[i] == node_path[i] for i in range(len(prefix))):
            return True
    return False


def prune_paths(data: Any, paths: list[str]) -> list[str]:
    if not paths:
        return paths

    kept: list[str] = []
    for key in paths:
        try:
            path = tuple(json.loads(key))
        except json.JSONDecodeError:
            continue

        cur: Any = data
        ok = True
        for seg in path:
            if cur is None or not isinstance(cur, (dict, list)):
                ok = False
                break
            if isinstance(cur, dict):
                if seg not in cur:
                    ok = False
                    break
                cur = cur[seg]
            else:
                if not isinstance(seg, int) or seg >= len(cur):
                    ok = False
                    break
                cur = cur[seg]

        if ok and isinstance(cur, (dict, list)):
            kept.append(key)

    return kept


def filter_collapsed_graph(
    graph: GraphData,
    collapsed: set[str],
) -> GraphData:
    if not collapsed:
        return graph

    collapsed_prefixes: list[JSONPath] = []
    for key in collapsed:
        try:
            collapsed_prefixes.append(tuple(json.loads(key)))
        except json.JSONDecodeError:
            continue

    visible_nodes: list[NodeData] = []
    visible_ids: set[str] = set()

    for node in graph.nodes:
        if is_node_hidden(collapsed_prefixes, node.path):
            continue
        visible_nodes.append(node)
        visible_ids.add(node.id)

    visible_edges: list[EdgeData] = []
    for edge in graph.edges:
        if edge.from_id in visible_ids and edge.to_id in visible_ids:
            visible_edges.append(edge)

    return GraphData(nodes=visible_nodes, edges=visible_edges)
