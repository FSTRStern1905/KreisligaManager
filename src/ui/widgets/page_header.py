from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class PageHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = title.strip()
        self._subtitle = subtitle.strip()

        self.setObjectName("PageHeader")

        self._root_layout = QHBoxLayout(self)
        self._text_layout = QVBoxLayout()
        self._actions_layout = QHBoxLayout()

        self.title_label = QLabel(self._title)
        self.subtitle_label = QLabel(self._subtitle)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self._text_layout.setContentsMargins(0, 0, 0, 0)
        self._text_layout.setSpacing(
            Metrics.SPACING_XXS
        )

        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(
            Metrics.SPACING_XS
        )

        self.title_label.setObjectName(
            "PageHeaderTitle"
        )
        self.title_label.setFont(
            Typography.title()
        )
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.subtitle_label.setObjectName(
            "PageHeaderSubtitle"
        )
        self.subtitle_label.setFont(
            Typography.body()
        )
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(
            bool(self._subtitle)
        )

        self._text_layout.addWidget(
            self.title_label
        )
        self._text_layout.addWidget(
            self.subtitle_label
        )

        self._root_layout.addLayout(
            self._text_layout,
            1,
        )
        self._root_layout.addLayout(
            self._actions_layout,
            0,
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#PageHeader {{
                background: transparent;
            }}

            QLabel#PageHeaderTitle {{
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}

            QLabel#PageHeaderSubtitle {{
                color: {Colors.TEXT_SECONDARY};
                background: transparent;
                border: none;
            }}
            """
        )

    def add_action(
        self,
        widget: QWidget,
    ) -> None:
        self._actions_layout.addWidget(widget)

    def add_action_stretch(
        self,
        stretch: int = 1,
    ) -> None:
        self._actions_layout.addStretch(stretch)

    def set_title(
        self,
        title: str,
    ) -> None:
        self._title = title.strip()
        self.title_label.setText(
            self._title
        )

    def set_subtitle(
        self,
        subtitle: str,
    ) -> None:
        self._subtitle = subtitle.strip()
        self.subtitle_label.setText(
            self._subtitle
        )
        self.subtitle_label.setVisible(
            bool(self._subtitle)
        )

    def clear_actions(self) -> None:
        while self._actions_layout.count():
            item = self._actions_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)