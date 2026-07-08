from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class ThemeColors:
    grid_bg: str
    grid_primary: str
    grid_secondary: str
    node_fill: str
    node_stroke: str
    edge_stroke: str
    text: str
    node_key: str
    node_value: str
    integer: str
    null_color: str
    bool_true: str
    bool_false: str
    child_count: str
    divider: str
    toolbar_bg: str
    editor_bg: str
    editor_fg: str
    selection_bg: str
    status_valid: str
    status_error: str
    highlight: str
    search_match: str
    brace: str


LIGHT_THEME = ThemeColors(
    grid_bg="#f7f7f7",
    grid_primary="#ebe8e8",
    grid_secondary="#f2eeee",
    node_fill="#ffffff",
    node_stroke="#BCBEC0",
    edge_stroke="#BCBEC0",
    text="#000000",
    node_key="#761CEA",
    node_value="#535353",
    integer="#FD0079",
    null_color="#afafaf",
    bool_true="#748700",
    bool_false="#FF0000",
    child_count="#535353",
    divider="#e6e6e6",
    toolbar_bg="#F6F8FA",
    editor_bg="#ffffff",
    editor_fg="#24292f",
    selection_bg="#b4d5fe",
    status_valid="#008736",
    status_error="#FF0000",
    highlight="#3B82F6",
    search_match="#FFF3B0",
    brace="#9A6700",
)

DARK_THEME = ThemeColors(
    grid_bg="#141414",
    grid_primary="#1c1b1b",
    grid_secondary="#191919",
    node_fill="#292929",
    node_stroke="#424242",
    edge_stroke="#444444",
    text="#DCE5E7",
    node_key="#59b8ff",
    node_value="#DCE5E7",
    integer="#e8c479",
    null_color="#939598",
    bool_true="#00DC7D",
    bool_false="#F85C50",
    child_count="#FFFFFF",
    divider="#383838",
    toolbar_bg="#1e1e1e",
    editor_bg="#1e1e1e",
    editor_fg="#DCE5E7",
    selection_bg="#264f78",
    status_valid="#00DC7D",
    status_error="#F85C50",
    highlight="#3B82F6",
    search_match="#4a4520",
    brace="#FFA657",
)


class ThemeManager:
    def __init__(self) -> None:
        settings = QSettings()
        stored = settings.value("theme", ThemeMode.LIGHT.value)
        self._mode = ThemeMode(stored) if stored in ThemeMode._value2member_map_ else ThemeMode.LIGHT

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    @property
    def colors(self) -> ThemeColors:
        return DARK_THEME if self._mode == ThemeMode.DARK else LIGHT_THEME

    def toggle(self) -> None:
        self._mode = ThemeMode.DARK if self._mode == ThemeMode.LIGHT else ThemeMode.LIGHT
        QSettings().setValue("theme", self._mode.value)

    def set_mode(self, mode: ThemeMode) -> None:
        self._mode = mode
        QSettings().setValue("theme", mode.value)

    def apply_to_app(self, app: QApplication) -> None:
        colors = self.colors
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.editor_bg))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.editor_fg))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.editor_bg))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.toolbar_bg))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.editor_fg))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.toolbar_bg))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.editor_fg))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.selection_bg))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.editor_fg))
        app.setPalette(palette)

    def value_color(self, value: Any, value_type: str) -> str:
        colors = self.colors
        if value_type == "null":
            return colors.null_color
        if value_type == "number":
            return colors.integer
        if value_type == "boolean":
            return colors.bool_true if value else colors.bool_false
        if value_type == "object":
            return colors.node_key
        if value_type == "array":
            return colors.child_count
        return colors.node_value
