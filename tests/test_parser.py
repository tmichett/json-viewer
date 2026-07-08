from __future__ import annotations

import json

from json_viewer.adapters.base import convert_content, format_content, parse_content
from json_viewer.adapters.types import DataFormat
from json_viewer.graph.parser import graph_data_from_result, parse_graph_from_data


def _root_id(graph):
    targets = {e.to_id for e in graph.edges}
    root = next(n for n in graph.nodes if n.id not in targets)
    return root.id


class TestParser:
    def test_empty_string(self):
        result = parse_content("", DataFormat.JSON)
        assert result.errors == []
        assert result.data == {}

    def test_primitive_via_json(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('"hello"')
        assert len(result.nodes) == 1
        assert result.edges == []
        assert result.nodes[0].text[0].value == "hello"

    def test_flat_object(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('{"name":"Apple","count":3,"active":true,"tag":null}')
        assert len(result.nodes) == 1
        assert result.edges == []
        rows = result.nodes[0].text
        assert rows[0].key == "name" and rows[0].value == "Apple"
        assert rows[1].key == "count" and rows[1].value == 3
        assert rows[2].key == "active" and rows[2].value is True
        assert rows[3].key == "tag" and rows[3].value is None

    def test_nested_object(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('{"user":{"name":"Ada"}}')
        assert len(result.nodes) == 2
        assert len(result.edges) == 1
        by_id = {n.id: n for n in result.nodes}
        edge = result.edges[0]
        assert edge.text == "user"
        assert by_id[edge.to_id].text[0].value == "Ada"

    def test_array_property(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('{"fruits":["apple","banana","cherry"]}')
        assert len(result.nodes) == 4
        assert len(result.edges) == 3
        root_id = _root_id(graph_data_from_result(result))
        for edge in result.edges:
            assert edge.from_id == root_id
            assert edge.text == "fruits"
        by_id = {n.id: n for n in result.nodes}
        values = [by_id[e.to_id].text[0].value for e in result.edges]
        assert values == ["apple", "banana", "cherry"]

    def test_root_array(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph("[1,2,3]")
        assert len(result.nodes) == 4
        assert len(result.edges) == 3
        root = next(n for n in result.nodes if n.id == _root_id(graph_data_from_result(result)))
        assert root.text[0].type == "array"
        assert root.text[0].children_count == 3
        by_id = {n.id: n for n in result.nodes}
        values = sorted(by_id[e.to_id].text[0].value for e in result.edges)
        assert values == [1, 2, 3]

    def test_deeply_nested(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('{"a":{"b":{"c":{"d":1}}}}')
        assert len(result.nodes) == 4
        assert len(result.edges) == 3

    def test_unique_ids(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('{"users":[{"id":1},{"id":2}]}')
        node_ids = {n.id for n in result.nodes}
        edge_ids = {e.id for e in result.edges}
        assert len(node_ids) == len(result.nodes)
        assert len(edge_ids) == len(result.edges)

    def test_edge_endpoints_valid(self):
        from json_viewer.graph.parser import parse_graph

        result = parse_graph('{"a":{"b":1},"c":[2,3]}')
        node_ids = {n.id for n in result.nodes}
        for edge in result.edges:
            assert edge.from_id in node_ids
            assert edge.to_id in node_ids


class TestAdapters:
    def test_yaml_round_trip(self):
        text = "name: Apple\ncount: 3\n"
        result = parse_content(text, DataFormat.YAML)
        assert result.errors == []
        assert result.data["name"] == "Apple"
        formatted = format_content(result.data, DataFormat.YAML)
        assert "Apple" in formatted

    def test_xml_parse(self):
        text = '<?xml version="1.0"?><catalog><item id="1">hello</item></catalog>'
        result = parse_content(text, DataFormat.XML)
        assert result.errors == []
        assert "catalog" in result.data
        assert result.data["catalog"]["item"]["#text"] == "hello"

    def test_json_invalid(self):
        result = parse_content('{"broken": }', DataFormat.JSON)
        assert len(result.errors) == 1


class TestViewFormatConversion:
    FRUITS_JSON = """{
  "fruits": [
    {
      "name": "Apple",
      "color": "#FF0000",
      "details": {"type": "Pome", "season": "Fall"},
      "nutrients": {"calories": 52, "fiber": "2.4g", "vitaminC": "4.6mg"}
    },
    {
      "name": "Banana",
      "color": "#FFFF00",
      "details": {"type": "Berry", "season": "Year-round"},
      "nutrients": {"calories": 89, "fiber": "2.6g", "potassium": "358mg"}
    }
  ]
}"""

    def test_json_to_yaml(self):
        json_text = '{"name": "Apple", "count": 3}'
        result = convert_content(json_text, DataFormat.JSON, DataFormat.YAML)
        assert result.errors == []
        assert "name:" in result.text
        assert "Apple" in result.text
        assert result.data["name"] == "Apple"

    def test_yaml_to_json(self):
        yaml_text = "name: Banana\ncount: 5\n"
        result = convert_content(yaml_text, DataFormat.YAML, DataFormat.JSON)
        assert result.errors == []
        parsed = json.loads(result.text)
        assert parsed["name"] == "Banana"

    def test_json_to_xml(self):
        json_text = '{"root": {"item": "hello"}}'
        result = convert_content(json_text, DataFormat.JSON, DataFormat.XML)
        assert result.errors == []
        assert "<root>" in result.text
        assert "hello" in result.text
        assert "[{" not in result.text

    def test_fruits_json_to_xml_not_corrupted(self):
        result = convert_content(self.FRUITS_JSON, DataFormat.JSON, DataFormat.XML)
        assert result.errors == []
        assert "[{" not in result.text
        assert "'name'" not in result.text
        assert "<fruits>" in result.text
        assert "<item>" in result.text
        assert "<name>Apple</name>" in result.text

    def test_fruits_xml_round_trip_to_json(self):
        xml_result = convert_content(self.FRUITS_JSON, DataFormat.JSON, DataFormat.XML)
        assert xml_result.errors == []

        json_result = convert_content(xml_result.text, DataFormat.XML, DataFormat.JSON)
        assert json_result.errors == []
        assert "[{" not in json_result.text

        original = json.loads(self.FRUITS_JSON)
        round_tripped = json.loads(json_result.text)
        assert round_tripped == original

    def test_fruits_xml_to_yaml_to_json(self):
        xml_result = convert_content(self.FRUITS_JSON, DataFormat.JSON, DataFormat.XML)
        yaml_result = convert_content(xml_result.text, DataFormat.XML, DataFormat.YAML)
        assert yaml_result.errors == []
        assert "fruits:" in yaml_result.text
        assert "Apple" in yaml_result.text

        json_result = convert_content(yaml_result.text, DataFormat.YAML, DataFormat.JSON)
        assert json_result.errors == []
        assert json.loads(json_result.text) == json.loads(self.FRUITS_JSON)

    def test_same_format_is_noop_text(self):
        json_text = '{\n  "a": 1\n}\n'
        result = convert_content(json_text, DataFormat.JSON, DataFormat.JSON)
        assert result.errors == []
        assert result.data == {"a": 1}

    def test_conversion_preserves_graph_shape(self):
        json_text = '{"fruits": ["apple", "banana"]}'
        converted = convert_content(json_text, DataFormat.JSON, DataFormat.YAML)
        assert converted.errors == []

        from_yaml = parse_content(converted.text, DataFormat.YAML)
        json_graph = graph_data_from_result(parse_graph_from_data(json.loads(json_text)))
        yaml_graph = graph_data_from_result(parse_graph_from_data(from_yaml.data))
        assert len(json_graph.nodes) == len(yaml_graph.nodes)
        assert len(json_graph.edges) == len(yaml_graph.edges)

    def test_fruits_xml_preserves_graph_node_count(self):
        original_graph = graph_data_from_result(
            parse_graph_from_data(json.loads(self.FRUITS_JSON))
        )
        xml_result = convert_content(self.FRUITS_JSON, DataFormat.JSON, DataFormat.XML)
        xml_graph = graph_data_from_result(parse_graph_from_data(xml_result.data))
        assert len(xml_graph.nodes) == len(original_graph.nodes)


class TestLayout:
    def test_layout_positions(self):
        result = parse_graph_from_data({"a": {"b": 1}, "c": [2, 3]})
        from json_viewer.graph.layout import layout_graph

        graph = graph_data_from_result(result)
        layout = layout_graph(graph)
        assert len(layout.positions) == len(graph.nodes)
        xs = [pos[0] for pos in layout.positions.values()]
        assert max(xs) > min(xs)


class TestNodeLimit:
    def test_large_graph_node_count(self):
        data = {"items": list(range(100))}
        result = parse_graph_from_data(data)
        assert len(result.nodes) > 0
