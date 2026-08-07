from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from src.database.repository import Repository
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.widgets.page_header import PageHeader
from src.ui.widgets.primary_button import PrimaryButton
from src.ui.widgets.secondary_button import SecondaryButton
from src.ui.widgets.stat_card import StatCard
from src.ui.widgets.toolbar import Toolbar


class Dashboard(QWidget):
    def __init__(
        self,
        repository: Repository,
    ) -> None:
        super().__init__()

        self.repository = repository

        self.setObjectName(
            "DashboardPage"
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
        )

        layout.setSpacing(
            Metrics.PAGE_SPACING
        )

        header = PageHeader(
            title="Dashboard",
            subtitle=(
                "Übersicht über die wichtigsten "
                "Daten im KreisligaManager"
            ),
        )

        refresh_button = SecondaryButton(
            "Aktualisieren"
        )

        import_button = PrimaryButton(
            "Import"
        )

        header.add_action(
            refresh_button
        )

        header.add_action(
            import_button
        )

        toolbar = Toolbar(
            search_placeholder=(
                "Im Dashboard suchen ..."
            )
        )

        layout.addWidget(
            header
        )

        layout.addWidget(
            toolbar
        )

        grid = QGridLayout()

        grid.setContentsMargins(
            0,
            Metrics.SPACING_SMALL,
            0,
            0,
        )

        grid.setHorizontalSpacing(
            Metrics.CARD_SPACING
        )

        grid.setVerticalSpacing(
            Metrics.CARD_SPACING
        )

        cards = (
            (
                "Vereine",
                self.repository.count(
                    "clubs"
                ),
                "🏟",
                Colors.PRIMARY,
            ),
            (
                "Mannschaften",
                self.repository.count(
                    "teams"
                ),
                "👥",
                Colors.INFO,
            ),
            (
                "Spieler",
                self.repository.count(
                    "players"
                ),
                "👤",
                Colors.SUCCESS,
            ),
            (
                "Spiele",
                self.repository.count(
                    "matches"
                ),
                "⚽",
                Colors.WARNING,
            ),
            (
                "Ereignisse",
                self.repository.count(
                    "events"
                ),
                "📊",
                Colors.ERROR,
            ),
            (
                "Eventtypen",
                self.repository.count(
                    "event_types"
                ),
                "🏷",
                Colors.PRIMARY,
            ),
        )

        for index, (
            card_title,
            value,
            icon,
            accent_color,
        ) in enumerate(cards):
            row = index // 3
            column = index % 3

            card = StatCard(
                title=card_title,
                value=value,
                icon=icon,
                accent_color=accent_color,
            )

            grid.addWidget(
                card,
                row,
                column,
            )

        for column in range(3):
            grid.setColumnStretch(
                column,
                1,
            )

        layout.addLayout(
            grid
        )

        layout.addStretch(
            1
        )

        self.setStyleSheet(
            f"""
            QWidget#DashboardPage {{
                background-color:
                    {Colors.BACKGROUND};
            }}
            """
        )