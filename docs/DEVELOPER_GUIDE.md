# JSON Viewer — Developer Guide

Technical reference for contributors working on the JSON Viewer codebase.

## Repository layout

```
json-viewer/
├── src/json_viewer/
│   ├── app.py              # QApplication bootstrap
│   ├── __main__.py         # Entry point (uv run json-viewer)
│   ├── adapters/           # JSON, YAML, XML parse/format/convert
│   ├── graph/              # Parser, layout, collapse, sizing
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
| Tests | pytest | 28+ tests |

## Architecture

```
Editor ──debounce──► adapters.parse_content() ──► graph.parser
                              │                        │
                              ▼                        ▼
                         lint (errors)          graph.layout
                              │                        │
                              ▼                        ▼
                    editor lint markers          GraphCanvas
```

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

Run before committing:

```bash
uv run pytest -q
```

## License

Apache-2.0. Graph algorithm and visual design inspired by [JSON Crack](https://github.com/AykutSarac/jsoncrack.com) (Apache-2.0). See [NOTICE](../NOTICE).
