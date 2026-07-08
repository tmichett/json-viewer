from __future__ import annotations

import re
from typing import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QStyleOptionGraphicsItem, QWidget

from json_viewer.graph.collapse import path_key
from json_viewer.graph.models import EdgeData, JSONPath, NodeData, NodeRow
from json_viewer.ui.theme import ThemeManager

HEX_PATTERN = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
ROW_HEIGHT = 30
PADDING_X = 10


class NodeGraphicsItem(QGraphicsRectItem):
    collapse_toggled = pyqtSignal(object)  # JSONPath

    def __init__(
        self,
        node: NodeData,
        theme_manager: ThemeManager,
        collapsed: set[str],
        on_collapse: Callable[[JSONPath], None] | None = None,
    ) -> None:
        super().__init__(0, 0, node.width, node.height)
        self.node = node
        self._theme = theme_manager
        self._collapsed = collapsed
        self._on_collapse = on_collapse
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self._hovered = False

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        colors = self._theme.colors
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)

        fill = QColor(colors.highlight if self.isSelected() else colors.node_fill)
        if self._hovered and not self.isSelected():
            fill = QColor(colors.node_fill).lighter(105)

        painter.fillPath(path, QBrush(fill))
        painter.setPen(QPen(QColor(colors.node_stroke), 1))
        painter.drawPath(path)

        font = QFont("Menlo, Monaco, Consolas, monospace", 10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)

        y = PADDING_X
        for index, row in enumerate(self.node.text):
            self._paint_row(painter, row, y, index)
            y += ROW_HEIGHT

    def _paint_row(self, painter: QPainter, row: NodeRow, y: float, index: int) -> None:
        colors = self._theme.colors
        x = PADDING_X

        is_container = row.type in ("object", "array") and (row.children_count or 0) > 0
        row_path: JSONPath | None = None
        if is_container and row.key is not None:
            row_path = (*self.node.path, row.key)
        elif is_container and row.key is None and self.node.path:
            row_path = self.node.path

        collapsed = row_path is not None and path_key(row_path) in self._collapsed

        if is_container and row_path is not None:
            painter.setPen(QColor(colors.node_key))
            painter.drawText(QRectF(x, y, 14, ROW_HEIGHT), Qt.AlignmentFlag.AlignVCenter, "+" if collapsed else "−")
            x += 16

        if row.key is not None:
            painter.setPen(QColor(colors.node_key))
            key_text = f"{row.key}: "
            painter.drawText(QRectF(x, y, self.rect().width(), ROW_HEIGHT), Qt.AlignmentFlag.AlignVCenter, key_text)
            x += painter.fontMetrics().horizontalAdvance(key_text)

        display = self._row_display(row, collapsed)
        painter.setPen(QColor(self._theme.value_color(row.value, row.type)))
        painter.drawText(QRectF(x, y, self.rect().width() - x, ROW_HEIGHT), Qt.AlignmentFlag.AlignVCenter, display)

        if isinstance(display, str) and HEX_PATTERN.match(display.strip()):
            swatch_x = x + painter.fontMetrics().horizontalAdvance(display) + 6
            painter.setBrush(QBrush(QColor(display.strip())))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(swatch_x + 6, y + ROW_HEIGHT / 2), 6, 6)

    def _row_display(self, row: NodeRow, collapsed: bool) -> str:
        if row.type == "object":
            count = row.children_count or 0
            return f"⋯ {count} keys" if collapsed else f"{{{count} keys}}"
        if row.type == "array":
            count = row.children_count or 0
            return f"⋯ {count} items" if collapsed else f"[{count} items]"
        if row.value is None:
            return "null"
        return str(row.value)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            row_index = int((pos.y() - PADDING_X) / ROW_HEIGHT)
            if 0 <= row_index < len(self.node.text):
                row = self.node.text[row_index]
                is_container = row.type in ("object", "array") and (row.children_count or 0) > 0
                if is_container:
                    row_path: JSONPath | None = None
                    if row.key is not None:
                        row_path = (*self.node.path, row.key)
                    if row_path and self._on_collapse:
                        self._on_collapse(row_path)
                        event.accept()
                        return
        super().mousePressEvent(event)


class EdgeGraphicsItem(QGraphicsItem):
    def __init__(
        self,
        edge: EdgeData,
        points: tuple[QPointF, QPointF, QPointF, QPointF],
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.edge = edge
        self._points = points
        self._theme = theme_manager
        xs = [p.x() for p in points]
        ys = [p.y() for p in points]
        self._bounds = QRectF(min(xs) - 20, min(ys) - 20, max(xs) - min(xs) + 40, max(ys) - min(ys) + 40)

    def boundingRect(self) -> QRectF:
        return self._bounds

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        colors = self._theme.colors
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(colors.edge_stroke), 1.5)
        painter.setPen(pen)

        p0, p1, p2, p3 = self._points
        path = QPainterPath(p0)
        path.cubicTo(p1, p2, p3)
        painter.drawPath(path)

        if self.edge.text:
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            font = QFont("Menlo, Monaco, Consolas, monospace", 9)
            painter.setFont(font)
            painter.setPen(QColor(colors.node_key))
            painter.drawText(mid, self.edge.text)
