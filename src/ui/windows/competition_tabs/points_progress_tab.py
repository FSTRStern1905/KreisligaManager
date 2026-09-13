import sqlite3

from src.services.statistics.points_progress_service import (
    PointsProgressService,
)
from src.ui.charts.base_line_chart import (
    BaseLineChart,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionPointsProgressTab(
    BaseStatisticsTab
):
    def __init__(self):
        super().__init__(
            title="📈 Punkteverlauf",
            refresh_button_text=(
                "🔄 Punkteverlauf aktualisieren"
            ),
        )

        self.chart_widget = BaseLineChart(
            title="Punkteentwicklung nach absolvierten Spielen",
            x_axis_title="Absolvierte Spiele",
            y_axis_title="Punkte",
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

                service = PointsProgressService(
                    connection
                )

                teams = service.get_points_progress(
                    self.competition_id
                )

                self.populate_chart(
                    teams=teams,
                )

                leader = max(
                    teams,
                    key=lambda team: (
                        int(team["progress"][-1]["points"])
                        if team.get("progress")
                        else -1
                    ),
                    default=None,
                )

                leader_text = ""

                if leader and leader.get("progress"):
                    leader_points = int(
                        leader["progress"][-1]["points"]
                    )
                    leader_text = (
                        f" | 🟢 Führend: "
                        f"{leader['team_name']} "
                        f"– {leader_points} Pkt."
                    )

                maximum_played = max(
                    (
                        int(team.get("played", 0))
                        for team in teams
                    ),
                    default=0,
                )

                self.set_info_text(
                    f"{competition_name} | "
                    f"{len(teams)} Mannschaften | "
                    f"Max. {maximum_played} absolvierte Spiele"
                    f"{leader_text} | "
                    f"Quelle: importierte Spieldaten"
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
                    "Der Punkteverlauf konnte "
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
                "Keine Spieldaten vorhanden"
            )
            return

        maximum_points = 0
        maximum_played = 0

        for team in teams:
            series_points = []

            for entry in team["progress"]:
                match_number = int(
                    entry["match_number"]
                )

                points = int(
                    entry["points"]
                )

                series_points.append(
                    (
                        match_number,
                        points,
                    )
                )

                maximum_points = max(
                    maximum_points,
                    points,
                )

                maximum_played = max(
                    maximum_played,
                    match_number,
                )

            self.chart_widget.create_line_series(
                name=team["team_name"],
                points=series_points,
            )

        self.chart_widget.restore_chart_title()

        self.chart_widget.set_axis_ranges(
            x_min=0,
            x_max=max(
                1,
                maximum_played,
            ),
            y_min=0,
            y_max=self.calculate_axis_maximum(
                maximum_points
            ),
        )

        x_interval = 1

        if maximum_played > 20:
            x_interval = 2

        if maximum_played > 36:
            x_interval = 3

        self.chart_widget.set_axis_tick_intervals(
            x_interval=x_interval,
            y_interval=5,
        )

    @staticmethod
    def calculate_axis_maximum(
        maximum_points: int,
    ) -> int:
        if maximum_points <= 0:
            return 5

        remainder = maximum_points % 5

        if remainder == 0:
            return maximum_points

        return maximum_points + (
            5 - remainder
        )

    def clear_content(self) -> None:
        if not hasattr(
            self,
            "chart_widget",
        ):
            return

        self.chart_widget.show_empty_chart(
            "Keine Daten geladen"
        )
