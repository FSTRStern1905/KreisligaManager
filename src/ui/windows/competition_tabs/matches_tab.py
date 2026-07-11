import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionMatchesTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None
        self.matches = []

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Spiele")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.match_list = QListWidget()

        self.refresh_button = QPushButton(
            "🔄 Spiele aktualisieren"
        )
        self.refresh_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.match_list)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def connect_signals(self):
        self.refresh_button.clicked.connect(
            self.load_data
        )

    def set_competition(
        self,
        competition_id: int | None,
    ):
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(self):
        self.matches.clear()
        self.match_list.clear()

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT name
                FROM competitions
                WHERE competition_id = ?
                """,
                (self.competition_id,),
            )

            competition = cursor.fetchone()

            if competition is None:
                self.clear_data()
                return

            competition_name = competition[0]

            cursor.execute(
                """
                SELECT
                    matches.match_id,
                    matches.matchday,
                    matches.match_date,
                    matches.kickoff_time,
                    home_teams.name,
                    home_teams.short_name,
                    away_teams.name,
                    away_teams.short_name,
                    matches.home_goals,
                    matches.away_goals,
                    matches.status
                FROM matches
                INNER JOIN teams AS home_teams
                    ON home_teams.team_id =
                       matches.home_team_id
                INNER JOIN teams AS away_teams
                    ON away_teams.team_id =
                       matches.away_team_id
                WHERE matches.competition_id = ?
                ORDER BY
                    matches.matchday,
                    matches.match_date,
                    matches.kickoff_time,
                    matches.match_id
                """,
                (self.competition_id,),
            )

            self.matches = cursor.fetchall()

            played_count = sum(
                1
                for match in self.matches
                if match[8] is not None
                and match[9] is not None
            )

            open_count = len(self.matches) - played_count

            self.info_label.setText(
                f"{competition_name} | "
                f"{len(self.matches)} Spiele | "
                f"{played_count} beendet | "
                f"{open_count} offen"
            )

            if not self.matches:
                self.match_list.addItem(
                    "Noch keine Spiele vorhanden."
                )
            else:
                self.show_matches()

            self.refresh_button.setEnabled(True)

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die Spiele konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_matches(self):
        current_matchday = None

        for match in self.matches:
            matchday = match[1]
            match_date = match[2]
            kickoff_time = match[3]

            home_name = self.format_team_name(
                match[4],
                match[5],
            )

            away_name = self.format_team_name(
                match[6],
                match[7],
            )

            home_goals = match[8]
            away_goals = match[9]
            status = match[10]

            if matchday != current_matchday:
                current_matchday = matchday

                if self.match_list.count() > 0:
                    self.match_list.addItem("")

                self.match_list.addItem(
                    f"========== Spieltag {matchday} =========="
                )

            date_text = match_date or "Kein Datum"
            time_text = kickoff_time or "--:--"

            if (
                home_goals is not None
                and away_goals is not None
            ):
                result_text = (
                    f"{home_goals} : {away_goals}"
                )
            else:
                result_text = "- : -"

            self.match_list.addItem(
                f"{date_text} | "
                f"{time_text} | "
                f"{home_name}  "
                f"{result_text}  "
                f"{away_name}  "
                f"[{status}]"
            )

    def format_team_name(
        self,
        name: str,
        short_name: str | None,
    ) -> str:
        if short_name:
            return f"{name} {short_name}"

        return name

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.matches.clear()
        self.match_list.clear()

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(False)