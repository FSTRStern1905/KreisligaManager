from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.result_margin_service import (
    ResultMarginService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionResultMarginTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="📏 Siegmargen",
            refresh_button_text=(
                "🔄 Siegmargen aktualisieren"
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
            10
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Sieg +1",
                "Sieg +2",
                "Sieg +3+",
                "Niederlage -1",
                "Niederlage -2",
                "Niederlage -3+",
                "Höchster Sieg",
                "Höchste Niederlage",
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
            10,
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

                service = ResultMarginService(
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

                biggest_winner = (
                    self._get_best_team(
                        statistics,
                        "biggest_win_margin",
                    )
                )

                biggest_loser = (
                    self._get_best_team(
                        statistics,
                        "biggest_loss_margin",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if biggest_winner is not None:
                    info_parts.append(
                        (
                            "Höchster Sieg: "
                            f"{biggest_winner['team_name']} "
                            "– "
                            f"{biggest_winner['biggest_win_score'] or '-'}"
                        )
                    )

                if biggest_loser is not None:
                    info_parts.append(
                        (
                            "Höchste Niederlage: "
                            f"{biggest_loser['team_name']} "
                            "– "
                            f"{biggest_loser['biggest_loss_score'] or '-'}"
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
                    "Die Siegmargen-Statistik "
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
                team["wins_by_1"],
                team["wins_by_2"],
                team["wins_by_3_plus"],
                team["losses_by_1"],
                team["losses_by_2"],
                team["losses_by_3_plus"],
                team["biggest_win_score"] or "-",
                team["biggest_loss_score"] or "-",
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
                int(
                    team.get(
                        key,
                        0,
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