from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.database.repositories.association_repository import (
    AssociationRepository,
)
from src.database.repositories.club_repository import (
    ClubRepository,
)
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import (
    LeagueRepository,
)
from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.database.repositories.season_repository import (
    SeasonRepository,
)
from src.database.repositories.team_repository import (
    TeamRepository,
)
from src.importer.fussballde.complete_season_importer import (
    CompleteSeasonImporter,
    CompleteSeasonImportResult,
)
from src.services.imports.import_connection import (
    ImportConnection,
    create_import_connection,
)
from src.services.imports.schedule_import_service import (
    ScheduleImportService,
)
from src.services.validation.import_validation_service import (
    ImportValidationService,
)
from src.services.validation.validation_report import (
    ValidationReport,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

REPORTS_PATH = Path(
    "reports/validation"
)


class ImportPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(
            self
        )
        main_layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )
        main_layout.setSpacing(
            20
        )

        title_label = QLabel(
            "Komplette Saison importieren"
        )
        title_label.setObjectName(
            "PageTitle"
        )

        description_label = QLabel(
            "Importiert Spielplan, Wettbewerb, Vereine, "
            "Mannschaften, Spieler, Stadien, Schiedsrichter, "
            "Ereignisse, Aufstellungen und Spielerstatistiken "
            "direkt von fussball.de."
        )
        description_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            title_label
        )
        main_layout.addWidget(
            description_label
        )

        import_frame = QFrame()
        import_frame.setObjectName(
            "ContentCard"
        )

        import_layout = QVBoxLayout(
            import_frame
        )
        import_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        import_layout.setSpacing(
            16
        )

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft
        )
        form_layout.setHorizontalSpacing(
            20
        )
        form_layout.setVerticalSpacing(
            14
        )

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "https://www.fussball.de/..."
        )
        self.url_input.setClearButtonEnabled(
            True
        )

        self.detail_limit_combo = QComboBox()
        self.detail_limit_combo.addItem(
            "5 Spiele – schneller Test",
            5,
        )
        self.detail_limit_combo.addItem(
            "20 Spiele – erweiterter Test",
            20,
        )
        self.detail_limit_combo.addItem(
            "Alle Spiele – kompletter Import",
            None,
        )

        form_layout.addRow(
            "Wettbewerbs-URL:",
            self.url_input,
        )
        form_layout.addRow(
            "Detailspiele:",
            self.detail_limit_combo,
        )

        import_layout.addLayout(
            form_layout
        )

        hint_label = QLabel(
            "Hinweis: Der vollständige Import kann je nach "
            "Anzahl der Spiele mehrere Minuten dauern."
        )
        hint_label.setWordWrap(
            True
        )
        import_layout.addWidget(
            hint_label
        )

        button_layout = QHBoxLayout()

        self.import_button = QPushButton(
            "📥 Saison importieren"
        )
        self.import_button.setMinimumHeight(
            42
        )
        self.import_button.setMinimumWidth(
            220
        )

        button_layout.addWidget(
            self.import_button
        )
        button_layout.addStretch()

        import_layout.addLayout(
            button_layout
        )
        main_layout.addWidget(
            import_frame
        )

        result_frame = QFrame()
        result_frame.setObjectName(
            "ContentCard"
        )

        result_layout = QVBoxLayout(
            result_frame
        )
        result_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        result_layout.setSpacing(
            12
        )

        result_title = QLabel(
            "Importergebnis"
        )
        result_title.setObjectName(
            "SectionTitle"
        )

        self.result_output = QTextEdit()
        self.result_output.setReadOnly(
            True
        )
        self.result_output.setPlaceholderText(
            "Noch kein Import durchgeführt."
        )
        self.result_output.setMinimumHeight(
            260
        )

        result_layout.addWidget(
            result_title
        )
        result_layout.addWidget(
            self.result_output
        )

        main_layout.addWidget(
            result_frame,
            1,
        )

    def connect_signals(self) -> None:
        self.import_button.clicked.connect(
            self.start_import
        )
        self.url_input.returnPressed.connect(
            self.start_import
        )

    def refresh_data(self) -> None:
        pass

    def start_import(self) -> None:
        url = self.url_input.text().strip()

        validation_error = (
            self._validate_import_data(
                url
            )
        )

        if validation_error:
            QMessageBox.warning(
                self,
                "Eingaben prüfen",
                validation_error,
            )
            return

        max_detail_matches = (
            self.detail_limit_combo.currentData()
        )

        if max_detail_matches is not None:
            max_detail_matches = int(
                max_detail_matches
            )

        self.set_import_running(
            True
        )

        self.show_result(
            "Import wird vorbereitet ...\n\n"
            "Die fussball.de-Seite wird geladen.\n"
            "Während des Imports kann das Fenster "
            "vorübergehend nicht reagieren."
        )

        QApplication.processEvents()

        start_time = time.perf_counter()
        connection: ImportConnection | None = None

        try:
            connection = create_import_connection(
                str(DATABASE_PATH)
            )

            schedule_import_service = (
                ScheduleImportService(
                    association_repository=(
                        AssociationRepository(
                            connection
                        )
                    ),
                    league_repository=(
                        LeagueRepository(
                            connection
                        )
                    ),
                    season_repository=(
                        SeasonRepository(
                            connection
                        )
                    ),
                    club_repository=(
                        ClubRepository(
                            connection
                        )
                    ),
                    team_repository=(
                        TeamRepository(
                            connection
                        )
                    ),
                    competition_repository=(
                        CompetitionRepository(
                            connection
                        )
                    ),
                    match_repository=(
                        MatchRepository(
                            connection
                        )
                    ),
                )
            )

            importer = CompleteSeasonImporter(
                connection=connection,
                schedule_import_service=(
                    schedule_import_service
                ),
            )

            result = importer.import_competition(
                url=url,
                headless=True,
                continue_on_detail_error=True,
                max_detail_matches=(
                    max_detail_matches
                ),
            )

            validation_service = (
                ImportValidationService(
                    connection
                )
            )
            validation_result = (
                validation_service.validate()
            )

            validation_report = (
                ValidationReport()
            )
            validation_text = (
                validation_report.build_text(
                    validation_result
                )
            )

            report_path = (
                self._save_validation_report(
                    validation_text
                )
            )

            if validation_result.has_errors:
                raise RuntimeError(
                    "Die Importvalidierung hat kritische "
                    "Fehler gefunden. Der komplette Import "
                    "wurde zurückgesetzt.\n\n"
                    f"Validierungsbericht: {report_path}"
                )

            connection.final_commit()

            duration = (
                time.perf_counter()
                - start_time
            )

            self.show_import_result(
                result=result,
                duration=duration,
                detail_limit=(
                    max_detail_matches
                ),
                validation_text=(
                    validation_text
                ),
                report_path=(
                    report_path
                ),
            )

            if result.match_details_failed == 0:
                QMessageBox.information(
                    self,
                    "Import abgeschlossen",
                    "Die Saison wurde erfolgreich "
                    "importiert.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Import mit Hinweisen abgeschlossen",
                    (
                        "Der Import wurde abgeschlossen.\n\n"
                        f"Fehlgeschlagene Detailspiele: "
                        f"{result.match_details_failed}"
                    ),
                )

        except Exception as error:
            if connection is not None:
                connection.rollback()

            self.show_error(
                str(error)
            )

            QMessageBox.critical(
                self,
                "Import fehlgeschlagen",
                (
                    "Die Saison konnte nicht "
                    "importiert werden.\n\n"
                    f"{error}"
                ),
            )

        finally:
            if connection is not None:
                connection.close()

            self.set_import_running(
                False
            )

    @staticmethod
    def _validate_import_data(
        url: str,
    ) -> str | None:
        if not url:
            return (
                "Bitte eine Wettbewerbs-URL "
                "eingeben."
            )

        if not url.startswith(
            (
                "https://",
                "http://",
            )
        ):
            return (
                "Die URL muss mit http:// "
                "oder https:// beginnen."
            )

        if "fussball.de" not in url.casefold():
            return (
                "Bitte eine gültige "
                "fussball.de-URL eingeben."
            )

        return None

    def set_import_running(
        self,
        running: bool,
    ) -> None:
        self.url_input.setDisabled(
            running
        )
        self.detail_limit_combo.setDisabled(
            running
        )
        self.import_button.setDisabled(
            running
        )

        if running:
            self.import_button.setText(
                "Import läuft ..."
            )
        else:
            self.import_button.setText(
                "📥 Saison importieren"
            )

    def show_import_result(
        self,
        result: CompleteSeasonImportResult,
        duration: float,
        detail_limit: int | None,
        validation_text: str,
        report_path: Path,
    ) -> None:
        schedule_result = (
            result.schedule_result
        )

        competitions_created = getattr(
            schedule_result,
            "competitions_created",
            0,
        )
        clubs_created = getattr(
            schedule_result,
            "clubs_created",
            0,
        )
        teams_created = getattr(
            schedule_result,
            "teams_created",
            0,
        )
        matches_created = getattr(
            schedule_result,
            "matches_created",
            0,
        )
        matches_updated = getattr(
            schedule_result,
            "matches_updated",
            0,
        )

        detail_mode = (
            "Alle Spiele"
            if detail_limit is None
            else f"Maximal {detail_limit} Spiele"
        )

        result_text = (
            "✔ Import abgeschlossen\n\n"
            f"Detailmodus:             {detail_mode}\n"
            f"Spiele gefunden:         {result.matches_found}\n"
            f"Detailimporte erfolgreich: "
            f"{result.match_details_imported}\n"
            f"Detailimporte fehlgeschlagen: "
            f"{result.match_details_failed}\n\n"
            f"Wettbewerbe erstellt:    {competitions_created}\n"
            f"Vereine erstellt:        {clubs_created}\n"
            f"Mannschaften erstellt:   {teams_created}\n"
            f"Spiele erstellt:         {matches_created}\n"
            f"Spiele aktualisiert:     {matches_updated}\n\n"
            f"Spielerzuordnungen:       "
            f"{result.players_imported}\n"
            f"Ereignisse importiert:   "
            f"{result.events_imported}\n"
            f"Importdauer:              "
            f"{duration:.2f} Sekunden"
        )

        if result.errors:
            error_lines = "\n".join(
                f"- {error}"
                for error in result.errors
            )

            result_text += (
                "\n\nFehler / Hinweise:\n"
                f"{error_lines}"
            )

        result_text += (
            "\n\n"
            + validation_text
            + "\n\n"
            + "Validierungsbericht gespeichert unter:\n"
            + str(report_path)
        )

        self.show_result(
            result_text
        )

    @staticmethod
    def _save_validation_report(
        report_text: str,
    ) -> Path:
        REPORTS_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        report_path = REPORTS_PATH / (
            f"validation_report_{timestamp}.txt"
        )

        report_path.write_text(
            report_text,
            encoding="utf-8",
        )

        return report_path

    def show_result(
        self,
        text: str,
    ) -> None:
        self.result_output.setPlainText(
            text
        )

    def show_error(
        self,
        message: str,
    ) -> None:
        self.result_output.setPlainText(
            "✖ Import fehlgeschlagen\n\n"
            f"{message}"
        )