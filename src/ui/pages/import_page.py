from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
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
from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import LeagueRepository
from src.database.repositories.match_repository import MatchRepository
from src.database.repositories.season_repository import SeasonRepository
from src.database.repositories.team_repository import TeamRepository
from src.importer.fussballde.importer import FussballDeImporter
from src.services.imports.import_result import ImportResult
from src.services.imports.schedule_import_service import (
    ScheduleImportService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class ImportPage(QWidget):

    def __init__(self) -> None:
        super().__init__()

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )
        main_layout.setSpacing(20)

        title_label = QLabel(
            "Spielplan importieren"
        )
        title_label.setObjectName(
            "PageTitle"
        )

        description_label = QLabel(
            "Spielplan von fussball.de importieren. "
            "Liga, Saison, Wettbewerb, Vereine und "
            "Mannschaften werden automatisch erkannt."
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

        form_layout.addRow(
            "Spielplan-URL:",
            self.url_input,
        )

        import_layout.addLayout(
            form_layout
        )

        button_layout = QHBoxLayout()

        self.import_button = QPushButton(
            "📥 Spielplan importieren"
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
            180
        )

        result_layout.addWidget(
            result_title
        )
        result_layout.addWidget(
            self.result_output
        )

        main_layout.addWidget(
            result_frame
        )
        main_layout.addStretch()

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
        validation_error = self._validate_import_data(
            url
        )

        if validation_error:
            QMessageBox.warning(
                self,
                "Eingaben prüfen",
                validation_error,
            )
            return

        self.set_import_running(
            True
        )
        self.show_result(
            "Import wird vorbereitet ...\n\n"
            "Die fussball.de-Seite wird geladen."
        )

        QApplication.processEvents()

        start_time = time.perf_counter()
        connection: sqlite3.Connection | None = None

        try:
            connection = sqlite3.connect(
                DATABASE_PATH
            )
            connection.row_factory = sqlite3.Row
            connection.execute(
                "PRAGMA foreign_keys = ON;"
            )

            import_service = ScheduleImportService(
                association_repository=AssociationRepository(
                    connection
                ),
                league_repository=LeagueRepository(
                    connection
                ),
                season_repository=SeasonRepository(
                    connection
                ),
                club_repository=ClubRepository(
                    connection
                ),
                team_repository=TeamRepository(
                    connection
                ),
                competition_repository=CompetitionRepository(
                    connection
                ),
                match_repository=MatchRepository(
                    connection
                ),
            )

            importer = FussballDeImporter(
                import_service=import_service
            )

            result = importer.import_schedule(
                url=url,
                headless=True,
            )

            duration = time.perf_counter() - start_time

            self.show_import_result(
                result=result,
                duration=duration,
            )

            QMessageBox.information(
                self,
                "Import abgeschlossen",
                "Der Spielplan wurde erfolgreich importiert.",
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
                "Der Spielplan konnte nicht "
                "importiert werden.\n\n"
                f"{error}",
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
            return "Bitte eine Spielplan-URL eingeben."

        if not url.startswith(("https://", "http://")):
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
        self.import_button.setDisabled(
            running
        )

        if running:
            self.import_button.setText(
                "Import läuft ..."
            )
        else:
            self.import_button.setText(
                "📥 Spielplan importieren"
            )

    def show_import_result(
        self,
        result: ImportResult,
        duration: float,
    ) -> None:
        result_text = (
            "✔ Import erfolgreich\n\n"
            f"Wettbewerbe erstellt:  {result.competitions_created}\n"
            f"Vereine erstellt:       {result.clubs_created}\n"
            f"Mannschaften erstellt:  {result.teams_created}\n"
            f"Spiele erstellt:        {result.matches_created}\n"
            f"Spiele aktualisiert:    {result.matches_updated}\n\n"
            f"Änderungen insgesamt:   {result.total_changes}\n"
            f"Importdauer:             {duration:.2f} Sekunden"
        )

        self.show_result(
            result_text
        )

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
