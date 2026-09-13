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
    REPORT_TYPE_SHORT = "short"
    REPORT_TYPE_FULL = "full"

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
            560
        )

        self.team_combo = QComboBox()
        self.report_type_combo = QComboBox()

        self.report_info_label = QLabel()
        self.report_info_label.setWordWrap(
            True
        )

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
        self.update_report_type_ui()

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
            "Wähle eine Mannschaft und den gewünschten "
            "PDF-Bericht aus."
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

        report_group = QGroupBox(
            "Berichtstyp"
        )

        report_layout = QVBoxLayout(
            report_group
        )

        self.report_type_combo.addItem(
            "Kurzreport",
            self.REPORT_TYPE_SHORT,
        )

        self.report_type_combo.addItem(
            "Vollständiger Teamreport",
            self.REPORT_TYPE_FULL,
        )

        report_layout.addWidget(
            self.report_type_combo
        )

        report_layout.addWidget(
            self.report_info_label
        )

        self.content_group = QGroupBox(
            "Inhalte"
        )

        content_layout = QVBoxLayout(
            self.content_group
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
            report_group
        )

        layout.addWidget(
            self.content_group
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

        self.report_type_combo.currentIndexChanged.connect(
            self.update_report_type_ui
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

    def update_report_type_ui(
        self,
    ) -> None:
        report_type = self.get_report_type()

        is_full_report = (
            report_type
            == self.REPORT_TYPE_FULL
        )

        if is_full_report:
            self.report_info_label.setText(
                "Der vollständige Teamreport enthält automatisch "
                "alle verfügbaren Statistikbereiche, Tabellen und "
                "Grafiken. Die einzelnen Inhalte müssen nicht "
                "separat ausgewählt werden."
            )

            self.select_all_checkbox.blockSignals(
                True
            )
            self.select_all_checkbox.setChecked(
                True
            )
            self.select_all_checkbox.blockSignals(
                False
            )

            self.select_all_checkbox.setEnabled(
                False
            )

            for checkbox in (
                self.section_checkboxes.values()
            ):
                checkbox.blockSignals(
                    True
                )
                checkbox.setChecked(
                    True
                )
                checkbox.setEnabled(
                    False
                )
                checkbox.blockSignals(
                    False
                )

            return

        self.report_info_label.setText(
            "Der Kurzreport entspricht dem bisherigen kompakten "
            "Teambericht. Die gewünschten Inhalte können frei "
            "ausgewählt werden."
        )

        self.select_all_checkbox.setEnabled(
            True
        )

        for checkbox in (
            self.section_checkboxes.values()
        ):
            checkbox.setEnabled(
                True
            )

        self.update_select_all_state()

    def select_all_sections(
        self,
        checked: bool,
    ) -> None:
        if (
            self.get_report_type()
            == self.REPORT_TYPE_FULL
        ):
            return

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
        if (
            self.get_report_type()
            == self.REPORT_TYPE_FULL
        ):
            return

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

        if (
            self.get_report_type()
            == self.REPORT_TYPE_SHORT
            and not self.get_selected_sections()
        ):
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

    def get_report_type(
        self,
    ) -> str:
        report_type = (
            self.report_type_combo.currentData()
        )

        if report_type not in {
            self.REPORT_TYPE_SHORT,
            self.REPORT_TYPE_FULL,
        }:
            return self.REPORT_TYPE_SHORT

        return str(
            report_type
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
            "report_type":
                self.get_report_type(),
            "sections":
                self.get_selected_sections(),
        }
