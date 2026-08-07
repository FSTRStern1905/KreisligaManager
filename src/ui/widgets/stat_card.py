from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography
from src.ui.widgets.card import Card


class StatCard(Card):
    def __init__(
        self,
        title: str,
        value: str | int | float,
        icon: str = "",
        subtitle: str = "Datenbankeinträge",
        accent_color: str = Colors.PRIMARY,
        parent: QWidget | None = None,
        hover_enabled: bool = True,
    ) -> None:
        super().__init__(
            title=title,
            icon=icon,
            parent=parent,
            hover_enabled=hover_enabled,
        )

        self._accent_color = accent_color

        self.setObjectName(
            "StatCard"
        )

        self.setMinimumHeight(
            150
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.value_label = QLabel(
            str(value)
        )

        self.value_label.setObjectName(
            "StatCardValue"
        )

        self.value_label.setFont(
            Typography.hero()
        )

        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.content_layout().addStretch(
            1
        )

        self.content_layout().addWidget(
            self.value_label
        )

        self.subtitle_label = QLabel(
            subtitle.strip()
        )

        self.subtitle_label.setObjectName(
            "StatCardSubtitle"
        )

        self.subtitle_label.setFont(
            Typography.small()
        )

        self.subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.subtitle_label.setWordWrap(
            True
        )

        self.subtitle_label.setVisible(
            bool(subtitle.strip())
        )

        self.content_layout().addWidget(
            self.subtitle_label
        )

        self.content_layout().addStretch(
            1
        )

        self._apply_stat_style()

    def _apply_stat_style(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QLabel#StatCardValue {{
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}

            QLabel#StatCardSubtitle {{
                color: {Colors.TEXT_SECONDARY};
                background: transparent;
                border: none;
            }}

            QLabel[cardIcon="true"] {{
                color: {self._accent_color};
                background: transparent;
                border: none;
            }}
            """
        )

    def set_value(
        self,
        value: str | int | float,
    ) -> None:
        self.value_label.setText(
            str(value)
        )

    def set_subtitle(
        self,
        subtitle: str,
    ) -> None:
        normalized_subtitle = (
            subtitle.strip()
        )

        self.subtitle_label.setText(
            normalized_subtitle
        )

        self.subtitle_label.setVisible(
            bool(normalized_subtitle)
        )

    def set_accent_color(
        self,
        accent_color: str,
    ) -> None:
        self._accent_color = accent_color
        self._apply_stat_style()