import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.season_service import SeasonService


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionScheduleTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None
        self.matches = []

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Spielplan")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.schedule_list = QListWidget()

        button_layout = QHBoxLayout()

        self.generate_button = QPushButton(
            "⚽ Spielplan erzeugen"
        )

        self.refresh_button = QPushButton(
            "🔄 Aktualisieren"
        )

        self.generate_button.setEnabled(False)
        self.refresh_button.setEnabled(False)

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()

        main_layout.addWidget(title)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.schedule_list)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_signals(self):
        self.generate_button.clicked.connect(
            self.generate_schedule
        )

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
        self.schedule_list.clear()
        self.matches.clear()

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
                    matches.matchday,
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
                    matches.match_id
                """,
                (self.competition_id,),
            )

            self.matches = cursor.fetchall()

            matchday_count = len(
                {
                    match[0]
                    for match in self.matches
                }
            )

            match_count = len(self.matches)

            self.info_label.setText(
                f"{competition_name} | "
                f"{matchday_count} Spieltage | "
                f"{match_count} Spiele"
            )

            if not self.matches:
                self.schedule_list.addItem(
                    "Noch kein Spielplan vorhanden."
                )

                self.generate_button.setEnabled(True)
                self.refresh_button.setEnabled(True)
                return

            self.show_schedule()

            self.generate_button.setEnabled(False)
            self.refresh_button.setEnabled(True)

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Der Spielplan konnte nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_schedule(self):
        current_matchday = None

        for match in self.matches:
            matchday = match[0]
            home_name = match[1]
            home_short_name = match[2]
            away_name = match[3]
            away_short_name = match[4]
            home_goals = match[5]
            away_goals = match[6]
            status = match[7]

            if matchday != current_matchday:
                current_matchday = matchday

                if self.schedule_list.count() > 0:
                    self.schedule_list.addItem("")

                self.schedule_list.addItem(
                    f"========== Spieltag {matchday} =========="
                )

            home_display = self.format_team_name(
                home_name,
                home_short_name,
            )

            away_display = self.format_team_name(
                away_name,
                away_short_name,
            )

            if (
                home_goals is not None
                and away_goals is not None
            ):
                result_text = (
                    f"{home_goals} : {away_goals}"
                )
            else:
                result_text = "- : -"

            self.schedule_list.addItem(
                f"{home_display}  "
                f"{result_text}  "
                f"{away_display}  "
                f"[{status}]"
            )

    def generate_schedule(self):
        if self.competition_id is None:
            QMessageBox.warning(
                self,
                "Kein Wettbewerb ausgewählt",
                "Bitte wähle zuerst einen Wettbewerb aus.",
            )
            return

        confirm = QMessageBox.question(
            self,
            "Spielplan erzeugen",
            (
                "Soll für den ausgewählten Wettbewerb "
                "ein Spielplan erzeugt werden?"
            ),
        )

        if confirm != QMessageBox.Yes:
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            service = SeasonService(connection)

            result = service.generate_schedule_for_competition(
                self.competition_id
            )

            QMessageBox.information(
                self,
                "Spielplan erzeugt",
                (
                    "Der Spielplan wurde erfolgreich erzeugt.\n\n"
                    f"Mannschaften: {result['team_count']}\n"
                    f"Spieltage: {result['matchday_count']}\n"
                    f"Spiele: {result['match_count']}"
                ),
            )

            self.load_data()

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Spielplan konnte nicht erzeugt werden",
                str(error),
            )

        finally:
            connection.close()

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
        self.schedule_list.clear()

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.generate_button.setEnabled(False)
        self.refresh_button.setEnabled(False)