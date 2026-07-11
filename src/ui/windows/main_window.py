from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from src.database.repository import Repository
from src.ui.windows.clubs_page import ClubsPage
from src.ui.windows.dashboard import Dashboard
from src.ui.windows.matches_page import MatchesPage
from src.ui.windows.seasons_page import SeasonsPage
from src.ui.windows.teams_page import TeamsPage


class MainWindow(QMainWindow):
    def __init__(self, repository: Repository):
        super().__init__()

        self.repository = repository

        self.setWindowTitle("KreisligaManager v0.2.0-dev")
        self.resize(1100, 700)

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)

        self.sidebar.addItems(
            [
                "Dashboard",
                "Vereine",
                "Saisons",
                "Mannschaften",
                "Spieler",
                "Spiele",
                "Import",
                "Statistiken",
                "Einstellungen",
            ]
        )

        self.pages = QStackedWidget()

        self.dashboard = Dashboard(self.repository)
        self.clubs_page = ClubsPage()
        self.seasons_page = SeasonsPage()
        self.teams_page = TeamsPage()
        self.matches_page = MatchesPage()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.clubs_page)
        self.pages.addWidget(self.seasons_page)
        self.pages.addWidget(self.teams_page)

        player_placeholder = QLabel("Spieler kommt später")
        player_placeholder.setAlignment(Qt.AlignCenter)
        self.pages.addWidget(player_placeholder)

        self.pages.addWidget(self.matches_page)

        placeholder_pages = [
            "Import",
            "Statistiken",
            "Einstellungen",
        ]

        for page_name in placeholder_pages:
            label = QLabel(f"{page_name} kommt später")
            label.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(label)

        self.sidebar.currentRowChanged.connect(self.change_page)
        self.sidebar.setCurrentRow(0)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("Bereit")

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

        current_text = self.sidebar.item(index).text()

        if current_text == "Dashboard":
            self.statusBar().showMessage("🏠 Dashboard geöffnet")

        elif current_text == "Vereine":
            self.clubs_page.load_clubs()
            self.statusBar().showMessage("🏟 Vereinsverwaltung")

        elif current_text == "Saisons":
            self.seasons_page.load_seasons()
            self.statusBar().showMessage("📅 Saisonverwaltung")

        elif current_text == "Mannschaften":
            self.teams_page.load_teams()
            self.statusBar().showMessage("👕 Mannschaftsverwaltung")

        elif current_text == "Spieler":
            self.statusBar().showMessage("👤 Spielerverwaltung")

        elif current_text == "Spiele":
            self.matches_page.load_matches()
            self.statusBar().showMessage(
                f"⚽ {len(self.matches_page.matches)} Spiele geladen"
            )

        elif current_text == "Import":
            self.statusBar().showMessage("📥 Import")

        elif current_text == "Statistiken":
            self.statusBar().showMessage("📊 Statistiken")

        elif current_text == "Einstellungen":
            self.statusBar().showMessage("⚙ Einstellungen")