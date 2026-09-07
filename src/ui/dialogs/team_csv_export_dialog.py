from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
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


class TeamCsvExportDialog(QDialog):
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
            "Team-Daten als CSV"
        )

        self.setModal(
            True
        )

        self.setMinimumWidth(
            460
        )

        self.team_combo = QComboBox()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )

        self.export_button = QPushButton(
            "📊 CSV exportieren"
        )

        self.button_box.addButton(
            self.export_button,
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
            "📊 Team-Daten als CSV"
        )

        title.setObjectName(
            "PageTitle"
        )

        info = QLabel(
            "Wähle die Mannschaft aus, deren "
            "verfügbare Saison- und Spieldaten "
            "als CSV-Dateien exportiert werden sollen."
        )

        info.setWordWrap(
            True
        )

        team_group = QGroupBox(
            "Mannschaft"
        )

        team_layout = QVBoxLayout(
            team_group
        )

        team_layout.addWidget(
            self.team_combo
        )

        hint = QLabel(
            "Exportiert werden unter anderem Spiele, "
            "Spieler, Ereignisse, Aufstellungen, "
            "Spielerstatistiken, Tabelle und "
            "Saisonmetriken."
        )

        hint.setWordWrap(
            True
        )

        hint.setObjectName(
            "MutedLabel"
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            info
        )

        layout.addWidget(
            team_group
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

        self.export_button.clicked.connect(
            self.accept_export
        )

    def load_teams(
        self,
    ) -> None:
        self.team_combo.clear()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            service = TeamPdfExportService(
                connection
            )

            teams = (
                service.get_competition_teams(
                    self.competition_id
                )
            )

            for team in teams:
                self.team_combo.addItem(
                    team[
                        "team_name"
                    ],
                    team[
                        "team_id"
                    ],
                )

            has_teams = bool(
                teams
            )

            self.team_combo.setEnabled(
                has_teams
            )

            self.export_button.setEnabled(
                has_teams
            )

            if not has_teams:
                QMessageBox.information(
                    self,
                    "Keine Mannschaften",
                    (
                        "Für diesen Wettbewerb "
                        "wurden keine Mannschaften "
                        "gefunden."
                    ),
                )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            self.team_combo.setEnabled(
                False
            )

            self.export_button.setEnabled(
                False
            )

            QMessageBox.critical(
                self,
                "Fehler",
                (
                    "Die Mannschaften konnten "
                    "nicht geladen werden.\n"
                    f"{error}"
                ),
            )

        finally:
            connection.close()

    def accept_export(
        self,
    ) -> None:
        if self.team_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Keine Mannschaft",
                "Bitte eine Mannschaft auswählen.",
            )
            return

        self.accept()

    def get_team_id(
        self,
    ) -> int | None:
        team_id = (
            self.team_combo.currentData()
        )

        if team_id is None:
            return None

        return int(
            team_id
        )

    def get_team_name(
        self,
    ) -> str:
        return (
            self.team_combo.currentText()
        )

    def get_export_options(
        self,
    ) -> dict:
        return {
            "competition_id":
                self.competition_id,
            "team_id":
                self.get_team_id(),
            "team_name":
                self.get_team_name(),
        }
