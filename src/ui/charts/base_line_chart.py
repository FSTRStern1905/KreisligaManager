from __future__ import annotations

from PySide6.QtCharts import (
    QLineSeries,
    QScatterSeries,
    QValueAxis,
)
from PySide6.QtCore import QPointF, QMargins, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QWidget

from src.ui.charts.base_chart import BaseChart


class BaseLineChart(BaseChart):
    def __init__(
        self,
        title: str,
        x_axis_title: str,
        y_axis_title: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.chart_title = title
        self.x_axis_title = x_axis_title
        self.y_axis_title = y_axis_title

        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()

        self.setup_chart()

    def setup_chart(
        self,
    ) -> None:
        self.set_title(
            self.chart_title
        )

        self.show_legend(
            True
        )

        self.chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        self.chart.setMargins(
            QMargins(
                24,
                10,
                24,
                10,
            )
        )

        self.setup_axes()

        self.chart.addAxis(
            self.axis_x,
            Qt.AlignmentFlag.AlignBottom,
        )

        self.chart.addAxis(
            self.axis_y,
            Qt.AlignmentFlag.AlignLeft,
        )

        self.set_x_range(
            0,
            1,
        )

        self.set_y_range(
            0,
            1,
        )

    def setup_axes(
        self,
    ) -> None:
        label_font = QFont()

        label_font.setFamily(
            "Segoe UI"
        )

        label_font.setPointSize(
            9
        )

        title_font = QFont()

        title_font.setFamily(
            "Segoe UI"
        )

        title_font.setPointSize(
            9
        )

        title_font.setBold(
            True
        )

        self.axis_x.setTitleText(
            self.x_axis_title
        )

        self.axis_y.setTitleText(
            self.y_axis_title
        )

        self.axis_x.setTitleFont(
            title_font
        )

        self.axis_y.setTitleFont(
            title_font
        )

        self.axis_x.setLabelsFont(
            label_font
        )

        self.axis_y.setLabelsFont(
            label_font
        )

        self.axis_x.setLabelsVisible(
            True
        )

        self.axis_y.setLabelsVisible(
            True
        )

        self.axis_x.setLabelsAngle(
            0
        )

        self.axis_y.setLabelsAngle(
            0
        )

        self.axis_x.setLabelFormat(
            "%.0f"
        )

        self.axis_y.setLabelFormat(
            "%.0f"
        )

        self.axis_x.setTickType(
            QValueAxis.TickType.TicksDynamic
        )

        self.axis_x.setTickAnchor(
            0.0
        )

        self.axis_x.setTickInterval(
            1.0
        )

        self.axis_y.setTickType(
            QValueAxis.TickType.TicksDynamic
        )

        self.axis_y.setTickAnchor(
            0.0
        )

        self.axis_y.setTickInterval(
            1.0
        )

        self.axis_x.setMinorTickCount(
            0
        )

        self.axis_y.setMinorTickCount(
            0
        )

        if hasattr(
            self.axis_x,
            "setTruncateLabels",
        ):
            self.axis_x.setTruncateLabels(
                False
            )

        if hasattr(
            self.axis_y,
            "setTruncateLabels",
        ):
            self.axis_y.setTruncateLabels(
                False
            )

    def clear(
        self,
    ) -> None:
        self.clear_series()

        self.axis_x.setReverse(
            False
        )

        self.axis_y.setReverse(
            False
        )

        self.axis_x.setLabelsVisible(
            True
        )

        self.axis_y.setLabelsVisible(
            True
        )

        self.axis_x.setLabelsAngle(
            0
        )

        self.axis_y.setLabelsAngle(
            0
        )

        self.axis_x.setLabelFormat(
            "%.0f"
        )

        self.axis_y.setLabelFormat(
            "%.0f"
        )

        self.axis_x.setTitleText(
            self.x_axis_title
        )

        self.axis_y.setTitleText(
            self.y_axis_title
        )

        if hasattr(
            self.axis_x,
            "setTruncateLabels",
        ):
            self.axis_x.setTruncateLabels(
                False
            )

        if hasattr(
            self.axis_y,
            "setTruncateLabels",
        ):
            self.axis_y.setTruncateLabels(
                False
            )

        self.set_title(
            self.chart_title
        )

    def create_line_series(
        self,
        name: str,
        points: list[
            tuple[
                float,
                float,
            ]
        ],
        show_points: bool = True,
    ) -> QLineSeries:
        series = QLineSeries()

        series.setName(
            name
        )

        for x_value, y_value in points:
            series.append(
                QPointF(
                    float(x_value),
                    float(y_value),
                )
            )

        series.setPointsVisible(
            show_points
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

    def create_scatter_series(
        self,
        name: str,
        points: list[
            tuple[
                float,
                float,
            ]
        ],
        color: str,
        marker_size: float = 9.0,
    ) -> QScatterSeries:
        series = QScatterSeries()

        series.setName(
            name
        )

        series.setMarkerSize(
            float(marker_size)
        )

        series.setColor(
            QColor(color)
        )

        series.setBorderColor(
            QColor(color)
        )

        for x_value, y_value in points:
            series.append(
                QPointF(
                    float(x_value),
                    float(y_value),
                )
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

    def set_x_range(
        self,
        minimum: float,
        maximum: float,
    ) -> None:
        if minimum == maximum:
            maximum += 1

        self.axis_x.setRange(
            float(minimum),
            float(maximum),
        )

    def set_y_range(
        self,
        minimum: float,
        maximum: float,
    ) -> None:
        if minimum == maximum:
            maximum += 1

        self.axis_y.setRange(
            float(minimum),
            float(maximum),
        )

    def set_x_tick_interval(
        self,
        interval: float,
    ) -> None:
        if interval <= 0:
            return

        self.axis_x.setTickType(
            QValueAxis.TickType.TicksDynamic
        )

        self.axis_x.setTickAnchor(
            0.0
        )

        self.axis_x.setTickInterval(
            float(interval)
        )

        self.axis_x.setMinorTickCount(
            0
        )

    def set_y_tick_interval(
        self,
        interval: float,
    ) -> None:
        if interval <= 0:
            return

        self.axis_y.setTickType(
            QValueAxis.TickType.TicksDynamic
        )

        self.axis_y.setTickAnchor(
            0.0
        )

        self.axis_y.setTickInterval(
            float(interval)
        )

        self.axis_y.setMinorTickCount(
            0
        )

    def set_y_axis_reversed(
        self,
        reversed_axis: bool,
    ) -> None:
        self.axis_y.setReverse(
            reversed_axis
        )

    def set_x_axis_reversed(
        self,
        reversed_axis: bool,
    ) -> None:
        self.axis_x.setReverse(
            reversed_axis
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

    def show_empty_chart(
        self,
        message: str = "Keine Daten vorhanden.",
    ) -> None:
        self.clear()

        self.set_title(
            message
        )

        self.set_x_range(
            0,
            1,
        )

        self.set_y_range(
            0,
            1,
        )