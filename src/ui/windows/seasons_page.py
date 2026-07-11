import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QMessageBox,
)

from src.services.season_service import SeasonService
from src.ui.dialogs.season_dialog import SeasonDialog


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class SeasonsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.seasons = []

        self.setup_ui()
        self.connect_signals()
        self.load_seasons()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📅 Saisons")
        title.setObjectName("PageTitle")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Saison suchen...")

        self.season_list = QListWidget()

        button_layout = QHBoxLayout()

        self.new_button = QPushButton("➕ Neue Saison")
        self.generate_schedule_button = QPushButton("📆 Spielplan erzeugen")
        self.edit_button = QPushButton("✏ Bearbeiten")
        self.delete_button = QPushButton("🗑 Löschen")

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.generate_schedule_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        layout.addWidget(title)
        layout.addWidget(self.search)
        layout.addWidget(self.season_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.new_button.clicked.connect(self.new_season)
        self.generate_schedule_button.clicked.connect(self.generate_schedule)
        self.search.textChanged.connect(self.filter_seasons)

    def load_seasons(self):
        self.seasons.clear()
        self.season_list.clear()

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(DATABASE_PATH)
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
                ORDER BY start_date DESC
                """
            )

            self.seasons = cursor.fetchall()

            for season in self.seasons:
                self.season_list.addItem(self.format_season(season))

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Saisons konnten nicht geladen werden:\n{error}",
            )

        finally:
            connection.close()

    def filter_seasons(self):
        search_text = self.search.text().lower().strip()

        self.season_list.clear()

        for season in self.seasons:
            season_id, name, start_date, end_date = season
            searchable_text = f"{name} {start_date} {end_date}".lower()

            if search_text in searchable_text:
                self.season_list.addItem(self.format_season(season))

    def new_season(self):
        dialog = SeasonDialog(self)

        if dialog.exec():
            data = dialog.get_data()

            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO seasons (
                        name,
                        start_date,
                        end_date
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        data["name"],
                        data["start_date"],
                        data["end_date"],
                    ),
                )

                connection.commit()
                self.load_seasons()

            except sqlite3.IntegrityError:
                QMessageBox.warning(
                    self,
                    "Saison existiert bereits",
                    "Diese Saison ist bereits vorhanden.",
                )

            except sqlite3.Error as error:
                QMessageBox.critical(
                    self,
                    "Datenbankfehler",
                    f"Saison konnte nicht gespeichert werden:\n{error}",
                )

            finally:
                connection.close()

    def generate_schedule(self):
        selected_row = self.season_list.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Keine Saison ausgewählt",
                "Bitte wähle zuerst eine Saison aus.",
            )
            return

        season = self.seasons[selected_row]
        season_id = season[0]
        season_name = season[1]

        confirm = QMessageBox.question(
            self,
            "Spielplan erzeugen",
            f"Soll für die Saison '{season_name}' ein Spielplan erzeugt werden?",
        )

        if confirm != QMessageBox.Yes:
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            service = SeasonService(connection)
            service.generate_schedule(season_id)

            QMessageBox.information(
                self,
                "Spielplan erzeugt",
                "Der Spielplan wurde erfolgreich erzeugt.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Spielplan konnte nicht erzeugt werden:\n{error}",
            )

        finally:
            connection.close()

    def format_season(self, season):
        season_id, name, start_date, end_date = season
        return f"{name} | {start_date} bis {end_date}"