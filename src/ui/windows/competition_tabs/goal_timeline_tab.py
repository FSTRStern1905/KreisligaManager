from __future__ import annotations

import sqlite3

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

        self.chart_widget = BaseBarChart(
            title="Torverteilung nach Spielminuten",
            x_axis_title="Spielminute",
            y_axis_title="Tore",
        )

        self.chart_widget.show_legend(
            True
        )

        self.add_content_widget(
            self.chart_widget,
            stretch=1,
        )

        self.clear_data()

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.chart_widget.clear()

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

                self.populate_chart(
                    timeline
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
                    "Die Torphasen konnten "
                    "nicht geladen werden."
                ),
                error=error,
            )

    def populate_chart(
        self,
        timeline: list[dict],
    ) -> None:
        self.chart_widget.clear()

        if not timeline:
            self.chart_widget.show_empty_chart(
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
            self.chart_widget.show_empty_chart(
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
                float(home_goals)
            )

            away_values.append(
                float(away_goals)
            )

            total_values.append(
                float(goals)
            )

            maximum_total = max(
                maximum_total,
                goals,
            )

        self.chart_widget.set_categories(
            categories
        )

        self.chart_widget.create_stacked_bar_series(
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
                maximum_total * 0.12
            ),
        )

        self.chart_widget.set_value_range(
            minimum=0,
            maximum=(
                maximum_total
                + padding
            ),
        )

        self.chart_widget.create_total_labels(
            total_values
        )

        self.chart_widget.restore_chart_title()

    @staticmethod
    def _get_strongest_phase(
        timeline: list[dict],
    ) -> dict | None:
        populated_intervals = [
            interval
            for interval in timeline
            if int(
                interval["goals"]
            ) > 0
        ]

        if not populated_intervals:
            return None

        return max(
            populated_intervals,
            key=lambda interval: (
                int(
                    interval["goals"]
                ),
                float(
                    interval["percentage"]
                ),
            ),
        )

    def clear_content(
        self,
    ) -> None:
        if not hasattr(
            self,
            "chart_widget",
        ):
            return

        self.chart_widget.show_empty_chart(
            "Keine Daten"
        )