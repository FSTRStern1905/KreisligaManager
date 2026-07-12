import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.match_repository import MatchRepository
from src.services.match_service import MatchService
from src.services.season_service import SeasonService
from src.ui.dialogs.match_dialog import MatchDialog


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

        self.info_label = QLabel("Kein Wettbewerb ausgewählt")
        self.info_label.setObjectName("InfoLabel")

        self.schedule_tree = QTreeWidget()
        self.schedule_tree.setColumnCount(5)
        self.schedule_tree.setHeaderLabels(
            [
                "Heim",
                "Ergebnis",
                "Auswärts",
                "Status",
                "Spiel-ID",
            ]
        )

        self.schedule_tree.setColumnHidden(4, True)
        self.schedule_tree.setRootIsDecorated(True)
        self.schedule_tree.setAlternatingRowColors(True)
        self.schedule_tree.setUniformRowHeights(True)

        header = self.schedule_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(
            0,
            header.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            1,
            header.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            header.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            3,
            header.ResizeMode.ResizeToContents,
        )

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
        main_layout.addWidget(self.schedule_tree)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_signals(self):
        self.generate_button.clicked.connect(
            self.generate_schedule
        )

        self.refresh_button.clicked.connect(
            self.load_data
        )

        self.schedule_tree.itemDoubleClicked.connect(
            self.edit_match
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
        self.schedule_tree.clear()
        self.matches.clear()

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            competition_repository = CompetitionRepository(
                connection
            )
            competition = competition_repository.get_by_id(
                self.competition_id
            )

            if competition is None:
                self.clear_data()
                return

            match_repository = MatchRepository(connection)
            match_service = MatchService(match_repository)

            self.matches = (
                match_service.get_matches_by_competition(
                    self.competition_id
                )
            )

            matchday_count = len(
                {
                    match.matchday
                    for match in self.matches
                    if match.matchday is not None
                }
            )

            self.info_label.setText(
                f"{competition.name} | "
                f"{matchday_count} Spieltage | "
                f"{len(self.matches)} Spiele"
            )

            if not self.matches:
                self.generate_button.setEnabled(True)
                self.refresh_button.setEnabled(True)
                return

            self.show_schedule()

            self.generate_button.setEnabled(False)
            self.refresh_button.setEnabled(True)

        except (sqlite3.Error, ValueError) as error:
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
        matchday_items = {}

        for match in self.matches:
            matchday = match.matchday

            if matchday not in matchday_items:
                matchday_item = QTreeWidgetItem(
                    [
                        f"Spieltag {matchday}",
                        "",
                        "",
                        "",
                        "",
                    ]
                )

                matchday_item.setFirstColumnSpanned(True)
                matchday_item.setExpanded(True)
                matchday_item.setFlags(
                    matchday_item.flags()
                    & ~Qt.ItemIsSelectable
                )

                self.schedule_tree.addTopLevelItem(
                    matchday_item
                )

                matchday_items[matchday] = matchday_item

            match_item = QTreeWidgetItem(
                [
                    match.home_team_name,
                    match.result_text,
                    match.away_team_name,
                    self.format_status(match.status),
                    str(match.match_id),
                ]
            )

            match_item.setTextAlignment(
                1,
                Qt.AlignCenter,
            )

            matchday_items[matchday].addChild(
                match_item
            )

    def edit_match(
        self,
        item: QTreeWidgetItem,
        column: int,
    ):
        if item.parent() is None:
            return

        match_id_text = item.text(4)

        if not match_id_text:
            return

        try:
            match_id = int(match_id_text)
        except ValueError:
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = MatchRepository(connection)
            service = MatchService(repository)

            match = service.get_match(match_id)

            if match is None:
                QMessageBox.warning(
                    self,
                    "Spiel nicht gefunden",
                    "Das ausgewählte Spiel wurde nicht gefunden.",
                )
                return

            stadiums = repository.get_all_stadiums()
            referees = repository.get_all_referees()

            dialog = MatchDialog(
                match_data={
                    "match_id": match.match_id,
                    "home_team": match.home_team_name,
                    "away_team": match.away_team_name,
                    "home_goals": match.home_goals,
                    "away_goals": match.away_goals,
                    "date": match.match_date,
                    "time": match.kickoff_time,
                    "stadium_id": match.stadium_id,
                    "referee_id": match.referee_id,
                    "attendance": match.attendance,
                    "status": match.status,
                    "notes": match.notes,
                },
                stadiums=stadiums,
                referees=referees,
                parent=self,
            )

            if not dialog.exec():
                return

            data = dialog.get_data()

            service.update_match(
                match_id=match_id,
                home_goals=data["home_goals"],
                away_goals=data["away_goals"],
                match_date=data["date"],
                kickoff_time=data["time"],
                attendance=data["attendance"],
                stadium_id=data["stadium_id"],
                referee_id=data["referee_id"],
                status=data["status"],
                notes=data["notes"],
            )

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Fehler",
                (
                    "Das Spiel konnte nicht "
                    f"gespeichert werden:\n{error}"
                ),
            )
            return

        finally:
            connection.close()

        self.load_data()

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

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Spielplan konnte nicht erzeugt werden",
                str(error),
            )
            return

        finally:
            connection.close()

        self.load_data()

    def format_status(
        self,
        status: str | None,
    ) -> str:
        status_map = {
            "scheduled": "🟡 Geplant",
            "live": "🔵 Live",
            "finished": "🟢 Beendet",
            "postponed": "🟠 Verlegt",
            "cancelled": "🔴 Abgesagt",
            "abandoned": "🔴 Abgebrochen",
        }

        return status_map.get(
            status or "",
            status or "Unbekannt",
        )

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.matches.clear()
        self.schedule_tree.clear()

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.generate_button.setEnabled(False)
        self.refresh_button.setEnabled(False)