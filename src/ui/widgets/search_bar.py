from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class SearchBar(QWidget):
    text_changed = Signal(str)
    search_submitted = Signal(str)

    def __init__(
        self,
        placeholder: str = "Suchen ...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "SearchBar"
        )

        self._layout = QHBoxLayout(
            self
        )

        self.icon_label = QLabel(
            "⌕"
        )

        self.input = QLineEdit()

        self._setup_ui(
            placeholder
        )

        self._apply_style()

        self.input.textChanged.connect(
            self.text_changed.emit
        )

        self.input.returnPressed.connect(
            self._emit_search
        )

    def _setup_ui(
        self,
        placeholder: str,
    ) -> None:
        self._layout.setContentsMargins(
            Metrics.SPACING_SMALL,
            0,
            Metrics.SPACING_SMALL,
            0,
        )

        self._layout.setSpacing(
            Metrics.SPACING_XS
        )

        self.setMinimumHeight(
            Metrics.INPUT_HEIGHT
        )

        self.icon_label.setObjectName(
            "SearchBarIcon"
        )

        self.icon_label.setFont(
            Typography.subtitle()
        )

        self.input.setObjectName(
            "SearchBarInput"
        )

        self.input.setPlaceholderText(
            placeholder.strip()
        )

        self.input.setFrame(
            False
        )

        self.input.setFont(
            Typography.body()
        )

        self._layout.addWidget(
            self.icon_label
        )

        self._layout.addWidget(
            self.input,
            1,
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#SearchBar {{
                background-color:
                    {Colors.INPUT_BACKGROUND};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.INPUT_BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
            }}

            QWidget#SearchBar:hover {{
                background-color:
                    {Colors.INPUT_BACKGROUND_HOVER};
            }}

            QLabel#SearchBarIcon {{
                color:
                    {Colors.TEXT_MUTED};
                background:
                    transparent;
                border:
                    none;
            }}

            QLineEdit#SearchBarInput {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
                border:
                    none;
                selection-background-color:
                    {Colors.PRIMARY};
                selection-color:
                    {Colors.TEXT_ON_PRIMARY};
            }}

            QLineEdit#SearchBarInput:focus {{
                border:
                    none;
            }}
            """
        )

    def _emit_search(self) -> None:
        self.search_submitted.emit(
            self.text()
        )

    def text(self) -> str:
        return self.input.text()

    def set_text(
        self,
        text: str,
    ) -> None:
        self.input.setText(
            text
        )

    def clear(self) -> None:
        self.input.clear()

    def set_placeholder(
        self,
        placeholder: str,
    ) -> None:
        self.input.setPlaceholderText(
            placeholder.strip()
        )

    def set_focus(self) -> None:
        self.input.setFocus()