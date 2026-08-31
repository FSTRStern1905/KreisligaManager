from __future__ import annotations

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QPercentBarSeries,
    QStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import (
    QGraphicsSimpleTextItem,
    QWidget,
)

from src.ui.charts.base_chart import BaseChart


class BaseBarChart(BaseChart):
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

        self.axis_x = QBarCategoryAxis()
        self.axis_y = QValueAxis()

        self._total_label_items: list[
            QGraphicsSimpleTextItem
        ] = []

        self._total_label_values: list[
            float
        ] = []

        self.setup_chart()

        self.chart.plotAreaChanged.connect(
            self._position_total_labels
        )

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

    def clear(
        self,
    ) -> None:
        self._clear_total_labels()

        self.clear_series()

        self.axis_x.clear()

        self.axis_y.setLabelFormat(
            "%.0f"
        )

        self.axis_y.setTitleText(
            self.y_axis_title
        )

        self.set_title(
            self.chart_title
        )

    def create_bar_series(
        self,
        name: str,
        values: list[float],
    ) -> QBarSeries:
        bar_set = QBarSet(
            name
        )

        for value in values:
            bar_set.append(
                float(value)
            )

        series = QBarSeries()

        series.append(
            bar_set
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

    def create_grouped_bar_series(
        self,
        sets: list[
            tuple[
                str,
                list[float],
            ]
        ],
        show_labels: bool = False,
    ) -> QBarSeries:
        series = QBarSeries()

        for (
            name,
            values,
        ) in sets:
            bar_set = QBarSet(
                name
            )

            for value in values:
                bar_set.append(
                    float(value)
                )

            series.append(
                bar_set
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

        series.setLabelsVisible(
            show_labels
        )

        return series

    def create_stacked_bar_series(
        self,
        sets: list[
            tuple[
                str,
                list[float],
            ]
        ],
        show_labels: bool = False,
    ) -> QStackedBarSeries:
        series = QStackedBarSeries()

        for (
            name,
            values,
        ) in sets:
            bar_set = QBarSet(
                name
            )

            for value in values:
                bar_set.append(
                    float(value)
                )

            if show_labels:
                bar_set.setLabel(
                    name
                )

            series.append(
                bar_set
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

        series.setLabelsVisible(
            show_labels
        )

        return series

    def create_percent_bar_series(
        self,
        sets: list[
            tuple[
                str,
                list[float],
            ]
        ],
        show_labels: bool = False,
    ) -> QPercentBarSeries:
        series = QPercentBarSeries()

        for (
            name,
            values,
        ) in sets:
            bar_set = QBarSet(
                name
            )

            for value in values:
                bar_set.append(
                    float(value)
                )

            series.append(
                bar_set
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

        series.setLabelsVisible(
            show_labels
        )

        self.axis_y.setRange(
            0.0,
            100.0,
        )

        self.axis_y.setLabelFormat(
            "%.0f %%"
        )

        self.axis_y.setTitleText(
            "Anteil"
        )

        return series

    def create_total_labels(
        self,
        values: list[float],
    ) -> None:
        self._clear_total_labels()

        if not values:
            return

        self._total_label_values = [
            float(value)
            for value in values
        ]

        for value in self._total_label_values:
            if float(value).is_integer():
                label_text = str(
                    int(value)
                )
            else:
                label_text = (
                    f"{value:.1f}"
                )

            label_item = (
                QGraphicsSimpleTextItem(
                    label_text,
                    self.chart,
                )
            )

            self._total_label_items.append(
                label_item
            )

        self._position_total_labels()

    def _position_total_labels(
        self,
        *_args,
    ) -> None:
        if not self._total_label_items:
            return

        if not self._total_label_values:
            return

        plot_area = (
            self.chart.plotArea()
        )

        if (
            plot_area.width() <= 0
            or plot_area.height() <= 0
        ):
            return

        category_count = len(
            self._total_label_values
        )

        if category_count <= 0:
            return

        minimum = float(
            self.axis_y.min()
        )

        maximum = float(
            self.axis_y.max()
        )

        value_range = (
            maximum
            - minimum
        )

        if value_range <= 0:
            return

        category_width = (
            plot_area.width()
            / category_count
        )

        for index, (
            label_item,
            value,
        ) in enumerate(
            zip(
                self._total_label_items,
                self._total_label_values,
            )
        ):
            normalized_value = (
                (
                    float(value)
                    - minimum
                )
                / value_range
            )

            normalized_value = max(
                0.0,
                min(
                    1.0,
                    normalized_value,
                ),
            )

            x_position = (
                plot_area.left()
                + category_width
                * (
                    index
                    + 0.5
                )
            )

            y_position = (
                plot_area.bottom()
                - (
                    normalized_value
                    * plot_area.height()
                )
            )

            bounding_rect = (
                label_item.boundingRect()
            )

            label_item.setPos(
                QPointF(
                    (
                        x_position
                        - bounding_rect.width()
                        / 2
                    ),
                    (
                        y_position
                        - bounding_rect.height()
                        - 4
                    ),
                )
            )

            label_item.setVisible(
                True
            )

    def _clear_total_labels(
        self,
    ) -> None:
        for label_item in (
            self._total_label_items
        ):
            label_item.setVisible(
                False
            )

            scene = (
                label_item.scene()
            )

            if scene is not None:
                scene.removeItem(
                    label_item
                )

        self._total_label_items.clear()
        self._total_label_values.clear()

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

        self._position_total_labels()

    def set_value_label_format(
        self,
        label_format: str,
    ) -> None:
        self.axis_y.setLabelFormat(
            label_format
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