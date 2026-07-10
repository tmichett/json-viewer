from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from json_viewer.graph.models import JSONPath
from json_viewer.graph.table_data import (
    RelationalTableSet,
    TableColumn,
    TableData,
    TableSection,
    TableTarget,
    build_relational_tables,
    can_add_top_level_dataset,
    discover_table_targets,
    format_cell,
    parse_cell_text,
)
from json_viewer.ui.theme import ThemeManager


class _ArrayTableModel(QAbstractTableModel):
    edit_requested = pyqtSignal(int, int, str)

    def __init__(self, section: TableSection | None = None, parent=None) -> None:
        super().__init__(parent)
        self._section = section
        self._columns: list[TableColumn] = []
        self._rows: list[list[Any]] = []
        if section is not None:
            self._columns = section.columns
            self._rows = section.rows

    def set_section(self, section: TableSection | None) -> None:
        self.beginResetModel()
        self._section = section
        if section is None:
            self._columns = []
            self._rows = []
        else:
            self._columns = section.columns
            self._rows = section.rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        if 0 <= section < len(self._columns):
            column = self._columns[section]
            if column.is_primary_key:
                return f"{column.header} 🔑"
            if column.is_foreign_key:
                return f"{column.header} →"
            return column.header
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row >= len(self._rows) or col >= len(self._columns):
            return None
        value = self._rows[row][col]
        column = self._columns[col]

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return format_cell(value)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column.is_foreign_key or column.is_primary_key:
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if column.value_type in ("number", "boolean"):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.ForegroundRole and (column.is_foreign_key or column.read_only):
            from PyQt6.QtGui import QBrush, QColor

            return QBrush(QColor(self._theme_gray()))
        return None

    def _theme_gray(self) -> str:
        return "#888888"

    def set_muted_color(self, color: str) -> None:
        self._theme_gray_value = color

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        column = self._columns[index.column()]
        base = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if not column.read_only:
            base |= Qt.ItemFlag.ItemIsEditable
        return base

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        self.edit_requested.emit(index.row(), index.column(), str(value))
        return True

    def column_at(self, index: int) -> TableColumn | None:
        if 0 <= index < len(self._columns):
            return self._columns[index]
        return None


ROW_HEIGHT = 28
SECTION_MARGIN = 12
SECTION_SPACING = 8


class _TableSectionWidget(QFrame):
    def __init__(
        self,
        section: TableSection,
        entity_label: str,
        *,
        show_add_row: bool = False,
        on_add_row=None,
        show_add_key: bool = False,
        on_add_key=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.section = section
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        if section.child_field:
            title = QLabel(section.label)
            subtitle = QLabel(f"Related to {entity_label} via {section.foreign_key}")
        else:
            title = QLabel(section.label)
            pk = section.columns[0].header if section.columns else "—"
            subtitle = QLabel(f"Primary key: {pk}")

        title_font = QFont(title.font())
        title_font.setWeight(QFont.Weight.DemiBold)
        title_font.setPointSize(10)
        title.setFont(title_font)

        subtitle_font = QFont(subtitle.font())
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: gray;")

        self.model = _ArrayTableModel(section)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setShowGrid(True)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._fit_table_height()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.table)

        if show_add_row and on_add_row is not None:
            self.add_row_btn = self._make_action_button("+ Add row", on_add_row)
            layout.addWidget(self.add_row_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        if show_add_key and on_add_key is not None:
            self.add_key_btn = self._make_action_button("+ Add key", on_add_key)
            layout.addWidget(self.add_key_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    @staticmethod
    def _make_action_button(label: str, handler) -> QPushButton:
        button = QPushButton(label)
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)
        return button

    def _fit_table_height(self) -> None:
        row_count = max(self.model.rowCount(), 1)
        header_height = self.table.horizontalHeader().sizeHint().height()
        if header_height <= 0:
            header_height = ROW_HEIGHT
        frame = self.table.frameWidth() * 2
        height = header_height + ROW_HEIGHT * row_count + frame + 2
        self.table.setFixedHeight(height)


class DataTableView(QWidget):
    cell_edited = pyqtSignal(int, int, object, object)  # section_index, row, TableColumn, value
    add_dataset_requested = pyqtSignal()
    add_row_requested = pyqtSignal()
    add_key_requested = pyqtSignal(int)

    def __init__(self, theme_manager: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme_manager
        self._data: Any = None
        self._targets: list[TableTarget] = []
        self._current_target: TableTarget | None = None
        self._table_set: RelationalTableSet | TableData | None = None
        self._section_widgets: list[_TableSectionWidget] = []
        self._updating = False

        self._path_combo = QComboBox()
        self._path_combo.setMinimumWidth(180)
        self._path_combo.currentIndexChanged.connect(self._on_path_changed)

        self._summary = QLabel("")
        self._summary.setStyleSheet("color: gray; font-size: 10px;")

        self._add_dataset_btn = QPushButton("+ Dataset")
        self._add_dataset_btn.clicked.connect(self.add_dataset_requested.emit)

        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 6)
        dataset_label = QLabel("Dataset:")
        dataset_label.setStyleSheet("color: gray; font-size: 10px; font-weight: 600;")
        header.addWidget(dataset_label)
        header.addWidget(self._path_combo, stretch=1)
        header.addWidget(self._add_dataset_btn)
        header.addWidget(self._summary)

        self._sections_container = QWidget()
        self._sections_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._sections_layout = QVBoxLayout(self._sections_container)
        self._sections_layout.setContentsMargins(12, 0, 12, 12)
        self._sections_layout.setSpacing(SECTION_SPACING)
        self._sections_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self._sections_container)

        self._empty_label = QLabel("No datasets yet. Click + Dataset to create one.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: gray; padding: 24px;")

        self._empty_add_dataset_btn = QPushButton("+ Dataset")
        self._empty_add_dataset_btn.clicked.connect(self.add_dataset_requested.emit)
        empty_layout = QVBoxLayout()
        empty_layout.addStretch()
        empty_layout.addWidget(self._empty_label)
        empty_layout.addWidget(self._empty_add_dataset_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        empty_layout.addStretch()
        self._empty_panel = QWidget()
        self._empty_panel.setLayout(empty_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(scroll, stretch=1)
        layout.addWidget(self._empty_panel)
        self._empty_panel.hide()

        self.apply_theme()

    def current_target(self) -> TableTarget | None:
        return self._current_target

    def set_data(self, data: Any, *, preferred_path: JSONPath | None = None) -> None:
        self._data = data
        self._targets = discover_table_targets(data)
        self._updating = True
        self._path_combo.clear()

        if not self._targets:
            self._current_target = None
            self._table_set = None
            self._clear_sections()
            self._sections_container.hide()
            self._empty_panel.show()
            self._path_combo.setEnabled(False)
            self._update_dataset_controls()
            self._summary.setText("0 datasets")
            self._updating = False
            return

        self._sections_container.show()
        self._empty_panel.hide()
        self._path_combo.setEnabled(True)
        self._update_dataset_controls()

        selected_index = 0
        for index, target in enumerate(self._targets):
            self._path_combo.addItem(target.label, target)
            if preferred_path is not None and target.path == preferred_path:
                selected_index = index

        self._path_combo.setCurrentIndex(selected_index)
        self._updating = False
        self._load_current_target()

    def current_path(self) -> JSONPath | None:
        return self._current_target.path if self._current_target else None

    def _clear_sections(self) -> None:
        while self._sections_layout.count():
            item = self._sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._section_widgets.clear()

    def _on_path_changed(self) -> None:
        if self._updating:
            return
        self._load_current_target()

    def _load_current_target(self) -> None:
        target = self._path_combo.currentData()
        if target is None or self._data is None:
            self._current_target = None
            self._table_set = None
            self._clear_sections()
            self._summary.setText("")
            return

        self._current_target = target
        self._table_set = build_relational_tables(self._data, target)
        self._clear_sections()

        if isinstance(self._table_set, TableData):
            section = TableSection("values", self._table_set.columns, self._table_set.rows)
            widget = _TableSectionWidget(
                section, target.label, show_add_row=True, on_add_row=self.add_row_requested.emit
            )
            widget.model.edit_requested.connect(
                lambda row, col, raw, w=widget: self._on_edit_requested(0, w, row, col, raw)
            )
            self._sections_layout.insertWidget(0, widget)
            self._section_widgets.append(widget)
            widget.table.resizeColumnsToContents()
            self._sections_layout.addStretch()
            self._summary.setText(f"{len(section.rows)} rows")
            self.apply_theme()
            return

        entity_label = self._table_set.sections[0].label if self._table_set.sections else target.label
        for index, section in enumerate(self._table_set.sections):
            is_main = section.child_field is None
            widget = _TableSectionWidget(
                section,
                entity_label,
                show_add_row=is_main,
                on_add_row=self.add_row_requested.emit if is_main else None,
                show_add_key=not is_main,
                on_add_key=(lambda _checked=False, idx=index: self.add_key_requested.emit(idx))
                if not is_main
                else None,
            )
            widget.model.edit_requested.connect(
                lambda row, col, raw, idx=index, w=widget: self._on_edit_requested(idx, w, row, col, raw)
            )
            self._sections_layout.insertWidget(index, widget)
            self._section_widgets.append(widget)
            widget.table.resizeColumnsToContents()

        self._sections_layout.addStretch()

        row_count = len(self._table_set.sections[0].rows) if self._table_set.sections else 0
        table_count = len(self._table_set.sections)
        self._summary.setText(f"{row_count} rows · {table_count} tables")
        self.apply_theme()

    def _on_edit_requested(
        self,
        section_index: int,
        widget: _TableSectionWidget,
        row: int,
        col: int,
        raw: str,
    ) -> None:
        if self._updating or self._current_target is None:
            return
        column = widget.model.column_at(col)
        if column is None or column.read_only:
            return
        try:
            value = parse_cell_text(raw, column.value_type)
        except ValueError:
            self._load_current_target()
            return
        self.cell_edited.emit(section_index, row, column, value)

    def section_at(self, index: int) -> TableSection | None:
        if isinstance(self._table_set, RelationalTableSet):
            if 0 <= index < len(self._table_set.sections):
                return self._table_set.sections[index]
        elif isinstance(self._table_set, TableData) and index == 0:
            return TableSection("values", self._table_set.columns, self._table_set.rows)
        return None

    def _update_dataset_controls(self) -> None:
        can_add = can_add_top_level_dataset(self._data)
        self._add_dataset_btn.setVisible(can_add)
        self._empty_add_dataset_btn.setVisible(can_add)

    def apply_theme(self) -> None:
        colors = self._theme.colors
        section_style = f"""
            QFrame {{
                background-color: {colors.node_fill};
                border: 1px solid {colors.divider};
                border-radius: 6px;
            }}
        """
        table_style = f"""
            QTableView {{
                background-color: {colors.editor_bg};
                color: {colors.editor_fg};
                gridline-color: {colors.divider};
                selection-background-color: {colors.selection_bg};
                selection-color: {colors.editor_fg};
                alternate-background-color: {colors.grid_bg};
                border: 1px solid {colors.divider};
            }}
            QHeaderView::section {{
                background-color: {colors.toolbar_bg};
                color: {colors.editor_fg};
                padding: 2px 8px;
                border: none;
                border-right: 1px solid {colors.divider};
                border-bottom: 1px solid {colors.divider};
                font-weight: 600;
                font-size: 11px;
            }}
        """
        action_style = f"""
            QPushButton {{
                color: {colors.highlight};
                border: none;
                padding: 2px 0;
                text-align: left;
                font-size: 11px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """
        for widget in self._section_widgets:
            widget.setStyleSheet(section_style)
            widget.table.setStyleSheet(table_style)
            if hasattr(widget, "add_row_btn"):
                widget.add_row_btn.setStyleSheet(action_style)
            if hasattr(widget, "add_key_btn"):
                widget.add_key_btn.setStyleSheet(action_style)
        self._add_dataset_btn.setStyleSheet(
            f"QPushButton {{ color: {colors.highlight}; border: 1px solid {colors.divider}; padding: 4px 10px; font-size: 11px; }}"
        )
        self._empty_add_dataset_btn.setStyleSheet(
            f"QPushButton {{ color: {colors.editor_fg}; padding: 6px 14px; }}"
        )
