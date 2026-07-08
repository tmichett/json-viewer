import sys

from PyQt6.QtWidgets import QApplication

from json_viewer.ui.main_window import MainWindow
from json_viewer.ui.theme import ThemeManager


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("JSON Viewer")
    app.setOrganizationName("json-viewer")

    theme_manager = ThemeManager()
    theme_manager.apply_to_app(app)

    window = MainWindow(theme_manager)
    window.show()

    return app.exec()
