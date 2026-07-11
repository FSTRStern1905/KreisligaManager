import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
from src.services.competition_service import CompetitionService


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionTeamsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Teilnehmer")
        title.setObjectName("PageTitle")

        self.info_label = QLabel("Kein Wettbewerb ausgewählt")
        self.info_label.setObjectName("InfoLabel")

        self.available_teams_list = QListWidget()
        self.selected_teams_list = QListWidget()

        available_layout = QVBoxLayout()
        available_layout.addWidget(
            QLabel("Verfügbare Mannschaften")
        )
        available_layout.addWidget(
            self.available_teams_list
        )

        available_widget = QWidget()
        available_widget.setLayout(available_layout)

        self.add_button = QPushButton("➡ Hinzufügen")
        self.remove_button = QPushButton("⬅ Entfernen")

        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        button_widget.setMaximumWidth(150)

        selected_layout = QVBoxLayout()
        selected_layout.addWidget(
            QLabel("Teilnehmende Mannschaften")
        )
        selected_layout.addWidget(
            self.selected_teams_list
        )

        self.team_count_label = QLabel(
            "0 Mannschaften ausgewählt"
        )

        selected_layout.addWidget(
            self.team_count_label
        )

        selected_widget = QWidget()
        selected_widget.setLayout(selected_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(available_widget)
        splitter.addWidget(button_widget)
        splitter.addWidget(selected_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([450, 140, 450])

        self.save_button = QPushButton(
            "💾 Mannschaftsauswahl speichern"
        )
        self.save_button.setEnabled(False)

        main_layout.addWidget(title)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.save_button)

        self.setLayout(main_layout)

    def connect_signals(self):
        self.add_button.clicked.connect(
            self.add_selected_teams
        )

        self.remove_button.clicked.connect(
            self.remove_selected_teams
        )

        self.available_teams_list.itemDoubleClicked.connect(
            self.add_team_item
        )

        self.selected_teams_list.itemDoubleClicked.connect(
            self.remove_team_item
        )

        self.save_button.clicked.connect(
            self.save_teams
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
        self.available_teams_list.clear()
        self.selected_teams_list.clear()

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = CompetitionRepository(connection)
            service = CompetitionService(repository)

            competition = service.get_competition(
                self.competition_id
            )

            if competition is None:
                self.clear_data()
                return

            self.info_label.setText(
                competition.name
            )

            all_teams = service.get_all_teams()

            selected_team_ids = set(
                service.get_competition_team_ids(
                    self.competition_id
                )
            )

            for team in all_teams:
                item = self.create_team_item(team)

                if team[0] in selected_team_ids:
                    self.selected_teams_list.addItem(item)
                else:
                    self.available_teams_list.addItem(item)

            self.save_button.setEnabled(True)
            self.update_team_count()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Mannschaften konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def create_team_item(
        self,
        team: tuple,
    ) -> QListWidgetItem:
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
            display_text += (
                f" | Mannschaft {team_number}"
            )

        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, team_id)

        return item

    def add_selected_teams(self):
        selected_items = (
            self.available_teams_list.selectedItems()
        )

        for item in selected_items:
            row = self.available_teams_list.row(item)

            moved_item = (
                self.available_teams_list.takeItem(row)
            )

            self.selected_teams_list.addItem(
                moved_item
            )

        self.update_team_count()

    def remove_selected_teams(self):
        selected_items = (
            self.selected_teams_list.selectedItems()
        )

        for item in selected_items:
            row = self.selected_teams_list.row(item)

            moved_item = (
                self.selected_teams_list.takeItem(row)
            )

            self.available_teams_list.addItem(
                moved_item
            )

        self.update_team_count()

    def add_team_item(
        self,
        item: QListWidgetItem,
    ):
        row = self.available_teams_list.row(item)

        moved_item = (
            self.available_teams_list.takeItem(row)
        )

        self.selected_teams_list.addItem(
            moved_item
        )

        self.update_team_count()

    def remove_team_item(
        self,
        item: QListWidgetItem,
    ):
        row = self.selected_teams_list.row(item)

        moved_item = (
            self.selected_teams_list.takeItem(row)
        )

        self.available_teams_list.addItem(
            moved_item
        )

        self.update_team_count()

    def save_teams(self):
        if self.competition_id is None:
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
                (
                    "Ein Wettbewerb benötigt "
                    "mindestens zwei Mannschaften."
                ),
            )
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = CompetitionRepository(connection)
            service = CompetitionService(repository)

            service.save_competition_teams(
                self.competition_id,
                team_ids,
            )

            QMessageBox.information(
                self,
                "Gespeichert",
                (
                    "Die Mannschaftsauswahl wurde "
                    "erfolgreich gespeichert.\n\n"
                    f"Mannschaften: {len(team_ids)}"
                ),
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die Mannschaftsauswahl konnte "
                    f"nicht gespeichert werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def get_selected_team_ids(self) -> list[int]:
        team_ids = []

        for index in range(
            self.selected_teams_list.count()
        ):
            item = self.selected_teams_list.item(index)

            team_ids.append(
                item.data(Qt.UserRole)
            )

        return team_ids

    def update_team_count(self):
        count = self.selected_teams_list.count()

        self.team_count_label.setText(
            f"{count} Mannschaften ausgewählt"
        )

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.available_teams_list.clear()
        self.selected_teams_list.clear()

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.save_button.setEnabled(False)

        self.update_team_count()