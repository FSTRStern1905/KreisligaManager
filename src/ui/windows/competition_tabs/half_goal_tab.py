from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.half_goal_service import (
    HalfGoalService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionHalfGoalTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⏱ Halbzeiten",
            refresh_button_text=(
                "🔄 Halbzeiten aktualisieren"
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
                "Tore 1. HZ",
                "Tore 2. HZ",
                "2.-HZ-Anteil %",
                "GT 1. HZ",
                "GT 2. HZ",
                "2.-HZ-GT %",
                "Bilanz 2. HZ",
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

                service = HalfGoalService(
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

                best_second_half_team = (
                    self._get_best_team(
                        statistics,
                        "second_half_balance",
                    )
                )

                highest_second_half_share = (
                    self._get_best_team(
                        statistics,
                        "second_half_goal_percentage",
                    )
                )

                worst_second_half_defence = (
                    self._get_best_team(
                        statistics,
                        "second_half_conceded_percentage",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_second_half_team is not None:
                    second_half_balance = (
                        self._format_signed_value(
                            best_second_half_team[
                                "second_half_balance"
                            ]
                        )
                    )

                    team_name = (
                        best_second_half_team[
                            "team_name"
                        ]
                    )

                    info_parts.append(
                        (
                            "Beste 2.-HZ-Bilanz: "
                            f"{team_name} "
                            f"– {second_half_balance}"
                        )
                    )

                if highest_second_half_share is not None:
                    team_name = (
                        highest_second_half_share[
                            "team_name"
                        ]
                    )

                    percentage = float(
                        highest_second_half_share[
                            "second_half_goal_percentage"
                        ]
                    )

                    info_parts.append(
                        (
                            "Höchster Toranteil nach Pause: "
                            f"{team_name} "
                            f"– {percentage:.1f} %"
                        )
                    )

                if worst_second_half_defence is not None:
                    team_name = (
                        worst_second_half_defence[
                            "team_name"
                        ]
                    )

                    percentage = float(
                        worst_second_half_defence[
                            "second_half_conceded_percentage"
                        ]
                    )

                    info_parts.append(
                        (
                            "Höchster Gegentoranteil "
                            "nach Pause: "
                            f"{team_name} "
                            f"– {percentage:.1f} %"
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
                    "Die Halbzeiten-Statistik "
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
            second_half_goal_percentage = float(
                team[
                    "second_half_goal_percentage"
                ]
            )

            second_half_conceded_percentage = float(
                team[
                    "second_half_conceded_percentage"
                ]
            )

            second_half_balance = (
                self._format_signed_value(
                    team[
                        "second_half_balance"
                    ]
                )
            )

            values = [
                team["position"],
                team["team_name"],
                team["first_half_goals"],
                team["second_half_goals"],
                (
                    f"{second_half_goal_percentage:.1f} %"
                ),
                team["first_half_goals_against"],
                team["second_half_goals_against"],
                (
                    f"{second_half_conceded_percentage:.1f} %"
                ),
                second_half_balance,
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

    @staticmethod
    def _format_signed_value(
        value: int,
    ) -> str:
        value = int(
            value
        )

        if value > 0:
            return f"+{value}"

        return str(
            value
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