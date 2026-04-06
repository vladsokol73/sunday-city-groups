from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#111827"))
    palette.setColor(QPalette.WindowText, QColor("#E5E7EB"))
    palette.setColor(QPalette.Base, QColor("#0F172A"))
    palette.setColor(QPalette.AlternateBase, QColor("#172033"))
    palette.setColor(QPalette.ToolTipBase, QColor("#111827"))
    palette.setColor(QPalette.ToolTipText, QColor("#E5E7EB"))
    palette.setColor(QPalette.Text, QColor("#E5E7EB"))
    palette.setColor(QPalette.Button, QColor("#1F2937"))
    palette.setColor(QPalette.ButtonText, QColor("#E5E7EB"))
    palette.setColor(QPalette.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Link, QColor("#60A5FA"))
    palette.setColor(QPalette.Highlight, QColor("#2563EB"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.PlaceholderText, QColor("#94A3B8"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget {
            color: #E5E7EB;
            font-size: 13px;
        }
        QMainWindow, QDialog {
            background-color: #0B1220;
        }
        QLabel#pageTitle {
            font-size: 28px;
            font-weight: 700;
            color: #F8FAFC;
        }
        QLabel#pageSubtitle {
            color: #94A3B8;
            font-size: 13px;
        }
        QLabel#sectionTitle {
            font-size: 18px;
            font-weight: 600;
            color: #F8FAFC;
        }
        QLabel#sectionDescription {
            color: #94A3B8;
        }
        QLabel#statValue {
            font-size: 22px;
            font-weight: 700;
            color: #F8FAFC;
        }
        QLabel#statCaption {
            color: #94A3B8;
        }
        QFrame#heroCard,
        QFrame#card,
        QGroupBox {
            background-color: #111827;
            border: 1px solid #243244;
            border-radius: 16px;
        }
        QGroupBox {
            margin-top: 12px;
            padding: 18px 16px 16px 16px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: #CBD5E1;
        }
        QFrame#statCard {
            background-color: #172033;
            border: 1px solid #2A3A50;
            border-radius: 14px;
        }
        QTabWidget::pane {
            border: none;
            top: -1px;
        }
        QTabBar::tab {
            background: #111827;
            border: 1px solid #243244;
            padding: 10px 18px;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            margin-right: 8px;
            color: #CBD5E1;
        }
        QTabBar::tab:selected {
            background: #1D4ED8;
            border-color: #1D4ED8;
            color: #FFFFFF;
        }
        QTabBar::tab:hover:!selected {
            background: #172033;
        }
        QPushButton {
            background-color: #1F2937;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 10px 16px;
            color: #E5E7EB;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #273449;
        }
        QPushButton:pressed {
            background-color: #1B2433;
        }
        QPushButton#primaryButton {
            background-color: #2563EB;
            border-color: #2563EB;
            color: #FFFFFF;
        }
        QPushButton#primaryButton:hover {
            background-color: #1D4ED8;
        }
        QPushButton#dangerButton {
            background-color: #7F1D1D;
            border-color: #991B1B;
            color: #FEE2E2;
        }
        QPushButton#dangerButton:hover {
            background-color: #991B1B;
        }
        QLineEdit,
        QComboBox,
        QSpinBox,
        QDateEdit,
        QTextEdit,
        QTableWidget {
            background-color: #0F172A;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 8px;
            selection-background-color: #1D4ED8;
            selection-color: #FFFFFF;
        }
        QLineEdit:focus,
        QComboBox:focus,
        QSpinBox:focus,
        QDateEdit:focus,
        QTextEdit:focus,
        QTableWidget:focus {
            border: 1px solid #60A5FA;
        }
        QComboBox::drop-down,
        QSpinBox::up-button,
        QSpinBox::down-button,
        QDateEdit::drop-down {
            border: none;
            background: transparent;
            width: 20px;
        }
        QHeaderView::section {
            background-color: #172033;
            color: #CBD5E1;
            border: none;
            border-bottom: 1px solid #334155;
            padding: 10px 8px;
            font-weight: 600;
        }
        QTableWidget {
            gridline-color: #223047;
            alternate-background-color: #111827;
        }
        QTableCornerButton::section {
            background-color: #172033;
            border: none;
            border-bottom: 1px solid #334155;
        }
        QAbstractScrollArea {
            background-color: #0F172A;
        }
        QScrollBar:vertical {
            background: #0F172A;
            width: 12px;
            margin: 4px 0 4px 0;
        }
        QScrollBar::handle:vertical {
            background: #334155;
            border-radius: 6px;
            min-height: 30px;
        }
        QScrollBar:horizontal {
            background: #0F172A;
            height: 12px;
            margin: 0 4px 0 4px;
        }
        QScrollBar::handle:horizontal {
            background: #334155;
            border-radius: 6px;
            min-width: 30px;
        }
        QScrollBar::add-line,
        QScrollBar::sub-line {
            width: 0;
            height: 0;
            background: transparent;
        }
        QCheckBox {
            spacing: 8px;
        }
        QMessageBox {
            background-color: #111827;
        }
        """
    )
