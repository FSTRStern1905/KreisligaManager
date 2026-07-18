from PySide6.QtCharts import (
    QChart,
    QChartView,
)
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)


class BaseChart(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.chart = QChart()

        self.chart_view = QChartView(
            self.chart
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(0)

        self.chart_view.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        layout.addWidget(
            self.chart_view
        )

    def clear_series(self) -> None:
        for series in list(
            self.chart.series()
        ):
            self.chart.removeSeries(
                series
            )

    def clear_axes(self) -> None:
        for axis in list(
            self.chart.axes()
        ):
            self.chart.removeAxis(
                axis
            )

    def clear(self) -> None:
        self.clear_series()
        self.clear_axes()

    def set_title(
        self,
        title: str,
    ) -> None:
        self.chart.setTitle(
            title
        )

    def show_legend(
        self,
        visible: bool = True,
    ) -> None:
        self.chart.legend().setVisible(
            visible
        )