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

from src.services.statistics.goal_timeline_service import (
    GoalTimelineService,
)
from src.services.statistics_service import (
    StatisticsService,
)

DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionGoalTimelineTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🔥 Torphasen")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.chart = QChart()
        self.chart.legend().setVisible(False)

        self.chart_view = QChartView(
            self.chart
        )
        self.chart_view.setRenderHint(
            QPainter.Antialiasing
        )

        self.refresh_button = QPushButton(
            "🔄 Torphasen aktualisieren"
        )
        self.refresh_button.setEnabled(False)

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
            statistics_service = StatisticsService(
                connection
            )

            goal_service = GoalTimelineService(
                connection
            )

            competition_name = (
                statistics_service.get_competition_name(
                    self.competition_id
                )
            )

            timeline = (
                goal_service.get_goal_timeline(
                    self.competition_id
                )
            )

            self.show_chart(
                timeline
            )

            total_goals = sum(
                interval["goals"]
                for interval in timeline
            )

            self.info_label.setText(
                f"{competition_name} | "
                f"{total_goals} Tore"
            )

            self.refresh_button.setEnabled(True)

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
        timeline: list[dict],
    ):
        self.clear_chart()

        series = QBarSeries()

        barset = QBarSet(
            "Tore"
        )

        categories = []

        maximum = 0

        for interval in timeline:

            barset.append(
                interval["goals"]
            )

            categories.append(
                interval["label"]
            )

            maximum = max(
                maximum,
                interval["goals"],
            )

        series.append(
            barset
        )

        self.chart.addSeries(
            series
        )

        axis_x = QBarCategoryAxis()
        axis_x.append(
            categories
        )

        axis_y = QValueAxis()
        axis_y.setRange(
            0,
            max(
                5,
                maximum + 2,
            ),
        )

        self.chart.addAxis(
            axis_x,
            Qt.AlignBottom,
        )

        self.chart.addAxis(
            axis_y,
            Qt.AlignLeft,
        )

        series.attachAxis(
            axis_x
        )

        series.attachAxis(
            axis_y
        )

        self.chart.setTitle(
            "Torverteilung nach Spielminuten"
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

        self.refresh_button.setEnabled(
            False
        )