from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QListWidget


class ModuleSidebar(QListWidget):
    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setObjectName(
            "ModuleSidebar"
        )

        self.setFixedWidth(
            250
        )

        self.setSpacing(
            4
        )

        self.setUniformItemSizes(
            True
        )

        self.setIconSize(
            QSize(
                20,
                20,
            )
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.setVerticalScrollMode(
            QListWidget.ScrollMode.ScrollPerPixel
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        font = QFont()
        font.setPointSize(
            10
        )

        self.setFont(
            font
        )

        self.setStyleSheet(
            """
            QListWidget#ModuleSidebar {
                background-color: #181A1F;
                border: none;
                padding: 14px 10px;
                outline: none;
            }

            QListWidget#ModuleSidebar::item {
                min-height: 44px;
                margin: 2px 0;
                padding: 0 14px;
                border-radius: 8px;
                color: #D7DBE3;
                background-color: transparent;
            }

            QListWidget#ModuleSidebar::item:hover {
                background-color: #252932;
                color: #FFFFFF;
            }

            QListWidget#ModuleSidebar::item:selected {
                background-color: #313743;
                color: #FFFFFF;
                border-left: 3px solid #6FA8FF;
                padding-left: 11px;
            }

            QListWidget#ModuleSidebar::item:selected:active {
                background-color: #313743;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px 0;
            }

            QScrollBar::handle:vertical {
                background: #3A404C;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #4A5261;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            """
        )