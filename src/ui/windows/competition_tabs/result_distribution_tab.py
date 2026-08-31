from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.result_distribution_service import (
    ResultDistributionService,
)
from src.ui.charts.base_bar_chart import (
    BaseBarChart,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionResultDistributionTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⚽ Ergebnisverteilung",
            refresh_button_text=(
                "🔄 Ergebnisse aktualisieren"
            ),
        )

        self.chart_widget = BaseBarChart(
            title="Spielausgänge",
            x_axis_title="Ergebnis",
            y_axis_title="Spiele",
        )

        self.chart_widget.show_legend(
            False
        )

        self.chart_widget.setMinimumHeight(
            320
        )

        self.add_content_widget(
            self.chart_widget
        )

        self.scoreline_title = QLabel(
            "📊 Häufigste Ergebnisse"
        )

        self.scoreline_title.setObjectName(
            "SectionTitle"
        )

        self.add_content_widget(
            self.scoreline_title
        )

        self.scoreline_table = QTableWidget()

        self.setup_scoreline_table()

        self.add_content_widget(
            self.scoreline_table,
            stretch=1,
        )

        self.clear_data()

    def setup_scoreline_table(
        self,
    ) -> None:
        self.scoreline_table.setColumnCount(
            4
        )

        self.scoreline_table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Ergebnis",
                "Anzahl",
                "Anteil",
            ]
        )

        self.scoreline_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.scoreline_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.scoreline_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.scoreline_table.setAlternatingRowColors(
            True
        )

        self.scoreline_table.verticalHeader().setVisible(
            False
        )

        header = (
            self.scoreline_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.chart_widget.clear()

        self.scoreline_table.setRowCount(
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

                service = (
                    ResultDistributionService(
                        connection
                    )
                )

                distribution = (
                    service.get_result_distribution(
                        self.competition_id
                    )
                )

                self.populate_chart(
                    distribution
                )

                self.populate_scoreline_table(
                    distribution[
                        "most_common_scorelines"
                    ]
                )

                self.set_info_text(
                    (
                        f"{competition_name} | "
                        f"{distribution['total_matches']} Spiele | "
                        f"{distribution['total_goals']} Tore | "
                        f"Ø {distribution['average_goals']:.2f} Tore | "
                        f"Über 2,5: "
                        f"{distribution['over_2_5_percentage']:.1f} % | "
                        f"Beide treffen: "
                        f"{distribution['both_teams_score_percentage']:.1f} %"
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
                    "Die Ergebnisverteilung "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_chart(
        self,
        distribution: dict,
    ) -> None:
        total_matches = int(
            distribution[
                "total_matches"
            ]
        )

        if total_matches <= 0:
            self.chart_widget.show_empty_chart(
                "Keine abgeschlossenen Spiele"
            )
            return

        categories = [
            "Heimsiege",
            "Remis",
            "Auswärtssiege",
        ]

        values = [
            float(
                distribution[
                    "home_wins"
                ]
            ),
            float(
                distribution[
                    "draws"
                ]
            ),
            float(
                distribution[
                    "away_wins"
                ]
            ),
        ]

        self.chart_widget.set_categories(
            categories
        )

        series = (
            self.chart_widget.create_bar_series(
                name="Spiele",
                values=values,
            )
        )

        series.setLabelsVisible(
            True
        )

        series.setLabelsFormat(
            "@value"
        )

        maximum_value = max(
            values,
            default=0,
        )

        padding = max(
            2,
            round(
                maximum_value
                * 0.15
            ),
        )

        self.chart_widget.set_value_range(
            minimum=0,
            maximum=(
                maximum_value
                + padding
            ),
        )

        self.chart_widget.restore_chart_title()

    def populate_scoreline_table(
        self,
        scorelines: list[dict],
    ) -> None:
        self.scoreline_table.setRowCount(
            len(
                scorelines
            )
        )

        for row_index, scoreline in enumerate(
            scorelines
        ):
            values = [
                row_index + 1,
                scoreline["score"],
                scoreline["count"],
                (
                    f"{scoreline['percentage']:.1f} %"
                ),
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

                self.scoreline_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "chart_widget",
        ):
            self.chart_widget.show_empty_chart(
                "Keine Daten"
            )

        if hasattr(
            self,
            "scoreline_table",
        ):
            self.scoreline_table.setRowCount(
                0
            )