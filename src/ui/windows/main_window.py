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
from src.ui.pages.import_page import ImportPage
from src.ui.windows.clubs_page import ClubsPage
from src.ui.windows.competition_workspace import CompetitionWorkspace
from src.ui.windows.dashboard import Dashboard
from src.ui.windows.leagues_page import LeaguesPage
from src.ui.windows.matches_page import MatchesPage
from src.ui.windows.seasons_page import SeasonsPage
from src.ui.windows.teams_page import TeamsPage


class MainWindow(QMainWindow):

    def __init__(
        self,
        repository: Repository,
    ) -> None:
        super().__init__()

        self.repository = repository

        self.setWindowTitle(
            "KreisligaManager v0.4.0-dev"
        )
        self.resize(
            1200,
            760,
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        central_widget = QWidget()
        main_layout = QHBoxLayout(
            central_widget
        )

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(
            220
        )

        self.sidebar.addItems(
            [
                "Dashboard",
                "Vereine",
                "Ligen",
                "Saisons",
                "Wettbewerbe",
                "Mannschaften",
                "Spieler",
                "Spiele",
                "Import",
                "Statistiken",
                "Einstellungen",
            ]
        )

        self.pages = QStackedWidget()

        self.dashboard = Dashboard(
            self.repository
        )
        self.clubs_page = ClubsPage()
        self.leagues_page = LeaguesPage()
        self.seasons_page = SeasonsPage()
        self.competition_workspace = (
            CompetitionWorkspace()
        )
        self.teams_page = TeamsPage()
        self.matches_page = MatchesPage()
        self.import_page = ImportPage()

        self.pages.addWidget(
            self.dashboard
        )
        self.pages.addWidget(
            self.clubs_page
        )
        self.pages.addWidget(
            self.leagues_page
        )
        self.pages.addWidget(
            self.seasons_page
        )
        self.pages.addWidget(
            self.competition_workspace
        )
        self.pages.addWidget(
            self.teams_page
        )

        player_placeholder = QLabel(
            "Spielerverwaltung kommt "
            "in einem späteren Sprint"
        )
        player_placeholder.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.pages.addWidget(
            player_placeholder
        )

        self.pages.addWidget(
            self.matches_page
        )
        self.pages.addWidget(
            self.import_page
        )

        statistics_placeholder = QLabel(
            "Statistiken kommen später"
        )
        statistics_placeholder.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.pages.addWidget(
            statistics_placeholder
        )

        settings_placeholder = QLabel(
            "Einstellungen kommen später"
        )
        settings_placeholder.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.pages.addWidget(
            settings_placeholder
        )

        self.sidebar.currentRowChanged.connect(
            self.change_page
        )
        self.sidebar.setCurrentRow(
            0
        )

        main_layout.addWidget(
            self.sidebar
        )
        main_layout.addWidget(
            self.pages
        )

        self.setCentralWidget(
            central_widget
        )

        self.statusBar().showMessage(
            "Bereit"
        )

    def change_page(
        self,
        index: int,
    ) -> None:
        self.pages.setCurrentIndex(
            index
        )

        current_item = self.sidebar.item(
            index
        )

        if current_item is None:
            return

        current_text = current_item.text()

        if current_text == "Dashboard":
            self.statusBar().showMessage(
                "🏠 Dashboard geöffnet"
            )

        elif current_text == "Vereine":
            self.clubs_page.load_clubs()
            self.statusBar().showMessage(
                "🏟 Vereinsverwaltung"
            )

        elif current_text == "Ligen":
            self.leagues_page.load_leagues()
            self.statusBar().showMessage(
                "🏆 Ligaverwaltung"
            )

        elif current_text == "Saisons":
            self.seasons_page.load_seasons()
            self.statusBar().showMessage(
                "📅 Saisonverwaltung"
            )

        elif current_text == "Wettbewerbe":
            self.competition_workspace.refresh()
            self.statusBar().showMessage(
                "🏆 Wettbewerbs-Arbeitsbereich"
            )

        elif current_text == "Mannschaften":
            self.teams_page.load_teams()
            self.statusBar().showMessage(
                "👕 Mannschaftsverwaltung"
            )

        elif current_text == "Spieler":
            self.statusBar().showMessage(
                "👤 Spielerverwaltung"
            )

        elif current_text == "Spiele":
            self.matches_page.load_matches()
            self.statusBar().showMessage(
                f"⚽ {len(self.matches_page.matches)} "
                "Spiele geladen"
            )

        elif current_text == "Import":
            self.statusBar().showMessage(
                "📥 Spielplanimport"
            )

        elif current_text == "Statistiken":
            self.statusBar().showMessage(
                "📊 Statistiken"
            )

        elif current_text == "Einstellungen":
            self.statusBar().showMessage(
                "⚙ Einstellungen"
            )

        elif current_text == "Import":
            self.import_page.refresh_data()
            self.statusBar().showMessage(
                "📥 Spielplanimport"
            )    