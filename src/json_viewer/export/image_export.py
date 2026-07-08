from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgGenerator
from PyQt6.QtWidgets import QGraphicsScene


def export_png(scene: QGraphicsScene, path: str, scale: float = 2.0) -> None:
    rect = scene.itemsBoundingRect()
    if not rect.isValid():
        rect = QRectF(0, 0, 800, 600)

    width = int(rect.width() * scale)
    height = int(rect.height() * scale)
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(0)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    target = QRectF(0, 0, width, height)
    scene.render(painter, target, rect)
    painter.end()

    image.save(path)


def export_svg(scene: QGraphicsScene, path: str) -> None:
    rect = scene.itemsBoundingRect()
    if not rect.isValid():
        rect = QRectF(0, 0, 800, 600)

    generator = QSvgGenerator()
    generator.setFileName(path)
    generator.setSize(QSize(int(rect.width()), int(rect.height())))
    generator.setViewBox(rect)

    painter = QPainter(generator)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scene.render(painter, rect, rect)
    painter.end()
