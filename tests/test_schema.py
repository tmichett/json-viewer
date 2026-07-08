from __future__ import annotations

from json_viewer.graph.schema import (
    build_object_from_fields,
    infer_array_item_schema,
    infer_field_schema,
)


FRUITS = [
    {
        "name": "Apple",
        "color": "#FF0000",
        "details": {"type": "Pome", "season": "Fall"},
        "nutrients": {"calories": 52, "fiber": "2.4g", "vitaminC": "4.6mg"},
    },
    {
        "name": "Banana",
        "color": "#FFFF00",
        "details": {"type": "Berry", "season": "Year-round"},
        "nutrients": {"calories": 89, "fiber": "2.6g", "potassium": "358mg"},
    },
]


class TestSchema:
    def test_infer_object_schema_merges_nested_keys(self):
        schema = infer_array_item_schema(FRUITS)
        assert schema is not None
        assert schema.value_type == "object"
        assert set(schema.children) == {"name", "color", "details", "nutrients"}
        assert schema.children["details"].children.keys() == {"season", "type"}
        assert set(schema.children["nutrients"].children) == {
            "calories",
            "fiber",
            "potassium",
            "vitaminC",
        }

    def test_infer_scalar_array(self):
        schema = infer_array_item_schema(["a", "b"])
        assert schema is not None
        assert schema.value_type == "string"

    def test_build_object_from_fields(self):
        schema = infer_field_schema(FRUITS)
        values = {
            ("name",): "Grapes",
            ("color",): "#800080",
            ("details", "type"): "Berry",
            ("details", "season"): "Summer",
            ("nutrients", "calories"): "69",
            ("nutrients", "fiber"): "0.9g",
            ("nutrients", "vitaminC"): "3.2mg",
            ("nutrients", "potassium"): "191mg",
        }
        item = build_object_from_fields(schema, values)
        assert item["name"] == "Grapes"
        assert item["details"]["season"] == "Summer"
        assert item["nutrients"]["calories"] == 69

    def test_empty_array_returns_none(self):
        assert infer_array_item_schema([]) is None
