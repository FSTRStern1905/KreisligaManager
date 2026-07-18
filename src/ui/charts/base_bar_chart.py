from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from src.ui.charts.base_chart import BaseChart


class BaseBarChart(BaseChart):
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

        self.axis_x = QBarCategoryAxis()
        self.axis_y = QValueAxis()

        self.setup_chart()

    def setup_chart(self) -> None:
        self.set_title(
            self.chart_title
        )

        self.show_legend(True)

        self.chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        self.axis_x.setTitleText(
            self.x_axis_title
        )

        self.axis_y.setTitleText(
            self.y_axis_title
        )

        self.axis_y.setLabelFormat(
            "%.0f"
        )

        self.chart.addAxis(
            self.axis_x,
            Qt.AlignmentFlag.AlignBottom,
        )

        self.chart.addAxis(
            self.axis_y,
            Qt.AlignmentFlag.AlignLeft,
        )

        self.set_value_range(
            0,
            1,
        )

    def clear(self) -> None:
        self.clear_series()

        self.axis_x.clear()

        self.set_title(
            self.chart_title
        )

    def create_bar_series(
        self,
        name: str,
        values: list[float],
    ) -> QBarSeries:

        bar_set = QBarSet(name)

        for value in values:
            bar_set.append(
                float(value)
            )

        series = QBarSeries()
        series.append(bar_set)

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

    def set_categories(
        self,
        categories: list[str],
    ) -> None:
        self.axis_x.clear()

        self.axis_x.append(
            categories
        )

    def set_value_range(
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
        self.clear()

        self.set_title(
            message
        )

        self.set_value_range(
            0,
            1,
        )