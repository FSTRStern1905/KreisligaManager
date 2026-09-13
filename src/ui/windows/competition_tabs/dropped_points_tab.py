from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.dropped_points_service import (
    DroppedPointsService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionDroppedPointsTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="📉 Liegen gelassene Punkte",
            refresh_button_text=(
                "🔄 Statistik aktualisieren"
            ),
        )

        self.table = QTableWidget()

        self.setup_table()

        self.add_content_widget(
            self.table,
            stretch=1,
        )

        self.clear_data()

    def setup_table(
        self,
    ) -> None:
        self.table.setColumnCount(
            4
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Rang",
                "Mannschaft",
                "Spiele mit Führung",
                "Liegen gelassene Punkte",
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.clear_content()

        try:
            with self.database_connection() as connection:
                competition_name = (
                    self.get_competition_name(
                        connection
                    )
                )

                if competition_name is None:
                    self.clear_data()
                    return

                service = DroppedPointsService(
                    connection
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                self.populate_table(
                    statistics
                )

                total_dropped_points = sum(
                    int(
                        team["dropped_points"]
                    )
                    for team in statistics
                )

                self.set_info_text(
                    f"{competition_name} | "
                    f"{len(statistics)} Mannschaften | "
                    f"{total_dropped_points} "
                    f"liegen gelassene Punkte gesamt"
                )

                self.set_refresh_enabled(
                    True
                )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            self.handle_load_error(
                message=(
                    "Die Statistik der liegen "
                    "gelassenen Punkte konnte "
                    "nicht geladen werden."
                ),
                error=error,
            )

    def populate_table(
        self,
        statistics: list[dict],
    ) -> None:
        self.table.setRowCount(
            len(statistics)
        )

        for row, team in enumerate(
            statistics
        ):
            position_item = QTableWidgetItem(
                str(
                    row + 1
                )
            )

            team_item = QTableWidgetItem(
                str(
                    team["team_name"]
                )
            )

            matches_leading_item = (
                QTableWidgetItem(
                    str(
                        team["matches_leading"]
                    )
                )
            )

            dropped_points_item = (
                QTableWidgetItem(
                    str(
                        team["dropped_points"]
                    )
                )
            )

            position_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            matches_leading_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            dropped_points_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.table.setItem(
                row,
                0,
                position_item,
            )

            self.table.setItem(
                row,
                1,
                team_item,
            )

            self.table.setItem(
                row,
                2,
                matches_leading_item,
            )

            self.table.setItem(
                row,
                3,
                dropped_points_item,
            )

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "table",
        ):
            self.table.setRowCount(
                0
            )
