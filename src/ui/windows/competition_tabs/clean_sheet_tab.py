from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.clean_sheet_service import (
    CleanSheetService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionCleanSheetTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="🧤 Zu Null",
            refresh_button_text=(
                "🔄 Zu-Null-Statistik aktualisieren"
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
            9
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Sp",
                "Zu Null",
                "Zu Null %",
                "Ohne Tor",
                "Ohne Tor %",
                "Getroffen %",
                "Gegentor %",
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

        header = (
            self.table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(
            2,
            9,
        ):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.table.setRowCount(
            0
        )

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

                service = CleanSheetService(
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

                best_clean_sheet_team = (
                    self._get_best_team(
                        statistics,
                        "clean_sheet_percentage",
                    )
                )

                worst_scoring_team = (
                    self._get_best_team(
                        statistics,
                        "failed_to_score_percentage",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_clean_sheet_team is not None:
                    info_parts.append(
                        (
                            "Beste Zu-Null-Quote: "
                            f"{best_clean_sheet_team['team_name']} "
                            "– "
                            f"{best_clean_sheet_team['clean_sheet_percentage']:.1f} %"
                        )
                    )

                if worst_scoring_team is not None:
                    info_parts.append(
                        (
                            "Am häufigsten ohne Tor: "
                            f"{worst_scoring_team['team_name']} "
                            "– "
                            f"{worst_scoring_team['failed_to_score_percentage']:.1f} %"
                        )
                    )

                self.set_info_text(
                    " | ".join(
                        info_parts
                    )
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
                    "Die Zu-Null-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_table(
        self,
        statistics: list[dict],
    ) -> None:
        self.table.setRowCount(
            len(
                statistics
            )
        )

        for row_index, team in enumerate(
            statistics
        ):
            values = [
                team["position"],
                team["team_name"],
                team["played"],
                team["clean_sheets"],
                (
                    f"{team['clean_sheet_percentage']:.1f} %"
                ),
                team["failed_to_score"],
                (
                    f"{team['failed_to_score_percentage']:.1f} %"
                ),
                (
                    f"{team['scored_percentage']:.1f} %"
                ),
                (
                    f"{team['conceded_percentage']:.1f} %"
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(
                        value
                    )
                )

                if column_index != 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    team["team_id"],
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    @staticmethod
    def _get_best_team(
        statistics: list[dict],
        key: str,
    ) -> dict | None:
        if not statistics:
            return None

        return max(
            statistics,
            key=lambda team: (
                float(
                    team.get(
                        key,
                        0.0,
                    )
                ),
                -int(
                    team.get(
                        "position",
                        9999,
                    )
                    or 9999
                ),
            ),
        )

    def clear_content(
        self,
    ) -> None:
        if not hasattr(
            self,
            "table",
        ):
            return

        self.table.setRowCount(
            0
        )