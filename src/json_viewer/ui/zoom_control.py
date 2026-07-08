from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

from json_viewer.ui.theme import ThemeManager

ZOOM_MIN = 10
ZOOM_MAX = 400
ZOOM_DEFAULT = 100


class GraphZoomControl(QWidget):
    zoom_changed = pyqtSignal(int)

    def __init__(self, theme_manager: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme_manager
        self._block_signals = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self._out_btn = QPushButton("−")
        self._out_btn.setFixedSize(28, 28)
        self._out_btn.clicked.connect(self._step_down)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(ZOOM_MIN, ZOOM_MAX)
        self._slider.setValue(ZOOM_DEFAULT)
        self._slider.setFixedWidth(140)
        self._slider.valueChanged.connect(self._on_slider_changed)

        self._in_btn = QPushButton("+")
        self._in_btn.setFixedSize(28, 28)
        self._in_btn.clicked.connect(self._step_up)

        self._label = QLabel("100%")
        self._label.setFixedWidth(42)
        self._label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._out_btn)
        layout.addWidget(self._slider)
        layout.addWidget(self._in_btn)
        layout.addWidget(self._label)

        self.apply_theme()

    def _on_slider_changed(self, value: int) -> None:
        self._label.setText(f"{value}%")
        if not self._block_signals:
            self.zoom_changed.emit(value)

    def _step_down(self) -> None:
        self.set_zoom_percent(max(ZOOM_MIN, self._slider.value() - 10))

    def _step_up(self) -> None:
        self.set_zoom_percent(min(ZOOM_MAX, self._slider.value() + 10))

    def set_zoom_percent(self, percent: int, *, emit: bool = True) -> None:
        clamped = max(ZOOM_MIN, min(ZOOM_MAX, percent))
        self._block_signals = True
        self._slider.setValue(clamped)
        self._label.setText(f"{clamped}%")
        self._block_signals = False
        if emit:
            self.zoom_changed.emit(clamped)

    def zoom_percent(self) -> int:
        return self._slider.value()

    def apply_theme(self) -> None:
        colors = self._theme.colors
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {colors.toolbar_bg};
                border: 1px solid {colors.divider};
                border-radius: 6px;
            }}
            QPushButton {{
                background-color: {colors.editor_bg};
                color: {colors.editor_fg};
                border: 1px solid {colors.divider};
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.selection_bg};
            }}
            QLabel {{
                color: {colors.editor_fg};
                border: none;
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: {colors.divider};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 14px;
                margin: -5px 0;
                background: {colors.highlight};
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {colors.highlight};
                border-radius: 2px;
            }}
            """
        )
