from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.database import Database
from app.resources import get_app_icon_path
from app.ui.main_window import MainWindow
from app.ui.theme import apply_dark_theme


def main() -> int:
    app = QApplication([])
    app.setApplicationName("Sunday City Groups")
    apply_dark_theme(app)

    icon_path = get_app_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    database = Database()
    window = MainWindow(database)
    if icon_path:
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    return app.exec()
