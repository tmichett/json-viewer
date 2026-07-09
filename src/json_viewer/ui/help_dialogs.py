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

<h3>Graph editing</h3>
<p>You can add and change data on the graph without editing the raw text. Changes sync to the editor automatically.</p>
<ul>
  <li><b>Add array item</b> — click the blue <b>+</b> on the right of an array row (e.g. <code>fruits: [3 items]</code>).
      A form opens with fields based on existing items (like a database record view).
      Nested groups (e.g. <code>details</code>, <code>nutrients</code>) appear as labeled sections.</li>
  <li><b>Add object key</b> — click <b>+ Add key</b> at the bottom of any object node.
      Enter the key name, type, and value in the dialog.</li>
  <li><b>Edit a value</b> — click any scalar row (string, number, boolean, null) on a node to edit it.</li>
</ul>
<p><b>Note:</b> The <b>+ / −</b> on the <i>left</i> of a row collapses or expands children.
The blue <b>+</b> on the <i>right</i> of an array row adds a new item.</p>

<h3>Table preview</h3>
<p>Switch the right pane to a database-style relational view instead of the graph.</p>
<ul>
  <li>Use the <b>Preview</b> dropdown in the status bar, or <b>View → Table Preview</b> (Ctrl+Shift+T)</li>
  <li>Choose which array to display from the <b>Dataset</b> dropdown (e.g. <code>fruits</code>)</li>
  <li><b>Main table</b> — primary key first (<code>name</code>), then top-level fields (<code>color</code>)</li>
  <li><b>Related tables</b> — nested objects like <code>details</code> and <code>nutrients</code> appear as separate tables linked via the primary key</li>
  <li>Double-click a cell to edit (foreign key columns in child tables are read-only)</li>
  <li><b>+ Dataset</b> — create a new top-level array (e.g. <code>vegetables</code> alongside <code>fruits</code>)</li>
  <li><b>+ Add row</b> — on the main table, add a new item (opens the same form as graph add-item)</li>
  <li><b>+ Add key</b> — on child tables (<code>details</code>, <code>nutrients</code>), add a new field to every row in that nested object</li>
  <li>In the add-item form, nested groups also have <b>+ Add key</b> for fields not yet in the schema</li>
  <li>Form fields and columns follow <b>JSON key order</b> (e.g. <code>name</code>, <code>color</code>, then nested groups) — not alphabetical</li>
  <li>Return to the graph with <b>View → Graph Preview</b> (Ctrl+Shift+G)</li>
</ul>

<h3>Graph navigation</h3>
<ul>
  <li>Drag to pan; <b>Ctrl+scroll</b> or the zoom slider to zoom</li>
  <li>Click <b>− / +</b> on the left of <b>{N keys}</b> or <b>[N items]</b> to collapse or expand</li>
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
  <li>Empty arrays have no template to copy — a blank <code>{}</code> is added; use <b>+ Add key</b> to build it up</li>
  <li>To add one extra field to an existing object, use <b>+ Add key</b> instead of adding a whole new array item</li>
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
    dialog.resize(560, 580)

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
