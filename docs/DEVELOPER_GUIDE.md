# JSON Viewer — Developer Guide

Technical reference for contributors working on the JSON Viewer codebase.

## Repository layout

```
json-viewer/
├── src/json_viewer/
│   ├── app.py              # QApplication bootstrap
│   ├── __main__.py         # Entry point (uv run json-viewer)
│   ├── adapters/           # JSON, YAML, XML parse/format/convert
│   ├── graph/              # Parser, layout, collapse, sizing, data_edit, schema
│   ├── lint/               # Live validation wrapper
│   ├── ui/                 # PyQt6 widgets (editor, canvas, menus)
│   └── export/             # PNG/SVG export
├── tests/                  # pytest suite
├── docs/                   # User and developer documentation
├── scripts/build.sh        # uv sync + pytest + PyInstaller
├── json-viewer.spec        # PyInstaller spec (macOS .app bundle)
├── pyproject.toml          # uv project config
└── uv.lock
```

## Tech stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Language | Python 3.12+ | |
| GUI | PyQt6 | QGraphicsView for graph; QPlainTextEdit for editor |
| Package manager | uv | `uv sync`, `uv run`, `uv add` |
| Syntax highlighting | Pygments | JSON/YAML/XML lexers |
| YAML | PyYAML | `safe_load` / `dump` |
| XML | defusedxml + ElementTree | Safe parsing; `$attr` prefix convention |
| Packaging | PyInstaller 6.x | `collect_all('PyQt6')` for Qt deps |
| Tests | pytest | 59 tests |

## Architecture

```
Editor ◄──sync──► GraphCanvas (edit signals)
  │                      │
  │ debounce             │ callbacks
  ▼                      ▼
adapters.parse_content()  graph.parser
  │                      │
  ▼                      ▼
lint (errors)       graph.layout
  │                      │
  ▼                      ▼
editor lint markers   GraphCanvas
```

Graph edits flow through `MainWindow`: the canvas emits signals, `data_edit` mutates the parsed Python object, and `format_content` writes the result back to the editor.

### Graph editing

| Module | Role |
|--------|------|
| `graph/data_edit.py` | Path-based mutations: `add_array_item`, `add_object_key`, `set_value_at_path` |
| `graph/schema.py` | Infers field schema from existing array items for the add-item form |
| `ui/graph_edit_dialog.py` | `AddKeyDialog`, `AddArrayItemDialog`, `EditValueDialog`, `AddScalarItemDialog` |
| `ui/graph_items.py` | Renders add buttons; uses callbacks (not signals) because `QGraphicsRectItem` is not a `QObject` |
| `ui/graph_canvas.py` | Re-emits edit signals from node item callbacks |
| `ui/main_window.py` | Handles edit signals, shows dialogs, syncs editor |

**Add array item flow:**

1. User clicks **+** on an array row in `NodeGraphicsItem`
2. `GraphCanvas.add_array_item` signal → `MainWindow._on_graph_add_array_item`
3. `infer_array_item_schema()` inspects existing items (ignoring empty `{}` entries)
4. `AddArrayItemDialog` shows a grouped form; `build_object_from_fields()` builds the new dict
5. `add_array_item(data, path, item)` appends to the array; editor text is reformatted

**Add object key flow:** `AddKeyDialog` → `add_object_key()` → editor sync.

**Edit scalar flow:** `EditValueDialog` → `set_value_at_path()` → editor sync.

When programmatically updating the editor after a graph edit, set `_converting = True` to avoid dirty/lint churn (same pattern as format conversion).

### Table preview

| Module | Role |
|--------|------|
| `graph/table_data.py` | Discovers arrays, builds relational sections (main + child tables), cell paths |
| `ui/table_view.py` | Stacked `QTableView` sections, **+ Dataset**, **+ Add row** |
| `ui/main_window.py` | `QStackedWidget` graph/table preview; table edit and add handlers |

**Relational layout:** main table with detected primary key first (`name`), top-level scalars next, then one child table per nested object (`details`, `nutrients`) linked via a read-only FK column.

**Field order:** `FieldSchema.child_order` preserves first-seen key order from sample dicts. Used by `AddArrayItemDialog` and `build_relational_tables()` column ordering — never sort alphabetically.

**Add row flow:** `TableView` → `MainWindow._on_table_add_row` → reuses `_add_array_item_at_path()` / `AddArrayItemDialog`.

**Add dataset flow:** `AddDatasetDialog` → `add_object_key(data, (), name, [])` for a new top-level array.

**Table edit flow:** double-click cell → `set_value_at_path` → editor refresh.

**Gotcha:** `_ArrayTableModel` must copy `section.columns` and `section.rows` in `__init__` or tables render empty headers with no data.

### Graph parser

Ported from JSON Crack's [`parser.ts`](https://github.com/AykutSarac/jsoncrack.com/blob/master/packages/jsoncrack-react/src/parser.ts). Walks Python `dict | list | scalar` trees and produces `NodeData` / `EdgeData` structures.

Key behaviors (validated in `tests/test_parser.py`):

- Flat objects → single node, no edges
- Nested objects → child node + labeled edge
- Arrays → one child per element; root arrays show `[N items]`
- Node limit guard at 1500 nodes (configurable in `GraphCanvas`)

### XML adapter

XML is the trickiest format for round-trip:

- **Serialize:** arrays become `<item>` children; single-key dicts become the root element
- **Parse:** repeated sibling tags become arrays; all-`item` children become lists
- **Never** use `str(list)` — the original bug that corrupted data on XML view

### View format conversion

`adapters.base.convert_content()` parses in the source format and serializes in the target format. The graph always operates on the parsed Python object, so it is format-agnostic.

## Development workflow

```bash
# Install deps
uv sync --group dev

# Run the app
uv run json-viewer

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_parser.py -v

# Add a dependency
uv add <package>
uv add --dev <package>
```

## Building

```bash
./scripts/build.sh
```

This runs `uv sync --group dev`, `pytest`, then `pyinstaller json-viewer.spec --noconfirm --clean`.

Output on macOS: `dist/JSON Viewer.app`

### PyInstaller notes

- Uses `QTextEdit.ExtraSelection` (not `QPlainTextEdit.ExtraSelection`) for lint markers
- `PyQt6.QtSvg` required for SVG export
- `collect_all('PyQt6')` bundles Qt plugins

## Adding features

### New file format

1. Add enum value to `adapters/types.py` → `DataFormat`
2. Create `adapters/<format>_adapter.py` with `parse_*` and `format_*`
3. Wire into `adapters/base.py` → `parse_content` / `format_content`
4. Add Pygments lexer mapping in `ui/editor.py`
5. Add tests in `tests/test_adapters.py`

### UI conventions

- Theme colors live in `ui/theme.py` (`ThemeColors` dataclass)
- Persist user prefs via `QSettings` (see theme toggle)
- Block `_converting` flag when programmatically setting editor text to avoid dirty/lint churn

## Testing

| Test file | Covers |
|-----------|--------|
| `test_parser.py` | Graph parser, adapters, format conversion, layout |
| `test_linter.py` | Lint error line/column reporting |
| `test_data_edit.py` | Path mutations (`add_array_item`, `add_object_key`, `set_value_at_path`) |
| `test_schema.py` | Schema inference and form-to-object building |
| `test_graph_items.py` | Graph item helpers (object/array node detection, paths) |
| `test_table_data.py` | Relational table discovery, column order, cell paths |
| `test_table_view.py` | Table view widget smoke tests |

Run before committing:

```bash
uv run pytest -q
```

## License

Apache-2.0. Graph algorithm and visual design inspired by [JSON Crack](https://github.com/AykutSarac/jsoncrack.com) (Apache-2.0). See [NOTICE](../NOTICE).
