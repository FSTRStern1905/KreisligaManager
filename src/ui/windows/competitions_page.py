import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import LeagueRepository
from src.services.competition_service import CompetitionService
from src.services.season_service import SeasonService
from src.ui.dialogs.competition_dialog import CompetitionDialog


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.competitions = []
        self.all_teams = []
        self.selected_competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.load_competitions()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("🏆 Wettbewerbe")
        title.setObjectName("PageTitle")

        self.info_label = QLabel("")
        self.info_label.setObjectName("InfoLabel")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Wettbewerb suchen...")

        self.competition_list = QListWidget()

        self.new_button = QPushButton("➕ Neuer Wettbewerb")

        competition_layout = QVBoxLayout()
        competition_layout.addWidget(QLabel("Wettbewerbe"))
        competition_layout.addWidget(self.search)
        competition_layout.addWidget(self.competition_list)
        competition_layout.addWidget(self.new_button)

        competition_widget = QWidget()
        competition_widget.setLayout(competition_layout)
        competition_widget.setMinimumWidth(320)

        self.available_teams_list = QListWidget()
        self.selected_teams_list = QListWidget()

        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("Verfügbare Mannschaften"))
        available_layout.addWidget(self.available_teams_list)

        available_widget = QWidget()
        available_widget.setLayout(available_layout)
        available_widget.setMinimumWidth(320)

        self.add_team_button = QPushButton("➡ Hinzufügen")
        self.remove_team_button = QPushButton("⬅ Entfernen")

        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.add_team_button)
        button_layout.addWidget(self.remove_team_button)
        button_layout.addStretch()

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        button_widget.setMaximumWidth(140)

        selected_layout = QVBoxLayout()
        selected_layout.addWidget(QLabel("Teilnehmende Mannschaften"))
        selected_layout.addWidget(self.selected_teams_list)

        self.team_count_label = QLabel("0 Mannschaften ausgewählt")
        selected_layout.addWidget(self.team_count_label)

        selected_widget = QWidget()
        selected_widget.setLayout(selected_layout)
        selected_widget.setMinimumWidth(320)

        team_splitter = QSplitter(Qt.Horizontal)
        team_splitter.addWidget(available_widget)
        team_splitter.addWidget(button_widget)
        team_splitter.addWidget(selected_widget)

        team_splitter.setStretchFactor(0, 1)
        team_splitter.setStretchFactor(1, 0)
        team_splitter.setStretchFactor(2, 1)
        team_splitter.setSizes([420, 120, 420])

        self.save_teams_button = QPushButton(
            "💾 Mannschaftsauswahl speichern"
        )
        self.save_teams_button.setEnabled(False)

        self.generate_schedule_button = QPushButton(
            "⚽ Spielplan erzeugen"
        )
        self.generate_schedule_button.setEnabled(False)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.save_teams_button)
        action_layout.addWidget(self.generate_schedule_button)

        teams_layout = QVBoxLayout()
        teams_layout.addWidget(team_splitter)
        teams_layout.addLayout(action_layout)

        teams_widget = QWidget()
        teams_widget.setLayout(teams_layout)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(competition_widget)
        content_splitter.addWidget(teams_widget)

        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([360, 1000])

        main_layout.addWidget(title)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(content_splitter)

        self.setLayout(main_layout)

    def connect_signals(self):
        self.new_button.clicked.connect(self.new_competition)
        self.search.textChanged.connect(self.filter_competitions)

        self.competition_list.currentItemChanged.connect(
            self.competition_changed
        )

        self.add_team_button.clicked.connect(self.add_selected_teams)
        self.remove_team_button.clicked.connect(
            self.remove_selected_teams
        )

        self.available_teams_list.itemDoubleClicked.connect(
            self.add_team_item
        )
        self.selected_teams_list.itemDoubleClicked.connect(
            self.remove_team_item
        )

        self.save_teams_button.clicked.connect(
            self.save_competition_teams
        )

        self.generate_schedule_button.clicked.connect(
            self.generate_schedule
        )

    def load_competitions(self):
        self.competitions.clear()
        self.competition_list.clear()

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = CompetitionRepository(connection)
            service = CompetitionService(repository)

            self.competitions = service.get_all_competitions()

            self.info_label.setText(
                f"🏆 {len(self.competitions)} Wettbewerbe"
            )

            for competition in self.competitions:
                self.add_competition_item(
                    connection,
                    competition,
                )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Wettbewerbe konnten nicht geladen werden:\n{error}",
            )

        finally:
            connection.close()

        if self.competition_list.count() > 0:
            self.competition_list.setCurrentRow(0)
        else:
            self.clear_team_lists()

    def add_competition_item(self, connection, competition):
        display_text = self.format_competition(
            connection,
            competition,
        )

        item = QListWidgetItem(display_text)
        item.setData(
            Qt.UserRole,
            competition.competition_id,
        )

        self.competition_list.addItem(item)

    def filter_competitions(self):
        search_text = self.search.text().lower().strip()

        self.competition_list.clear()

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            for competition in self.competitions:
                display_text = self.format_competition(
                    connection,
                    competition,
                )

                if search_text in display_text.lower():
                    item = QListWidgetItem(display_text)
                    item.setData(
                        Qt.UserRole,
                        competition.competition_id,
                    )
                    self.competition_list.addItem(item)

        finally:
            connection.close()

        if self.competition_list.count() > 0:
            self.competition_list.setCurrentRow(0)
        else:
            self.clear_team_lists()

    def competition_changed(self, current, previous):
        if current is None:
            self.clear_team_lists()
            return

        competition_id = current.data(Qt.UserRole)

        if competition_id is None:
            self.clear_team_lists()
            return

        self.selected_competition_id = competition_id
        self.load_competition_teams()

    def load_competition_teams(self):
        self.available_teams_list.clear()
        self.selected_teams_list.clear()

        if self.selected_competition_id is None:
            self.save_teams_button.setEnabled(False)
            self.generate_schedule_button.setEnabled(False)
            self.update_team_count()
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = CompetitionRepository(connection)
            service = CompetitionService(repository)

            self.all_teams = service.get_all_teams()

            selected_team_ids = set(
                service.get_competition_team_ids(
                    self.selected_competition_id
                )
            )

            for team in self.all_teams:
                item = self.create_team_item(team)

                if team[0] in selected_team_ids:
                    self.selected_teams_list.addItem(item)
                else:
                    self.available_teams_list.addItem(item)

            self.save_teams_button.setEnabled(True)
            self.generate_schedule_button.setEnabled(
                len(selected_team_ids) >= 2
            )

            self.update_team_count()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Mannschaften konnten nicht geladen werden:\n{error}",
            )

        finally:
            connection.close()

    def create_team_item(self, team):
        team_id = team[0]
        club_name = team[1]
        team_name = team[2]
        short_name = team[3]
        team_number = team[4]

        display_text = club_name

        if short_name:
            display_text += f" {short_name}"
        elif team_name and team_name != club_name:
            display_text += f" - {team_name}"

        if team_number:
            display_text += f" | Mannschaft {team_number}"

        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, team_id)

        return item

    def add_selected_teams(self):
        selected_items = self.available_teams_list.selectedItems()

        for item in selected_items:
            row = self.available_teams_list.row(item)
            moved_item = self.available_teams_list.takeItem(row)
            self.selected_teams_list.addItem(moved_item)

        self.update_team_count()

    def remove_selected_teams(self):
        selected_items = self.selected_teams_list.selectedItems()

        for item in selected_items:
            row = self.selected_teams_list.row(item)
            moved_item = self.selected_teams_list.takeItem(row)
            self.available_teams_list.addItem(moved_item)

        self.update_team_count()

    def add_team_item(self, item):
        row = self.available_teams_list.row(item)
        moved_item = self.available_teams_list.takeItem(row)
        self.selected_teams_list.addItem(moved_item)

        self.update_team_count()

    def remove_team_item(self, item):
        row = self.selected_teams_list.row(item)
        moved_item = self.selected_teams_list.takeItem(row)
        self.available_teams_list.addItem(moved_item)

        self.update_team_count()

    def save_competition_teams(self):
        if self.selected_competition_id is None:
            QMessageBox.warning(
                self,
                "Kein Wettbewerb ausgewählt",
                "Bitte wähle zuerst einen Wettbewerb aus.",
            )
            return

        team_ids = self.get_selected_team_ids()

        if len(team_ids) < 2:
            QMessageBox.warning(
                self,
                "Zu wenige Mannschaften",
                "Ein Wettbewerb benötigt mindestens zwei Mannschaften.",
            )
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = CompetitionRepository(connection)
            service = CompetitionService(repository)

            service.save_competition_teams(
                self.selected_competition_id,
                team_ids,
            )

            self.generate_schedule_button.setEnabled(True)

            QMessageBox.information(
                self,
                "Gespeichert",
                (
                    "Die Mannschaftsauswahl wurde gespeichert.\n\n"
                    f"Mannschaften: {len(team_ids)}"
                ),
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                f"Auswahl konnte nicht gespeichert werden:\n{error}",
            )

        finally:
            connection.close()

    def generate_schedule(self):
        if self.selected_competition_id is None:
            QMessageBox.warning(
                self,
                "Kein Wettbewerb ausgewählt",
                "Bitte wähle zuerst einen Wettbewerb aus.",
            )
            return

        team_count = self.selected_teams_list.count()

        if team_count < 2:
            QMessageBox.warning(
                self,
                "Zu wenige Mannschaften",
                "Der Wettbewerb benötigt mindestens zwei Mannschaften.",
            )
            return

        confirm = QMessageBox.question(
            self,
            "Spielplan erzeugen",
            (
                "Soll der Spielplan für den ausgewählten Wettbewerb "
                "erzeugt werden?"
            ),
        )

        if confirm != QMessageBox.Yes:
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            service = SeasonService(connection)

            result = service.generate_schedule_for_competition(
                self.selected_competition_id
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

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Spielplan konnte nicht erzeugt werden",
                str(error),
            )

        finally:
            connection.close()

    def get_selected_team_ids(self):
        team_ids = []

        for index in range(self.selected_teams_list.count()):
            item = self.selected_teams_list.item(index)
            team_ids.append(item.data(Qt.UserRole))

        return team_ids

    def new_competition(self):
        connection = sqlite3.connect(DATABASE_PATH)

        try:
            league_repository = LeagueRepository(connection)
            leagues = league_repository.get_all()

            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    season_id,
                    name
                FROM seasons
                ORDER BY start_date DESC, name DESC
                """
            )

            seasons = cursor.fetchall()

            if not leagues:
                QMessageBox.warning(
                    self,
                    "Keine Ligen vorhanden",
                    "Bitte lege zuerst mindestens eine Liga an.",
                )
                return

            if not seasons:
                QMessageBox.warning(
                    self,
                    "Keine Saisons vorhanden",
                    "Bitte lege zuerst mindestens eine Saison an.",
                )
                return

            dialog = CompetitionDialog(
                leagues,
                seasons,
                self,
            )

            if not dialog.exec():
                return

            data = dialog.get_data()

            repository = CompetitionRepository(connection)
            service = CompetitionService(repository)

            service.create_competition(
                name=data["name"],
                league_id=data["league_id"],
                season_id=data["season_id"],
                active=data["active"],
            )

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Wettbewerb konnte nicht gespeichert werden:\n{error}",
            )
            return

        finally:
            connection.close()

        self.load_competitions()

    def clear_team_lists(self):
        self.selected_competition_id = None
        self.all_teams = []

        self.available_teams_list.clear()
        self.selected_teams_list.clear()

        self.save_teams_button.setEnabled(False)
        self.generate_schedule_button.setEnabled(False)

        self.update_team_count()

    def update_team_count(self):
        count = self.selected_teams_list.count()

        self.team_count_label.setText(
            f"{count} Mannschaften ausgewählt"
        )

    def format_competition(self, connection, competition):
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM leagues
            WHERE league_id = ?
            """,
            (competition.league_id,),
        )

        league_result = cursor.fetchone()
        league_name = (
            league_result[0]
            if league_result is not None
            else "Keine Liga"
        )

        cursor.execute(
            """
            SELECT name
            FROM seasons
            WHERE season_id = ?
            """,
            (competition.season_id,),
        )

        season_result = cursor.fetchone()
        season_name = (
            season_result[0]
            if season_result is not None
            else "Keine Saison"
        )

        status = "Aktiv" if competition.active else "Inaktiv"

        return (
            f"{competition.name} | "
            f"{league_name} | "
            f"{season_name} | "
            f"{status}"
        )