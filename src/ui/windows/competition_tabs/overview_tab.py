import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.info_card import InfoCard


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionOverviewTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Übersicht")
        title.setObjectName("PageTitle")

        self.competition_name_label = QLabel("")
        self.competition_name_label.setObjectName("InfoLabel")

        card_layout = QGridLayout()

        self.league_card = InfoCard(
            title="Liga",
            value="-",
            icon="🏆",
        )

        self.season_card = InfoCard(
            title="Saison",
            value="-",
            icon="📅",
        )

        self.teams_card = InfoCard(
            title="Mannschaften",
            value="0",
            icon="👕",
        )

        self.matchdays_card = InfoCard(
            title="Spieltage",
            value="0",
            icon="📆",
        )

        self.matches_card = InfoCard(
            title="Spiele",
            value="0",
            icon="⚽",
        )

        self.status_card = InfoCard(
            title="Status",
            value="-",
            icon="🟢",
        )

        card_layout.addWidget(self.league_card, 0, 0)
        card_layout.addWidget(self.season_card, 0, 1)
        card_layout.addWidget(self.status_card, 0, 2)

        card_layout.addWidget(self.teams_card, 1, 0)
        card_layout.addWidget(self.matchdays_card, 1, 1)
        card_layout.addWidget(self.matches_card, 1, 2)

        layout.addWidget(title)
        layout.addWidget(self.competition_name_label)
        layout.addLayout(card_layout)
        layout.addStretch()

        self.setLayout(layout)

    def set_competition(self, competition_id: int | None):
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(self):
        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    competitions.name,
                    competitions.active,
                    leagues.name,
                    seasons.name
                FROM competitions
                LEFT JOIN leagues
                    ON leagues.league_id = competitions.league_id
                INNER JOIN seasons
                    ON seasons.season_id = competitions.season_id
                WHERE competitions.competition_id = ?
                """,
                (self.competition_id,),
            )

            competition = cursor.fetchone()

            if competition is None:
                self.clear_data()
                return

            competition_name = competition[0]
            active = bool(competition[1])
            league_name = competition[2] or "Keine Liga"
            season_name = competition[3]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM competition_teams
                WHERE competition_id = ?
                """,
                (self.competition_id,),
            )

            team_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    COUNT(DISTINCT matchday)
                FROM matches
                WHERE competition_id = ?
                """,
                (self.competition_id,),
            )

            match_count, matchday_count = cursor.fetchone()

            self.competition_name_label.setText(competition_name)
            self.league_card.set_value(league_name)
            self.season_card.set_value(season_name)
            self.teams_card.set_value(str(team_count))
            self.matchdays_card.set_value(str(matchday_count))
            self.matches_card.set_value(str(match_count))
            self.status_card.set_value(
                "Aktiv" if active else "Inaktiv"
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Wettbewerbsdaten konnten nicht geladen werden:\n{error}",
            )
            self.clear_data()

        finally:
            connection.close()

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.competition_name_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.league_card.set_value("-")
        self.season_card.set_value("-")
        self.teams_card.set_value("0")
        self.matchdays_card.set_value("0")
        self.matches_card.set_value("0")
        self.status_card.set_value("-")