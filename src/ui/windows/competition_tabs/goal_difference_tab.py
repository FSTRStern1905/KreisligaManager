import sqlite3
from pathlib import Path

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.goal_difference_service import (
    GoalDifferenceService,
)
from src.services.statistics_service import (
    StatisticsService,
)

DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionGoalDifferenceTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("⚖️ Torverhältnis")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.chart = QChart()
        self.chart.legend().setVisible(False)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(
            QPainter.Antialiasing
        )

        self.refresh_button = QPushButton(
            "🔄 Torverhältnis aktualisieren"
        )

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.chart_view)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def connect_signals(self):
        self.refresh_button.clicked.connect(
            self.load_data
        )

    def set_competition(
        self,
        competition_id: int | None,
    ):
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(self):
        self.clear_chart()

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            statistics = StatisticsService(
                connection
            )

            service = GoalDifferenceService(
                connection
            )

            competition_name = (
                statistics.get_competition_name(
                    self.competition_id
                )
            )

            teams = service.get_goal_differences(
                self.competition_id
            )

            self.show_chart(
                teams
            )

            self.info_label.setText(
                f"{competition_name} | {len(teams)} Mannschaften"
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:

            QMessageBox.critical(
                self,
                "Fehler",
                str(error),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_chart(
        self,
        teams: list[dict],
    ):
        self.clear_chart()

        series = QBarSeries()
        barset = QBarSet("Torverhältnis")

        categories = []

        minimum = 0
        maximum = 0

        for team in teams:

            value = team["goal_difference"]

            barset.append(value)

            categories.append(
                team["team_name"]
            )

            minimum = min(
                minimum,
                value,
            )

            maximum = max(
                maximum,
                value,
            )

        series.append(barset)

        self.chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)

        axis_y = QValueAxis()

        axis_y.setRange(
            minimum - 2,
            maximum + 2,
        )

        self.chart.addAxis(
            axis_x,
            Qt.AlignBottom,
        )

        self.chart.addAxis(
            axis_y,
            Qt.AlignLeft,
        )

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        self.chart.setTitle(
            "Torverhältnis"
        )

    def clear_chart(self):
        self.chart.removeAllSeries()

        for axis in self.chart.axes():
            self.chart.removeAxis(
                axis
            )

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.clear_chart()

        self.chart.setTitle(
            "Keine Daten"
        )

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )