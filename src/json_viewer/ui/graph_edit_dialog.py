from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from json_viewer.graph.data_edit import parse_typed_value
from json_viewer.graph.schema import FieldSchema, build_object_from_fields


VALUE_TYPES = [
    ("String", "string"),
    ("Number", "number"),
    ("Boolean", "boolean"),
    ("Null", "null"),
    ("Object {}", "object"),
    ("Array []", "array"),
]


class AddKeyDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Key")
        self.resize(360, 160)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("key name")

        self._type_combo = QComboBox()
        for label, value in VALUE_TYPES:
            self._type_combo.addItem(label, value)

        self._value_input = QLineEdit()
        self._value_input.setPlaceholderText("value")

        form = QFormLayout()
        form.addRow("Key", self._key_input)
        form.addRow("Type", self._type_combo)
        form.addRow("Value", self._value_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._type_combo.currentIndexChanged.connect(self._sync_value_field)
        self._sync_value_field()

    def _sync_value_field(self) -> None:
        value_type = self._type_combo.currentData()
        needs_value = value_type in ("string", "number", "boolean")
        self._value_input.setEnabled(needs_value)
        if not needs_value:
            self._value_input.clear()

    def _on_accept(self) -> None:
        key = self._key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Add Key", "Key name is required.")
            return
        try:
            self._parsed_value = parse_typed_value(
                self._value_input.text(), self._type_combo.currentData()
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Add Key", str(exc))
            return
        self._parsed_key = key
        self.accept()

    def result_key_value(self) -> tuple[str, object]:
        return self._parsed_key, self._parsed_value


class EditValueDialog(QDialog):
    def __init__(self, key: str | None, current: object, value_type: str, parent=None) -> None:
        super().__init__(parent)
        title = f"Edit {key}" if key else "Edit Value"
        self.setWindowTitle(title)
        self.resize(360, 120)

        self._value_type = value_type
        self._type_combo = QComboBox()
        for label, vt in VALUE_TYPES:
            if vt in ("object", "array"):
                continue
            self._type_combo.addItem(label, vt)
        index = self._type_combo.findData(value_type)
        if index >= 0:
            self._type_combo.setCurrentIndex(index)

        self._value_input = QLineEdit()
        if current is None:
            self._value_input.setText("")
        else:
            self._value_input.setText(str(current).lower() if value_type == "boolean" else str(current))

        form = QFormLayout()
        form.addRow("Type", self._type_combo)
        form.addRow("Value", self._value_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._type_combo.currentIndexChanged.connect(self._sync_value_field)
        self._sync_value_field()

    def _sync_value_field(self) -> None:
        value_type = self._type_combo.currentData()
        self._value_input.setEnabled(value_type != "null")

    def _on_accept(self) -> None:
        try:
            self._parsed_value = parse_typed_value(
                self._value_input.text(), self._type_combo.currentData()
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Edit Value", str(exc))
            return
        self.accept()

    def parsed_value(self) -> object:
        return self._parsed_value


class AddArrayItemDialog(QDialog):
    def __init__(
        self,
        schema: FieldSchema,
        *,
        title: str = "Add Item",
        subtitle: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 480)
        self._schema = schema
        self._inputs: dict[tuple[str, ...], QLineEdit] = {}

        layout = QVBoxLayout(self)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setWordWrap(True)
            subtitle_label.setStyleSheet("color: gray; margin-bottom: 4px;")
            layout.addWidget(subtitle_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form_layout = QVBoxLayout(form_host)
        self._build_fields(form_layout, schema, ())
        scroll.setWidget(form_host)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_fields(self, layout: QVBoxLayout, schema: FieldSchema, prefix: tuple[str, ...]) -> None:
        if schema.value_type != "object":
            return

        for key in schema.child_order or sorted(schema.children):
            child = schema.children[key]
            child_prefix = (*prefix, key)
            if child.value_type == "object" and child.children:
                group = QGroupBox(key)
                group_layout = QVBoxLayout(group)
                self._build_fields(group_layout, child, child_prefix)
                layout.addWidget(group)
                continue

            row_host = QWidget()
            row_form = QFormLayout(row_host)
            row_form.setContentsMargins(0, 0, 0, 0)
            field = QLineEdit()
            field.setPlaceholderText(self._placeholder_for(child))
            row_form.addRow(key, field)
            self._inputs[child_prefix] = field
            layout.addWidget(row_host)

    def _placeholder_for(self, schema: FieldSchema) -> str:
        if schema.value_type == "number":
            return "0"
        if schema.value_type == "boolean":
            return "true or false"
        if schema.value_type == "null":
            return "null"
        return ""

    def _on_accept(self) -> None:
        try:
            values = {path: field.text() for path, field in self._inputs.items()}
            self._parsed_item = build_object_from_fields(self._schema, values)
        except ValueError as exc:
            QMessageBox.warning(self, self.windowTitle(), str(exc))
            return
        self.accept()

    def parsed_item(self) -> object:
        return self._parsed_item


class AddScalarItemDialog(QDialog):
    def __init__(self, value_type: str, *, title: str = "Add Item", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(360, 120)

        self._value_input = QLineEdit()
        self._value_input.setPlaceholderText(self._placeholder_for(value_type))

        form = QFormLayout()
        form.addRow("Value", self._value_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._value_type = value_type

    def _placeholder_for(self, value_type: str) -> str:
        if value_type == "number":
            return "0"
        if value_type == "boolean":
            return "true or false"
        return ""

    def _on_accept(self) -> None:
        try:
            self._parsed_item = parse_typed_value(self._value_input.text(), self._value_type)
        except ValueError as exc:
            QMessageBox.warning(self, self.windowTitle(), str(exc))
            return
        self.accept()

    def parsed_item(self) -> object:
        return self._parsed_item


class AddDatasetDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Dataset")
        self.resize(380, 140)

        intro = QLabel(
            "Create a new top-level array in the document (e.g. vegetables alongside fruits)."
        )
        intro.setWordWrap(True)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("dataset name, e.g. vegetables")

        form = QFormLayout()
        form.addRow("Name", self._name_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Add Dataset", "Dataset name is required.")
            return
        if not name.replace("_", "").isalnum():
            QMessageBox.warning(self, "Add Dataset", "Use letters, numbers, and underscores only.")
            return
        self._name = name
        self.accept()

    def dataset_name(self) -> str:
        return self._name
