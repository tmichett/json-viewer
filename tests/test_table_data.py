from __future__ import annotations

from json_viewer.graph.table_data import (
    RelationalTableSet,
    TableData,
    build_relational_tables,
    build_table_data,
    cell_path,
    discover_table_targets,
    format_cell,
    parse_cell_text,
    path_label,
)

FRUITS_DOC = {
    "fruits": [
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
}


class TestTableData:
    def test_discover_fruits_array(self):
        targets = discover_table_targets(FRUITS_DOC)
        assert len(targets) == 1
        assert targets[0].label == "fruits"
        assert targets[0].path == ("fruits",)
        assert targets[0].kind == "array_object"

    def test_relational_main_table_primary_key_first(self):
        target = discover_table_targets(FRUITS_DOC)[0]
        result = build_relational_tables(FRUITS_DOC, target)
        assert isinstance(result, RelationalTableSet)
        main = result.sections[0]
        assert main.label == "fruits"
        assert result.primary_key == "name"
        assert main.columns[0].header == "name"
        assert main.columns[0].is_primary_key
        assert [c.header for c in main.columns[1:]] == ["color"]

    def test_relational_child_tables(self):
        target = discover_table_targets(FRUITS_DOC)[0]
        result = build_relational_tables(FRUITS_DOC, target)
        assert isinstance(result, RelationalTableSet)
        assert len(result.sections) == 3
        child_labels = [s.label for s in result.sections[1:]]
        assert child_labels == ["details", "nutrients"]

        details = result.sections[1]
        assert details.child_field == "details"
        assert details.foreign_key == "name"
        assert details.columns[0].is_foreign_key
        assert details.columns[0].read_only
        assert [c.header for c in details.columns[1:]] == ["season", "type"]

        nutrients = result.sections[2]
        assert [c.header for c in nutrients.columns[1:]] == [
            "calories",
            "fiber",
            "potassium",
            "vitaminC",
        ]

    def test_relational_row_values(self):
        target = discover_table_targets(FRUITS_DOC)[0]
        result = build_relational_tables(FRUITS_DOC, target)
        assert isinstance(result, RelationalTableSet)
        main = result.sections[0]
        assert main.rows[0][0] == "Apple"
        assert main.rows[0][1] == "#FF0000"

        details = result.sections[1]
        assert details.rows[0][0] == "Apple"
        assert details.rows[0][1] == "Fall"
        assert details.rows[1][2] == "Berry"

    def test_cell_path_main_and_child(self):
        target = discover_table_targets(FRUITS_DOC)[0]
        result = build_relational_tables(FRUITS_DOC, target)
        assert isinstance(result, RelationalTableSet)
        main = result.sections[0]
        details = result.sections[1]
        name_col = main.columns[0]
        season_col = details.columns[1]
        assert cell_path(target, main, 1, name_col) == ("fruits", 1, "name")
        assert cell_path(target, details, 0, season_col) == ("fruits", 0, "details", "season")

    def test_scalar_array(self):
        doc = {"tags": ["alpha", "beta", "gamma"]}
        target = discover_table_targets(doc)[0]
        result = build_relational_tables(doc, target)
        assert isinstance(result, TableData)
        assert len(result.columns) == 1
        assert result.rows[1][0] == "beta"

    def test_build_table_data_scalar_compat(self):
        doc = {"tags": ["a"]}
        target = discover_table_targets(doc)[0]
        table = build_table_data(doc, target)
        assert table.columns[0].header == "value"

    def test_format_and_parse_cell(self):
        assert format_cell(True) == "true"
        assert format_cell(None) == ""
        assert parse_cell_text("42", "number") == 42
        assert parse_cell_text("hello", "string") == "hello"

    def test_path_label(self):
        assert path_label(("fruits",)) == "fruits"
        assert path_label(()) == "[root]"

    def test_nested_arrays_discovered(self):
        doc = {"data": {"items": [{"id": 1}], "labels": ["x"]}}
        labels = {t.label for t in discover_table_targets(doc)}
        assert "data.items" in labels
        assert "data.labels" in labels

    def test_primary_key_prefers_id(self):
        doc = {
            "users": [
                {"id": 1, "email": "a@example.com", "profile": {"role": "admin"}},
                {"id": 2, "email": "b@example.com", "profile": {"role": "user"}},
            ]
        }
        target = discover_table_targets(doc)[0]
        result = build_relational_tables(doc, target)
        assert isinstance(result, RelationalTableSet)
        assert result.primary_key == "id"
        assert result.sections[0].columns[0].header == "id"
