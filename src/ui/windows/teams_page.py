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

from src.ui.dialogs.team_dialog import TeamDialog


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class TeamsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.teams = []

        self.setup_ui()
        self.connect_signals()
        self.load_teams()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("👕 Mannschaften")
        title.setObjectName("PageTitle")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Mannschaft suchen...")

        self.team_list = QListWidget()

        button_layout = QHBoxLayout()

        self.new_button = QPushButton("➕ Neue Mannschaft")
        self.edit_button = QPushButton("✏ Bearbeiten")
        self.delete_button = QPushButton("🗑 Löschen")

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        layout.addWidget(title)
        layout.addWidget(self.search)
        layout.addWidget(self.team_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.new_button.clicked.connect(self.new_team)
        self.search.textChanged.connect(self.filter_teams)

    def load_teams(self):
        self.teams.clear()
        self.team_list.clear()

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    teams.team_id,
                    teams.name,
                    teams.short_name,
                    teams.team_number,
                    clubs.name
                FROM teams
                INNER JOIN clubs
                    ON teams.club_id = clubs.club_id
                ORDER BY clubs.name ASC, teams.team_number ASC
                """
            )

            self.teams = cursor.fetchall()

            for team in self.teams:
                self.team_list.addItem(self.format_team(team))

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Mannschaften konnten nicht geladen werden:\n{error}",
            )

        finally:
            connection.close()

    def filter_teams(self):
        search_text = self.search.text().lower().strip()

        self.team_list.clear()

        for team in self.teams:
            team_id, team_name, short_name, team_number, club_name = team
            searchable_text = f"{team_name} {short_name} {team_number} {club_name}".lower()

            if search_text in searchable_text:
                self.team_list.addItem(self.format_team(team))

    def new_team(self):
        clubs = self.load_clubs_for_dialog()

        if not clubs:
            QMessageBox.warning(
                self,
                "Keine Vereine vorhanden",
                "Bitte lege zuerst mindestens einen Verein an.",
            )
            return

        dialog = TeamDialog(clubs, self)

        if dialog.exec():
            data = dialog.get_data()

            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()

            try:
                club_name = self.get_club_name(cursor, data["club_id"])

                cursor.execute(
                    """
                    INSERT INTO teams (
                        club_id,
                        name,
                        short_name,
                        team_number
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        data["club_id"],
                        club_name,
                        data["team_name"],
                        data["team_number"],
                    ),
                )

                connection.commit()
                self.load_teams()

            except sqlite3.Error as error:
                QMessageBox.critical(
                    self,
                    "Datenbankfehler",
                    f"Mannschaft konnte nicht gespeichert werden:\n{error}",
                )

            finally:
                connection.close()

    def load_clubs_for_dialog(self):
        if not DATABASE_PATH.exists():
            return []

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    club_id,
                    name
                FROM clubs
                ORDER BY name ASC
                """
            )

            return cursor.fetchall()

        except sqlite3.Error:
            return []

        finally:
            connection.close()

    def get_club_name(self, cursor, club_id):
        cursor.execute(
            """
            SELECT name
            FROM clubs
            WHERE club_id = ?
            """,
            (club_id,),
        )

        result = cursor.fetchone()

        if result is None:
            raise ValueError("Verein wurde nicht gefunden.")

        return result[0]

    def format_team(self, team):
        team_id, team_name, short_name, team_number, club_name = team
        return f"{club_name} {short_name} | Mannschaft {team_number}"