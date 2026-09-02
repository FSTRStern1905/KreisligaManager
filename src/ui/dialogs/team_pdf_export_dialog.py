from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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


class TeamPdfExportDialog(QDialog):
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
            "Team-Statistik als PDF"
        )

        self.setModal(
            True
        )

        self.setMinimumWidth(
            520
        )

        self.team_combo = QComboBox()

        self.select_all_checkbox = QCheckBox(
            "Alle Inhalte auswählen"
        )

        self.section_checkboxes: dict[
            str,
            QCheckBox,
        ] = {}

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )

        self.create_button = QPushButton(
            "📄 PDF erstellen"
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
            "📄 Team-Statistik als PDF"
        )

        title.setObjectName(
            "PageTitle"
        )

        info = QLabel(
            "Wähle eine Mannschaft und die Inhalte "
            "für den späteren PDF-Report aus."
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

        content_group = QGroupBox(
            "Inhalte"
        )

        content_layout = QVBoxLayout(
            content_group
        )

        content_layout.addWidget(
            self.select_all_checkbox
        )

        sections = [
            (
                "overview",
                "Übersicht",
            ),
            (
                "table_form",
                "Tabelle & Form",
            ),
            (
                "results",
                "Ergebnisse",
            ),
            (
                "goals",
                "Tore & Torphasen",
            ),
            (
                "match_flow",
                "Spielverlauf",
            ),
            (
                "players",
                "Spieler",
            ),
            (
                "records",
                "Rekorde",
            ),
        ]

        for key, label in sections:
            checkbox = QCheckBox(
                label
            )

            checkbox.setChecked(
                True
            )

            self.section_checkboxes[
                key
            ] = checkbox

            content_layout.addWidget(
                checkbox
            )

        self.select_all_checkbox.setChecked(
            True
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
            content_group
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

        self.select_all_checkbox.toggled.connect(
            self.select_all_sections
        )

        for checkbox in (
            self.section_checkboxes.values()
        ):
            checkbox.toggled.connect(
                self.update_select_all_state
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

            self.create_button.setEnabled(
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

            self.create_button.setEnabled(
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

    def select_all_sections(
        self,
        checked: bool,
    ) -> None:
        for checkbox in (
            self.section_checkboxes.values()
        ):
            checkbox.blockSignals(
                True
            )

            checkbox.setChecked(
                checked
            )

            checkbox.blockSignals(
                False
            )

    def update_select_all_state(
        self,
    ) -> None:
        all_checked = all(
            checkbox.isChecked()
            for checkbox in (
                self.section_checkboxes.values()
            )
        )

        self.select_all_checkbox.blockSignals(
            True
        )

        self.select_all_checkbox.setChecked(
            all_checked
        )

        self.select_all_checkbox.blockSignals(
            False
        )

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

        if not self.get_selected_sections():
            QMessageBox.warning(
                self,
                "Keine Inhalte",
                (
                    "Bitte mindestens einen "
                    "PDF-Inhalt auswählen."
                ),
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

    def get_selected_sections(
        self,
    ) -> list[str]:
        return [
            key
            for key, checkbox
            in self.section_checkboxes.items()
            if checkbox.isChecked()
        ]

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
            "sections":
                self.get_selected_sections(),
        }
