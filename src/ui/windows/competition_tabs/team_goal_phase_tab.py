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

from src.services.statistics.team_goal_phase_service import (
    TeamGoalPhaseService,
)
from src.ui.charts.base_bar_chart import (
    BaseBarChart,
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

        self.inner_tabs = QTabWidget()

        self.league_tab = QWidget()
        self.team_tab = QWidget()
        self.goals_tab = QWidget()
        self.conceded_tab = QWidget()

        self.team_table = QTableWidget()

        self.goals_chart = BaseBarChart(
            title="Frühe / späte Tore vs. Liga-Ø",
            x_axis_title="Spielphase",
            y_axis_title="Tore",
        )
        self.goals_chart.show_legend(
            True
        )

        self.conceded_chart = BaseBarChart(
            title="Frühe / späte Gegentore vs. Liga-Ø",
            x_axis_title="Spielphase",
            y_axis_title="Gegentore",
        )
        self.conceded_chart.show_legend(
            True
        )

        self.team_selector_widget = QWidget()
        selector_layout = QHBoxLayout(
            self.team_selector_widget
        )
        selector_layout.setContentsMargins(
            8,
            0,
            0,
            0,
        )
        selector_layout.setSpacing(
            8
        )

        selector_layout.addWidget(
            QLabel("Mannschaft:")
        )

        self.team_combo = QComboBox()
        self.team_combo.setMinimumWidth(
            260
        )
        selector_layout.addWidget(
            self.team_combo
        )

        self.statistics_cache: list[dict] = []

        self.setup_table()
        self.setup_team_table()
        self.setup_tabs()

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

    def setup_team_table(
        self,
    ) -> None:
        self.team_table.setColumnCount(
            5
        )
        self.team_table.setHorizontalHeaderLabels(
            [
                "Phase",
                "Tore",
                "Gegentore",
                "Bilanz",
                "Anteil Tore %",
            ]
        )
        self.team_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.team_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.team_table.setAlternatingRowColors(
            True
        )
        self.team_table.verticalHeader().setVisible(
            False
        )

        header = self.team_table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def setup_tabs(
        self,
    ) -> None:
        league_layout = QVBoxLayout(
            self.league_tab
        )
        league_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        league_layout.addWidget(
            self.table
        )

        team_layout = QVBoxLayout(
            self.team_tab
        )
        team_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        team_layout.addWidget(
            self.team_table
        )

        goals_layout = QVBoxLayout(
            self.goals_tab
        )
        goals_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        goals_layout.addWidget(
            self.goals_chart
        )

        conceded_layout = QVBoxLayout(
            self.conceded_tab
        )
        conceded_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        conceded_layout.addWidget(
            self.conceded_chart
        )

        self.inner_tabs.addTab(
            self.league_tab,
            "Liga",
        )
        self.inner_tabs.addTab(
            self.team_tab,
            "Mannschaft",
        )
        self.inner_tabs.addTab(
            self.goals_tab,
            "Erzielte Tore",
        )
        self.inner_tabs.addTab(
            self.conceded_tab,
            "Gegentore",
        )

        self.inner_tabs.setCornerWidget(
            self.team_selector_widget
        )
        self.team_selector_widget.setVisible(
            False
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

        for team in sorted(
            statistics,
            key=lambda item: str(
                item["team_name"]
            ).lower(),
        ):
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

    def inner_tab_changed(
        self,
        index: int,
    ) -> None:
        current_widget = self.inner_tabs.widget(
            index
        )
        needs_team = current_widget in (
            self.team_tab,
            self.goals_tab,
            self.conceded_tab,
        )

        self.team_selector_widget.setVisible(
            needs_team
        )

        if needs_team:
            self.load_selected_team()

    def team_changed(
        self,
        index: int,
    ) -> None:
        if index >= 0:
            self.load_selected_team()

    def load_selected_team(
        self,
    ) -> None:
        team_id = self.team_combo.currentData()

        if (
            team_id is None
            or not self.statistics_cache
        ):
            return

        team = next(
            (
                item
                for item in self.statistics_cache
                if int(
                    item["team_id"]
                ) == int(
                    team_id
                )
            ),
            None,
        )

        if team is None:
            return

        self.populate_team_table(
            team
        )
        self.populate_goals_chart(
            team
        )
        self.populate_conceded_chart(
            team
        )

    def populate_team_table(
        self,
        team: dict,
    ) -> None:
        rows = [
            (
                "0–15 Min.",
                int(
                    team["early_goals"]
                ),
                int(
                    team["early_goals_against"]
                ),
                int(
                    team["early_goals"]
                )
                - int(
                    team["early_goals_against"]
                ),
                float(
                    team["early_goal_percentage"]
                ),
            ),
            (
                "76–90 Min.",
                int(
                    team["late_goals"]
                ),
                int(
                    team["late_goals_against"]
                ),
                int(
                    team["late_balance"]
                ),
                float(
                    team["late_goal_percentage"]
                ),
            ),
        ]

        self.team_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, row in enumerate(
            rows
        ):
            phase, goals, against, balance, percentage = row

            balance_text = (
                f"+{balance}"
                if balance > 0
                else str(
                    balance
                )
            )

            values = [
                phase,
                goals,
                against,
                balance_text,
                f"{percentage:.1f} %",
            ]

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
                self.team_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def _league_average(
        self,
        key: str,
    ) -> float:
        if not self.statistics_cache:
            return 0.0

        return sum(
            float(
                team[key]
            )
            for team in self.statistics_cache
        ) / len(
            self.statistics_cache
        )

    def _populate_average_chart(
        self,
        chart: BaseBarChart,
        series_name: str,
        team_values: list[float],
        league_values: list[float],
        lower_is_better: bool,
    ) -> None:
        chart.clear()

        chart.set_categories(
            [
                "0–15 Min.",
                "76–90 Min.",
            ]
        )

        chart.create_bar_series(
            name=series_name,
            values=team_values,
        )

        chart.create_total_labels(
            team_values
        )

        maximum = max(
            team_values
            + league_values
        )
        padding = max(
            2.0,
            maximum * 0.22,
        )

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

    def populate_goals_chart(
        self,
        team: dict,
    ) -> None:
        team_values = [
            float(
                team["early_goals"]
            ),
            float(
                team["late_goals"]
            ),
        ]
        league_values = [
            self._league_average(
                "early_goals"
            ),
            self._league_average(
                "late_goals"
            ),
        ]

        self._populate_average_chart(
            chart=self.goals_chart,
            series_name="Erzielte Tore",
            team_values=team_values,
            league_values=league_values,
            lower_is_better=False,
        )

    def populate_conceded_chart(
        self,
        team: dict,
    ) -> None:
        team_values = [
            float(
                team["early_goals_against"]
            ),
            float(
                team["late_goals_against"]
            ),
        ]
        league_values = [
            self._league_average(
                "early_goals_against"
            ),
            self._league_average(
                "late_goals_against"
            ),
        ]

        self._populate_average_chart(
            chart=self.conceded_chart,
            series_name="Gegentore",
            team_values=team_values,
            league_values=league_values,
            lower_is_better=True,
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

                self.statistics_cache = [
                    dict(
                        team
                    )
                    for team in statistics
                ]

                self.populate_team_combo(
                    statistics
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

            self.load_selected_team()

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
        self.statistics_cache = []

        if hasattr(
            self,
            "table",
        ):
            self.table.setRowCount(
                0
            )

        if hasattr(
            self,
            "team_table",
        ):
            self.team_table.setRowCount(
                0
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
            "goals_chart",
        ):
            self.goals_chart.show_empty_chart(
                "Keine Daten"
            )

        if hasattr(
            self,
            "conceded_chart",
        ):
            self.conceded_chart.show_empty_chart(
                "Keine Daten"
            )

        if hasattr(
            self,
            "team_selector_widget",
        ):
            self.team_selector_widget.setVisible(
                False
            )
