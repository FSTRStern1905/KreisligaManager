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
)

from src.database.repositories.league_repository import LeagueRepository
from src.services.league_service import LeagueService
from src.ui.dialogs.league_dialog import LeagueDialog


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class LeaguesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setup_ui()
        self.connect_signals()
        self.load_leagues()

    def setup_ui(self):

        layout = QVBoxLayout()

        title = QLabel("🏆 Ligen")
        title.setObjectName("PageTitle")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Liga suchen...")

        self.league_list = QListWidget()

        button_layout = QHBoxLayout()

        self.new_button = QPushButton("➕ Neue Liga")
        self.edit_button = QPushButton("✏ Bearbeiten")
        self.delete_button = QPushButton("🗑 Löschen")

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        layout.addWidget(title)
        layout.addWidget(self.search)
        layout.addWidget(self.league_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.new_button.clicked.connect(self.new_league)
        self.search.textChanged.connect(self.filter_leagues)

    def load_leagues(self):

        self.league_list.clear()

        connection = sqlite3.connect(DATABASE_PATH)

        repository = LeagueRepository(connection)
        service = LeagueService(repository)

        self.leagues = service.get_all_leagues()

        for league in self.leagues:
            self.league_list.addItem(league.display_name)

        connection.close()

    def filter_leagues(self):

        search = self.search.text().lower()

        self.league_list.clear()

        for league in self.leagues:

            if search in league.display_name.lower():
                self.league_list.addItem(league.display_name)

    def new_league(self):

        dialog = LeagueDialog(self)

        if dialog.exec():

            data = dialog.get_data()

            connection = sqlite3.connect(DATABASE_PATH)

            repository = LeagueRepository(connection)
            service = LeagueService(repository)

            service.create_league(
                name=data["name"],
                level=data["level"],
            )

            connection.close()

            self.load_leagues()