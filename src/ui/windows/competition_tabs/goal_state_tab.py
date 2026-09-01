from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.goal_state_service import (
    GoalStateService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionGoalStateTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="🎯 Tore nach Spielstand",
            refresh_button_text=(
                "🔄 Spielstand-Statistik aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.goal_state_tab = QWidget()
        self.trailing_reaction_tab = QWidget()

        self.goal_state_table = QTableWidget()
        self.trailing_reaction_table = QTableWidget()

        self.setup_goal_state_tab()
        self.setup_trailing_reaction_tab()

        self.inner_tabs.addTab(
            self.goal_state_tab,
            "Tore nach Spielstand",
        )

        self.inner_tabs.addTab(
            self.trailing_reaction_tab,
            "Reaktion auf Rückstand",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_goal_state_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.goal_state_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.goal_state_table.setColumnCount(
            8
        )

        self.goal_state_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Tore bei Gleichstand",
                "Tore bei Führung",
                "Tore bei Rückstand",
                "Anteil Gleichstand %",
                "Anteil Führung %",
                "Anteil Rückstand %",
            ]
        )

        self._setup_table(
            self.goal_state_table,
            8,
        )

        layout.addWidget(
            self.goal_state_table
        )

    def setup_trailing_reaction_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.trailing_reaction_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.trailing_reaction_table.setColumnCount(
            9
        )

        self.trailing_reaction_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Rückstand",
                "Ausgeglichen",
                "Ausgleich %",
                "Nächstes Tor selbst",
                "Nächstes Tor Gegner",
                "Ø Min. bis Ausgleich",
                "Tore bei Rückstand",
            ]
        )

        self._setup_table(
            self.trailing_reaction_table,
            9,
        )

        layout.addWidget(
            self.trailing_reaction_table
        )

    def _setup_table(
        self,
        table: QTableWidget,
        column_count: int,
    ) -> None:
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        table.setAlternatingRowColors(
            True
        )

        table.verticalHeader().setVisible(
            False
        )

        header = (
            table.horizontalHeader()
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
            column_count,
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

        self.goal_state_table.setRowCount(
            0
        )

        self.trailing_reaction_table.setRowCount(
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

                service = GoalStateService(
                    connection
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                self.populate_goal_state_table(
                    statistics
                )

                self.populate_trailing_reaction_table(
                    statistics
                )

                best_trailing_goal_team = (
                    self._get_max_team(
                        statistics,
                        "goal_while_trailing_percentage",
                    )
                )

                best_equalizer_team = (
                    self._get_max_team(
                        statistics,
                        "equalizer_percentage",
                    )
                )

                fastest_equalizer_team = (
                    self._get_fastest_equalizer_team(
                        statistics
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_trailing_goal_team is not None:
                    info_parts.append(
                        (
                            "Höchster Toranteil bei Rückstand: "
                            f"{best_trailing_goal_team['team_name']} "
                            "– "
                            f"{best_trailing_goal_team['goal_while_trailing_percentage']:.1f} %"
                        )
                    )

                if best_equalizer_team is not None:
                    info_parts.append(
                        (
                            "Beste Ausgleichsquote: "
                            f"{best_equalizer_team['team_name']} "
                            "– "
                            f"{best_equalizer_team['equalizer_percentage']:.1f} %"
                        )
                    )

                if fastest_equalizer_team is not None:
                    info_parts.append(
                        (
                            "Schnellster Ausgleich: "
                            f"{fastest_equalizer_team['team_name']} "
                            "– "
                            f"{fastest_equalizer_team['average_equalizer_minutes']:.1f} Min."
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
                    "Die Spielstand-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_goal_state_table(
        self,
        statistics: list[dict],
    ) -> None:
        sorted_statistics = sorted(
            statistics,
            key=lambda team: (
                -float(
                    team[
                        "goal_while_trailing_percentage"
                    ]
                ),
                -int(
                    team[
                        "goals_while_trailing"
                    ]
                ),
                int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            ),
        )

        self.goal_state_table.setRowCount(
            len(
                sorted_statistics
            )
        )

        for row_index, team in enumerate(
            sorted_statistics
        ):
            values = [
                team["position"],
                team["team_name"],
                team["goals_while_level"],
                team["goals_while_leading"],
                team["goals_while_trailing"],
                (
                    f"{team['goal_while_level_percentage']:.1f} %"
                ),
                (
                    f"{team['goal_while_leading_percentage']:.1f} %"
                ),
                (
                    f"{team['goal_while_trailing_percentage']:.1f} %"
                ),
            ]

            self._populate_row(
                table=self.goal_state_table,
                row_index=row_index,
                team=team,
                values=values,
            )

    def populate_trailing_reaction_table(
        self,
        statistics: list[dict],
    ) -> None:
        sorted_statistics = sorted(
            statistics,
            key=lambda team: (
                -float(
                    team[
                        "equalizer_percentage"
                    ]
                ),
                -int(
                    team[
                        "equalized_after_trailing"
                    ]
                ),
                float(
                    team[
                        "average_equalizer_minutes"
                    ]
                )
                if int(
                    team[
                        "equalizer_response_count"
                    ]
                ) > 0
                else 9999.0,
                int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            ),
        )

        self.trailing_reaction_table.setRowCount(
            len(
                sorted_statistics
            )
        )

        for row_index, team in enumerate(
            sorted_statistics
        ):
            response_count = int(
                team[
                    "equalizer_response_count"
                ]
            )

            if response_count > 0:
                average_minutes = (
                    f"{team['average_equalizer_minutes']:.1f}"
                )
            else:
                average_minutes = "-"

            values = [
                team["position"],
                team["team_name"],
                team["matches_trailing"],
                team["equalized_after_trailing"],
                (
                    f"{team['equalizer_percentage']:.1f} %"
                ),
                team["next_goal_after_trailing_own"],
                team["next_goal_after_trailing_opponent"],
                average_minutes,
                team["goals_while_trailing"],
            ]

            self._populate_row(
                table=self.trailing_reaction_table,
                row_index=row_index,
                team=team,
                values=values,
            )

    @staticmethod
    def _populate_row(
        table: QTableWidget,
        row_index: int,
        team: dict,
        values: list,
    ) -> None:
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

            table.setItem(
                row_index,
                column_index,
                item,
            )

    @staticmethod
    def _get_max_team(
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
    def _get_fastest_equalizer_team(
        statistics: list[dict],
    ) -> dict | None:
        candidates = [
            team
            for team in statistics
            if int(
                team.get(
                    "equalizer_response_count",
                    0,
                )
            ) > 0
        ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda team: (
                float(
                    team[
                        "average_equalizer_minutes"
                    ]
                ),
                int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            ),
        )

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "goal_state_table",
        ):
            self.goal_state_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "trailing_reaction_table",
        ):
            self.trailing_reaction_table.setRowCount(
                0
            )