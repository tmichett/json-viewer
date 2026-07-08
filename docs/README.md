# JSON Viewer Documentation

Documentation for the **JSON Viewer** desktop application — a PyQt6 graph visualizer for JSON, YAML, and XML inspired by [JSON Crack](https://jsoncrack.com).

## Guides

| Document | Audience | Description |
|----------|----------|-------------|
| [User Guide](USER_GUIDE.md) | End users | Interface tour, graph editing, workflows, shortcuts, troubleshooting |
| [Developer Guide](DEVELOPER_GUIDE.md) | Contributors | Architecture, build, test, packaging |

## Quick start

```bash
cd json-viewer
uv sync --group dev
uv run json-viewer
```

Build a standalone macOS app:

```bash
./scripts/build.sh
open "dist/JSON Viewer.app"
```

## Repository

- **Path:** `/Users/travis/Github/json-viewer`
- **Stack:** Python 3.12+, PyQt6, uv, PyInstaller
- **License:** Apache-2.0 (see [NOTICE](../NOTICE) for JSON Crack attribution)
