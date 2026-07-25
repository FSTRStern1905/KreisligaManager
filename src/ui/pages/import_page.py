from __future__ import annotations

import sqlite3
import time
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

from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.match_repository import MatchRepository
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
        self.load_leagues()
        self.load_seasons()

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
            "Spielplan von fussball.de importieren."
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

        self.league_combo = QComboBox()
        self.league_combo.addItem(
            "Liga auswählen",
            None,
        )

        self.season_combo = QComboBox()
        self.season_combo.addItem(
            "Saison auswählen",
            None,
        )

        form_layout.addRow(
            "Spielplan-URL:",
            self.url_input,
        )
        form_layout.addRow(
            "Liga:",
            self.league_combo,
        )
        form_layout.addRow(
            "Saison:",
            self.season_combo,
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

    def load_leagues(self) -> None:
        self.league_combo.clear()
        self.league_combo.addItem(
            "Liga auswählen",
            None,
        )

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    league_id,
                    name,
                    level
                FROM leagues
                ORDER BY
                    level ASC,
                    name ASC
                """
            )

            for (
                league_id,
                name,
                level,
            ) in cursor.fetchall():
                display_name = name

                if level is not None:
                    display_name = (
                        f"{name} | Ebene {level}"
                    )

                self.league_combo.addItem(
                    display_name,
                    league_id,
                )

        finally:
            connection.close()

    def load_seasons(self) -> None:
        self.season_combo.clear()
        self.season_combo.addItem(
            "Saison auswählen",
            None,
        )

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    season_id,
                    name,
                    start_date,
                    end_date
                FROM seasons
                ORDER BY
                    start_date DESC
                """
            )

            for (
                season_id,
                name,
                start_date,
                end_date,
            ) in cursor.fetchall():
                display_name = name

                if start_date and end_date:
                    display_name = (
                        f"{name} | "
                        f"{start_date} bis {end_date}"
                    )

                self.season_combo.addItem(
                    display_name,
                    season_id,
                )

        finally:
            connection.close()

    def refresh_data(self) -> None:
        selected_league_id = (
            self.selected_league_id()
        )
        selected_season_id = (
            self.selected_season_id()
        )

        self.load_leagues()
        self.load_seasons()

        self._restore_combo_selection(
            combo=self.league_combo,
            item_id=selected_league_id,
        )

        self._restore_combo_selection(
            combo=self.season_combo,
            item_id=selected_season_id,
        )

    def start_import(self) -> None:
        url = self.url_input.text().strip()
        league_id = self.selected_league_id()
        season_id = self.selected_season_id()

        validation_error = self._validate_import_data(
            url=url,
            league_id=league_id,
            season_id=season_id,
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

            import_service = ScheduleImportService(
                club_repository=ClubRepository(
                    connection
                ),
                team_repository=TeamRepository(
                    connection
                ),
                competition_repository=(
                    CompetitionRepository(
                        connection
                    )
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
                league_id=league_id,
                season_id=season_id,
                headless=True,
            )

            duration = (
                time.perf_counter()
                - start_time
            )

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
        league_id: int | None,
        season_id: int | None,
    ) -> str | None:
        if not url:
            return (
                "Bitte eine Spielplan-URL eingeben."
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

        if league_id is None:
            return (
                "Bitte eine Liga auswählen."
            )

        if season_id is None:
            return (
                "Bitte eine Saison auswählen."
            )

        return None

    @staticmethod
    def _restore_combo_selection(
        combo: QComboBox,
        item_id: int | None,
    ) -> None:
        if item_id is None:
            return

        index = combo.findData(
            item_id
        )

        if index >= 0:
            combo.setCurrentIndex(
                index
            )

    def selected_league_id(
        self,
    ) -> int | None:
        league_id = (
            self.league_combo.currentData()
        )

        if league_id is None:
            return None

        return int(
            league_id
        )

    def selected_season_id(
        self,
    ) -> int | None:
        season_id = (
            self.season_combo.currentData()
        )

        if season_id is None:
            return None

        return int(
            season_id
        )

    def set_import_running(
        self,
        running: bool,
    ) -> None:
        self.url_input.setDisabled(
            running
        )
        self.league_combo.setDisabled(
            running
        )
        self.season_combo.setDisabled(
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
            f"Wettbewerbe erstellt:  "
            f"{result.competitions_created}\n"
            f"Vereine erstellt:       "
            f"{result.clubs_created}\n"
            f"Mannschaften erstellt:  "
            f"{result.teams_created}\n"
            f"Spiele erstellt:        "
            f"{result.matches_created}\n"
            f"Spiele aktualisiert:    "
            f"{result.matches_updated}\n\n"
            f"Änderungen insgesamt:   "
            f"{result.total_changes}\n"
            f"Importdauer:             "
            f"{duration:.2f} Sekunden"
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
            f"✖ Import fehlgeschlagen\n\n"
            f"{message}"
        )