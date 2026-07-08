from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class SearchBar(QWidget):
    search_changed = pyqtSignal(str)
    next_match = pyqtSignal()
    prev_match = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Search nodes...")
        self._input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self._input)

        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(28)
        prev_btn.clicked.connect(self.prev_match.emit)
        layout.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(28)
        next_btn.clicked.connect(self.next_match.emit)
        layout.addWidget(next_btn)

        self._count_label = QPushButton("0 matches")
        self._count_label.setEnabled(False)
        self._count_label.setFlat(True)
        layout.addWidget(self._count_label)

    def set_match_count(self, count: int) -> None:
        self._count_label.setText(f"{count} match{'es' if count != 1 else ''}")

    def clear(self) -> None:
        self._input.clear()
