from __future__ import annotations

from PySide6.QtCharts import QLineSeries, QScatterSeries, QValueAxis
from PySide6.QtCore import QPointF, QMargins, Qt
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import QWidget

from src.ui.charts.base_chart import BaseChart


class PointsProgressChart(BaseChart):
    BACKGROUND = "#20242a"
    TEXT = "#e8edf3"
    MUTED = "#9aa6b2"
    GRID = "#3a4149"
    LINE = "#4f8fc9"
    WIN = "#2f9e44"
    DRAW = "#d4a72c"
    LOSS = "#d94848"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()

        self.chart.setTitle("")
        self.chart.legend().hide()
        self.chart.setBackgroundVisible(True)
        self.chart.setBackgroundBrush(QColor(self.BACKGROUND))
        self.chart.setPlotAreaBackgroundVisible(False)
        self.chart.setMargins(QMargins(28, 8, 18, 8))

        self._setup_axis(self.axis_x, "Spieltag")
        self._setup_axis(self.axis_y, "Punkte")

        self.axis_x.setGridLineVisible(False)
        self.axis_y.setGridLineVisible(True)

        # Genug Platz für numerische Y-Achsenlabels reservieren.
        # Ohne Mindestbreite kürzt QtCharts die Werte bei engem Layout zu "..." ab.
        self.axis_y.setLabelsAngle(0)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.setMinimumHeight(300)
        self.clear()

    def _setup_axis(self, axis: QValueAxis, title: str) -> None:
        font = QFont("Segoe UI", 8)
        title_font = QFont("Segoe UI", 9)
        title_font.setBold(True)

        axis.setTitleText(title)
        axis.setTitleFont(title_font)
        axis.setTitleBrush(QColor(self.MUTED))
        axis.setLabelsFont(font)
        axis.setLabelsBrush(QColor(self.MUTED))
        axis.setLabelFormat("%.0f")
        axis.setMinorTickCount(0)
        axis.setLineVisible(False)

        grid_pen = QPen(QColor(self.GRID))
        grid_pen.setWidthF(0.7)
        axis.setGridLinePen(grid_pen)

    def clear(self) -> None:
        self.clear_series()
        self.axis_x.setRange(0.0, 1.0)
        self.axis_y.setRange(0.0, 3.0)
        self.axis_x.setTickType(QValueAxis.TickType.TicksDynamic)
        self.axis_y.setTickType(QValueAxis.TickType.TicksDynamic)
        self.axis_x.setTickAnchor(0.0)
        self.axis_y.setTickAnchor(0.0)
        self.axis_x.setTickInterval(1.0)
        self.axis_y.setTickInterval(5.0)

    def show_empty_chart(self, _message: str = "Keine Daten vorhanden") -> None:
        self.clear()

    def set_ranges(
        self,
        maximum_matchday: int,
        maximum_points: int,
    ) -> None:
        x_max = max(1, maximum_matchday)
        padding = max(3, round(maximum_points * 0.08))
        y_max = max(3, maximum_points + padding)

        self.axis_x.setRange(0.0, float(x_max))
        self.axis_y.setRange(0.0, float(y_max))

        x_interval = 1.0
        if maximum_matchday > 20:
            x_interval = 2.0
        if maximum_matchday > 36:
            x_interval = 3.0

        self.axis_x.setTickInterval(x_interval)
        self.axis_y.setTickInterval(5.0)

    def add_team(
        self,
        name: str,
        points: list[tuple[float, float]],
        single_team: bool,
        wins: list[tuple[float, float]] | None = None,
        draws: list[tuple[float, float]] | None = None,
        losses: list[tuple[float, float]] | None = None,
    ) -> None:
        line = QLineSeries()
        line.setName(name)

        for x_value, y_value in points:
            line.append(QPointF(float(x_value), float(y_value)))

        pen = QPen(QColor(self.LINE))
        pen.setWidthF(3.0 if single_team else 1.6)
        line.setPen(pen)

        self.chart.addSeries(line)
        line.attachAxis(self.axis_x)
        line.attachAxis(self.axis_y)

        if not single_team:
            return

        self._add_markers(wins or [], self.WIN, 10.0)
        self._add_markers(draws or [], self.DRAW, 10.0)
        self._add_markers(losses or [], self.LOSS, 10.0)

        if len(points) > 1:
            last = points[-1]
            self._add_markers([last], self.TEXT, 13.0)

    def _add_markers(
        self,
        points: list[tuple[float, float]],
        color: str,
        size: float,
    ) -> None:
        if not points:
            return

        series = QScatterSeries()
        series.setMarkerSize(size)
        series.setColor(QColor(color))
        series.setBorderColor(QColor(color))

        for x_value, y_value in points:
            series.append(QPointF(float(x_value), float(y_value)))

        self.chart.addSeries(series)
        series.attachAxis(self.axis_x)
        series.attachAxis(self.axis_y)
