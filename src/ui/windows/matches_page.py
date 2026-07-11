import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QLineEdit,
    QMessageBox,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class MatchesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.matches = []

        self.setup_ui()
        self.connect_signals()
        self.load_matches()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("⚽ Spiele")
        title.setObjectName("PageTitle")

        self.info_label = QLabel("")
        self.info_label.setObjectName("InfoLabel")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Spiel suchen...")

        self.match_list = QListWidget()

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.search)
        layout.addWidget(self.match_list)

        self.setLayout(layout)

    def connect_signals(self):
        self.search.textChanged.connect(self.filter_matches)

    def load_matches(self):
        self.matches.clear()
        self.match_list.clear()

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    m.matchday,
                    h.name,
                    h.short_name,
                    a.name,
                    a.short_name,
                    m.status
                FROM matches m
                JOIN teams h
                    ON h.team_id = m.home_team_id
                JOIN teams a
                    ON a.team_id = m.away_team_id
                ORDER BY
                    m.matchday,
                    m.match_id
                """
            )

            self.matches = cursor.fetchall()

            matchdays = len({match[0] for match in self.matches})
            matches = len(self.matches)

            self.info_label.setText(
                f"📅 {matchdays} Spieltage    ⚽ {matches} Spiele"
            )

            self.show_matches(self.matches)

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Fehler",
                str(error),
            )

        finally:
            connection.close()

    def filter_matches(self):
        search = self.search.text().lower().strip()

        filtered_matches = []

        for match in self.matches:
            text = (
                f"{match[1]} {match[2]} "
                f"{match[3]} {match[4]} "
                f"{match[5]}"
            ).lower()

            if search in text:
                filtered_matches.append(match)

        self.show_matches(filtered_matches)

    def show_matches(self, matches):
        self.match_list.clear()

        current_matchday = None

        for match in matches:
            matchday = match[0]
            home_name = match[1]
            home_short = match[2]
            away_name = match[3]
            away_short = match[4]
            status = match[5]

            if current_matchday != matchday:
                current_matchday = matchday

                self.match_list.addItem("")
                self.match_list.addItem(
                    f"========== Spieltag {current_matchday} =========="
                )

            self.match_list.addItem(
                f"{home_name} {home_short}  vs.  {away_name} {away_short}    [{status}]"
            )