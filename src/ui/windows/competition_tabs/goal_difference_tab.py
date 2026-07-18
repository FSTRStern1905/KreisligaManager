import sqlite3

from src.services.statistics.goal_difference_service import (
    GoalDifferenceService,
)
from src.ui.charts.base_bar_chart import (
    BaseBarChart,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionGoalDifferenceTab(
    BaseStatisticsTab
):
    def __init__(self):
        super().__init__(
            title="⚖️ Torverhältnis",
            refresh_button_text=(
                "🔄 Torverhältnis aktualisieren"
            ),
        )

        self.chart_widget = BaseBarChart(
            title="Torverhältnis",
            x_axis_title="Mannschaften",
            y_axis_title="Tordifferenz",
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

                service = GoalDifferenceService(
                    connection
                )

                teams = (
                    service.get_goal_differences(
                        self.competition_id
                    )
                )

                self.populate_chart(
                    teams
                )

                self.set_info_text(
                    f"{competition_name} | "
                    f"{len(teams)} Mannschaften"
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
                    "Das Torverhältnis konnte "
                    "nicht geladen werden."
                ),
                error=error,
            )

    def populate_chart(
        self,
        teams: list[dict],
    ) -> None:
        self.chart_widget.clear()

        if not teams:
            self.chart_widget.show_empty_chart(
                "Keine Daten vorhanden"
            )
            return

        categories = []
        values = []

        minimum = 0
        maximum = 0

        for team in teams:
            goal_difference = int(
                team["goal_difference"]
            )

            categories.append(
                team["team_name"]
            )

            values.append(
                goal_difference
            )

            minimum = min(
                minimum,
                goal_difference,
            )

            maximum = max(
                maximum,
                goal_difference,
            )

        self.chart_widget.set_categories(
            categories
        )

        self.chart_widget.create_bar_series(
            name="Torverhältnis",
            values=values,
        )

        self.chart_widget.set_value_range(
            minimum=minimum - 2,
            maximum=maximum + 2,
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