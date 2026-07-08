from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class GraphToolbar(QWidget):
    zoom_in_clicked = pyqtSignal()
    zoom_out_clicked = pyqtSignal()
    fit_clicked = pyqtSignal()
    focus_root_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addStretch()

        for label, signal in [
            ("−", self.zoom_out_clicked),
            ("+", self.zoom_in_clicked),
            ("Fit", self.fit_clicked),
            ("Root", self.focus_root_clicked),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.clicked.connect(signal.emit)
            layout.addWidget(btn)
