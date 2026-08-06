from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.database.repository import Repository
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography
from src.ui.widgets.stat_card import StatCard


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

        title = QLabel(
            "Dashboard"
        )

        title.setObjectName(
            "PageTitle"
        )

        title.setFont(
            Typography.title()
        )

        subtitle = QLabel(
            "Übersicht über die wichtigsten "
            "Daten im KreisligaManager"
        )

        subtitle.setObjectName(
            "PageSubtitle"
        )

        subtitle.setFont(
            Typography.body()
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
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

            QLabel#PageTitle {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
            }}

            QLabel#PageSubtitle {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
            }}
            """
        )