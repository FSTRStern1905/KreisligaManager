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

from src.services.statistics.opening_goal_service import (
    OpeningGoalService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionOpeningGoalTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⚽ Toreröffnung",
            refresh_button_text=(
                "🔄 Toreröffnung aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.scored_first_tab = QWidget()
        self.conceded_first_tab = QWidget()

        self.scored_first_table = QTableWidget()
        self.conceded_first_table = QTableWidget()

        self.setup_scored_first_tab()
        self.setup_conceded_first_tab()

        self.inner_tabs.addTab(
            self.scored_first_tab,
            "Eigenes 1:0",
        )

        self.inner_tabs.addTab(
            self.conceded_first_tab,
            "0:1 kassiert",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_scored_first_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.scored_first_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.scored_first_table.setColumnCount(
            9
        )

        self.scored_first_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "1:0 erzielt",
                "Danach Sieg",
                "Danach Remis",
                "Danach Niederlage",
                "Siegquote %",
                "Punktequote %",
                "Ø Minute 1:0",
            ]
        )

        self._setup_table(
            self.scored_first_table,
            9,
        )

        layout.addWidget(
            self.scored_first_table
        )

    def setup_conceded_first_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.conceded_first_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.conceded_first_table.setColumnCount(
            9
        )

        self.conceded_first_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "0:1 kassiert",
                "Danach Sieg",
                "Danach Remis",
                "Danach Niederlage",
                "Siegquote %",
                "Punktequote %",
                "Ø Minute 0:1",
            ]
        )

        self._setup_table(
            self.conceded_first_table,
            9,
        )

        layout.addWidget(
            self.conceded_first_table
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

        header = table.horizontalHeader()

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

        self.scored_first_table.setRowCount(
            0
        )

        self.conceded_first_table.setRowCount(
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

                service = OpeningGoalService(
                    connection
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                self.populate_scored_first_table(
                    statistics
                )

                self.populate_conceded_first_table(
                    statistics
                )

                best_after_scoring_first = (
                    self._get_max_team(
                        statistics,
                        "win_percentage_after_scoring_first",
                    )
                )

                best_after_conceding_first = (
                    self._get_max_team(
                        statistics,
                        "points_percentage_after_conceding_first",
                    )
                )

                earliest_opening_goal = (
                    self._get_earliest_team(
                        statistics,
                        count_key="opening_goal_minute_count",
                        minute_key="average_opening_goal_minute",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_after_scoring_first is not None:
                    info_parts.append(
                        (
                            "Stärkstes Team nach 1:0: "
                            f"{best_after_scoring_first['team_name']} "
                            "– "
                            f"{best_after_scoring_first['win_percentage_after_scoring_first']:.1f} % Siege"
                        )
                    )

                if best_after_conceding_first is not None:
                    info_parts.append(
                        (
                            "Beste Reaktion auf 0:1: "
                            f"{best_after_conceding_first['team_name']} "
                            "– "
                            f"{best_after_conceding_first['points_percentage_after_conceding_first']:.1f} % Punktequote"
                        )
                    )

                if earliest_opening_goal is not None:
                    info_parts.append(
                        (
                            "Frühestes Ø 1:0: "
                            f"{earliest_opening_goal['team_name']} "
                            "– "
                            f"{earliest_opening_goal['average_opening_goal_minute']:.1f}. Min."
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
            KeyError,
        ) as error:
            self.handle_load_error(
                message=(
                    "Die Toreröffnungs-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_scored_first_table(
        self,
        statistics: list[dict],
    ) -> None:
        rows = sorted(
            statistics,
            key=lambda team: (
                -float(
                    team[
                        "win_percentage_after_scoring_first"
                    ]
                ),
                -int(
                    team[
                        "scored_first"
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

        self.scored_first_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, team in enumerate(
            rows
        ):
            values = [
                team["position"],
                team["team_name"],
                team["scored_first"],
                team["won_after_scoring_first"],
                team["drawn_after_scoring_first"],
                team["lost_after_scoring_first"],
                (
                    f"{team['win_percentage_after_scoring_first']:.1f} %"
                ),
                (
                    f"{team['points_percentage_after_scoring_first']:.1f} %"
                ),
                self._format_minute(
                    team[
                        "average_opening_goal_minute"
                    ],
                    team[
                        "opening_goal_minute_count"
                    ],
                ),
            ]

            self._populate_row(
                table=self.scored_first_table,
                row_index=row_index,
                team=team,
                values=values,
            )

    def populate_conceded_first_table(
        self,
        statistics: list[dict],
    ) -> None:
        rows = sorted(
            statistics,
            key=lambda team: (
                -float(
                    team[
                        "points_percentage_after_conceding_first"
                    ]
                ),
                -int(
                    team[
                        "won_after_conceding_first"
                    ]
                ),
                -int(
                    team[
                        "drawn_after_conceding_first"
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

        self.conceded_first_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, team in enumerate(
            rows
        ):
            values = [
                team["position"],
                team["team_name"],
                team["conceded_first"],
                team["won_after_conceding_first"],
                team["drawn_after_conceding_first"],
                team["lost_after_conceding_first"],
                (
                    f"{team['win_percentage_after_conceding_first']:.1f} %"
                ),
                (
                    f"{team['points_percentage_after_conceding_first']:.1f} %"
                ),
                self._format_minute(
                    team[
                        "average_opening_conceded_minute"
                    ],
                    team[
                        "opening_conceded_minute_count"
                    ],
                ),
            ]

            self._populate_row(
                table=self.conceded_first_table,
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

    @staticmethod
    def _get_earliest_team(
        statistics: list[dict],
        count_key: str,
        minute_key: str,
    ) -> dict | None:
        candidates = [
            team
            for team in statistics
            if int(
                team.get(
                    count_key,
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
                        minute_key
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

    @staticmethod
    def _format_minute(
        minute: float,
        count: int,
    ) -> str:
        if int(
            count
        ) <= 0:
            return "-"

        return f"{float(minute):.1f}"

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "scored_first_table",
        ):
            self.scored_first_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "conceded_first_table",
        ):
            self.conceded_first_table.setRowCount(
                0
            )