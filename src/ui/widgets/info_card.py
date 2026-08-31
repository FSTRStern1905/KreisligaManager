from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)


class InfoCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        icon: str = "",
    ) -> None:
        super().__init__()

        self.setObjectName(
            "InfoCard"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setMinimumHeight(
            86
        )

        self.setMaximumHeight(
            96
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            2
        )

        self.icon_label = QLabel(
            icon
        )

        self.icon_label.setObjectName(
            "InfoCardIcon"
        )

        self.icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.icon_label.setFixedHeight(
            18
        )

        self.icon_label.setVisible(
            bool(icon)
        )

        self.title_label = QLabel(
            title
        )

        self.title_label.setObjectName(
            "InfoCardTitle"
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.title_label.setFixedHeight(
            18
        )

        self.title_label.setWordWrap(
            False
        )

        self.value_label = QLabel(
            value
        )

        self.value_label.setObjectName(
            "InfoCardValue"
        )

        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.value_label.setMinimumHeight(
            24
        )

        self.value_label.setWordWrap(
            False
        )

        layout.addWidget(
            self.icon_label
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.value_label
        )

        self._update_value_font()

    def set_value(
        self,
        value: str,
    ) -> None:
        self.value_label.setText(
            str(value)
        )

        self._update_value_font()

    def value(
        self,
    ) -> str:
        return self.value_label.text()

    def set_title(
        self,
        title: str,
    ) -> None:
        self.title_label.setText(
            title
        )

    def set_icon(
        self,
        icon: str,
    ) -> None:
        self.icon_label.setText(
            icon
        )

        self.icon_label.setVisible(
            bool(icon)
        )

    def _update_value_font(
        self,
    ) -> None:
        text = self.value_label.text()

        length = len(
            text
        )

        if length <= 22:
            self.value_label.setStyleSheet(
                ""
            )

        elif length <= 32:
            self.value_label.setStyleSheet(
                """
                font-size: 16px;
                font-weight: 600;
                """
            )

        elif length <= 44:
            self.value_label.setStyleSheet(
                """
                font-size: 14px;
                font-weight: 600;
                """
            )

        elif length <= 58:
            self.value_label.setStyleSheet(
                """
                font-size: 12px;
                font-weight: 600;
                """
            )

        else:
            self.value_label.setStyleSheet(
                """
                font-size: 10px;
                font-weight: 600;
                """
            )