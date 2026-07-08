from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTextBrowser,
    QVBoxLayout,
)

from json_viewer import __version__

USAGE_HTML = """
<h2>JSON Viewer</h2>
<p>Edit structured data in the left pane and explore it as an interactive graph on the right.
Supports <b>JSON</b>, <b>YAML</b>, and <b>XML</b>. All processing happens locally on your machine.</p>

<h3>Getting started</h3>
<ul>
  <li>Open a file with <b>File → Open</b> or drag and drop onto the window</li>
  <li>Edit the document in the syntax-highlighted editor</li>
  <li>The graph updates automatically when <b>Live Transform</b> is on</li>
</ul>

<h3>Editor</h3>
<ul>
  <li>Live syntax validation — errors appear in the status bar</li>
  <li>Press <b>F8</b> or click <b>Invalid</b> in the status bar to jump to the first error</li>
  <li>Use <b>View as</b> (status bar or View menu) to convert between JSON, YAML, and XML</li>
  <li><b>Tools → Format Document</b> beautifies the current document</li>
</ul>

<h3>Graph</h3>
<ul>
  <li>Drag to pan; <b>Ctrl+scroll</b> or the zoom slider to zoom</li>
  <li>Click <b>{N keys}</b> or <b>[N items]</b> on a node to collapse or expand that section</li>
  <li>Search nodes by key or value in the search bar below the graph</li>
  <li>Use <b>− + Fit Root</b> on the toolbar to zoom and navigate</li>
  <li>Export the graph as PNG or SVG from the File menu</li>
</ul>

<h3>Keyboard shortcuts</h3>
<table cellpadding="4">
  <tr><td><b>Open</b></td><td>Ctrl+O</td></tr>
  <tr><td><b>Save</b></td><td>Ctrl+S</td></tr>
  <tr><td><b>Format document</b></td><td>Ctrl+Shift+F</td></tr>
  <tr><td><b>Validate document</b></td><td>Ctrl+Shift+V</td></tr>
  <tr><td><b>Toggle theme</b></td><td>Ctrl+T</td></tr>
  <tr><td><b>Toggle live transform</b></td><td>Ctrl+L</td></tr>
  <tr><td><b>Fit graph</b></td><td>Ctrl+0</td></tr>
  <tr><td><b>Search nodes</b></td><td>Ctrl+F</td></tr>
  <tr><td><b>Go to error</b></td><td>F8</td></tr>
</table>

<h3>Tips</h3>
<ul>
  <li>Graphs with more than 1500 nodes show a limit warning — collapse large sections to continue</li>
  <li>Toggle <b>View → Toggle Theme</b> for light or dark mode</li>
</ul>
"""


def show_about(parent) -> None:
    QMessageBox.about(
        parent,
        "About JSON Viewer",
        f"<h3>JSON Viewer</h3>"
        f"<p>Version {__version__}</p>"
        f"<p>Desktop graph visualizer for JSON, YAML, and XML.</p>"
        f"<p>Inspired by <a href='https://jsoncrack.com'>JSON Crack</a>.</p>"
        f"<p>Apache License 2.0</p>",
    )


def show_usage_help(parent) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle("JSON Viewer — Usage")
    dialog.resize(560, 520)

    browser = QTextBrowser(dialog)
    browser.setOpenExternalLinks(True)
    browser.setHtml(USAGE_HTML)
    browser.setFrameShape(QTextBrowser.Shape.NoFrame)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    buttons.accepted.connect(dialog.accept)

    layout = QVBoxLayout(dialog)
    layout.addWidget(browser)
    layout.addWidget(buttons)

    dialog.exec()
