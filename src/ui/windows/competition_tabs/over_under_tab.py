from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.over_under_service import (
    OverUnderService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionOverUnderTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="📈 Over / Under",
            refresh_button_text=(
                "🔄 Over/Under aktualisieren"
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
                "Ø Tore",
                "Over 0,5 %",
                "Over 1,5 %",
                "Over 2,5 %",
                "Over 3,5 %",
                "Beide treffen %",
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

                service = OverUnderService(
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

                highest_over_2_5 = (
                    self._get_best_team(
                        statistics,
                        "over_2_5_percentage",
                    )
                )

                highest_both_score = (
                    self._get_best_team(
                        statistics,
                        "btts_percentage",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if highest_over_2_5 is not None:
                    info_parts.append(
                        (
                            "Höchste Over-2,5-Quote: "
                            f"{highest_over_2_5['team_name']} "
                            "– "
                            f"{highest_over_2_5['over_2_5_percentage']:.1f} %"
                        )
                    )

                if highest_both_score is not None:
                    info_parts.append(
                        (
                            "Höchste Beide-treffen-Quote: "
                            f"{highest_both_score['team_name']} "
                            "– "
                            f"{highest_both_score['btts_percentage']:.1f} %"
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
                    "Die Over/Under-Statistik "
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
                (
                    f"{team['average_match_goals']:.2f}"
                ),
                (
                    f"{team['over_0_5_percentage']:.1f} %"
                ),
                (
                    f"{team['over_1_5_percentage']:.1f} %"
                ),
                (
                    f"{team['over_2_5_percentage']:.1f} %"
                ),
                (
                    f"{team['over_3_5_percentage']:.1f} %"
                ),
                (
                    f"{team['btts_percentage']:.1f} %"
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