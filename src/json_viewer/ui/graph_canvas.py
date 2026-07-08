from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QWheelEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QLabel, QWidget

from json_viewer.graph.collapse import filter_collapsed_graph, path_key
from json_viewer.graph.layout import edge_points, layout_graph
from json_viewer.graph.models import GraphData, JSONPath, NodeData
from json_viewer.ui.graph_items import EdgeGraphicsItem, NodeGraphicsItem
from json_viewer.ui.theme import ThemeManager
from json_viewer.ui.zoom_control import GraphZoomControl

DEFAULT_MAX_NODES = 1500


class GridScene(QGraphicsScene):
    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__()
        self._theme = theme_manager

    def drawBackground(self, painter: QPainter, rect) -> None:
        colors = self._theme.colors
        painter.fillRect(rect, QBrush(QColor(colors.grid_bg)))

        grid_size = 20
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        lines_minor = QPen(QColor(colors.grid_secondary))
        lines_minor.setWidth(0)
        painter.setPen(lines_minor)
        for x in range(left, int(rect.right()), grid_size):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), grid_size):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

        lines_major = QPen(QColor(colors.grid_primary))
        lines_major.setWidth(0)
        painter.setPen(lines_major)
        major = grid_size * 5
        left_m = int(rect.left()) - (int(rect.left()) % major)
        top_m = int(rect.top()) - (int(rect.top()) % major)
        for x in range(left_m, int(rect.right()), major):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top_m, int(rect.bottom()), major):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)


class GraphCanvas(QGraphicsView):
    search_matches_changed = pyqtSignal(int)
    add_array_item = pyqtSignal(object)  # JSONPath
    add_object_key = pyqtSignal(object)  # JSONPath
    edit_scalar = pyqtSignal(object, object, str)  # JSONPath, value, type

    def __init__(self, theme_manager: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme_manager
        self._scene = GridScene(theme_manager)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._graph: GraphData | None = None
        self._collapsed: set[str] = set()
        self._node_items: dict[str, NodeGraphicsItem] = {}
        self._max_nodes = DEFAULT_MAX_NODES
        self._search_query = ""
        self._search_matches: list[str] = []
        self._search_index = 0
        self._syncing_zoom = False

        self._overlay = QLabel("Graph exceeds node limit")
        self._overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay.setStyleSheet("background: rgba(0,0,0,0.5); color: white; font-size: 14px;")
        self._overlay.hide()
        self._overlay.setParent(self.viewport())

        self._zoom_control = GraphZoomControl(theme_manager, self.viewport())
        self._zoom_control.zoom_changed.connect(self._set_zoom_percent)
        self._zoom_control.show()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        viewport = self.viewport()
        if self._overlay.isVisible():
            self._overlay.setGeometry(viewport.rect())

        margin = 12
        zoom_width = self._zoom_control.sizeHint().width()
        zoom_height = self._zoom_control.sizeHint().height()
        self._zoom_control.setGeometry(
            viewport.width() - zoom_width - margin,
            viewport.height() - zoom_height - margin,
            zoom_width,
            zoom_height,
        )
        self._zoom_control.raise_()

    def set_max_nodes(self, limit: int) -> None:
        self._max_nodes = limit

    def set_graph(self, graph: GraphData | None) -> None:
        self._graph = graph
        self._rebuild_scene()

    def toggle_collapse(self, path: JSONPath) -> None:
        key = path_key(path)
        if key in self._collapsed:
            self._collapsed.discard(key)
        else:
            self._collapsed.add(key)
        self._rebuild_scene()

    def expand_path(self, path: JSONPath) -> None:
        key = path_key(path)
        if key in self._collapsed:
            self._collapsed.discard(key)
            self._rebuild_scene()

    def collapse_all(self) -> None:
        if not self._graph:
            return
        for node in self._graph.nodes:
            for row in node.text:
                if row.type in ("object", "array") and row.key is not None:
                    self._collapsed.add(path_key((*node.path, row.key)))
        self._rebuild_scene()

    def expand_all(self) -> None:
        self._collapsed.clear()
        self._rebuild_scene()

    def _rebuild_scene(self) -> None:
        self._scene.clear()
        self._node_items.clear()

        if not self._graph or not self._graph.nodes:
            self._overlay.hide()
            return

        if len(self._graph.nodes) > self._max_nodes:
            self._overlay.setText(
                f"Graph has {len(self._graph.nodes)} nodes (limit: {self._max_nodes}). "
                "Collapse sections or reduce data size."
            )
            self._overlay.setGeometry(self.viewport().rect())
            self._overlay.show()
            self._overlay.raise_()
            return

        self._overlay.hide()
        filtered = filter_collapsed_graph(self._graph, self._collapsed)
        layout = layout_graph(filtered)
        nodes_by_id = {n.id: n for n in filtered.nodes}

        for node in filtered.nodes:
            pos = layout.positions.get(node.id, (0.0, 0.0))
            item = NodeGraphicsItem(
                node,
                self._theme,
                self._collapsed,
                self.toggle_collapse,
                on_add_array_item=self.add_array_item.emit,
                on_add_object_key=self.add_object_key.emit,
                on_edit_scalar=self.edit_scalar.emit,
            )
            item.setPos(pos[0], pos[1])
            self._scene.addItem(item)
            self._node_items[node.id] = item

        for edge in filtered.edges:
            from_node = nodes_by_id.get(edge.from_id)
            to_node = nodes_by_id.get(edge.to_id)
            if not from_node or not to_node:
                continue
            from_pos = layout.positions[edge.from_id]
            to_pos = layout.positions[edge.to_id]
            pts = edge_points(from_node, to_node, from_pos, to_pos)
            qpts = tuple(QPointF(x, y) for x, y in pts)
            self._scene.addItem(EdgeGraphicsItem(edge, qpts, self._theme))

        margin = 50
        self._scene.setSceneRect(
            -margin,
            -margin,
            layout.width + margin * 2,
            layout.height + margin * 2,
        )
        self._apply_search_highlight()

    def fit_view(self) -> None:
        rect = self._scene.itemsBoundingRect()
        if rect.isValid():
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            self._sync_zoom_slider()

    def focus_root(self) -> None:
        if self._node_items:
            first = next(iter(self._node_items.values()))
            self.centerOn(first)

    def zoom_in(self) -> None:
        self._set_zoom_percent(min(400, self._zoom_control.zoom_percent() + 15))

    def zoom_out(self) -> None:
        self._set_zoom_percent(max(10, self._zoom_control.zoom_percent() - 15))

    def _set_zoom_percent(self, percent: int) -> None:
        if self._syncing_zoom:
            return

        self._syncing_zoom = True
        anchor = self.transformationAnchor()
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        current = self.transform().m11()
        target = percent / 100.0
        if current > 0:
            self.scale(target / current, target / current)
        else:
            self.resetTransform()
            self.scale(target, target)

        self._zoom_control.set_zoom_percent(percent, emit=False)
        self.setTransformationAnchor(anchor)
        self._syncing_zoom = False

    def _sync_zoom_slider(self) -> None:
        percent = max(10, min(400, round(self.transform().m11() * 100)))
        self._zoom_control.set_zoom_percent(percent, emit=False)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = 10 if event.angleDelta().y() > 0 else -10
            self._set_zoom_percent(self._zoom_control.zoom_percent() + delta)
            event.accept()
        else:
            super().wheelEvent(event)

    def search_nodes(self, query: str) -> None:
        self._search_query = query.strip().lower()
        self._search_matches = []
        self._search_index = 0

        if not self._search_query or not self._graph:
            self._apply_search_highlight()
            self.search_matches_changed.emit(0)
            return

        for node in self._graph.nodes:
            for row in node.text:
                key_match = row.key and self._search_query in str(row.key).lower()
                val_match = row.value is not None and self._search_query in str(row.value).lower()
                if key_match or val_match:
                    self._search_matches.append(node.id)
                    break

        self._apply_search_highlight()
        if self._search_matches:
            self._focus_search_match(0)
        self.search_matches_changed.emit(len(self._search_matches))

    def next_search_match(self) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self._focus_search_match(self._search_index)

    def prev_search_match(self) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self._focus_search_match(self._search_index)

    def _focus_search_match(self, index: int) -> None:
        node_id = self._search_matches[index]
        item = self._node_items.get(node_id)
        if item:
            for nid, ni in self._node_items.items():
                ni.setSelected(nid == node_id)
            self.centerOn(item)

    def _apply_search_highlight(self) -> None:
        if not self._search_query:
            for item in self._node_items.values():
                item.setSelected(False)
            return

        selected_id = (
            self._search_matches[self._search_index] if self._search_matches else None
        )
        for node_id, item in self._node_items.items():
            item.setSelected(node_id == selected_id)

    def apply_theme(self) -> None:
        self._scene._theme = self._theme
        self._scene.update()
        self._zoom_control.apply_theme()
        self._rebuild_scene()

    def node_count(self) -> int:
        return len(self._graph.nodes) if self._graph else 0
