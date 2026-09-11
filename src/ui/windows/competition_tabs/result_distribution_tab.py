from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
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
            x_axis_title="",
            y_axis_title="Spiele",
        )

        self.chart_widget.show_legend(
            False
        )

        self.chart_widget.setMinimumHeight(
            320
        )

        self.context_frame = QFrame()
        self.context_frame.setObjectName(
            "StatisticsInsightBox"
        )

        context_layout = QVBoxLayout(
            self.context_frame
        )
        context_layout.setContentsMargins(
            16, 12, 16, 12
        )
        context_layout.setSpacing(6)

        self.context_title = QLabel(
            "📌 Einordnung"
        )
        self.context_title.setObjectName(
            "StatisticsInsightTitle"
        )

        self.context_label = QLabel(
            "Noch keine Ergebnisdaten"
        )
        self.context_label.setObjectName(
            "StatisticsContextLabel"
        )
        self.context_label.setWordWrap(True)

        self.insight_label = QLabel("")
        self.insight_label.setObjectName(
            "StatisticsInsightLabel"
        )
        self.insight_label.setWordWrap(True)

        self.context_frame.setStyleSheet(
            """
            QFrame#StatisticsInsightBox {
                background-color: #252a32;
                border: 1px solid #3b424d;
                border-radius: 10px;
            }
            QLabel#StatisticsInsightTitle {
                color: #ffffff;
                font-weight: 700;
                border: none;
                background: transparent;
            }
            QLabel#StatisticsContextLabel {
                color: #d7dde8;
                border: none;
                background: transparent;
            }
            QLabel#StatisticsInsightLabel {
                color: #aebbd0;
                border: none;
                background: transparent;
            }
            """
        )

        context_layout.addWidget(
            self.context_title
        )
        context_layout.addWidget(
            self.context_label
        )
        context_layout.addWidget(
            self.insight_label
        )

        self.add_content_widget(
            self.context_frame
        )

        self.scoreline_button = QPushButton(
            "📊 Häufigste Ergebnisse anzeigen"
        )
        self.scoreline_button.setObjectName(
            "StatisticsSecondaryButton"
        )
        self.scoreline_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self.scoreline_button.setMinimumHeight(
            34
        )
        self.scoreline_button.clicked.connect(
            self.open_scoreline_dialog
        )

        self.header_row.removeWidget(
            self.refresh_button
        )

        actions_layout = QVBoxLayout()
        actions_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        actions_layout.setSpacing(
            6
        )

        actions_layout.addWidget(
            self.refresh_button
        )
        actions_layout.addWidget(
            self.scoreline_button
        )

        self.header_row.addLayout(
            actions_layout
        )

        self.add_content_widget(
            self.chart_widget
        )

        self._scorelines: list[dict] = []

        self.clear_data()

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.chart_widget.clear()

        self._scorelines = []

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

                self.populate_context(
                    distribution
                )

                self.populate_chart(
                    distribution
                )

                self._scorelines = list(
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

    def populate_context(
        self,
        distribution: dict,
    ) -> None:
        total_matches = int(
            distribution["total_matches"]
        )

        if total_matches <= 0:
            self.context_label.setText(
                "Noch keine abgeschlossenen Spiele"
            )
            self.insight_label.setText(
                ""
            )
            return

        home_wins = int(
            distribution["home_wins"]
        )
        draws = int(
            distribution["draws"]
        )
        away_wins = int(
            distribution["away_wins"]
        )

        home_percentage = (
            home_wins / total_matches * 100.0
        )
        draw_percentage = (
            draws / total_matches * 100.0
        )
        away_percentage = (
            away_wins / total_matches * 100.0
        )

        self.context_label.setText(
            (
                f"Heimsiege: {home_wins} "
                f"({home_percentage:.1f} %) · "
                f"Remis: {draws} "
                f"({draw_percentage:.1f} %) · "
                f"Auswärtssiege: {away_wins} "
                f"({away_percentage:.1f} %)"
            )
        )

        self.insight_label.setText(
            self._build_insight_text(
                home_percentage,
                draw_percentage,
                away_percentage,
            )
        )

    def _build_insight_text(
        self,
        home_percentage: float,
        draw_percentage: float,
        away_percentage: float,
    ) -> str:
        values = {
            "Heimsiege": home_percentage,
            "Remis": draw_percentage,
            "Auswärtssiege": away_percentage,
        }

        highest_label = max(
            values,
            key=values.get,
        )
        lowest_label = min(
            values,
            key=values.get,
        )

        highest_value = values[
            highest_label
        ]
        lowest_value = values[
            lowest_label
        ]

        if (
            highest_value
            - lowest_value
            < 5.0
        ):
            return (
                "Einordnung: Die drei "
                "Spielausgänge sind nahezu "
                "gleich verteilt."
            )

        if (
            lowest_label == "Remis"
            and lowest_value <= 15.0
        ):
            return (
                "Auffällig: Remis sind mit "
                f"{lowest_value:.1f} % deutlich "
                "seltener als die übrigen "
                "Spielausgänge."
            )

        return (
            "Einordnung: "
            f"{highest_label} treten mit "
            f"{highest_value:.1f} % am häufigsten "
            f"auf; {lowest_label} mit "
            f"{lowest_value:.1f} % am seltensten."
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

    def open_scoreline_dialog(
        self,
    ) -> None:
        dialog = QDialog(
            self
        )
        dialog.setWindowTitle(
            "Häufigste Ergebnisse"
        )
        dialog.setMinimumSize(
            700,
            480,
        )
        dialog.resize(
            820,
            560,
        )
        dialog.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(
            dialog
        )
        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        layout.setSpacing(
            12
        )

        title = QLabel(
            "📊 Häufigste Ergebnisse"
        )
        title.setObjectName(
            "SectionTitle"
        )
        layout.addWidget(
            title
        )

        table = QTableWidget()
        table.setColumnCount(
            4
        )
        table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Ergebnis",
                "Anzahl",
                "Anteil",
            ]
        )
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
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        table.setRowCount(
            len(
                self._scorelines
            )
        )

        for row_index, scoreline in enumerate(
            self._scorelines
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
                table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        if not self._scorelines:
            table.setRowCount(
                1
            )
            empty_item = QTableWidgetItem(
                "Keine Daten vorhanden"
            )
            empty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            table.setSpan(
                0,
                0,
                1,
                4,
            )
            table.setItem(
                0,
                0,
                empty_item,
            )

        layout.addWidget(
            table,
            1,
        )

        close_button = QPushButton(
            "Schließen"
        )
        close_button.clicked.connect(
            dialog.accept
        )
        close_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        layout.addWidget(
            close_button,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        dialog.exec()

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
            "context_label",
        ):
            self.context_label.setText(
                "Noch keine Ergebnisdaten"
            )

        if hasattr(
            self,
            "insight_label",
        ):
            self.insight_label.setText(
                ""
            )

        self._scorelines = []

