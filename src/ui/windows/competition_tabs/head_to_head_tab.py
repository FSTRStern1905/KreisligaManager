from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
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


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionHeadToHeadTab(QWidget):
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
            "⚔ Direkte Duelle"
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
            "🔄 Duelle aktualisieren"
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

        self.summary_label = QLabel(
            "Keine direkten Duelle"
        )

        self.summary_label.setObjectName(
            "InfoLabel"
        )

        self.matches_table = QTableWidget()

        self.matches_table.setColumnCount(
            4
        )

        self.matches_table.setHorizontalHeaderLabels(
            [
                "ST",
                "Heim",
                "Ergebnis",
                "Auswärts",
            ]
        )

        self.matches_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.matches_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        self.matches_table.setAlternatingRowColors(
            True
        )

        self.matches_table.verticalHeader().setVisible(
            False
        )

        header = (
            self.matches_table.horizontalHeader()
        )

        header.setStretchLastSection(
            True
        )

        header.setSectionResizeMode(
            0,
            header.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            header.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            header.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            header.ResizeMode.Stretch,
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
            self.summary_label
        )

        layout.addWidget(
            self.matches_table,
            1,
        )

    def connect_signals(
        self,
    ) -> None:
        self.refresh_button.clicked.connect(
            self.load_head_to_head
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

            enabled = (
                len(
                    self.teams
                )
                >= 2
            )

            self.team_a_combo.setEnabled(
                enabled
            )

            self.team_b_combo.setEnabled(
                enabled
            )

            self.refresh_button.setEnabled(
                enabled
            )

            self.info_label.setText(
                competition_name
            )

            self.load_head_to_head()

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die direkten Duelle "
                    "konnten nicht geladen werden:\n"
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

        self.load_head_to_head()

    def load_head_to_head(
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
            self.clear_content()
            return

        if team_a_id == team_b_id:
            self.matches_table.setRowCount(
                0
            )

            self.summary_label.setText(
                "Bitte zwei unterschiedliche Mannschaften auswählen."
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

            team_a = comparison[
                "team_a"
            ]

            team_b = comparison[
                "team_b"
            ]

            head_to_head = comparison[
                "head_to_head"
            ]

            self.info_label.setText(
                (
                    f"{team_a['team_name']} "
                    "vs. "
                    f"{team_b['team_name']}"
                )
            )

            self.populate_summary(
                team_a,
                team_b,
                head_to_head,
            )

            self.populate_matches(
                head_to_head
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Vergleichsfehler",
                (
                    "Die direkten Duelle "
                    "konnten nicht geladen werden:\n"
                    f"{error}"
                ),
            )

            self.clear_content()

        finally:
            connection.close()

    def populate_summary(
        self,
        team_a: dict,
        team_b: dict,
        head_to_head: dict,
    ) -> None:
        matches_played = int(
            head_to_head.get(
                "matches_played",
                0,
            )
        )

        if matches_played <= 0:
            self.summary_label.setText(
                "Noch keine direkten Duelle "
                "in diesem Wettbewerb."
            )

            return

        team_a_wins = int(
            head_to_head.get(
                "team_a_wins",
                0,
            )
        )

        draws = int(
            head_to_head.get(
                "draws",
                0,
            )
        )

        team_b_wins = int(
            head_to_head.get(
                "team_b_wins",
                0,
            )
        )

        team_a_goals = int(
            head_to_head.get(
                "team_a_goals",
                0,
            )
        )

        team_b_goals = int(
            head_to_head.get(
                "team_b_goals",
                0,
            )
        )

        self.summary_label.setText(
            (
                f"{matches_played} Spiele | "
                f"{team_a['team_name']}: "
                f"{team_a_wins} Siege | "
                f"{draws} Remis | "
                f"{team_b['team_name']}: "
                f"{team_b_wins} Siege | "
                f"Tore "
                f"{team_a_goals}:"
                f"{team_b_goals}"
            )
        )

    def populate_matches(
        self,
        head_to_head: dict,
    ) -> None:
        matches = head_to_head.get(
            "matches",
            [],
        )

        self.matches_table.setRowCount(
            len(
                matches
            )
        )

        for row_index, match in enumerate(
            matches
        ):
            matchday = match.get(
                "matchday"
            )

            home_team_name = match.get(
                "home_team_name",
                "-",
            )

            away_team_name = match.get(
                "away_team_name",
                "-",
            )

            home_goals = int(
                match.get(
                    "home_goals",
                    0,
                )
            )

            away_goals = int(
                match.get(
                    "away_goals",
                    0,
                )
            )

            values = [
                (
                    matchday
                    if matchday is not None
                    else "-"
                ),
                home_team_name,
                f"{home_goals}:{away_goals}",
                away_team_name,
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(
                        value
                    )
                )

                if column_index in (
                    0,
                    2,
                ):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.matches_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

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

    def refresh(
        self,
    ) -> None:
        self.load_data()

    def clear_content(
        self,
    ) -> None:
        self.matches_table.setRowCount(
            0
        )

        self.summary_label.setText(
            "Keine direkten Duelle"
        )

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

        self.refresh_button.setEnabled(
            False
        )

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.clear_content()