# Changelog

All notable changes to JSON Viewer. Version follows `src/json_viewer/__init__.py` (`0.1.0`).

## Branch: `feat-add-items` (ahead of `main`)

**Commit:** `85c3599` — *FEAT: Easier editing and adding items*

Graph-based data editing: add array items, add object keys, and edit scalar values directly on the node canvas. Changes sync back to the text editor.

### Added

- **Add array item** — blue **+** on the right of array rows opens a schema-based form (`AddArrayItemDialog`) for object arrays, or a simple value dialog for scalar arrays
- **Add object key** — **+ Add key** row at the bottom of object nodes (`AddKeyDialog`)
- **Edit scalar values** — click any string/number/boolean/null row (`EditValueDialog`)
- **Schema inference** — `graph/schema.py` merges field keys across existing array items (nested groups like `details`, `nutrients`)
- **Path mutations** — `graph/data_edit.py` (`add_array_item`, `add_object_key`, `set_value_at_path`)
- **Graph edit dialogs** — `ui/graph_edit_dialog.py`
- **Tests** — `test_data_edit.py`, `test_schema.py`, `test_graph_items.py` (45 tests total)

### Changed

- `ui/graph_items.py` — add buttons, hover states, click handlers (callbacks, not signals — `QGraphicsRectItem` is not a `QObject`)
- `ui/graph_canvas.py` — re-emits `add_array_item`, `add_object_key`, `edit_scalar` signals
- `ui/main_window.py` — wires graph edit handlers; reformats editor after mutations
- `ui/help_dialogs.py` — usage help includes graph editing section
- `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`, `README.md` — graph editing documented

---

## `main` — Initial application (`cf2e8d9`)

**Commit:** `cf2e8d9` — *FEAT: Initial Python application*

First working PyQt6 desktop app inspired by JSON Crack.

### Added

- Split-pane syntax-highlighted editor + interactive graph canvas
- JSON, YAML, XML adapters with **View as** format switching
- Live linter (gutter markers, wavy underline, F8 / click Invalid to jump)
- Syntax highlighting — bold orange braces, bold keys, bracket matching
- Graph zoom slider (10–400%), −/+ Fit Root toolbar, pan/zoom
- Collapse/expand nested objects and arrays
- Search nodes by key or value
- Format/beautify, PNG/SVG export, drag-and-drop open
- Light/dark themes (QSettings persisted)
- 1500-node limit guard
- **Help menu** — Usage (F1), About JSON Viewer (shows version from `__version__`)
- PyInstaller macOS bundle (`scripts/build.sh` → `dist/JSON Viewer.app`)
- Documentation — `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`, `docs/README.md`
- Tests — `test_parser.py`, `test_linter.py` (28 tests at initial release)

### Fixed during development

- XML round-trip corruption — rewrote `xml_adapter.py` (`<item>` for arrays, never `str(list)`)
- Linter crash — use `QTextEdit.ExtraSelection` (not `QPlainTextEdit.ExtraSelection`)
- Packaging — setuptools src layout in `pyproject.toml`
- Circular imports — split `adapters/types.py` from `base.py`
