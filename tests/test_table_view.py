from __future__ import annotations

from json_viewer.graph.table_data import TableColumn, TableSection, build_relational_tables, discover_table_targets
from json_viewer.ui.table_view import _ArrayTableModel

FRUITS_DOC = {
    "fruits": [
        {"name": "Apple", "color": "#FF0000", "details": {"type": "Pome", "season": "Fall"}},
    ]
}


def test_array_table_model_loads_section_rows():
    target = discover_table_targets(FRUITS_DOC)[0]
    result = build_relational_tables(FRUITS_DOC, target)
    section = result.sections[0]
    model = _ArrayTableModel(section)
    assert model.rowCount() == 1
    assert model.columnCount() == 2
    index = model.index(0, 0)
    assert model.data(index) == "Apple"
