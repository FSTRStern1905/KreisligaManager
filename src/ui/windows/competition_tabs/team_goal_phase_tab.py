from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.team_goal_phase_service import (
    TeamGoalPhaseService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionTeamGoalPhaseTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⏱ Früh / Spät",
            refresh_button_text=(
                "🔄 Torphasen aktualisieren"
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
                "Tore 0–15",
                "Anteil früh %",
                "Gegentore 0–15",
                "Tore 76–90",
                "Anteil spät %",
                "Gegentore 76–90",
                "Späte Gegentore %",
                "Bilanz 76–90",
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

                service = TeamGoalPhaseService(
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

                best_late_team = (
                    self._get_best_team(
                        statistics,
                        "late_goal_percentage",
                    )
                )

                worst_late_team = (
                    self._get_best_team(
                        statistics,
                        "late_conceded_percentage",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_late_team is not None:
                    info_parts.append(
                        (
                            "Spätzünder: "
                            f"{best_late_team['team_name']} "
                            "– "
                            f"{best_late_team['late_goal_percentage']:.1f} %"
                        )
                    )

                if worst_late_team is not None:
                    info_parts.append(
                        (
                            "Später Einbruch: "
                            f"{worst_late_team['team_name']} "
                            "– "
                            f"{worst_late_team['late_conceded_percentage']:.1f} %"
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
                    "Die Früh-/Spät-Statistik "
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
            late_balance = int(
                team[
                    "late_balance"
                ]
            )

            late_balance_text = (
                f"+{late_balance}"
                if late_balance > 0
                else str(
                    late_balance
                )
            )

            values = [
                team["position"],
                team["team_name"],
                team["early_goals"],
                (
                    f"{team['early_goal_percentage']:.1f} %"
                ),
                team["early_goals_against"],
                team["late_goals"],
                (
                    f"{team['late_goal_percentage']:.1f} %"
                ),
                team["late_goals_against"],
                (
                    f"{team['late_conceded_percentage']:.1f} %"
                ),
                late_balance_text,
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