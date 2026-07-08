from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings, QTimer, Qt
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from json_viewer.adapters.base import convert_content, format_content, parse_content
from json_viewer.adapters.types import DataFormat
from json_viewer.export.image_export import export_png, export_svg
from json_viewer.graph.parser import graph_data_from_result, parse_graph_from_data
from json_viewer.lint.linter import lint_content
from json_viewer.ui.editor import CodeEditor
from json_viewer.ui.graph_canvas import GraphCanvas
from json_viewer.ui.search_bar import SearchBar
from json_viewer.ui.theme import ThemeManager, ThemeMode
from json_viewer.ui.toolbar import GraphToolbar
from json_viewer.ui.help_dialogs import show_about, show_usage_help
from json_viewer.ui.widgets import ClickableLabel

EXAMPLE_JSON = """{
  "fruits": [
    {
      "name": "Apple",
      "color": "#FF0000",
      "details": {
        "type": "Pome",
        "season": "Fall"
      },
      "nutrients": {
        "calories": 52,
        "fiber": "2.4g",
        "vitaminC": "4.6mg"
      }
    },
    {
      "name": "Banana",
      "color": "#FFFF00",
      "details": {
        "type": "Berry",
        "season": "Year-round"
      },
      "nutrients": {
        "calories": 89,
        "fiber": "2.6g",
        "potassium": "358mg"
      }
    },
    {
      "name": "Orange",
      "color": "#FFA500",
      "details": {
        "type": "Citrus",
        "season": "Winter"
      },
      "nutrients": {
        "calories": 47,
        "fiber": "2.4g",
        "vitaminC": "53.2mg"
      }
    }
  ]
}
"""


class MainWindow(QMainWindow):
    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__()
        self._theme = theme_manager
        self._current_file: Path | None = None
        self._dirty = False
        self._live_transform = True
        self._view_format = DataFormat.JSON
        self._converting = False

        self.setWindowTitle("JSON Viewer")
        self.resize(1400, 900)
        self.setAcceptDrops(True)

        self._editor = CodeEditor(self._theme)
        self._editor.textChanged.connect(self._on_editor_changed)

        self._graph = GraphCanvas(self._theme)
        self._graph_toolbar = GraphToolbar()
        self._search_bar = SearchBar()

        graph_panel = QWidget()
        graph_layout = QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(0)
        graph_layout.addWidget(self._graph, stretch=1)
        graph_layout.addWidget(self._search_bar)
        graph_layout.addWidget(self._graph_toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._editor)
        splitter.addWidget(graph_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([500, 900])
        self.setCentralWidget(splitter)

        self._build_menus()

        status = QStatusBar()
        self.setStatusBar(status)
        self._status_valid = ClickableLabel("Valid")
        self._status_valid.clicked.connect(self._go_to_lint_error)
        self._status_detail = QLabel("")
        self._status_detail.setStyleSheet("color: gray;")
        self._status_live = QLabel("Live Transform: On")
        self._status_nodes = QLabel("Nodes: 0")
        self._view_format_combo = QComboBox()
        for fmt in DataFormat:
            self._view_format_combo.addItem(fmt.label, fmt)
        self._view_format_combo.currentIndexChanged.connect(self._on_view_format_changed)

        status.addWidget(self._status_valid)
        status.addWidget(self._status_detail, stretch=1)
        status.addPermanentWidget(self._status_live)
        status.addPermanentWidget(self._status_nodes)
        status.addPermanentWidget(QLabel("View as:"))
        status.addPermanentWidget(self._view_format_combo)

        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._refresh_graph)

        self._lint_debounce = QTimer()
        self._lint_debounce.setSingleShot(True)
        self._lint_debounce.setInterval(200)
        self._lint_debounce.timeout.connect(self._run_lint)

        self._graph_toolbar.zoom_in_clicked.connect(self._graph.zoom_in)
        self._graph_toolbar.zoom_out_clicked.connect(self._graph.zoom_out)
        self._graph_toolbar.fit_clicked.connect(self._graph.fit_view)
        self._graph_toolbar.focus_root_clicked.connect(self._graph.focus_root)
        self._search_bar.search_changed.connect(self._graph.search_nodes)
        self._search_bar.next_match.connect(self._graph.next_search_match)
        self._search_bar.prev_match.connect(self._graph.prev_search_match)
        self._graph.search_matches_changed.connect(self._search_bar.set_match_count)

        self._editor.set_data_format(self._view_format)
        self._sync_view_format_combo()
        self._editor.setPlainText(EXAMPLE_JSON)
        self._run_lint()
        self._refresh_graph()
        self._graph.fit_view()

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()
        export_png_action = QAction("Export PNG...", self)
        export_png_action.triggered.connect(lambda: self._export_image("png"))
        file_menu.addAction(export_png_action)

        export_svg_action = QAction("Export SVG...", self)
        export_svg_action.triggered.connect(lambda: self._export_image("svg"))
        file_menu.addAction(export_svg_action)

        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menubar.addMenu("&View")
        theme_action = QAction("Toggle &Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        fit_action = QAction("&Fit Graph", self)
        fit_action.setShortcut(QKeySequence("Ctrl+0"))
        fit_action.triggered.connect(self._graph.fit_view)
        view_menu.addAction(fit_action)

        focus_action = QAction("Focus &Root Node", self)
        focus_action.triggered.connect(self._graph.focus_root)
        view_menu.addAction(focus_action)

        view_menu.addSeparator()
        view_as_menu = view_menu.addMenu("View &As")
        for fmt in DataFormat:
            action = QAction(fmt.label, self)
            action.triggered.connect(lambda checked=False, f=fmt: self._set_view_format(f))
            view_as_menu.addAction(action)

        tools_menu = menubar.addMenu("&Tools")
        validate_action = QAction("&Validate Document", self)
        validate_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        validate_action.triggered.connect(self._validate_document)
        tools_menu.addAction(validate_action)

        goto_error_action = QAction("&Go to Error", self)
        goto_error_action.setShortcut(QKeySequence("F8"))
        goto_error_action.triggered.connect(self._go_to_lint_error)
        tools_menu.addAction(goto_error_action)

        tools_menu.addSeparator()
        format_action = QAction("&Format Document", self)
        format_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        format_action.triggered.connect(self._format_document)
        tools_menu.addAction(format_action)

        search_action = QAction("&Search Nodes", self)
        search_action.setShortcut(QKeySequence.StandardKey.Find)
        search_action.triggered.connect(self._search_bar._input.setFocus)
        tools_menu.addAction(search_action)

        live_action = QAction("Toggle &Live Transform", self)
        live_action.setShortcut(QKeySequence("Ctrl+L"))
        live_action.triggered.connect(self._toggle_live_transform)
        tools_menu.addAction(live_action)

        collapse_action = QAction("Collapse &All", self)
        collapse_action.triggered.connect(self._graph.collapse_all)
        tools_menu.addAction(collapse_action)

        expand_action = QAction("&Expand All", self)
        expand_action.triggered.connect(self._graph.expand_all)
        tools_menu.addAction(expand_action)

        help_menu = menubar.addMenu("&Help")
        usage_action = QAction("&Usage...", self)
        usage_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        usage_action.triggered.connect(lambda: show_usage_help(self))
        help_menu.addAction(usage_action)

        about_action = QAction("&About JSON Viewer", self)
        about_action.triggered.connect(lambda: show_about(self))
        help_menu.addAction(about_action)

    def _on_editor_changed(self) -> None:
        if self._converting:
            return
        self._dirty = True
        self._update_title()
        self._lint_debounce.start()
        if self._live_transform:
            self._debounce.start()

    def _run_lint(self) -> None:
        text = self._editor.toPlainText()
        result = lint_content(text, self._view_format)
        self._editor.set_lint_errors(result.errors)
        self._update_lint_status(result.errors)

    def _update_lint_status(self, errors: list) -> None:
        if not errors:
            self._status_valid.setText("Valid")
            self._status_valid.setStyleSheet(f"color: {self._theme.colors.status_valid}")
            self._status_valid.setCursor(Qt.CursorShape.ArrowCursor)
            self._status_detail.setText("")
            return

        err = errors[0]
        loc = ""
        if err.line is not None:
            loc = f"line {err.line}"
            if err.column is not None:
                loc += f", col {err.column}"
        suffix = f" ({len(errors)} errors)" if len(errors) > 1 else ""
        self._status_valid.setText(f"Invalid — click to jump")
        self._status_valid.setStyleSheet(f"color: {self._theme.colors.status_error}; font-weight: 600;")
        self._status_valid.setCursor(Qt.CursorShape.PointingHandCursor)
        detail = err.message
        if loc:
            detail = f"{loc}: {detail}"
        self._status_detail.setText(f"{detail}{suffix}")

    def _go_to_lint_error(self) -> None:
        self._editor.go_to_error()

    def _validate_document(self) -> None:
        self._run_lint()
        text = self._editor.toPlainText()
        result = lint_content(text, self._view_format)
        if not result.errors:
            QMessageBox.information(self, "Validation", "No issues found.")
            return

        lines = []
        for index, err in enumerate(result.errors, start=1):
            loc = ""
            if err.line is not None:
                loc = f"Line {err.line}"
                if err.column is not None:
                    loc += f", column {err.column}"
                loc += " — "
            lines.append(f"{index}. {loc}{err.message}")

        QMessageBox.warning(self, "Validation Errors", "\n".join(lines))
        self._editor.go_to_error(result.errors[0])

    def _on_view_format_changed(self) -> None:
        new_format = self._view_format_combo.currentData()
        if new_format == self._view_format:
            return
        self._set_view_format(new_format)

    def _set_view_format(self, new_format: DataFormat) -> None:
        if new_format == self._view_format:
            return

        text = self._editor.toPlainText()
        if not text.strip():
            self._view_format = new_format
            self._sync_view_format_combo()
            self._editor.set_data_format(new_format)
            return

        result = convert_content(text, self._view_format, new_format)
        if result.errors:
            QMessageBox.warning(
                self,
                "View Format Error",
                f"Cannot convert {self._view_format.label} to {new_format.label}:\n"
                f"{result.errors[0].message}",
            )
            self._sync_view_format_combo()
            return

        self._view_format = new_format
        self._converting = True
        self._editor.setPlainText(result.text)
        self._editor.set_data_format(new_format)
        self._converting = False
        self._dirty = True
        self._update_title()
        self._run_lint()
        if self._live_transform:
            self._refresh_graph()

    def _sync_view_format_combo(self) -> None:
        index = self._view_format_combo.findData(self._view_format)
        if index >= 0:
            self._view_format_combo.blockSignals(True)
            self._view_format_combo.setCurrentIndex(index)
            self._view_format_combo.blockSignals(False)

    def _toggle_live_transform(self) -> None:
        self._live_transform = not self._live_transform
        self._status_live.setText(f"Live Transform: {'On' if self._live_transform else 'Off'}")
        if self._live_transform:
            self._refresh_graph()

    def _toggle_theme(self) -> None:
        from PyQt6.QtWidgets import QApplication

        self._theme.toggle()
        app = QApplication.instance()
        if app is not None:
            self._theme.apply_to_app(app)
        self._editor.apply_theme()
        self._graph.apply_theme()

    def _refresh_graph(self) -> None:
        text = self._editor.toPlainText()
        result = parse_content(text, self._view_format)

        if result.errors:
            self._update_lint_status(result.errors)
            self._editor.set_lint_errors(result.errors)
            self._graph.set_graph(None)
            self._status_nodes.setText("Nodes: 0")
            return

        self._update_lint_status([])
        self._editor.clear_lint_errors()

        graph_result = parse_graph_from_data(result.data)
        graph = graph_data_from_result(graph_result)
        self._graph.set_graph(graph)
        self._status_nodes.setText(f"Nodes: {len(graph.nodes)}")

    def _format_document(self) -> None:
        text = self._editor.toPlainText()
        result = parse_content(text, self._view_format)
        if result.errors:
            QMessageBox.warning(self, "Format Error", result.errors[0].message)
            return
        formatted = format_content(result.data, self._view_format)
        self._converting = True
        self._editor.setPlainText(formatted)
        self._converting = False
        self._refresh_graph()

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Data Files (*.json *.yaml *.yml *.xml);;All Files (*)",
        )
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Open Error", str(exc))
            return

        self._current_file = path
        self._view_format = DataFormat.from_extension(str(path))
        self._sync_view_format_combo()
        self._editor.set_data_format(self._view_format)
        self._converting = True
        self._editor.setPlainText(text)
        self._converting = False
        self._dirty = False
        self._update_title()
        self._run_lint()
        self._refresh_graph()
        self._graph.fit_view()
        self._add_recent(path)

    def _save_file(self) -> None:
        if self._current_file is None:
            self._save_file_as()
        else:
            self._write_file(self._current_file)

    def _save_file_as(self) -> None:
        filters = {
            DataFormat.JSON: "JSON Files (*.json)",
            DataFormat.YAML: "YAML Files (*.yaml *.yml)",
            DataFormat.XML: "XML Files (*.xml)",
        }
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", filters.get(self._view_format, "All Files (*)")
        )
        if path:
            self._current_file = Path(path)
            self._write_file(self._current_file)

    def _write_file(self, path: Path) -> None:
        try:
            path.write_text(self._editor.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            return
        self._dirty = False
        self._update_title()
        self._add_recent(path)

    def _export_image(self, fmt: str) -> None:
        if self._graph.node_count() == 0:
            QMessageBox.information(self, "Export", "Nothing to export.")
            return

        ext = "png" if fmt == "png" else "svg"
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {ext.upper()}", "", f"{ext.upper()} Files (*.{ext})"
        )
        if not path:
            return
        scene = self._graph._scene
        if fmt == "png":
            export_png(scene, path)
        else:
            export_svg(scene, path)

    def _update_title(self) -> None:
        name = self._current_file.name if self._current_file else "Untitled"
        prefix = "*" if self._dirty else ""
        self.setWindowTitle(f"{prefix}{name} — JSON Viewer")

    def _add_recent(self, path: Path) -> None:
        settings = QSettings()
        recent = settings.value("recent_files", [])
        if not isinstance(recent, list):
            recent = []
        path_str = str(path)
        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        settings.setValue("recent_files", recent[:10])

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self._load_file(path)
                break

    def closeEvent(self, event) -> None:
        if self._dirty:
            answer = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Save:
                self._save_file()
            elif answer == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()
