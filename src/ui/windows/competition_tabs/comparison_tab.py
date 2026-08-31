from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.comparison_service import (
    ComparisonService,
)
from src.services.statistics_service import (
    StatisticsService,
)
from src.ui.charts.base_bar_chart import (
    BaseBarChart,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionComparisonTab(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competition_id: int | None = None
        self.teams: list[dict] = []

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        layout.setSpacing(
            14
        )

        title = QLabel(
            "⚔ Mannschaftsvergleich"
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

        selector_layout = QHBoxLayout()

        team_a_label = QLabel(
            "Mannschaft A:"
        )

        self.team_a_combo = QComboBox()

        self.team_a_combo.setMinimumWidth(
            260
        )

        team_b_label = QLabel(
            "Mannschaft B:"
        )

        self.team_b_combo = QComboBox()

        self.team_b_combo.setMinimumWidth(
            260
        )

        self.refresh_button = QPushButton(
            "🔄 Vergleich aktualisieren"
        )

        self.refresh_button.setEnabled(
            False
        )

        selector_layout.addWidget(
            team_a_label
        )

        selector_layout.addWidget(
            self.team_a_combo
        )

        selector_layout.addSpacing(
            20
        )

        selector_layout.addWidget(
            team_b_label
        )

        selector_layout.addWidget(
            self.team_b_combo
        )

        selector_layout.addStretch(
            1
        )

        selector_layout.addWidget(
            self.refresh_button
        )

        self.splitter = QSplitter(
            Qt.Orientation.Vertical
        )

        self.comparison_table = QTableWidget()

        self.comparison_table.setColumnCount(
            3
        )

        self.comparison_table.setHorizontalHeaderLabels(
            [
                "Kennzahl",
                "Mannschaft A",
                "Mannschaft B",
            ]
        )

        self.comparison_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.comparison_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )

        self.comparison_table.setAlternatingRowColors(
            True
        )

        self.comparison_table.verticalHeader().setVisible(
            False
        )

        header = (
            self.comparison_table.horizontalHeader()
        )

        header.setStretchLastSection(
            True
        )

        header.setSectionResizeMode(
            0,
            header.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            1,
            header.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            header.ResizeMode.Stretch,
        )

        chart_container = QWidget()

        chart_layout = QVBoxLayout(
            chart_container
        )

        chart_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        chart_layout.setSpacing(
            8
        )

        chart_title = QLabel(
            "📊 Leistungsprofil"
        )

        chart_title.setObjectName(
            "SectionTitle"
        )

        self.comparison_chart = BaseBarChart(
            title="Direkter Leistungsvergleich",
            x_axis_title="Kennzahl",
            y_axis_title="Wert pro Spiel",
        )

        self.comparison_chart.setMinimumHeight(
            300
        )

        chart_layout.addWidget(
            chart_title
        )

        chart_layout.addWidget(
            self.comparison_chart,
            1,
        )

        self.splitter.addWidget(
            self.comparison_table
        )

        self.splitter.addWidget(
            chart_container
        )

        self.splitter.setStretchFactor(
            0,
            1
        )

        self.splitter.setStretchFactor(
            1,
            1
        )

        self.splitter.setSizes(
            [
                420,
                360,
            ]
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            self.info_label
        )

        layout.addLayout(
            selector_layout
        )

        layout.addWidget(
            self.splitter,
            1,
        )

    def connect_signals(
        self,
    ) -> None:
        self.refresh_button.clicked.connect(
            self.load_comparison
        )

        self.team_a_combo.currentIndexChanged.connect(
            self.selection_changed
        )

        self.team_b_combo.currentIndexChanged.connect(
            self.selection_changed
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
        if self.competition_id is None:
            self.clear_data()
            return

        previous_team_a = (
            self.team_a_combo.currentData()
        )

        previous_team_b = (
            self.team_b_combo.currentData()
        )

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            statistics_service = (
                StatisticsService(
                    connection
                )
            )

            comparison_service = (
                ComparisonService(
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

            self.teams = (
                comparison_service.get_teams(
                    self.competition_id
                )
            )

            self.populate_team_combos(
                previous_team_a,
                previous_team_b,
            )

            self.info_label.setText(
                competition_name
            )

            enabled = (
                len(
                    self.teams
                )
                >= 2
            )

            self.refresh_button.setEnabled(
                enabled
            )

            self.team_a_combo.setEnabled(
                enabled
            )

            self.team_b_combo.setEnabled(
                enabled
            )

            self.load_comparison()

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Der Mannschaftsvergleich "
                    "konnte nicht geladen werden:\n"
                    f"{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def populate_team_combos(
        self,
        previous_team_a=None,
        previous_team_b=None,
    ) -> None:
        self.team_a_combo.blockSignals(
            True
        )

        self.team_b_combo.blockSignals(
            True
        )

        self.team_a_combo.clear()
        self.team_b_combo.clear()

        for team in self.teams:
            display_text = (
                f"{team['position']}. "
                f"{team['team_name']}"
            )

            self.team_a_combo.addItem(
                display_text,
                team["team_id"],
            )

            self.team_b_combo.addItem(
                display_text,
                team["team_id"],
            )

        team_a_index = self._find_combo_index(
            self.team_a_combo,
            previous_team_a,
        )

        team_b_index = self._find_combo_index(
            self.team_b_combo,
            previous_team_b,
        )

        if team_a_index < 0:
            team_a_index = 0

        if team_b_index < 0:
            team_b_index = (
                1
                if self.team_b_combo.count() > 1
                else 0
            )

        if (
            team_a_index == team_b_index
            and self.team_b_combo.count() > 1
        ):
            team_b_index = (
                1
                if team_a_index != 1
                else 0
            )

        self.team_a_combo.setCurrentIndex(
            team_a_index
        )

        self.team_b_combo.setCurrentIndex(
            team_b_index
        )

        self.team_a_combo.blockSignals(
            False
        )

        self.team_b_combo.blockSignals(
            False
        )

    def selection_changed(
        self,
        _index: int,
    ) -> None:
        if self.competition_id is None:
            return

        team_a_id = (
            self.team_a_combo.currentData()
        )

        team_b_id = (
            self.team_b_combo.currentData()
        )

        if (
            team_a_id is None
            or team_b_id is None
        ):
            return

        if team_a_id == team_b_id:
            self.comparison_table.setRowCount(
                0
            )

            self.comparison_chart.show_empty_chart(
                "Bitte zwei unterschiedliche Mannschaften auswählen"
            )

            return

        self.load_comparison()

    def load_comparison(
        self,
    ) -> None:
        if self.competition_id is None:
            return

        team_a_id = (
            self.team_a_combo.currentData()
        )

        team_b_id = (
            self.team_b_combo.currentData()
        )

        if (
            team_a_id is None
            or team_b_id is None
        ):
            self.comparison_table.setRowCount(
                0
            )

            self.comparison_chart.show_empty_chart(
                "Keine Vergleichsdaten"
            )

            return

        if team_a_id == team_b_id:
            self.comparison_table.setRowCount(
                0
            )

            self.comparison_chart.show_empty_chart(
                "Bitte zwei unterschiedliche Mannschaften auswählen"
            )

            self.info_label.setText(
                "Bitte zwei unterschiedliche "
                "Mannschaften auswählen."
            )

            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            service = ComparisonService(
                connection
            )

            comparison = (
                service.get_team_comparison(
                    competition_id=self.competition_id,
                    team_a_id=int(
                        team_a_id
                    ),
                    team_b_id=int(
                        team_b_id
                    ),
                )
            )

            self.populate_comparison(
                comparison
            )

            self.populate_chart(
                comparison
            )

            team_a = comparison[
                "team_a"
            ]

            team_b = comparison[
                "team_b"
            ]

            self.info_label.setText(
                (
                    f"{team_a['team_name']} "
                    "vs. "
                    f"{team_b['team_name']}"
                )
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Vergleichsfehler",
                (
                    "Der Vergleich konnte "
                    "nicht geladen werden:\n"
                    f"{error}"
                ),
            )

            self.comparison_chart.show_empty_chart(
                "Vergleich konnte nicht geladen werden"
            )

        finally:
            connection.close()

    def populate_comparison(
        self,
        comparison: dict,
    ) -> None:
        team_a = comparison[
            "team_a"
        ]

        team_b = comparison[
            "team_b"
        ]

        rows = [
            (
                "Tabellenplatz",
                team_a["position"],
                team_b["position"],
            ),
            (
                "Spiele",
                team_a["played"],
                team_b["played"],
            ),
            (
                "Siege",
                team_a["wins"],
                team_b["wins"],
            ),
            (
                "Unentschieden",
                team_a["draws"],
                team_b["draws"],
            ),
            (
                "Niederlagen",
                team_a["losses"],
                team_b["losses"],
            ),
            (
                "Punkte",
                team_a["points"],
                team_b["points"],
            ),
            (
                "Punkte / Spiel",
                self._format_decimal(
                    team_a["points_per_game"]
                ),
                self._format_decimal(
                    team_b["points_per_game"]
                ),
            ),
            (
                "Tore",
                team_a["goals_for"],
                team_b["goals_for"],
            ),
            (
                "Gegentore",
                team_a["goals_against"],
                team_b["goals_against"],
            ),
            (
                "Tordifferenz",
                self._format_signed(
                    team_a["goal_difference"]
                ),
                self._format_signed(
                    team_b["goal_difference"]
                ),
            ),
            (
                "Tore / Spiel",
                self._format_decimal(
                    team_a["goals_per_game"]
                ),
                self._format_decimal(
                    team_b["goals_per_game"]
                ),
            ),
            (
                "Gegentore / Spiel",
                self._format_decimal(
                    team_a[
                        "goals_against_per_game"
                    ]
                ),
                self._format_decimal(
                    team_b[
                        "goals_against_per_game"
                    ]
                ),
            ),
            (
                "Form letzte 5",
                "",
                "",
            ),
            (
                "Heim-Platz",
                team_a["home_position"],
                team_b["home_position"],
            ),
            (
                "Heim-Punkte",
                team_a["home_points"],
                team_b["home_points"],
            ),
            (
                "Heim Punkte / Spiel",
                self._format_decimal(
                    team_a[
                        "home_points_per_game"
                    ]
                ),
                self._format_decimal(
                    team_b[
                        "home_points_per_game"
                    ]
                ),
            ),
            (
                "Heim-Tordifferenz",
                self._format_signed(
                    team_a[
                        "home_goal_difference"
                    ]
                ),
                self._format_signed(
                    team_b[
                        "home_goal_difference"
                    ]
                ),
            ),
            (
                "Auswärts-Platz",
                team_a["away_position"],
                team_b["away_position"],
            ),
            (
                "Auswärts-Punkte",
                team_a["away_points"],
                team_b["away_points"],
            ),
            (
                "Auswärts Punkte / Spiel",
                self._format_decimal(
                    team_a[
                        "away_points_per_game"
                    ]
                ),
                self._format_decimal(
                    team_b[
                        "away_points_per_game"
                    ]
                ),
            ),
            (
                "Auswärts-Tordifferenz",
                self._format_signed(
                    team_a[
                        "away_goal_difference"
                    ]
                ),
                self._format_signed(
                    team_b[
                        "away_goal_difference"
                    ]
                ),
            ),
        ]

        self.comparison_table.setRowCount(
            len(
                rows
            )
        )

        self.comparison_table.setHorizontalHeaderLabels(
            [
                "Kennzahl",
                team_a["team_name"],
                team_b["team_name"],
            ]
        )

        for row_index, row in enumerate(
            rows
        ):
            metric_name = row[0]
            value_a = row[1]
            value_b = row[2]

            metric_item = QTableWidgetItem(
                str(
                    metric_name
                )
            )

            metric_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.comparison_table.setItem(
                row_index,
                0,
                metric_item,
            )

            if metric_name == "Form letzte 5":
                self.comparison_table.setCellWidget(
                    row_index,
                    1,
                    self._create_form_widget(
                        team_a.get(
                            "form",
                            [],
                        )
                    ),
                )

                self.comparison_table.setCellWidget(
                    row_index,
                    2,
                    self._create_form_widget(
                        team_b.get(
                            "form",
                            [],
                        )
                    ),
                )

                self.comparison_table.setRowHeight(
                    row_index,
                    32,
                )

                continue

            value_a_item = QTableWidgetItem(
                self._display_value(
                    value_a
                )
            )

            value_b_item = QTableWidgetItem(
                self._display_value(
                    value_b
                )
            )

            value_a_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            value_b_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.comparison_table.setItem(
                row_index,
                1,
                value_a_item,
            )

            self.comparison_table.setItem(
                row_index,
                2,
                value_b_item,
            )

    def populate_chart(
        self,
        comparison: dict,
    ) -> None:
        self.comparison_chart.clear()

        team_a = comparison[
            "team_a"
        ]

        team_b = comparison[
            "team_b"
        ]

        categories = [
            "Punkte / Spiel",
            "Tore / Spiel",
            "Gegentore / Spiel",
        ]

        team_a_values = [
            float(
                team_a["points_per_game"]
            ),
            float(
                team_a["goals_per_game"]
            ),
            float(
                team_a[
                    "goals_against_per_game"
                ]
            ),
        ]

        team_b_values = [
            float(
                team_b["points_per_game"]
            ),
            float(
                team_b["goals_per_game"]
            ),
            float(
                team_b[
                    "goals_against_per_game"
                ]
            ),
        ]

        self.comparison_chart.set_categories(
            categories
        )

        self.comparison_chart.create_grouped_bar_series(
            sets=[
                (
                    team_a["team_name"],
                    team_a_values,
                ),
                (
                    team_b["team_name"],
                    team_b_values,
                ),
            ],
            show_labels=True,
        )

        maximum_value = max(
            team_a_values
            + team_b_values
        )

        padding = max(
            0.5,
            maximum_value * 0.20,
        )

        self.comparison_chart.set_value_range(
            minimum=0,
            maximum=(
                maximum_value
                + padding
            ),
        )

        self.comparison_chart.set_value_label_format(
            "%.1f"
        )

        self.comparison_chart.show_legend(
            True
        )

        self.comparison_chart.restore_chart_title()

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

    @staticmethod
    def _find_combo_index(
        combo: QComboBox,
        value,
    ) -> int:
        if value is None:
            return -1

        return combo.findData(
            value
        )

    @staticmethod
    def _display_value(
        value,
    ) -> str:
        if value is None:
            return "-"

        return str(
            value
        )

    @staticmethod
    def _format_decimal(
        value: float,
    ) -> str:
        return f"{float(value):.2f}"

    @staticmethod
    def _format_signed(
        value: int,
    ) -> str:
        if value > 0:
            return f"+{value}"

        return str(
            value
        )

    def refresh(
        self,
    ) -> None:
        self.load_data()

    def clear_data(
        self,
    ) -> None:
        self.teams = []

        self.team_a_combo.blockSignals(
            True
        )

        self.team_b_combo.blockSignals(
            True
        )

        self.team_a_combo.clear()
        self.team_b_combo.clear()

        self.team_a_combo.blockSignals(
            False
        )

        self.team_b_combo.blockSignals(
            False
        )

        self.team_a_combo.setEnabled(
            False
        )

        self.team_b_combo.setEnabled(
            False
        )

        self.comparison_table.setRowCount(
            0
        )

        self.comparison_table.setHorizontalHeaderLabels(
            [
                "Kennzahl",
                "Mannschaft A",
                "Mannschaft B",
            ]
        )

        self.comparison_chart.show_empty_chart(
            "Keine Vergleichsdaten"
        )

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(
            False
        )