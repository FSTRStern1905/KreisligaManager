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


class PrimaryButton(QPushButton):
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
            "PrimaryButton"
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
            QPushButton#PrimaryButton {{
                background-color:
                    {Colors.PRIMARY};
                color:
                    {Colors.TEXT_ON_PRIMARY};
                border:
                    none;
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
                padding-left:
                    {Metrics.BUTTON_PADDING_HORIZONTAL}px;
                padding-right:
                    {Metrics.BUTTON_PADDING_HORIZONTAL}px;
            }}

            QPushButton#PrimaryButton:hover {{
                background-color:
                    {Colors.PRIMARY_HOVER};
            }}

            QPushButton#PrimaryButton:pressed {{
                background-color:
                    {Colors.PRIMARY_ACTIVE};
            }}

            QPushButton#PrimaryButton:disabled {{
                background-color:
                    {Colors.CARD_BACKGROUND_ACTIVE};
                color:
                    {Colors.TEXT_DISABLED};
            }}
            """
        )