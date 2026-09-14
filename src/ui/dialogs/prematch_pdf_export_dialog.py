from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.export.team_pdf_export_service import (
    TeamPdfExportService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class PrematchPdfExportDialog(QDialog):
    def __init__(
        self,
        competition_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        self.competition_id = competition_id

        self.setWindowTitle(
            "Prematch-/Zwei-Team-Report"
        )

        self.setModal(
            True
        )

        self.setMinimumWidth(
            650
        )

        self.team_a_combo = QComboBox()
        self.team_b_combo = QComboBox()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )

        self.create_button = QPushButton(
            "⚔ Prematch-Report erstellen"
        )

        self.button_box.addButton(
            self.create_button,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        self.setup_ui()
        self.connect_signals()
        self.load_teams()

    def setup_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )

        layout.setSpacing(
            16
        )

        title = QLabel(
            "⚔ Prematch-/Zwei-Team-Report"
        )

        title.setObjectName(
            "PageTitle"
        )

        info = QLabel(
            "Wähle zwei Mannschaften desselben Wettbewerbs. "
            "Der Report vergleicht Form, Heim-/Auswärtsleistung, "
            "Tore, Spielmuster, Spielkontrolle sowie Stärken "
            "und Schwächen direkt miteinander."
        )

        info.setWordWrap(
            True
        )

        teams_group = QGroupBox(
            "Mannschaften"
        )

        teams_layout = QHBoxLayout(
            teams_group
        )

        teams_layout.setSpacing(
            14
        )

        team_a_layout = QVBoxLayout()

        team_a_label = QLabel(
            "Team A / Heimteam"
        )

        team_a_layout.addWidget(
            team_a_label
        )

        team_a_layout.addWidget(
            self.team_a_combo
        )

        team_b_layout = QVBoxLayout()

        team_b_label = QLabel(
            "Team B / Auswärtsteam"
        )

        team_b_layout.addWidget(
            team_b_label
        )

        team_b_layout.addWidget(
            self.team_b_combo
        )

        teams_layout.addLayout(
            team_a_layout,
            1,
        )

        versus_label = QLabel(
            "VS"
        )

        versus_label.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        teams_layout.addWidget(
            versus_label
        )

        teams_layout.addLayout(
            team_b_layout,
            1,
        )

        hint = QLabel(
            "Die Zuordnung Heimteam/Auswärtsteam wird später "
            "für venue-spezifische Vergleiche verwendet."
        )

        hint.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            info
        )

        layout.addWidget(
            teams_group
        )

        layout.addWidget(
            hint
        )

        layout.addStretch()

        layout.addWidget(
            self.button_box
        )

    def connect_signals(
        self,
    ) -> None:
        self.button_box.rejected.connect(
            self.reject
        )

        self.create_button.clicked.connect(
            self.accept_export
        )

        self.team_a_combo.currentIndexChanged.connect(
            self.update_create_button
        )

        self.team_b_combo.currentIndexChanged.connect(
            self.update_create_button
        )

    def load_teams(
        self,
    ) -> None:
        self.team_a_combo.clear()
        self.team_b_combo.clear()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            service = TeamPdfExportService(
                connection
            )

            teams = service.get_competition_teams(
                self.competition_id
            )
        finally:
            connection.close()

        for team in teams:
            team_name = str(
                team[
                    "team_name"
                ]
            )
            team_id = int(
                team[
                    "team_id"
                ]
            )

            self.team_a_combo.addItem(
                team_name,
                team_id,
            )

            self.team_b_combo.addItem(
                team_name,
                team_id,
            )

        has_enough_teams = (
            len(
                teams
            )
            >= 2
        )

        self.team_a_combo.setEnabled(
            has_enough_teams
        )

        self.team_b_combo.setEnabled(
            has_enough_teams
        )

        if has_enough_teams:
            self.team_a_combo.setCurrentIndex(
                0
            )

            self.team_b_combo.setCurrentIndex(
                1
            )

        self.update_create_button()

    def update_create_button(
        self,
    ) -> None:
        team_a_id = self.team_a_combo.currentData()
        team_b_id = self.team_b_combo.currentData()

        valid = (
            team_a_id is not None
            and team_b_id is not None
            and int(
                team_a_id
            )
            != int(
                team_b_id
            )
        )

        self.create_button.setEnabled(
            valid
        )

    def accept_export(
        self,
    ) -> None:
        team_a_id = self.team_a_combo.currentData()
        team_b_id = self.team_b_combo.currentData()

        if (
            team_a_id is None
            or team_b_id is None
        ):
            QMessageBox.warning(
                self,
                "Prematch-Report",
                "Bitte wähle zwei Mannschaften aus.",
            )
            return

        if int(
            team_a_id
        ) == int(
            team_b_id
        ):
            QMessageBox.warning(
                self,
                "Prematch-Report",
                (
                    "Team A und Team B müssen "
                    "unterschiedliche Mannschaften sein."
                ),
            )
            return

        self.accept()

    def get_export_options(
        self,
    ) -> dict:
        team_a_id = self.team_a_combo.currentData()
        team_b_id = self.team_b_combo.currentData()

        if (
            team_a_id is None
            or team_b_id is None
        ):
            raise ValueError(
                "Es wurden keine gültigen Mannschaften ausgewählt."
            )

        return {
            "competition_id":
                self.competition_id,
            "team_a_id":
                int(
                    team_a_id
                ),
            "team_a_name":
                self.team_a_combo.currentText(),
            "team_b_id":
                int(
                    team_b_id
                ),
            "team_b_name":
                self.team_b_combo.currentText(),
        }
