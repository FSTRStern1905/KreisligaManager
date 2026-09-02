from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.matchday_statistics_service import (
    MatchdayStatisticsService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionMatchdayStatisticsTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="📅 Spieltage",
            refresh_button_text=(
                "🔄 Spieltagsstatistik aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.overview_tab = QWidget()
        self.goals_tab = QWidget()
        self.results_tab = QWidget()
        self.home_away_tab = QWidget()

        self.matchday_records_line_1 = QLabel()
        self.matchday_records_line_2 = QLabel()

        self.overview_table = QTableWidget()
        self.goals_table = QTableWidget()
        self.results_table = QTableWidget()
        self.home_away_table = QTableWidget()

        self.setup_overview_tab()
        self.setup_goals_tab()
        self.setup_results_tab()
        self.setup_home_away_tab()

        self.inner_tabs.addTab(
            self.overview_tab,
            "Übersicht",
        )

        self.inner_tabs.addTab(
            self.goals_tab,
            "Tore",
        )

        self.inner_tabs.addTab(
            self.results_tab,
            "Ergebnisse",
        )

        self.inner_tabs.addTab(
            self.home_away_tab,
            "Heim/Auswärts",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_overview_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.overview_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.overview_table.setColumnCount(
            7
        )

        self.overview_table.setHorizontalHeaderLabels(
            [
                "ST",
                "Spiele",
                "Tore",
                "Ø Tore",
                "Heimtore",
                "Auswärtstore",
                "Torbilanz H/A",
            ]
        )

        self._setup_table(
            self.overview_table,
            stretch_column=6,
        )

        layout.addWidget(
            self.matchday_records_line_1
        )

        layout.addWidget(
            self.matchday_records_line_2
        )

        layout.addWidget(
            self.overview_table
        )

    def setup_goals_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.goals_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.goals_table.setColumnCount(
            7
        )

        self.goals_table.setHorizontalHeaderLabels(
            [
                "ST",
                "Tore",
                "Ø Tore",
                "Abw. Liga-Ø",
                "Kumulierte Tore",
                "Heimtore",
                "Auswärtstore",
            ]
        )

        self._setup_table(
            self.goals_table,
            stretch_column=4,
        )

        layout.addWidget(
            self.goals_table
        )

    def setup_results_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.results_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.results_table.setColumnCount(
            7
        )

        self.results_table.setHorizontalHeaderLabels(
            [
                "ST",
                "Heimsiege",
                "Remis",
                "Auswärtssiege",
                "Heimsieg %",
                "Remis %",
                "Auswärtssieg %",
            ]
        )

        self._setup_table(
            self.results_table,
            stretch_column=None,
        )

        layout.addWidget(
            self.results_table
        )

    def setup_home_away_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.home_away_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.home_away_table.setColumnCount(
            7
        )

        self.home_away_table.setHorizontalHeaderLabels(
            [
                "ST",
                "Heimtore",
                "Auswärtstore",
                "Tor-Diff.",
                "Heimsiege",
                "Auswärtssiege",
                "Sieg-Diff.",
            ]
        )

        self._setup_table(
            self.home_away_table,
            stretch_column=None,
        )

        layout.addWidget(
            self.home_away_table
        )

    @staticmethod
    def _setup_table(
        table: QTableWidget,
        stretch_column: int | None,
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

        for column in range(
            table.columnCount()
        ):
            if (
                stretch_column is not None
                and column == stretch_column
            ):
                header.setSectionResizeMode(
                    column,
                    QHeaderView.ResizeMode.Stretch,
                )
            else:
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

                service = (
                    MatchdayStatisticsService(
                        connection
                    )
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                summary = (
                    service.get_summary(
                        self.competition_id
                    )
                )

                self.populate_overview_table(
                    statistics
                )

                self.populate_goals_table(
                    statistics,
                    summary,
                )

                self.populate_results_table(
                    statistics
                )

                self.populate_home_away_table(
                    statistics
                )

                self.populate_matchday_records(
                    statistics
                )

                info_parts = [
                    competition_name
                ]

                highest = summary.get(
                    "highest_scoring_matchday"
                )

                lowest = summary.get(
                    "lowest_scoring_matchday"
                )

                if highest is not None:
                    info_parts.append(
                        (
                            "Torreichster Spieltag: "
                            f"ST {highest['matchday']} "
                            f"– {highest['goals']} Tore"
                        )
                    )

                if lowest is not None:
                    info_parts.append(
                        (
                            "Torärmster Spieltag: "
                            f"ST {lowest['matchday']} "
                            f"– {lowest['goals']} Tore"
                        )
                    )

                info_parts.append(
                    (
                        "Ø Tore/Spiel: "
                        f"{summary['goals_per_match']:.2f}"
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
                    "Die Spieltagsstatistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_matchday_records(
        self,
        statistics: list[dict],
    ) -> None:
        if not statistics:
            self.matchday_records_label.clear()
            return

        most_home_wins = max(
            statistics,
            key=lambda row: (
                int(
                    row.get(
                        "home_wins",
                        0,
                    )
                ),
                -int(
                    row.get(
                        "matchday",
                        0,
                    )
                ),
            ),
        )

        most_away_wins = max(
            statistics,
            key=lambda row: (
                int(
                    row.get(
                        "away_wins",
                        0,
                    )
                ),
                -int(
                    row.get(
                        "matchday",
                        0,
                    )
                ),
            ),
        )

        most_draws = max(
            statistics,
            key=lambda row: (
                int(
                    row.get(
                        "draws",
                        0,
                    )
                ),
                -int(
                    row.get(
                        "matchday",
                        0,
                    )
                ),
            ),
        )

        biggest_home_goal_advantage = max(
            statistics,
            key=lambda row: (
                int(
                    row.get(
                        "home_goals",
                        0,
                    )
                )
                - int(
                    row.get(
                        "away_goals",
                        0,
                    )
                ),
                -int(
                    row.get(
                        "matchday",
                        0,
                    )
                ),
            ),
        )

        biggest_away_goal_advantage = min(
            statistics,
            key=lambda row: (
                int(
                    row.get(
                        "home_goals",
                        0,
                    )
                )
                - int(
                    row.get(
                        "away_goals",
                        0,
                    )
                ),
                int(
                    row.get(
                        "matchday",
                        0,
                    )
                ),
            ),
        )

        home_goal_difference = (
            int(
                biggest_home_goal_advantage.get(
                    "home_goals",
                    0,
                )
            )
            - int(
                biggest_home_goal_advantage.get(
                    "away_goals",
                    0,
                )
            )
        )

        away_goal_difference = (
            int(
                biggest_away_goal_advantage.get(
                    "away_goals",
                    0,
                )
            )
            - int(
                biggest_away_goal_advantage.get(
                    "home_goals",
                    0,
                )
            )
        )

        parts = [
            (
                "🏠 Meiste Heimsiege: "
                f"ST {most_home_wins['matchday']} "
                f"– {most_home_wins['home_wins']}"
            ),
            (
                "🚌 Meiste Auswärtssiege: "
                f"ST {most_away_wins['matchday']} "
                f"– {most_away_wins['away_wins']}"
            ),
            (
                "🤝 Meiste Remis: "
                f"ST {most_draws['matchday']} "
                f"– {most_draws['draws']}"
            ),
            (
                "🏠 Größter Heim-Torvorteil: "
                f"ST {biggest_home_goal_advantage['matchday']} "
                f"– +{home_goal_difference}"
            ),
            (
                "🚌 Größter Auswärts-Torvorteil: "
                f"ST {biggest_away_goal_advantage['matchday']} "
                f"– +{away_goal_difference}"
            ),
        ]

        self.matchday_records_line_1.setText(
            "Rekorde | "
            + " | ".join(
                parts[:3]
            )
        )

        self.matchday_records_line_2.setText(
            "          "
            + " | ".join(
                parts[3:]
            )
        )

    def populate_overview_table(
        self,
        statistics: list[dict],
    ) -> None:
        self.overview_table.setRowCount(
            len(
                statistics
            )
        )

        for row_index, row in enumerate(
            statistics
        ):
            goal_difference = (
                int(
                    row[
                        "home_goals"
                    ]
                )
                - int(
                    row[
                        "away_goals"
                    ]
                )
            )

            values = [
                row["matchday"],
                row["matches"],
                row["goals"],
                f"{row['goals_per_match']:.2f}",
                row["home_goals"],
                row["away_goals"],
                self._format_signed_value(
                    goal_difference
                ),
            ]

            self._populate_row(
                self.overview_table,
                row_index,
                values,
            )

    def populate_goals_table(
        self,
        statistics: list[dict],
        summary: dict,
    ) -> None:
        self.goals_table.setRowCount(
            len(
                statistics
            )
        )

        league_average = float(
            summary.get(
                "goals_per_match",
                0.0,
            )
        )

        cumulative_goals = 0

        for row_index, row in enumerate(
            statistics
        ):
            cumulative_goals += int(
                row[
                    "goals"
                ]
            )

            deviation = (
                float(
                    row[
                        "goals_per_match"
                    ]
                )
                - league_average
            )

            values = [
                row["matchday"],
                row["goals"],
                f"{row['goals_per_match']:.2f}",
                self._format_signed_float(
                    deviation
                ),
                cumulative_goals,
                row["home_goals"],
                row["away_goals"],
            ]

            self._populate_row(
                self.goals_table,
                row_index,
                values,
            )

    def populate_results_table(
        self,
        statistics: list[dict],
    ) -> None:
        self.results_table.setRowCount(
            len(
                statistics
            )
        )

        for row_index, row in enumerate(
            statistics
        ):
            values = [
                row["matchday"],
                row["home_wins"],
                row["draws"],
                row["away_wins"],
                f"{row['home_win_percentage']:.1f} %",
                f"{row['draw_percentage']:.1f} %",
                f"{row['away_win_percentage']:.1f} %",
            ]

            self._populate_row(
                self.results_table,
                row_index,
                values,
            )

    def populate_home_away_table(
        self,
        statistics: list[dict],
    ) -> None:
        self.home_away_table.setRowCount(
            len(
                statistics
            )
        )

        for row_index, row in enumerate(
            statistics
        ):
            goal_difference = (
                int(
                    row[
                        "home_goals"
                    ]
                )
                - int(
                    row[
                        "away_goals"
                    ]
                )
            )

            win_difference = (
                int(
                    row[
                        "home_wins"
                    ]
                )
                - int(
                    row[
                        "away_wins"
                    ]
                )
            )

            values = [
                row["matchday"],
                row["home_goals"],
                row["away_goals"],
                self._format_signed_value(
                    goal_difference
                ),
                row["home_wins"],
                row["away_wins"],
                self._format_signed_value(
                    win_difference
                ),
            ]

            self._populate_row(
                self.home_away_table,
                row_index,
                values,
            )

    @staticmethod
    def _populate_row(
        table: QTableWidget,
        row_index: int,
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

            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            table.setItem(
                row_index,
                column_index,
                item,
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

    @staticmethod
    def _format_signed_float(
        value: float,
    ) -> str:
        value = float(
            value
        )

        if value > 0:
            return f"+{value:.2f}"

        return f"{value:.2f}"

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "matchday_records_line_1",
        ):
            self.matchday_records_line_1.clear()

        if hasattr(
            self,
            "matchday_records_line_2",
        ):
            self.matchday_records_line_2.clear()

        if hasattr(
            self,
            "overview_table",
        ):
            self.overview_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "goals_table",
        ):
            self.goals_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "results_table",
        ):
            self.results_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "home_away_table",
        ):
            self.home_away_table.setRowCount(
                0
            )