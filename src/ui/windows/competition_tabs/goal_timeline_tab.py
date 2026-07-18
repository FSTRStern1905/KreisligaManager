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
    def __init__(self):
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
            False
        )

        self.add_content_widget(
            self.chart_widget,
            stretch=1,
        )

        self.clear_data()

    def load_data(self) -> None:
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
                    int(interval["goals"])
                    for interval in timeline
                )

                self.set_info_text(
                    f"{competition_name} | "
                    f"{total_goals} Tore"
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

        categories = []
        values = []

        maximum = 0

        for interval in timeline:
            goals = int(
                interval["goals"]
            )

            categories.append(
                interval["label"]
            )

            values.append(
                goals
            )

            maximum = max(
                maximum,
                goals,
            )

        self.chart_widget.set_categories(
            categories
        )

        self.chart_widget.create_bar_series(
            name="Tore",
            values=values,
        )

        self.chart_widget.set_value_range(
            minimum=0,
            maximum=max(
                5,
                maximum + 2,
            ),
        )

        self.chart_widget.restore_chart_title()

    def clear_content(self) -> None:
        if not hasattr(
            self,
            "chart_widget",
        ):
            return

        self.chart_widget.show_empty_chart(
            "Keine Daten"
        )