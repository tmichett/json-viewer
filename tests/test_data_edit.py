from __future__ import annotations

import pytest

from json_viewer.graph.data_edit import (
    add_array_item,
    add_object_key,
    parse_typed_value,
    set_value_at_path,
)


class TestDataEdit:
    def test_add_array_item_object_array(self):
        data = {"fruits": [{"name": "Apple"}]}
        updated = add_array_item(data, ("fruits",))
        assert len(updated["fruits"]) == 2
        assert updated["fruits"][1] == {"name": ""}
        assert data["fruits"] == [{"name": "Apple"}]

    def test_add_array_item_copies_nested_shape(self):
        data = {
            "fruits": [
                {"name": "Apple", "details": {"type": "Pome"}, "nutrients": {"calories": 52}},
            ]
        }
        updated = add_array_item(data, ("fruits",))
        assert updated["fruits"][1] == {"name": "", "details": {}, "nutrients": {}}

    def test_add_array_item_string_array(self):
        data = {"tags": ["a", "b"]}
        updated = add_array_item(data, ("tags",))
        assert updated["tags"] == ["a", "b", ""]

    def test_add_array_item_with_explicit_item(self):
        data = {"fruits": [{"name": "Apple"}]}
        updated = add_array_item(data, ("fruits",), {"name": "Banana"})
        assert updated["fruits"][1] == {"name": "Banana"}

    def test_add_array_item_empty_array(self):
        data = {"items": []}
        updated = add_array_item(data, ("items",))
        assert updated["items"] == [{}]

    def test_add_object_key_top_level_array(self):
        data = {"fruits": [{"name": "Apple"}]}
        updated = add_object_key(data, (), "vegetables", [])
        assert updated["vegetables"] == []
        assert len(updated["fruits"]) == 1

    def test_add_object_key_duplicate(self):
        data = {"name": "Apple"}
        assert add_object_key(data, (), "name", "Banana") is None

    def test_set_value_at_path(self):
        data = {"fruits": [{"name": "Apple"}]}
        updated = set_value_at_path(data, ("fruits", 0, "name"), "Banana")
        assert updated["fruits"][0]["name"] == "Banana"

    def test_parse_typed_value(self):
        assert parse_typed_value("42", "number") == 42
        assert parse_typed_value("3.14", "number") == 3.14
        assert parse_typed_value("true", "boolean") is True
        assert parse_typed_value("", "null") is None
        assert parse_typed_value("", "object") == {}
        assert parse_typed_value("", "array") == []

    def test_parse_typed_value_invalid_boolean(self):
        with pytest.raises(ValueError):
            parse_typed_value("maybe", "boolean")
