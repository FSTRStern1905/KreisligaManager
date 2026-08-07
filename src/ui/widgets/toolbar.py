from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
)

from src.ui.theme.metrics import Metrics
from src.ui.widgets.search_bar import SearchBar


class Toolbar(QWidget):
    def __init__(
        self,
        search_placeholder: str = "Suchen ...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "Toolbar"
        )

        self._layout = QHBoxLayout(
            self
        )

        self.search_bar = SearchBar(
            placeholder=search_placeholder,
            parent=self,
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        self._layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self._layout.setSpacing(
            Metrics.SPACING_XS
        )

        self.search_bar.setMinimumWidth(
            260
        )

        self._layout.addWidget(
            self.search_bar,
            1,
        )

    def add_action(
        self,
        widget: QWidget,
    ) -> None:
        self._layout.addWidget(
            widget
        )

    def add_spacer(
        self,
        stretch: int = 1,
    ) -> None:
        self._layout.addStretch(
            stretch
        )

    def clear_actions(self) -> None:
        while self._layout.count() > 1:
            item = self._layout.takeAt(
                1
            )

            widget = item.widget()

            if widget is not None:
                widget.setParent(
                    None
                )

    def set_search_visible(
        self,
        visible: bool,
    ) -> None:
        self.search_bar.setVisible(
            visible
        )

    def set_search_placeholder(
        self,
        placeholder: str,
    ) -> None:
        self.search_bar.set_placeholder(
            placeholder
        )