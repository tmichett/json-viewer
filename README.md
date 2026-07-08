# JSON Viewer

Desktop graph visualizer for **JSON**, **YAML**, and **XML**, inspired by [JSON Crack](https://jsoncrack.com).

## Features

- Split-pane editor and interactive graph canvas
- JSON, YAML, and XML parsing with live preview
- **View as** format switching — edit JSON and convert the editor to YAML or XML (and back) while the graph stays in sync
- **Live linter** — syntax errors highlighted inline with line/column markers; click status or press F8 to jump to the error
- Light and dark themes
- Zoom, pan, fit-to-view, and focus root node
- Collapse/expand nested objects and arrays
- **Graph editing** — add array items via schema-based forms, add object keys, edit scalar values; changes sync to the editor
- Search nodes by key or value
- Format/beautify documents
- Export graph as PNG or SVG
- Node limit guard (default 1500 nodes)
- Drag-and-drop file open

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Development

```bash
cd json-viewer
uv sync --group dev
uv run json-viewer
```

Run tests:

```bash
uv run pytest
```

## Build (PyInstaller)

```bash
chmod +x scripts/build.sh
./scripts/build.sh
```

On macOS the app bundle is created at `dist/JSON Viewer.app`.

## Documentation

| Guide | Description |
|-------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Interface tour, workflows, shortcuts, troubleshooting |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Architecture, build, test, packaging |
| [Docs index](docs/README.md) | Overview and quick links |

## Usage

| Action | Shortcut |
|--------|----------|
| Open file | Cmd/Ctrl+O |
| Save | Cmd/Ctrl+S |
| Format document | Cmd/Ctrl+Shift+F |
| Toggle theme | Cmd/Ctrl+T |
| Toggle live transform | Cmd/Ctrl+L |
| View as JSON / YAML / XML | View → View As menu, or status bar **View as** dropdown |
| Validate document | Cmd/Ctrl+Shift+V |
| Go to error | F8, or click **Invalid** in the status bar |
| Fit graph | Cmd/Ctrl+0 |
| Search nodes | Cmd/Ctrl+F |
| Graph editing | Click **+** on array rows, **+ Add key** on objects, or click scalar values |

## Project structure

```
src/json_viewer/
  adapters/     # JSON, YAML, XML parse/format
  graph/        # Parser, layout, collapse, data_edit, schema
  ui/           # PyQt6 widgets
  export/       # PNG/SVG export
```

## License

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
