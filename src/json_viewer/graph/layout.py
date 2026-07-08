from __future__ import annotations

from dataclasses import dataclass

from json_viewer.graph.models import EdgeData, GraphData, NodeData

HORIZONTAL_GAP = 80
VERTICAL_GAP = 40
EDGE_LABEL_OFFSET = 15


@dataclass
class LayoutResult:
    positions: dict[str, tuple[float, float]]
    width: float
    height: float


def _build_children_map(graph: GraphData) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        children.setdefault(edge.from_id, []).append(edge.to_id)
    return children


def _find_roots(graph: GraphData) -> list[str]:
    targets = {edge.to_id for edge in graph.edges}
    roots = [node.id for node in graph.nodes if node.id not in targets]
    return roots or ([graph.nodes[0].id] if graph.nodes else [])


def _subtree_height(node_id: str, nodes_by_id: dict[str, NodeData], children: dict[str, list[str]]) -> float:
    node = nodes_by_id[node_id]
    child_ids = children.get(node_id, [])
    if not child_ids:
        return node.height

    total = sum(_subtree_height(cid, nodes_by_id, children) for cid in child_ids)
    total += VERTICAL_GAP * max(0, len(child_ids) - 1)
    return max(node.height, total)


def layout_graph(graph: GraphData) -> LayoutResult:
    if not graph.nodes:
        return LayoutResult(positions={}, width=0, height=0)

    nodes_by_id = {node.id: node for node in graph.nodes}
    children = _build_children_map(graph)
    positions: dict[str, tuple[float, float]] = {}

    def place(node_id: str, x: float, y_center: float) -> tuple[float, float]:
        node = nodes_by_id[node_id]
        node_y = y_center - node.height / 2
        positions[node_id] = (x, node_y)

        child_ids = children.get(node_id, [])
        if not child_ids:
            return node.width, node.height

        child_x = x + node.width + HORIZONTAL_GAP
        subtree_heights = [_subtree_height(cid, nodes_by_id, children) for cid in child_ids]
        total_height = sum(subtree_heights) + VERTICAL_GAP * max(0, len(child_ids) - 1)
        current_y = y_center - total_height / 2

        max_child_width = 0.0
        for cid, sh in zip(child_ids, subtree_heights):
            cy = current_y + sh / 2
            cw, _ = place(cid, child_x, cy)
            max_child_width = max(max_child_width, cw)
            current_y += sh + VERTICAL_GAP

        total_width = node.width + HORIZONTAL_GAP + max_child_width
        return total_width, max(node.height, total_height)

    roots = _find_roots(graph)
    current_y = 0.0
    max_width = 0.0
    total_height = 0.0

    root_heights = [_subtree_height(rid, nodes_by_id, children) for rid in roots]
    overall_height = sum(root_heights) + VERTICAL_GAP * max(0, len(roots) - 1)
    y_offset = 0.0

    for root_id, rh in zip(roots, root_heights):
        cy = y_offset + rh / 2
        w, _ = place(root_id, 0.0, cy)
        max_width = max(max_width, w)
        y_offset += rh + VERTICAL_GAP

    total_height = overall_height
    return LayoutResult(positions=positions, width=max_width, height=total_height)


def edge_points(
    from_node: NodeData,
    to_node: NodeData,
    from_pos: tuple[float, float],
    to_pos: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
    x1 = from_pos[0] + from_node.width
    y1 = from_pos[1] + from_node.height / 2
    x2 = to_pos[0]
    y2 = to_pos[1] + to_node.height / 2
    cx = (x1 + x2) / 2
    return (x1, y1), (cx, y1), (cx, y2), (x2, y2)
