from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.half_goal_service import (
    HalfGoalService,
)
from src.ui.charts.base_bar_chart import (
    BaseBarChart,
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

        self.inner_tabs = QTabWidget()

        self.first_half_tab = QWidget()
        self.second_half_tab = QWidget()

        self.first_half_table = QTableWidget()
        self.second_half_table = QTableWidget()

        self.goals_comparison_tab = QWidget()
        self.goals_comparison_chart = BaseBarChart(
            title="Erzielte Tore vs. Liga-Ø",
            x_axis_title="Halbzeit",
            y_axis_title="Tore",
        )
        self.goals_comparison_chart.show_legend(True)

        self.conceded_comparison_tab = QWidget()
        self.conceded_comparison_chart = BaseBarChart(
            title="Gegentore vs. Liga-Ø",
            x_axis_title="Halbzeit",
            y_axis_title="Gegentore",
        )
        self.conceded_comparison_chart.show_legend(True)

        self.team_selector_widget = QWidget()
        self.team_selector_layout = QHBoxLayout(
            self.team_selector_widget
        )
        self.team_selector_layout.setContentsMargins(
            8,
            0,
            0,
            0,
        )
        self.team_selector_layout.setSpacing(
            8
        )

        self.team_selector_label = QLabel(
            "Mannschaft:"
        )

        self.team_combo = QComboBox()
        self.team_combo.setMinimumWidth(
            260
        )

        self.team_selector_layout.addWidget(
            self.team_selector_label
        )
        self.team_selector_layout.addWidget(
            self.team_combo
        )

        self.statistics_cache: list[dict] = []

        self.setup_first_half_tab()
        self.setup_second_half_tab()
        self.setup_goals_comparison_tab()
        self.setup_conceded_comparison_tab()

        self.inner_tabs.addTab(
            self.first_half_tab,
            "1. HZ",
        )

        self.inner_tabs.addTab(
            self.second_half_tab,
            "2. HZ",
        )

        self.inner_tabs.addTab(
            self.goals_comparison_tab,
            "Erzielte Tore",
        )
        self.inner_tabs.addTab(
            self.conceded_comparison_tab,
            "Gegentore",
        )

        self.inner_tabs.setCornerWidget(
            self.team_selector_widget
        )

        self.team_selector_widget.setVisible(
            False
        )

        self.team_combo.currentIndexChanged.connect(
            self.team_changed
        )

        self.inner_tabs.currentChanged.connect(
            self.inner_tab_changed
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_first_half_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.first_half_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.first_half_table.setColumnCount(
            7
        )

        self.first_half_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Tore 1. HZ",
                "GT 1. HZ",
                "Bilanz 1. HZ",
                "Toranteil 1. HZ %",
                "GT-Anteil 1. HZ %",
            ]
        )

        self._setup_table(
            self.first_half_table,
            7,
        )

        layout.addWidget(
            self.first_half_table
        )

    def setup_second_half_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.second_half_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.second_half_table.setColumnCount(
            7
        )

        self.second_half_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Tore 2. HZ",
                "GT 2. HZ",
                "Bilanz 2. HZ",
                "Toranteil 2. HZ %",
                "GT-Anteil 2. HZ %",
            ]
        )

        self._setup_table(
            self.second_half_table,
            7,
        )

        layout.addWidget(
            self.second_half_table
        )

    def setup_goals_comparison_tab(self) -> None:
        layout = QVBoxLayout(self.goals_comparison_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.goals_comparison_chart, 1)

    def setup_conceded_comparison_tab(self) -> None:
        layout = QVBoxLayout(self.conceded_comparison_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.conceded_comparison_chart, 1)

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

        self.first_half_table.setRowCount(
            0
        )

        self.second_half_table.setRowCount(
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

                self.statistics_cache = [
                    dict(team)
                    for team in statistics
                ]

                self.populate_team_combo(
                    statistics
                )

                first_half_statistics = (
                    self._prepare_first_half_statistics(
                        statistics
                    )
                )

                self.populate_first_half_table(
                    first_half_statistics
                )

                self.populate_second_half_table(
                    statistics
                )

                best_first_half_team = (
                    self._get_best_first_half_team(
                        first_half_statistics
                    )
                )

                best_second_half_team = (
                    self._get_best_second_half_team(
                        statistics
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_first_half_team is not None:
                    first_half_balance_text = (
                        self._format_signed_value(
                            best_first_half_team[
                                "first_half_balance"
                            ]
                        )
                    )

                    info_parts.append(
                        (
                            "Beste 1.-HZ-Bilanz: "
                            f"{best_first_half_team['team_name']} "
                            f"– {first_half_balance_text}"
                        )
                    )

                if best_second_half_team is not None:
                    second_half_balance_text = (
                        self._format_signed_value(
                            best_second_half_team[
                                "second_half_balance"
                            ]
                        )
                    )

                    info_parts.append(
                        (
                            "Beste 2.-HZ-Bilanz: "
                            f"{best_second_half_team['team_name']} "
                            f"– {second_half_balance_text}"
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

            self.load_selected_team()

        except (
            sqlite3.Error,
            ValueError,
            KeyError,
        ) as error:
            self.handle_load_error(
                message=(
                    "Die Halbzeiten-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_team_combo(
        self,
        statistics: list[dict],
    ) -> None:
        previous_team_id = (
            self.team_combo.currentData()
        )

        self.team_combo.blockSignals(
            True
        )

        self.team_combo.clear()

        teams = sorted(
            statistics,
            key=lambda team: str(
                team["team_name"]
            ).lower(),
        )

        for team in teams:
            self.team_combo.addItem(
                str(
                    team["team_name"]
                ),
                int(
                    team["team_id"]
                ),
            )

        if previous_team_id is not None:
            for index in range(
                self.team_combo.count()
            ):
                if (
                    self.team_combo.itemData(
                        index
                    )
                    == previous_team_id
                ):
                    self.team_combo.setCurrentIndex(
                        index
                    )
                    break

        self.team_combo.blockSignals(
            False
        )

    def inner_tab_changed(self, index: int) -> None:
        current_widget = self.inner_tabs.widget(index)
        is_comparison = current_widget in (
            self.goals_comparison_tab,
            self.conceded_comparison_tab,
        )
        self.team_selector_widget.setVisible(is_comparison)

        if is_comparison:
            self.load_selected_team()

    def team_changed(
        self,
        index: int,
    ) -> None:
        if index < 0:
            return

        self.load_selected_team()

    def load_selected_team(self) -> None:
        if not self.statistics_cache:
            self.goals_comparison_chart.show_empty_chart("Keine Daten vorhanden")
            self.conceded_comparison_chart.show_empty_chart("Keine Daten vorhanden")
            return

        team_id = self.team_combo.currentData()
        if team_id is None:
            return

        team = next(
            (
                row for row in self.statistics_cache
                if int(row["team_id"]) == int(team_id)
            ),
            None,
        )

        if team is None:
            return

        self.populate_goals_comparison_chart(team)
        self.populate_conceded_comparison_chart(team)

    def _league_half_averages(
        self,
        first_key: str,
        second_key: str,
    ) -> list[float]:
        count = len(self.statistics_cache)
        if count <= 0:
            return [0.0, 0.0]

        return [
            sum(float(row[first_key]) for row in self.statistics_cache) / count,
            sum(float(row[second_key]) for row in self.statistics_cache) / count,
        ]

    def _populate_average_chart(
        self,
        chart: BaseBarChart,
        series_name: str,
        team_values: list[float],
        league_values: list[float],
        lower_is_better: bool,
    ) -> None:
        chart.clear()
        chart.set_categories(["1. Halbzeit", "2. Halbzeit"])

        chart.create_bar_series(
            name=series_name,
            values=team_values,
        )

        chart.create_total_labels(
            team_values
        )

        maximum = max(team_values + league_values)
        padding = max(2.0, maximum * 0.22)

        chart.set_value_range(
            minimum=0,
            maximum=maximum + padding,
        )

        chart.create_reference_markers(
            reference_values=league_values,
            comparison_values=team_values,
            lower_is_better=lower_is_better,
        )

        chart.restore_chart_title()

    def populate_goals_comparison_chart(self, team: dict) -> None:
        team_values = [
            float(team["first_half_goals"]),
            float(team["second_half_goals"]),
        ]
        league_values = self._league_half_averages(
            "first_half_goals",
            "second_half_goals",
        )

        self._populate_average_chart(
            chart=self.goals_comparison_chart,
            series_name="Erzielte Tore",
            team_values=team_values,
            league_values=league_values,
            lower_is_better=False,
        )

    def populate_conceded_comparison_chart(self, team: dict) -> None:
        team_values = [
            float(team["first_half_goals_against"]),
            float(team["second_half_goals_against"]),
        ]
        league_values = self._league_half_averages(
            "first_half_goals_against",
            "second_half_goals_against",
        )

        self._populate_average_chart(
            chart=self.conceded_comparison_chart,
            series_name="Gegentore",
            team_values=team_values,
            league_values=league_values,
            lower_is_better=True,
        )

    def _prepare_first_half_statistics(
        self,
        statistics: list[dict],
    ) -> list[dict]:
        rows: list[dict] = []

        for team in statistics:
            first_half_goals = int(
                team[
                    "first_half_goals"
                ]
            )

            first_half_goals_against = int(
                team[
                    "first_half_goals_against"
                ]
            )

            total_goals = int(
                team[
                    "total_goals"
                ]
            )

            total_goals_against = int(
                team[
                    "total_goals_against"
                ]
            )

            first_half_balance = (
                first_half_goals
                - first_half_goals_against
            )

            first_half_goal_percentage = (
                self._percentage(
                    first_half_goals,
                    total_goals,
                )
            )

            first_half_conceded_percentage = (
                self._percentage(
                    first_half_goals_against,
                    total_goals_against,
                )
            )

            rows.append(
                {
                    **team,
                    "first_half_balance": (
                        first_half_balance
                    ),
                    "first_half_goal_percentage": (
                        first_half_goal_percentage
                    ),
                    "first_half_conceded_percentage": (
                        first_half_conceded_percentage
                    ),
                }
            )

        return rows

    def populate_first_half_table(
        self,
        statistics: list[dict],
    ) -> None:
        rows = sorted(
            statistics,
            key=lambda team: (
                -int(
                    team[
                        "first_half_balance"
                    ]
                ),
                -int(
                    team[
                        "first_half_goals"
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

        self.first_half_table.setRowCount(
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
                team["first_half_goals"],
                team["first_half_goals_against"],
                self._format_signed_value(
                    team[
                        "first_half_balance"
                    ]
                ),
                (
                    f"{team['first_half_goal_percentage']:.1f} %"
                ),
                (
                    f"{team['first_half_conceded_percentage']:.1f} %"
                ),
            ]

            self._populate_row(
                table=self.first_half_table,
                row_index=row_index,
                team=team,
                values=values,
            )

    def populate_second_half_table(
        self,
        statistics: list[dict],
    ) -> None:
        rows = sorted(
            statistics,
            key=lambda team: (
                -int(
                    team[
                        "second_half_balance"
                    ]
                ),
                -int(
                    team[
                        "second_half_goals"
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

        self.second_half_table.setRowCount(
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
                team["second_half_goals"],
                team["second_half_goals_against"],
                self._format_signed_value(
                    team[
                        "second_half_balance"
                    ]
                ),
                (
                    f"{team['second_half_goal_percentage']:.1f} %"
                ),
                (
                    f"{team['second_half_conceded_percentage']:.1f} %"
                ),
            ]

            self._populate_row(
                table=self.second_half_table,
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
    def _get_best_first_half_team(
        statistics: list[dict],
    ) -> dict | None:
        if not statistics:
            return None

        return max(
            statistics,
            key=lambda team: (
                int(
                    team[
                        "first_half_balance"
                    ]
                ),
                int(
                    team[
                        "first_half_goals"
                    ]
                ),
                -int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            ),
        )

    @staticmethod
    def _get_best_second_half_team(
        statistics: list[dict],
    ) -> dict | None:
        if not statistics:
            return None

        return max(
            statistics,
            key=lambda team: (
                int(
                    team[
                        "second_half_balance"
                    ]
                ),
                int(
                    team[
                        "second_half_goals"
                    ]
                ),
                -int(
                    team[
                        "position"
                    ]
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

    @staticmethod
    def _percentage(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            value
            / total
            * 100,
            1,
        )

    def clear_content(
        self,
    ) -> None:
        self.statistics_cache = []

        if hasattr(self, "goals_comparison_chart"):
            self.goals_comparison_chart.show_empty_chart("Keine Daten")

        if hasattr(self, "conceded_comparison_chart"):
            self.conceded_comparison_chart.show_empty_chart("Keine Daten")

        if hasattr(
            self,
            "team_selector_widget",
        ):
            self.team_selector_widget.setVisible(
                False
            )

        if hasattr(
            self,
            "team_combo",
        ):
            self.team_combo.blockSignals(
                True
            )
            self.team_combo.clear()
            self.team_combo.blockSignals(
                False
            )

        if hasattr(
            self,
            "first_half_table",
        ):
            self.first_half_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "second_half_table",
        ):
            self.second_half_table.setRowCount(
                0
            )