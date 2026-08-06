from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class Card(QFrame):
    def __init__(
        self,
        title: str = "",
        icon: str = "",
        parent: QWidget | None = None,
        hover_enabled: bool = False,
    ) -> None:
        super().__init__(parent)

        self._title = title.strip()
        self._icon = icon.strip()
        self._hover_enabled = hover_enabled

        self._content_layout = QVBoxLayout()
        self._title_label: QLabel | None = None
        self._icon_label: QLabel | None = None

        self.setProperty(
            "cardWidget",
            True,
        )

        self.setProperty(
            "hovered",
            False,
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True,
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.setMinimumHeight(
            Metrics.CARD_MIN_HEIGHT
        )

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            Metrics.CARD_PADDING,
            Metrics.CARD_PADDING,
            Metrics.CARD_PADDING,
            Metrics.CARD_PADDING,
        )

        root_layout.setSpacing(
            Metrics.CARD_SPACING
        )

        if self._title or self._icon:
            header_layout = QHBoxLayout()

            header_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            header_layout.setSpacing(
                Metrics.SPACING_XS
            )

            if self._icon:
                self._icon_label = QLabel(
                    self._icon
                )

                self._icon_label.setProperty(
                    "cardIcon",
                    True,
                )

                self._icon_label.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self._icon_label.setFont(
                    Typography.subtitle()
                )

                header_layout.addWidget(
                    self._icon_label
                )

            if self._title:
                self._title_label = QLabel(
                    self._title
                )

                self._title_label.setProperty(
                    "cardTitle",
                    True,
                )

                self._title_label.setFont(
                    Typography.heading()
                )

                header_layout.addWidget(
                    self._title_label
                )

            header_layout.addStretch(
                1
            )

            root_layout.addLayout(
                header_layout
            )

        self._content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self._content_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        root_layout.addLayout(
            self._content_layout
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QFrame[cardWidget="true"] {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_LARGE}px;
            }}

            QFrame[cardWidget="true"][hovered="true"] {{
                background-color:
                    {Colors.CARD_BACKGROUND_HOVER};
                border-color:
                    {Colors.BORDER_LIGHT};
            }}

            QLabel[cardTitle="true"] {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel[cardIcon="true"] {{
                color:
                    {Colors.PRIMARY};
                background:
                    transparent;
                border:
                    none;
            }}
            """
        )

    def _refresh_style(self) -> None:
        self.style().unpolish(
            self
        )

        self.style().polish(
            self
        )

        self.update()

    def content_layout(
        self,
    ) -> QVBoxLayout:
        return self._content_layout

    def add_widget(
        self,
        widget: QWidget,
        stretch: int = 0,
        alignment: (
            Qt.AlignmentFlag
            | Qt.Alignment
        ) = Qt.AlignmentFlag.AlignTop,
    ) -> None:
        self._content_layout.addWidget(
            widget,
            stretch,
            alignment,
        )

    def add_layout(
        self,
        layout,
        stretch: int = 0,
    ) -> None:
        self._content_layout.addLayout(
            layout,
            stretch,
        )

    def add_stretch(
        self,
        stretch: int = 1,
    ) -> None:
        self._content_layout.addStretch(
            stretch
        )

    def set_content_spacing(
        self,
        spacing: int,
    ) -> None:
        self._content_layout.setSpacing(
            spacing
        )

    def set_title(
        self,
        title: str,
    ) -> None:
        normalized_title = title.strip()
        self._title = normalized_title

        if self._title_label is not None:
            self._title_label.setText(
                normalized_title
            )

    def enterEvent(
        self,
        event: QEnterEvent,
    ) -> None:
        if self._hover_enabled:
            self.setProperty(
                "hovered",
                True,
            )

            self._refresh_style()

        super().enterEvent(
            event
        )

    def leaveEvent(
        self,
        event,
    ) -> None:
        if self._hover_enabled:
            self.setProperty(
                "hovered",
                False,
            )

            self._refresh_style()

        super().leaveEvent(
            event
        )