from json_viewer.adapters.types import DataFormat
from json_viewer.lint.linter import lint_content


class TestLinter:
    def test_valid_json_has_no_errors(self):
        result = lint_content('{"name": "Apple"}', DataFormat.JSON)
        assert result.errors == []

    def test_invalid_json_reports_line(self):
        text = '{\n  "name": "Apple",\n  "broken": ,\n}'
        result = lint_content(text, DataFormat.JSON)
        assert len(result.errors) == 1
        assert result.errors[0].line == 3
        assert result.errors[0].column is not None

    def test_invalid_yaml_reports_line(self):
        text = "name: Apple\n  bad indent: true\n"
        result = lint_content(text, DataFormat.YAML)
        assert len(result.errors) == 1
        assert result.errors[0].line is not None

    def test_invalid_xml_reports_position(self):
        text = '<?xml version="1.0"?><root><unclosed></root>'
        result = lint_content(text, DataFormat.XML)
        assert len(result.errors) == 1

    def test_empty_text_is_valid(self):
        result = lint_content("   \n", DataFormat.JSON)
        assert result.errors == []
