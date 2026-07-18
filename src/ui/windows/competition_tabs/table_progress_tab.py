import sqlite3

from src.services.statistics.table_progress_service import (
    TableProgressService,
)
from src.ui.charts.base_line_chart import (
    BaseLineChart,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionTableProgressTab(
    BaseStatisticsTab
):
    def __init__(self):
        super().__init__(
            title="📉 Tabellenentwicklung",
            refresh_button_text=(
                "🔄 Tabellenentwicklung aktualisieren"
            ),
        )

        self.chart_widget = BaseLineChart(
            title="Tabellenplätze nach Spieltagen",
            x_axis_title="Spieltag",
            y_axis_title="Tabellenplatz",
        )

        self.chart_widget.set_y_axis_reversed(
            True
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

                service = TableProgressService(
                    connection
                )

                teams = service.get_table_progress(
                    self.competition_id
                )

                matchdays = service.get_matchdays(
                    self.competition_id
                )

                self.populate_chart(
                    teams=teams,
                    matchdays=matchdays,
                )

                self.set_info_text(
                    f"{competition_name} | "
                    f"{len(teams)} Mannschaften | "
                    f"{len(matchdays)} Spieltage"
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
                    "Die Tabellenentwicklung "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_chart(
        self,
        teams: list[dict],
        matchdays: list[int],
    ) -> None:
        self.chart_widget.clear()

        if not teams or not matchdays:
            self.chart_widget.show_empty_chart(
                "Keine Spieldaten vorhanden"
            )
            return

        for team in teams:
            series_points = []

            for entry in team["positions"]:
                series_points.append(
                    (
                        int(entry["matchday"]),
                        int(entry["position"]),
                    )
                )

            self.chart_widget.create_line_series(
                name=team["team_name"],
                points=series_points,
            )

        self.chart_widget.restore_chart_title()

        self.chart_widget.set_axis_ranges(
            x_min=1,
            x_max=max(matchdays),
            y_min=1,
            y_max=len(teams),
        )

        self.chart_widget.set_axis_tick_intervals(
            x_interval=1,
            y_interval=1,
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