from PySide6.QtCharts import (
    QLineSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from src.ui.charts.base_chart import BaseChart


class BaseLineChart(BaseChart):
    def __init__(
        self,
        title: str,
        x_axis_title: str,
        y_axis_title: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.chart_title = title
        self.x_axis_title = x_axis_title
        self.y_axis_title = y_axis_title

        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()

        self.setup_chart()

    def setup_chart(self) -> None:
        self.set_title(
            self.chart_title
        )

        self.show_legend(
            True
        )

        self.chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        self.axis_x.setTitleText(
            self.x_axis_title
        )
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTickType(
            QValueAxis.TickType.TicksDynamic
        )
        self.axis_x.setTickAnchor(1)
        self.axis_x.setTickInterval(1)

        self.axis_y.setTitleText(
            self.y_axis_title
        )
        self.axis_y.setLabelFormat("%d")
        self.axis_y.setTickType(
            QValueAxis.TickType.TicksDynamic
        )
        self.axis_y.setTickAnchor(0)
        self.axis_y.setTickInterval(1)

        self.chart.addAxis(
            self.axis_x,
            Qt.AlignmentFlag.AlignBottom,
        )

        self.chart.addAxis(
            self.axis_y,
            Qt.AlignmentFlag.AlignLeft,
        )

        self.set_axis_ranges(
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=1,
        )

    def clear(self) -> None:
        self.clear_series()
        self.restore_chart_title()

    def create_line_series(
        self,
        name: str,
        points: list[
            tuple[float, float]
        ],
    ) -> QLineSeries:
        series = QLineSeries()
        series.setName(name)

        for x_value, y_value in points:
            series.append(
                float(x_value),
                float(y_value),
            )

        self.chart.addSeries(
            series
        )

        series.attachAxis(
            self.axis_x
        )

        series.attachAxis(
            self.axis_y
        )

        return series

    def set_axis_ranges(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
    ) -> None:
        if x_min == x_max:
            x_max = x_min + 1

        if y_min == y_max:
            y_max = y_min + 1

        self.axis_x.setRange(
            float(x_min),
            float(x_max),
        )

        self.axis_y.setRange(
            float(y_min),
            float(y_max),
        )

    def set_axis_tick_intervals(
        self,
        x_interval: float = 1,
        y_interval: float = 1,
    ) -> None:
        self.axis_x.setTickInterval(
            float(x_interval)
        )

        self.axis_y.setTickInterval(
            float(y_interval)
        )

    def set_chart_title(
        self,
        title: str,
    ) -> None:
        self.chart_title = title

        self.set_title(
            title
        )

    def restore_chart_title(
        self,
    ) -> None:
        self.set_title(
            self.chart_title
        )

    def set_legend_visible(
        self,
        visible: bool,
    ) -> None:
        self.show_legend(
            visible
        )

    def set_y_axis_reversed(
        self,
        reversed_axis: bool,
    ) -> None:
        self.axis_y.setReverse(
            reversed_axis
        )

    def show_empty_chart(
        self,
        message: str = "Keine Daten vorhanden.",
    ) -> None:
        self.clear_series()

        self.set_title(
            message
        )

        self.set_axis_ranges(
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=1,
        )