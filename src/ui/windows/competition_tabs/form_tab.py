from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.form_service import (
    FormService,
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


class CompetitionFormTab(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competition_id: int | None = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        title = QLabel(
            "📈 Formtabelle"
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

        root_layout.addWidget(
            title
        )

        root_layout.addWidget(
            self.info_label
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        content_widget = QWidget()

        content_layout = QVBoxLayout(
            content_widget
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            16
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            10
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Mannschaft",
                "Sp",
                "S",
                "U",
                "N",
                "Tore",
                "Diff",
                "Pkt",
                "Form",
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setMinimumHeight(
            420
        )

        header = (
            self.table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(
            2,
            9,
        ):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            9,
            QHeaderView.ResizeMode.Fixed,
        )

        self.table.setColumnWidth(
            9,
            190,
        )

        content_layout.addWidget(
            self.table
        )

        points_title = QLabel(
            "📈 Punkteentwicklung"
        )

        points_title.setObjectName(
            "SectionTitle"
        )

        content_layout.addWidget(
            points_title
        )

        self.points_chart = BaseLineChart(
            title="Punkteentwicklung nach Spieltag",
            x_axis_title="Spieltag",
            y_axis_title="Punkte",
        )

        self.points_chart.setMinimumHeight(
            430
        )

        content_layout.addWidget(
            self.points_chart
        )

        self.scroll_area.setWidget(
            content_widget
        )

        root_layout.addWidget(
            self.scroll_area,
            1,
        )

        self.refresh_button = QPushButton(
            "🔄 Form aktualisieren"
        )

        self.refresh_button.setEnabled(
            False
        )

        root_layout.addWidget(
            self.refresh_button
        )

    def connect_signals(
        self,
    ) -> None:
        self.refresh_button.clicked.connect(
            self.load_data
        )

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(
        self,
    ) -> None:
        self.table.setRowCount(
            0
        )

        self.points_chart.clear()

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            statistics_service = (
                StatisticsService(
                    connection
                )
            )

            form_service = FormService(
                connection
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

            standings = (
                form_service.get_form_table(
                    competition_id=self.competition_id,
                    matches=5,
                )
            )

            progress = (
                progress_service.get_table_progress(
                    self.competition_id
                )
            )

            self.show_standings(
                standings
            )

            self.show_points_progress(
                progress
            )

            self.info_label.setText(
                (
                    f"{competition_name} | "
                    "Letzte 5 Spiele"
                )
            )

            self.refresh_button.setEnabled(
                True
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die Formdaten "
                    "konnten nicht geladen "
                    f"werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_standings(
        self,
        standings: list[dict],
    ) -> None:
        self.table.setRowCount(
            len(standings)
        )

        for row_index, team in enumerate(
            standings
        ):
            goal_text = (
                f"{team['goals_for']}:"
                f"{team['goals_against']}"
            )

            goal_difference = (
                f"+{team['goal_difference']}"
                if team["goal_difference"] > 0
                else str(
                    team["goal_difference"]
                )
            )

            values = [
                row_index + 1,
                team["team_name"],
                team["played"],
                team["wins"],
                team["draws"],
                team["losses"],
                goal_text,
                goal_difference,
                team["points"],
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                if column_index != 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    team["team_id"],
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

            form_widget = (
                self._create_form_widget(
                    team.get(
                        "form",
                        [],
                    )
                )
            )

            self.table.setCellWidget(
                row_index,
                9,
                form_widget,
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
            ] = []

            points.append(
                (
                    0.0,
                    0.0,
                )
            )

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

        point_padding = max(
            3,
            round(
                maximum_points * 0.08
            ),
        )

        self.points_chart.set_y_range(
            0,
            max(
                3,
                maximum_points
                + point_padding,
            ),
        )

        self.points_chart.set_y_tick_interval(
            5
        )

        self.points_chart.restore_chart_title()

    def _create_form_widget(
        self,
        sequence: list[str],
    ) -> QWidget:
        widget = QWidget()

        layout = QHBoxLayout(
            widget
        )

        layout.setContentsMargins(
            6,
            2,
            6,
            2,
        )

        layout.setSpacing(
            4
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        if not sequence:
            label = QLabel(
                "-"
            )

            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            layout.addWidget(
                label
            )

            return widget

        for result in sequence:
            label = QLabel(
                result
            )

            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            label.setFixedSize(
                24,
                24,
            )

            label.setToolTip(
                self._form_tooltip(
                    result
                )
            )

            label.setStyleSheet(
                self._form_style(
                    result
                )
            )

            layout.addWidget(
                label
            )

        return widget

    @staticmethod
    def _form_style(
        result: str,
    ) -> str:
        if result == "S":
            background = "#2e7d32"
            border = "#43a047"

        elif result == "U":
            background = "#b7791f"
            border = "#d69e2e"

        elif result == "N":
            background = "#b83232"
            border = "#d64545"

        else:
            background = "#4b5563"
            border = "#6b7280"

        return (
            f"""
            QLabel {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 12px;
                color: white;
                font-weight: 700;
                font-size: 11px;
            }}
            """
        )

    @staticmethod
    def _form_tooltip(
        result: str,
    ) -> str:
        if result == "S":
            return "Sieg"

        if result == "U":
            return "Unentschieden"

        if result == "N":
            return "Niederlage"

        return "Unbekannt"

    def refresh(
        self,
    ) -> None:
        self.load_data()

    def clear_data(
        self,
    ) -> None:
        self.table.setRowCount(
            0
        )

        self.points_chart.show_empty_chart(
            "Keine Daten"
        )

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(
            False
        )