from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCharts import QValueAxis
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.table_progress_service import (
    TableProgressService,
)
from src.services.statistics_service import (
    StatisticsService,
)
from src.ui.charts.base_line_chart import (
    BaseLineChart,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionProgressTab(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competition_id: int | None = None

        self.progress_data: list[dict] = []

        self._competition_changed = True

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        root_layout.setSpacing(
            10
        )

        title = QLabel(
            "📈 Saisonverlauf"
        )

        title.setObjectName(
            "PageTitle"
        )

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )

        self.info_label.setObjectName(
            "InfoLabel"
        )

        filter_layout = QHBoxLayout()

        filter_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        filter_label = QLabel(
            "Mannschaft:"
        )

        self.team_combo = QComboBox()

        self.team_combo.setMinimumWidth(
            280
        )

        self.team_combo.setEnabled(
            False
        )

        filter_layout.addWidget(
            filter_label
        )

        filter_layout.addWidget(
            self.team_combo
        )

        filter_layout.addStretch(
            1
        )

        self.refresh_button = QPushButton(
            "🔄 Verlauf aktualisieren"
        )

        self.refresh_button.setEnabled(
            False
        )

        filter_layout.addWidget(
            self.refresh_button
        )

        root_layout.addWidget(
            title
        )

        root_layout.addWidget(
            self.info_label
        )

        root_layout.addLayout(
            filter_layout
        )

        self.chart_tabs = QTabWidget()

        self.chart_tabs.setObjectName(
            "ProgressChartTabs"
        )

        self.chart_tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.points_page = QWidget()

        points_layout = QVBoxLayout(
            self.points_page
        )

        points_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        self.points_chart = BaseLineChart(
            title="Punkteentwicklung nach Spieltag",
            x_axis_title="Spieltag",
            y_axis_title="Punkte",
        )

        self.points_chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        points_layout.addWidget(
            self.points_chart,
            1,
        )

        self.position_page = QWidget()

        position_layout = QVBoxLayout(
            self.position_page
        )

        position_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        self.position_chart = BaseLineChart(
            title="Tabellenplatz nach Spieltag",
            x_axis_title="Spieltag",
            y_axis_title="Platz",
        )

        self.position_chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        position_layout.addWidget(
            self.position_chart,
            1,
        )

        self.chart_tabs.addTab(
            self.points_page,
            "📈 Punkteentwicklung",
        )

        self.chart_tabs.addTab(
            self.position_page,
            "📉 Platzierungsverlauf",
        )

        root_layout.addWidget(
            self.chart_tabs,
            1,
        )

    def connect_signals(
        self,
    ) -> None:
        self.refresh_button.clicked.connect(
            self.load_data
        )

        self.team_combo.currentIndexChanged.connect(
            self.team_filter_changed
        )

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        if competition_id != self.competition_id:
            self._competition_changed = True

        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        previous_team_id = (
            self.team_combo.currentData()
        )

        previous_index = (
            self.team_combo.currentIndex()
        )

        preserve_all_selection = (
            not self._competition_changed
            and previous_index == 0
            and self.team_combo.count() > 1
        )

        self.points_chart.clear()
        self.position_chart.clear()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            statistics_service = (
                StatisticsService(
                    connection
                )
            )

            progress_service = (
                TableProgressService(
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

            self.progress_data = (
                progress_service.get_table_progress(
                    self.competition_id
                )
            )

            self.populate_team_combo(
                selected_team_id=previous_team_id,
                preserve_all_selection=preserve_all_selection,
            )

            self.update_charts()

            matchdays = (
                progress_service.get_matchdays(
                    self.competition_id
                )
            )

            if matchdays:
                last_matchday = max(
                    matchdays
                )

                self.info_label.setText(
                    (
                        f"{competition_name} | "
                        f"Verlauf bis Spieltag "
                        f"{last_matchday}"
                    )
                )

            else:
                self.info_label.setText(
                    (
                        f"{competition_name} | "
                        "Keine abgeschlossenen "
                        "Spieltage"
                    )
                )

            self.refresh_button.setEnabled(
                True
            )

            self.team_combo.setEnabled(
                bool(
                    self.progress_data
                )
            )

            self._competition_changed = False

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Der Saisonverlauf "
                    "konnte nicht geladen "
                    f"werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def populate_team_combo(
        self,
        selected_team_id=None,
        preserve_all_selection: bool = False,
    ) -> None:
        self.team_combo.blockSignals(
            True
        )

        self.team_combo.clear()

        self.team_combo.addItem(
            "Alle Mannschaften",
            None,
        )

        teams = sorted(
            self.progress_data,
            key=lambda team: (
                (
                    team.get(
                        "current_position"
                    )
                    if team.get(
                        "current_position"
                    ) is not None
                    else 9999
                ),
                str(
                    team.get(
                        "team_name",
                        "",
                    )
                ).casefold(),
            ),
        )

        for team in teams:
            team_id = team.get(
                "team_id"
            )

            team_name = team.get(
                "team_name",
                "Unbekannt",
            )

            position = team.get(
                "current_position"
            )

            if position is not None:
                display_text = (
                    f"{position}. {team_name}"
                )
            else:
                display_text = str(
                    team_name
                )

            self.team_combo.addItem(
                display_text,
                team_id,
            )

        selected_index = -1

        if selected_team_id is not None:
            for index in range(
                self.team_combo.count()
            ):
                if (
                    self.team_combo.itemData(
                        index
                    )
                    == selected_team_id
                ):
                    selected_index = index
                    break

        if selected_index >= 0:
            self.team_combo.setCurrentIndex(
                selected_index
            )

        elif preserve_all_selection:
            self.team_combo.setCurrentIndex(
                0
            )

        elif self.team_combo.count() > 1:
            self.team_combo.setCurrentIndex(
                1
            )

        else:
            self.team_combo.setCurrentIndex(
                0
            )

        self.team_combo.blockSignals(
            False
        )

    def team_filter_changed(
        self,
        _index: int,
    ) -> None:
        self.update_charts()

    def get_filtered_progress(
        self,
    ) -> list[dict]:
        selected_team_id = (
            self.team_combo.currentData()
        )

        if selected_team_id is None:
            return self.progress_data

        return [
            team
            for team in self.progress_data
            if team.get(
                "team_id"
            )
            == selected_team_id
        ]

    def update_charts(
        self,
    ) -> None:
        progress = (
            self.get_filtered_progress()
        )

        self.show_points_progress(
            progress
        )

        self.show_position_progress(
            progress
        )

    def show_points_progress(
        self,
        progress: list[dict],
    ) -> None:
        self.points_chart.clear()

        if not progress:
            self.points_chart.show_empty_chart(
                "Keine Punkteentwicklung vorhanden"
            )
            return

        maximum_matchday = 0
        maximum_points = 0
        series_count = 0

        for team in progress:
            points_progress = team.get(
                "points_progress",
                [],
            )

            if not points_progress:
                continue

            points: list[
                tuple[
                    float,
                    float,
                ]
            ] = [
                (
                    0.0,
                    0.0,
                )
            ]

            for row in points_progress:
                matchday = int(
                    row["matchday"]
                )

                team_points = int(
                    row["points"]
                )

                points.append(
                    (
                        float(matchday),
                        float(team_points),
                    )
                )

                maximum_matchday = max(
                    maximum_matchday,
                    matchday,
                )

                maximum_points = max(
                    maximum_points,
                    team_points,
                )

            self.points_chart.create_line_series(
                name=team["team_name"],
                points=points,
                show_points=True,
            )

            series_count += 1

        if series_count == 0:
            self.points_chart.show_empty_chart(
                "Keine Punkteentwicklung vorhanden"
            )
            return

        self.points_chart.set_x_range(
            0,
            max(
                1,
                maximum_matchday,
            ),
        )

        self.points_chart.set_x_tick_interval(
            1
        )

        padding = max(
            3,
            round(
                maximum_points * 0.08
            ),
        )

        self.points_chart.set_y_range(
            0,
            max(
                3,
                maximum_points + padding,
            ),
        )

        self.points_chart.set_y_tick_interval(
            5
        )

        self.points_chart.restore_chart_title()

    def show_position_progress(
        self,
        progress: list[dict],
    ) -> None:
        self.position_chart.clear()

        if not progress:
            self.position_chart.show_empty_chart(
                "Kein Platzierungsverlauf vorhanden"
            )
            return

        maximum_matchday = 0

        team_count = len(
            self.progress_data
        )

        series_count = 0

        for team in progress:
            positions = team.get(
                "positions",
                [],
            )

            if not positions:
                continue

            points: list[
                tuple[
                    float,
                    float,
                ]
            ] = []

            for row in positions:
                matchday = int(
                    row["matchday"]
                )

                position = int(
                    row["position"]
                )

                points.append(
                    (
                        float(matchday),
                        float(position),
                    )
                )

                maximum_matchday = max(
                    maximum_matchday,
                    matchday,
                )

            self.position_chart.create_line_series(
                name=team["team_name"],
                points=points,
                show_points=True,
            )

            series_count += 1

        if series_count == 0:
            self.position_chart.show_empty_chart(
                "Kein Platzierungsverlauf vorhanden"
            )
            return

        self.position_chart.set_x_range(
            1,
            max(
                2,
                maximum_matchday,
            ),
        )

        self.position_chart.set_x_tick_interval(
            1
        )

        maximum_position = max(
            2,
            team_count,
        )

        self.position_chart.set_y_range(
            1,
            maximum_position,
        )

        self.position_chart.axis_y.setLabelFormat(
            "%d"
        )

        self.position_chart.axis_y.setTickType(
            QValueAxis.TickType.TicksDynamic
        )

        self.position_chart.axis_y.setTickAnchor(
            1.0
        )

        self.position_chart.axis_y.setTickInterval(
            1.0
        )

        self.position_chart.axis_y.setMinorTickCount(
            0
        )

        self.position_chart.set_y_axis_reversed(
            True
        )

        self.position_chart.restore_chart_title()

    def refresh(
        self,
    ) -> None:
        self.load_data()

    def clear_data(
        self,
    ) -> None:
        self.progress_data = []

        self._competition_changed = True

        self.team_combo.blockSignals(
            True
        )

        self.team_combo.clear()

        self.team_combo.addItem(
            "Alle Mannschaften",
            None,
        )

        self.team_combo.setCurrentIndex(
            0
        )

        self.team_combo.blockSignals(
            False
        )

        self.team_combo.setEnabled(
            False
        )

        self.points_chart.show_empty_chart(
            "Keine Daten"
        )

        self.position_chart.show_empty_chart(
            "Keine Daten"
        )

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(
            False
        )