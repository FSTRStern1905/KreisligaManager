import sqlite3
from pathlib import Path

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
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

from src.services.statistics.points_progress_service import (
    PointsProgressService,
)
from src.services.statistics_service import (
    StatisticsService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionPointsProgressTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📈 Punkteverlauf")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.chart = QChart()
        self.chart.setTitle(
            "Punkte nach Spieltagen"
        )
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(
            Qt.AlignBottom
        )

        self.chart_view = QChartView(
            self.chart
        )
        self.chart_view.setRenderHint(
            QPainter.Antialiasing
        )

        self.refresh_button = QPushButton(
            "🔄 Punkteverlauf aktualisieren"
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

            progress_service = (
                PointsProgressService(
                    connection
                )
            )

            competition_name = (
                statistics_service.get_competition_name(
                    self.competition_id
                )
            )

            if competition_name is None:
                self.clear_data()
                return

            teams = (
                progress_service.get_points_progress(
                    self.competition_id
                )
            )

            matchdays = (
                progress_service.get_matchdays(
                    self.competition_id
                )
            )

            self.show_chart(
                teams=teams,
                matchdays=matchdays,
            )

            self.info_label.setText(
                f"{competition_name} | "
                f"{len(teams)} Mannschaften | "
                f"{len(matchdays)} Spieltage"
            )

            self.refresh_button.setEnabled(True)

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Fehler",
                (
                    "Der Punkteverlauf konnte "
                    "nicht geladen werden:\n"
                    f"{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_chart(
        self,
        teams: list[dict],
        matchdays: list[int],
    ):
        self.clear_chart()

        if not teams or not matchdays:
            self.chart.setTitle(
                "Keine Spieldaten vorhanden"
            )
            return

        maximum_points = 0

        for team in teams:
            series = QLineSeries()
            series.setName(
                team["team_name"]
            )

            for entry in team["progress"]:
                matchday = entry["matchday"]
                points = entry["points"]

                series.append(
                    float(matchday),
                    float(points),
                )

                maximum_points = max(
                    maximum_points,
                    points,
                )

            self.chart.addSeries(series)

        x_axis = QValueAxis()
        x_axis.setTitleText("Spieltag")
        x_axis.setLabelFormat("%d")
        x_axis.setTickInterval(1)
        x_axis.setRange(
            0,
            max(matchdays),
        )

        y_axis = QValueAxis()
        y_axis.setTitleText("Punkte")
        y_axis.setLabelFormat("%d")
        y_axis.setTickInterval(5)
        y_axis.setRange(
            0,
            self.calculate_axis_maximum(
                maximum_points
            ),
        )

        self.chart.addAxis(
            x_axis,
            Qt.AlignBottom,
        )

        self.chart.addAxis(
            y_axis,
            Qt.AlignLeft,
        )

        for series in self.chart.series():
            series.attachAxis(x_axis)
            series.attachAxis(y_axis)

        self.chart.setTitle(
            "Punkteverlauf nach Spieltagen"
        )

    def calculate_axis_maximum(
        self,
        maximum_points: int,
    ) -> int:
        if maximum_points <= 0:
            return 5

        remainder = maximum_points % 5

        if remainder == 0:
            return maximum_points + 5

        return maximum_points + (
            5 - remainder
        )

    def clear_chart(self):
        self.chart.removeAllSeries()

        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.clear_chart()

        self.chart.setTitle(
            "Keine Daten geladen"
        )

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(False)