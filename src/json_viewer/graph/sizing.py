from __future__ import annotations

from json_viewer.graph.models import GraphData, NodeData

ROW_HEIGHT = 30
PARENT_HEIGHT = 36
MAX_NODE_WIDTH = 700


def calculate_node_size(
    text: str | list[tuple[str, str]], *, single: bool = False, is_parent: bool = False
) -> tuple[float, float]:
    if isinstance(text, list):
        lines = [f"{k}: {v}"[:80] for k, v in text]
        display = "\n".join(lines)
        single = False
    else:
        display = str(text)
        single = True

    if not display:
        return 45.0, 45.0

    longest = max((len(line) for line in display.split("\n")), default=0)
    line_count = display.count("\n") + 1
    width = min(MAX_NODE_WIDTH, max(45.0, longest * 7.5 + 24))
    height = PARENT_HEIGHT if single else line_count * ROW_HEIGHT

    if is_parent:
        width += 80

    return width, height


def measure_node(node: NodeData) -> None:
    if not node.text:
        return

    if node.text[0].key is None:
        if node.text[0].type == "array" and node.text[0].children_count is not None:
            display = f"[{node.text[0].children_count} items]"
        else:
            display = str(node.text[0].value)
        node.width, node.height = calculate_node_size(display, single=True)
        return

    rows: list[tuple[str, str]] = []
    for row in node.text:
        key_str = "" if row.key is None else str(row.key)
        if row.type == "object":
            count = row.children_count or 0
            rows.append((key_str, f"{{{count} keys}}"))
        elif row.type == "array":
            count = row.children_count or 0
            rows.append((key_str, f"[{count} items]"))
        elif row.value is None:
            rows.append((key_str, "null"))
        else:
            rows.append((key_str, str(row.value)))

    node.width, node.height = calculate_node_size(rows)
