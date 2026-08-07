from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class SecondaryButton(QPushButton):
    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            text.strip(),
            parent,
        )

        self.setObjectName(
            "SecondaryButton"
        )

        self.setMinimumHeight(
            Metrics.BUTTON_HEIGHT
        )

        self.setMinimumWidth(
            Metrics.BUTTON_MIN_WIDTH
        )

        self.setCursor(
            QCursor(
                Qt.CursorShape.PointingHandCursor
            )
        )

        self.setFont(
            Typography.body()
        )

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QPushButton#SecondaryButton {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
                padding-left:
                    {Metrics.BUTTON_PADDING_HORIZONTAL}px;
                padding-right:
                    {Metrics.BUTTON_PADDING_HORIZONTAL}px;
            }}

            QPushButton#SecondaryButton:hover {{
                background-color:
                    {Colors.CARD_BACKGROUND_HOVER};
                border-color:
                    {Colors.BORDER_LIGHT};
            }}

            QPushButton#SecondaryButton:pressed {{
                background-color:
                    {Colors.CARD_BACKGROUND_ACTIVE};
            }}

            QPushButton#SecondaryButton:disabled {{
                background-color:
                    {Colors.BACKGROUND_ELEVATED};
                color:
                    {Colors.TEXT_DISABLED};
                border-color:
                    {Colors.DIVIDER};
            }}
            """
        )