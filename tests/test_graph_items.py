from __future__ import annotations

from json_viewer.graph.models import NodeData, NodeRow
from json_viewer.ui.graph_items import array_row_path, is_object_node, is_root_array_node, object_path


class TestGraphItemHelpers:
    def test_is_object_node_with_keys(self):
        node = NodeData(
            id="1",
            text=[NodeRow(key="name", value="Apple", type="string")],
            width=0,
            height=0,
            path=("fruits", 0),
        )
        assert is_object_node(node)

    def test_is_object_node_empty_object(self):
        node = NodeData(
            id="1",
            text=[NodeRow(key=None, value="{0 keys}", type="object", children_count=0)],
            width=0,
            height=0,
            path=("fruits", 3),
        )
        assert is_object_node(node)

    def test_is_root_array_node(self):
        node = NodeData(
            id="1",
            text=[NodeRow(key=None, value="[2 items]", type="array", children_count=2)],
            width=0,
            height=0,
            path=(),
        )
        assert is_root_array_node(node)

    def test_paths(self):
        node = NodeData(
            id="1",
            text=[NodeRow(key="fruits", value="[1 items]", type="array", children_count=1)],
            width=0,
            height=0,
            path=(),
        )
        row = node.text[0]
        assert object_path(node) == ()
        assert array_row_path(node, row) == ("fruits",)
