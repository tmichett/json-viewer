#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Syncing dependencies with uv"
uv sync --group dev

echo "==> Running tests"
uv run pytest -q

echo "==> Building with PyInstaller"
uv run pyinstaller json-viewer.spec --noconfirm --clean

echo "==> Build complete"
if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "    macOS app: dist/JSON Viewer.app"
else
  echo "    Binary: dist/json-viewer/json-viewer"
fi
