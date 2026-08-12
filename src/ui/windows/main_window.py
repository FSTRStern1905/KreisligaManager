from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from src.core.module_registry import (
    create_default_registry,
)
from src.database.repository import Repository
from src.services.settings.module_settings_service import (
    ModuleSettingsService,
)
from src.ui.pages.calendar_page import CalendarPage
from src.ui.pages.import_page import ImportPage
from src.ui.pages.players_page import PlayersPage
from src.ui.sidebar.sidebar_manager import (
    SidebarManager,
)
from src.ui.windows.clubs_page import ClubsPage
from src.ui.windows.competition_workspace import (
    CompetitionWorkspace,
)
from src.ui.windows.dashboard import Dashboard
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

        self.registry = create_default_registry()

        self.module_settings_service = (
            ModuleSettingsService(
                self.registry
            )
        )

        self.module_settings = (
            self.module_settings_service.load()
        )

        self.sidebar = QListWidget()
        self.pages = QStackedWidget()

        self.page_instances: dict[
            str,
            QWidget,
        ] = {}

        self.sidebar_manager: (
            SidebarManager
            | None
        ) = None

        self.setWindowTitle(
            "KreisligaManager v0.5.0-dev"
        )

        self.resize(
            1280,
            800,
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        central_widget = QWidget()

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        self._setup_sidebar()
        self._create_pages()
        self._create_sidebar_manager()

        main_layout.addWidget(
            self.sidebar
        )

        main_layout.addWidget(
            self.pages,
            1,
        )

        self.setCentralWidget(
            central_widget
        )

        self.statusBar().showMessage(
            "Bereit"
        )

        if self.sidebar_manager is not None:
            self.sidebar_manager.build()

    def _setup_sidebar(self) -> None:
        self.sidebar.setFixedWidth(
            240
        )

        self.sidebar.setObjectName(
            "MainSidebar"
        )

        self.sidebar.setSpacing(
            2
        )

        self.sidebar.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    def _create_pages(self) -> None:
        dashboard = Dashboard(
            self.repository
        )

        clubs_page = ClubsPage()
        seasons_page = SeasonsPage()
        competition_workspace = (
            CompetitionWorkspace()
        )
        teams_page = TeamsPage()
        players_page = PlayersPage(
            self.repository
        )
        matches_page = MatchesPage()
        import_page = ImportPage()

        calendar_page = CalendarPage()

        calendar_page.match_requested.connect(
            self._open_match_from_calendar
        )

        statistics_placeholder = (
            self._create_placeholder(
                icon="📊",
                title="Statistiken",
                text=(
                    "Das Statistik-Modul "
                    "wird vorbereitet."
                ),
            )
        )

        settings_placeholder = (
            self._create_placeholder(
                icon="⚙",
                title="Einstellungen",
                text=(
                    "Hier entsteht die "
                    "Modulverwaltung."
                ),
            )
        )

        self.page_instances = {
            "dashboard": dashboard,
            "calendar": calendar_page,
            "clubs": clubs_page,
            "seasons": seasons_page,
            "competitions":
                competition_workspace,
            "teams": teams_page,
            "players": players_page,
            "matches": matches_page,
            "import": import_page,
            "statistics":
                statistics_placeholder,
            "settings":
                settings_placeholder,
        }

    def _create_sidebar_manager(
        self,
    ) -> None:
        refresh_callbacks = {
            "calendar": self._refresh_calendar,
            "clubs": self._refresh_clubs,
            "seasons": self._refresh_seasons,
            "competitions":
                self._refresh_competitions,
            "teams": self._refresh_teams,
            "players": self._refresh_players,
            "matches": self._refresh_matches,
            "import": self._refresh_import,
        }

        self.sidebar_manager = SidebarManager(
            registry=self.registry,
            settings=self.module_settings,
            sidebar=self.sidebar,
            pages=self.pages,
            page_instances=(
                self.page_instances
            ),
            refresh_callbacks=(
                refresh_callbacks
            ),
            parent=self,
        )

        self.sidebar_manager.module_changed.connect(
            self._on_module_changed
        )

    @staticmethod
    def _create_placeholder(
        icon: str,
        title: str,
        text: str,
    ) -> QLabel:
        label = QLabel(
            f"{icon}  {title}\n\n{text}"
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        label.setObjectName(
            "ModulePlaceholder"
        )

        return label

    @staticmethod
    def _refresh_calendar(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            CalendarPage,
        ):
            page.refresh_data()

    @staticmethod
    def _refresh_clubs(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            ClubsPage,
        ):
            page.load_clubs()

    @staticmethod
    def _refresh_seasons(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            SeasonsPage,
        ):
            page.load_seasons()

    @staticmethod
    def _refresh_competitions(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            CompetitionWorkspace,
        ):
            page.refresh()

    @staticmethod
    def _refresh_teams(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            TeamsPage,
        ):
            page.load_teams()

    @staticmethod
    def _refresh_players(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            PlayersPage,
        ):
            page.refresh()

    @staticmethod
    def _refresh_matches(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            MatchesPage,
        ):
            page.load_matches()

    @staticmethod
    def _refresh_import(
        page: QWidget,
    ) -> None:
        if isinstance(
            page,
            ImportPage,
        ):
            page.refresh_data()

    def _open_match_from_calendar(
        self,
        match_id: int,
    ) -> None:
        if match_id <= 0:
            return

        if not self.open_module(
            "matches"
        ):
            return

        page = self.page_instances.get(
            "matches"
        )

        if not isinstance(
            page,
            MatchesPage,
        ):
            return

        page.focus_match(
            match_id
        )

    def _on_module_changed(
        self,
        module_id: str,
    ) -> None:
        messages = {
            "dashboard":
                "🏠 Dashboard geöffnet",
            "calendar":
                "📅 Fußball-Kalender",
            "clubs":
                "🏟 Vereinsverwaltung",
            "seasons":
                "🗓 Saisonverwaltung",
            "competitions":
                "🏆 Wettbewerbs-Arbeitsbereich",
            "teams":
                "👥 Mannschaftsverwaltung",
            "players":
                "👤 Spielerverwaltung",
            "matches":
                "⚽ Spiele",
            "import":
                "📥 Spielplanimport",
            "statistics":
                "📊 Statistiken",
            "settings":
                "⚙ Einstellungen",
            "groundhopping":
                "🗺 Groundhopping",
            "photography":
                "📸 Fotografenmodus",
            "training":
                "🏋 Training",
            "simulation":
                "🎲 Simulation",
        }

        self.statusBar().showMessage(
            messages.get(
                module_id,
                "Modul geöffnet",
            )
        )

    def reload_module_settings(
        self,
    ) -> None:
        self.module_settings = (
            self.module_settings_service.load()
        )

        if self.sidebar_manager is None:
            return

        self.sidebar_manager.rebuild(
            self.module_settings
        )

    def open_module(
        self,
        module_id: str,
    ) -> bool:
        if self.sidebar_manager is None:
            return False

        return self.sidebar_manager.open_module(
            module_id
        )