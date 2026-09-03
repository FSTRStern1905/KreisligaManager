from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCharts import (
    QCategoryAxis,
    QLineSeries,
    QScatterSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.charts.base_bar_chart import (
    BaseBarChart,
)
from src.ui.charts.base_chart import BaseChart


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class DevelopmentLineChart(BaseChart):
    def __init__(
        self,
        title: str,
        y_axis_title: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.chart_title = title
        self.y_axis_title = y_axis_title

        self.axis_x = QCategoryAxis()
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

        self.axis_x.setTitleText(
            "Saison"
        )
        self.axis_x.setLabelsPosition(
            QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue
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

        self.axis_x.setRange(
            0,
            1,
        )
        self.axis_y.setRange(
            1,
            5,
        )
        self.axis_y.setReverse(
            True
        )

    def clear_data(
        self,
    ) -> None:
        self.clear_series()
        self._clear_x_categories()

        self.set_title(
            "Keine Daten vorhanden."
        )

        self.axis_x.setRange(
            0,
            1,
        )
        self.axis_y.setRange(
            1,
            5,
        )
        self.axis_y.setReverse(
            True
        )

    def set_league_history(
        self,
        categories: list[str],
        values: list[float],
    ) -> None:
        self.clear_series()
        self._clear_x_categories()

        if (
            not categories
            or not values
            or len(categories) != len(values)
        ):
            self.clear_data()
            return

        self.set_title(
            self.chart_title
        )

        for index, season_name in enumerate(
            categories
        ):
            self.axis_x.append(
                str(
                    season_name
                ),
                float(index),
            )

        max_index = max(
            1,
            len(values) - 1,
        )

        self.axis_x.setRange(
            0,
            float(max_index),
        )

        self.axis_y.setRange(
            1,
            5,
        )
        self.axis_y.setReverse(
            True
        )

        line_series = QLineSeries()
        line_series.setName(
            "Ligaverlauf"
        )

        line_pen = QPen(
            QColor(
                "#299ED9"
            )
        )
        line_pen.setWidthF(
            3.0
        )
        line_series.setPen(
            line_pen
        )

        promotion_series = QScatterSeries()
        promotion_series.setName(
            "Aufstieg"
        )
        promotion_series.setMarkerSize(
            11.0
        )
        promotion_series.setColor(
            QColor(
                "#2E9B4B"
            )
        )
        promotion_series.setBorderColor(
            QColor(
                "#2E9B4B"
            )
        )

        relegation_series = QScatterSeries()
        relegation_series.setName(
            "Abstieg"
        )
        relegation_series.setMarkerSize(
            11.0
        )
        relegation_series.setColor(
            QColor(
                "#D63B3B"
            )
        )
        relegation_series.setBorderColor(
            QColor(
                "#D63B3B"
            )
        )

        stable_series = QScatterSeries()
        stable_series.setName(
            "Ligastufe gehalten"
        )
        stable_series.setMarkerSize(
            8.0
        )
        stable_series.setColor(
            QColor(
                "#299ED9"
            )
        )
        stable_series.setBorderColor(
            QColor(
                "#299ED9"
            )
        )

        for index, value in enumerate(
            values
        ):
            x_value = float(
                index
            )
            y_value = float(
                value
            )

            line_series.append(
                x_value,
                y_value,
            )

            if index == 0:
                stable_series.append(
                    x_value,
                    y_value,
                )
                continue

            previous_value = float(
                values[
                    index - 1
                ]
            )

            if y_value < previous_value:
                promotion_series.append(
                    x_value,
                    y_value,
                )
            elif y_value > previous_value:
                relegation_series.append(
                    x_value,
                    y_value,
                )
            else:
                stable_series.append(
                    x_value,
                    y_value,
                )

        for series in (
            line_series,
            promotion_series,
            relegation_series,
            stable_series,
        ):
            self.chart.addSeries(
                series
            )
            series.attachAxis(
                self.axis_x
            )
            series.attachAxis(
                self.axis_y
            )

        if promotion_series.count() == 0:
            self.chart.removeSeries(
                promotion_series
            )

        if relegation_series.count() == 0:
            self.chart.removeSeries(
                relegation_series
            )

        if stable_series.count() == 0:
            self.chart.removeSeries(
                stable_series
            )

    def _clear_x_categories(
        self,
    ) -> None:
        labels = list(
            self.axis_x.categoriesLabels()
        )

        for label in labels:
            self.axis_x.remove(
                label
            )


class CompetitionTeamDevelopmentTab(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competition_id: int | None = None
        self.team_rows: list[sqlite3.Row] = []

        self.setup_ui()

    def setup_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(
            8
        )

        selector_layout = QHBoxLayout()
        selector_layout.addStretch()

        selector_layout.addWidget(
            QLabel(
                "Mannschaft:"
            )
        )

        self.team_combo = QComboBox()
        self.team_combo.setMinimumWidth(
            280
        )

        selector_layout.addWidget(
            self.team_combo
        )

        layout.addLayout(
            selector_layout
        )

        self.tabs = QTabWidget()

        self.league_tab = QWidget()
        self.attendance_tab = QWidget()

        self.setup_league_tab()
        self.setup_attendance_tab()

        self.tabs.addTab(
            self.league_tab,
            "Ligaentwicklung",
        )
        self.tabs.addTab(
            self.attendance_tab,
            "Zuschauer",
        )

        layout.addWidget(
            self.tabs,
            1,
        )

        self.team_combo.currentIndexChanged.connect(
            self.team_changed
        )

    def setup_league_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.league_tab
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.league_chart = DevelopmentLineChart(
            title="Ligaentwicklung",
            y_axis_title="Ligastufe",
        )

        layout.addWidget(
            self.league_chart
        )

    def setup_attendance_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.attendance_tab
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.attendance_chart = BaseBarChart(
            title="Zuschauerentwicklung",
            x_axis_title="Saison",
            y_axis_title="Zuschauer-Ø",
        )

        self.attendance_chart.show_legend(
            False
        )

        layout.addWidget(
            self.attendance_chart
        )

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        self.competition_id = competition_id
        self.load_data()

    def refresh(
        self,
    ) -> None:
        self.load_data()

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )
        connection.row_factory = sqlite3.Row

        try:
            competition = connection.execute(
                """
                SELECT
                    competition_id,
                    season_id
                FROM competitions
                WHERE competition_id = ?
                LIMIT 1;
                """,
                (
                    self.competition_id,
                ),
            ).fetchone()

            if competition is None:
                self.clear_data()
                return

            teams = connection.execute(
                """
                SELECT
                    teams.team_id,
                    teams.name
                FROM competition_teams
                INNER JOIN teams
                    ON teams.team_id =
                       competition_teams.team_id
                WHERE
                    competition_teams.competition_id = ?
                ORDER BY
                    teams.name COLLATE NOCASE;
                """,
                (
                    self.competition_id,
                ),
            ).fetchall()

            previous_team_id = (
                self.team_combo.currentData()
            )

            self.team_combo.blockSignals(
                True
            )
            self.team_combo.clear()

            for team in teams:
                self.team_combo.addItem(
                    str(
                        team["name"]
                    ),
                    int(
                        team["team_id"]
                    ),
                )

            if previous_team_id is not None:
                for index in range(
                    self.team_combo.count()
                ):
                    if (
                        self.team_combo.itemData(
                            index
                        )
                        == previous_team_id
                    ):
                        self.team_combo.setCurrentIndex(
                            index
                        )
                        break

            self.team_combo.blockSignals(
                False
            )

        finally:
            connection.close()

        self.load_selected_team()

    def team_changed(
        self,
        index: int,
    ) -> None:
        if index < 0:
            return

        self.load_selected_team()

    def load_selected_team(
        self,
    ) -> None:
        team_id = self.team_combo.currentData()

        if team_id is None:
            self.clear_charts()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(
                """
                SELECT
                    seasons.season_id,
                    seasons.name AS season_name,
                    seasons.start_date,
                    leagues.name AS league_name,
                    leagues.level AS league_level,
                    competitions.competition_id,
                    standings.position,
                    standings.played,
                    standings.points,
                    standings.goals_for,
                    standings.goals_against,
                    team_season_metrics.average_attendance,
                    team_season_metrics.goalkeeper_strength,
                    team_season_metrics.defense_strength,
                    team_season_metrics.midfield_strength,
                    team_season_metrics.attack_strength,
                    team_season_metrics.overall_strength
                FROM competition_teams
                INNER JOIN competitions
                    ON competitions.competition_id =
                       competition_teams.competition_id
                INNER JOIN seasons
                    ON seasons.season_id =
                       competitions.season_id
                INNER JOIN leagues
                    ON leagues.league_id =
                       competitions.league_id
                LEFT JOIN standings
                    ON standings.competition_id =
                       competitions.competition_id
                    AND standings.team_id =
                        competition_teams.team_id
                LEFT JOIN team_season_metrics
                    ON team_season_metrics.competition_id =
                       competitions.competition_id
                    AND team_season_metrics.team_id =
                        competition_teams.team_id
                WHERE
                    competition_teams.team_id = ?
                ORDER BY
                    seasons.start_date,
                    seasons.season_id;
                """,
                (
                    int(
                        team_id
                    ),
                ),
            ).fetchall()

        finally:
            connection.close()

        self.team_rows = list(
            rows
        )

        self.populate_charts()

    def populate_charts(
        self,
    ) -> None:
        if not self.team_rows:
            self.clear_charts()
            return

        categories = [
            str(
                row["season_name"]
            )
            for row in self.team_rows
        ]

        league_values = [
            float(
                row["league_level"]
                if row["league_level"] is not None
                else 0
            )
            for row in self.team_rows
        ]

        attendance_values = [
            float(
                row["average_attendance"]
                if row["average_attendance"] is not None
                else 0
            )
            for row in self.team_rows
        ]

        self.populate_league_chart(
            categories=categories,
            values=league_values,
        )

        self.populate_attendance_chart(
            categories=categories,
            values=attendance_values,
        )

    def populate_league_chart(
        self,
        categories: list[str],
        values: list[float],
    ) -> None:
        self.league_chart.set_league_history(
            categories=categories,
            values=values,
        )

    def populate_attendance_chart(
        self,
        categories: list[str],
        values: list[float],
    ) -> None:
        self.attendance_chart.clear()

        self.attendance_chart.set_categories(
            categories
        )

        self.attendance_chart.create_bar_series(
            name="Zuschauer-Ø",
            values=values,
        )

        self.attendance_chart.create_total_labels(
            values
        )

        maximum = max(
            values
        )

        self.attendance_chart.set_value_range(
            minimum=0,
            maximum=max(
                1,
                maximum * 1.15,
            ),
        )

        self.attendance_chart.restore_chart_title()

    def clear_charts(
        self,
    ) -> None:
        self.league_chart.clear_data()
        self.attendance_chart.show_empty_chart(
            "Keine historischen Zuschauerdaten"
        )

    def clear_data(
        self,
    ) -> None:
        self.team_rows = []

        self.team_combo.blockSignals(
            True
        )
        self.team_combo.clear()
        self.team_combo.blockSignals(
            False
        )

        self.clear_charts()
