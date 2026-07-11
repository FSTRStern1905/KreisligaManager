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

from src.ui.dialogs.club_dialog import ClubDialog


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class ClubsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.clubs = []

        self.setup_ui()
        self.connect_signals()
        self.load_clubs()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🏟 Vereine")
        title.setObjectName("PageTitle")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Verein suchen...")

        self.club_list = QListWidget()

        button_layout = QHBoxLayout()

        self.new_button = QPushButton("➕ Neuer Verein")
        self.edit_button = QPushButton("✏ Bearbeiten")
        self.delete_button = QPushButton("🗑 Löschen")

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        layout.addWidget(title)
        layout.addWidget(self.search)
        layout.addWidget(self.club_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.new_button.clicked.connect(self.new_club)
        self.search.textChanged.connect(self.filter_clubs)

    def load_clubs(self):
        self.clubs.clear()
        self.club_list.clear()

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    club_id,
                    name,
                    short_name,
                    city
                FROM clubs
                ORDER BY name ASC
                """
            )

            self.clubs = cursor.fetchall()

            for club in self.clubs:
                club_id, name, short_name, city = club
                display_text = f"{name} ({short_name}) - {city}"
                self.club_list.addItem(display_text)

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Vereine konnten nicht geladen werden:\n{error}",
            )

        finally:
            connection.close()

    def filter_clubs(self):
        search_text = self.search.text().lower().strip()

        self.club_list.clear()

        for club in self.clubs:
            club_id, name, short_name, city = club

            searchable_text = f"{name} {short_name} {city}".lower()

            if search_text in searchable_text:
                display_text = f"{name} ({short_name}) - {city}"
                self.club_list.addItem(display_text)

    def new_club(self):
        dialog = ClubDialog(self)

        if dialog.exec():
            data = dialog.get_data()

            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO clubs (
                        name,
                        short_name,
                        city
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        data["name"],
                        data["short_name"],
                        data["city"],
                    ),
                )

                connection.commit()
                self.load_clubs()

            except sqlite3.IntegrityError:
                QMessageBox.warning(
                    self,
                    "Verein existiert bereits",
                    "Dieser Verein ist bereits vorhanden.",
                )

            except sqlite3.Error as error:
                QMessageBox.critical(
                    self,
                    "Datenbankfehler",
                    f"Verein konnte nicht gespeichert werden:\n{error}",
                )

            finally:
                connection.close()