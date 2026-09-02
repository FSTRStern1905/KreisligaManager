from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.goal_timeline_service import (
    GoalTimelineService,
)
from src.ui.charts.base_bar_chart import (
    BaseBarChart,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionGoalTimelineTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="🔥 Torphasen",
            refresh_button_text=(
                "🔄 Torphasen aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.league_info_text = ""
        self.team_info_text = ""

        self.league_tab = QWidget()
        self.team_tab = QWidget()

        self.league_chart = BaseBarChart(
            title="Torverteilung nach Spielminuten",
            x_axis_title="Spielminute",
            y_axis_title="Tore",
        )

        self.league_chart.show_legend(
            True
        )

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

        self.team_chart = BaseBarChart(
            title="Mannschafts-Torphasen",
            x_axis_title="Spielminute",
            y_axis_title="Tore",
        )

        self.team_chart.show_legend(
            True
        )

        self.setup_league_tab()
        self.setup_team_tab()

        self.inner_tabs.addTab(
            self.league_tab,
            "Liga",
        )

        self.inner_tabs.addTab(
            self.team_tab,
            "Mannschaft",
        )

        self.inner_tabs.setCornerWidget(
            self.team_selector_widget
        )

        self.team_selector_widget.setVisible(
            False
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.team_combo.currentIndexChanged.connect(
            self.team_changed
        )

        self.inner_tabs.currentChanged.connect(
            self.inner_tab_changed
        )

        self.clear_data()

    def setup_league_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.league_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.league_chart,
            1,
        )

    def setup_team_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.team_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.team_chart,
            1,
        )

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.league_chart.clear()
        self.team_chart.clear()

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

                service = GoalTimelineService(
                    connection
                )

                timeline = (
                    service.get_goal_timeline(
                        self.competition_id
                    )
                )

                teams = (
                    service.get_competition_teams(
                        self.competition_id
                    )
                )

                self.populate_league_chart(
                    timeline
                )

                self.populate_team_combo(
                    teams
                )

                total_goals = sum(
                    int(
                        interval["goals"]
                    )
                    for interval in timeline
                )

                home_goals = sum(
                    int(
                        interval["home_goals"]
                    )
                    for interval in timeline
                )

                away_goals = sum(
                    int(
                        interval["away_goals"]
                    )
                    for interval in timeline
                )

                unassigned_goals = sum(
                    int(
                        interval["unassigned_goals"]
                    )
                    for interval in timeline
                )

                assigned_goals = (
                    home_goals
                    + away_goals
                )

                home_share = (
                    round(
                        home_goals
                        / assigned_goals
                        * 100,
                        1,
                    )
                    if assigned_goals > 0
                    else 0.0
                )

                away_share = (
                    round(
                        away_goals
                        / assigned_goals
                        * 100,
                        1,
                    )
                    if assigned_goals > 0
                    else 0.0
                )

                strongest_phase = (
                    self._get_strongest_phase(
                        timeline
                    )
                )

                info_parts = [
                    competition_name,
                    f"{total_goals} Tore",
                    (
                        f"🏠 {home_goals} "
                        f"({home_share:.1f} %)"
                    ),
                    (
                        f"🚌 {away_goals} "
                        f"({away_share:.1f} %)"
                    ),
                ]

                if strongest_phase is not None:
                    info_parts.append(
                        (
                            "Torreichste Phase: "
                            f"{strongest_phase['label']} Min. "
                            f"("
                            f"{strongest_phase['goals']} Tore / "
                            f"{strongest_phase['percentage']:.1f} %"
                            f")"
                        )
                    )

                if unassigned_goals > 0:
                    info_parts.append(
                        (
                            f"{unassigned_goals} Tore "
                            "ohne Zuordnung"
                        )
                    )

                self.league_info_text = (
                    " | ".join(
                        info_parts
                    )
                )

                if (
                    self.inner_tabs.currentWidget()
                    is self.league_tab
                ):
                    self.set_info_text(
                        self.league_info_text
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
                    "Die Torphasen konnten "
                    "nicht geladen werden."
                ),
                error=error,
            )

    def populate_team_combo(
        self,
        teams: list[dict],
    ) -> None:
        previous_team_id = (
            self.team_combo.currentData()
        )

        self.team_combo.blockSignals(
            True
        )

        self.team_combo.clear()

        for team in teams:
            self.team_combo.addItem(
                team["team_name"],
                team["team_id"],
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
        is_team_tab = (
            self.inner_tabs.widget(
                index
            )
            is self.team_tab
        )

        self.team_selector_widget.setVisible(
            is_team_tab
        )

        if is_team_tab:
            if self.team_info_text:
                self.set_info_text(
                    self.team_info_text
                )

            self.load_selected_team()

        else:
            if self.league_info_text:
                self.set_info_text(
                    self.league_info_text
                )

    def team_changed(
        self,
        index: int,
    ) -> None:
        if index < 0:
            return

        self.load_selected_team()

    def load_selected_team(
        self,
    ) -> None:
        if self.competition_id is None:
            return

        team_id = self.team_combo.currentData()

        if team_id is None:
            self.team_chart.show_empty_chart(
                "Keine Mannschaft ausgewählt"
            )
            return

        try:
            with self.database_connection() as connection:
                service = GoalTimelineService(
                    connection
                )

                timeline = (
                    service.get_team_goal_timeline(
                        competition_id=self.competition_id,
                        team_id=int(
                            team_id
                        ),
                    )
                )

            self.populate_team_chart(
                timeline
            )

            team_name = (
                self.team_combo.currentText()
            )

            total_for = sum(
                int(
                    interval[
                        "goals_for"
                    ]
                )
                for interval in timeline
            )

            total_against = sum(
                int(
                    interval[
                        "goals_against"
                    ]
                )
                for interval in timeline
            )

            strongest_offensive_phase = (
                self._get_team_strongest_phase(
                    timeline,
                    key="goals_for",
                )
            )

            weakest_defensive_phase = (
                self._get_team_strongest_phase(
                    timeline,
                    key="goals_against",
                )
            )

            info_parts = [
                team_name,
                f"{total_for} Tore",
                f"{total_against} Gegentore",
                (
                    "Differenz "
                    f"{self._format_signed_value(total_for - total_against)}"
                ),
            ]

            if strongest_offensive_phase is not None:
                info_parts.append(
                    (
                        "Stärkste Offensive: "
                        f"{strongest_offensive_phase['label']} Min. "
                        f"({strongest_offensive_phase['goals_for']} Tore)"
                    )
                )

            if weakest_defensive_phase is not None:
                info_parts.append(
                    (
                        "Meiste Gegentore: "
                        f"{weakest_defensive_phase['label']} Min. "
                        f"({weakest_defensive_phase['goals_against']})"
                    )
                )

            self.team_info_text = (
                " | ".join(
                    info_parts
                )
            )

            if (
                self.inner_tabs.currentWidget()
                is self.team_tab
            ):
                self.set_info_text(
                    self.team_info_text
                )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            self.handle_load_error(
                message=(
                    "Die Mannschafts-Torphasen "
                    "konnten nicht geladen werden."
                ),
                error=error,
            )

    def populate_league_chart(
        self,
        timeline: list[dict],
    ) -> None:
        self.league_chart.clear()

        if not timeline:
            self.league_chart.show_empty_chart(
                "Keine Daten vorhanden"
            )
            return

        total_goals = sum(
            int(
                interval["goals"]
            )
            for interval in timeline
        )

        if total_goals <= 0:
            self.league_chart.show_empty_chart(
                "Keine Tore mit Minutenangabe"
            )
            return

        categories: list[str] = []
        home_values: list[float] = []
        away_values: list[float] = []
        total_values: list[float] = []

        maximum_total = 0

        for interval in timeline:
            goals = int(
                interval["goals"]
            )

            home_goals = int(
                interval["home_goals"]
            )

            away_goals = int(
                interval["away_goals"]
            )

            categories.append(
                f"{interval['label']} Min."
            )

            home_values.append(
                float(
                    home_goals
                )
            )

            away_values.append(
                float(
                    away_goals
                )
            )

            total_values.append(
                float(
                    goals
                )
            )

            maximum_total = max(
                maximum_total,
                goals,
            )

        self.league_chart.set_categories(
            categories
        )

        self.league_chart.create_stacked_bar_series(
            sets=[
                (
                    "Heimtore",
                    home_values,
                ),
                (
                    "Auswärtstore",
                    away_values,
                ),
            ],
            show_labels=True,
        )

        padding = max(
            10,
            round(
                maximum_total
                * 0.12
            ),
        )

        self.league_chart.set_value_range(
            minimum=0,
            maximum=(
                maximum_total
                + padding
            ),
        )

        self.league_chart.create_total_labels(
            total_values
        )

        self.league_chart.restore_chart_title()

    def populate_team_chart(
        self,
        timeline: list[dict],
    ) -> None:
        self.team_chart.clear()

        if not timeline:
            self.team_chart.show_empty_chart(
                "Keine Daten vorhanden"
            )
            return

        categories: list[str] = []
        goals_for_values: list[float] = []
        goals_against_values: list[float] = []
        total_values: list[float] = []

        maximum_total = 0

        for interval in timeline:
            goals_for = int(
                interval[
                    "goals_for"
                ]
            )

            goals_against = int(
                interval[
                    "goals_against"
                ]
            )

            total = (
                goals_for
                + goals_against
            )

            categories.append(
                f"{interval['label']} Min."
            )

            goals_for_values.append(
                float(
                    goals_for
                )
            )

            goals_against_values.append(
                float(
                    goals_against
                )
            )

            total_values.append(
                float(
                    total
                )
            )

            maximum_total = max(
                maximum_total,
                total,
            )

        if maximum_total <= 0:
            self.team_chart.show_empty_chart(
                "Keine Tore mit Minutenangabe"
            )
            return

        self.team_chart.set_categories(
            categories
        )

        self.team_chart.create_stacked_bar_series(
            sets=[
                (
                    "Erzielte Tore",
                    goals_for_values,
                ),
                (
                    "Gegentore",
                    goals_against_values,
                ),
            ],
            show_labels=True,
        )

        padding = max(
            2,
            round(
                maximum_total
                * 0.15
            ),
        )

        self.team_chart.set_value_range(
            minimum=0,
            maximum=(
                maximum_total
                + padding
            ),
        )

        self.team_chart.create_total_labels(
            total_values
        )

        self.team_chart.restore_chart_title()

    @staticmethod
    def _get_strongest_phase(
        timeline: list[dict],
    ) -> dict | None:
        populated_intervals = [
            interval
            for interval in timeline
            if int(
                interval[
                    "goals"
                ]
            ) > 0
        ]

        if not populated_intervals:
            return None

        return max(
            populated_intervals,
            key=lambda interval: (
                int(
                    interval[
                        "goals"
                    ]
                ),
                float(
                    interval[
                        "percentage"
                    ]
                ),
            ),
        )

    @staticmethod
    def _get_team_strongest_phase(
        timeline: list[dict],
        key: str,
    ) -> dict | None:
        populated_intervals = [
            interval
            for interval in timeline
            if int(
                interval.get(
                    key,
                    0,
                )
            ) > 0
        ]

        if not populated_intervals:
            return None

        return max(
            populated_intervals,
            key=lambda interval: (
                int(
                    interval.get(
                        key,
                        0,
                    )
                ),
                int(
                    interval.get(
                        "goal_difference",
                        0,
                    )
                ),
            ),
        )

    @staticmethod
    def _format_signed_value(
        value: int,
    ) -> str:
        if value > 0:
            return (
                f"+{value}"
            )

        return str(
            value
        )

    def clear_content(
        self,
    ) -> None:
        self.league_info_text = ""
        self.team_info_text = ""

        if hasattr(
            self,
            "league_chart",
        ):
            self.league_chart.show_empty_chart(
                "Keine Daten"
            )

        if hasattr(
            self,
            "team_chart",
        ):
            self.team_chart.show_empty_chart(
                "Keine Daten"
            )

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
