import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import (
    LeagueRepository,
)
from src.services.competition_service import CompetitionService
from src.ui.dialogs.competition_dialog import CompetitionDialog
from src.ui.windows.competition_tabs.away_table_tab import (
    CompetitionAwayTableTab,
)
from src.ui.windows.competition_tabs.fairplay_tab import (
    CompetitionFairplayTab,
)
from src.ui.windows.competition_tabs.home_table_tab import (
    CompetitionHomeTableTab,
)
from src.ui.windows.competition_tabs.matches_tab import (
    CompetitionMatchesTab,
)
from src.ui.windows.competition_tabs.overview_tab import (
    CompetitionOverviewTab,
)
from src.ui.windows.competition_tabs.schedule_tab import (
    CompetitionScheduleTab,
)
from src.ui.windows.competition_tabs.statistics_tab import (
    CompetitionStatisticsTab,
)
from src.ui.windows.competition_tabs.table_tab import (
    CompetitionTableTab,
)
from src.ui.windows.competition_tabs.teams_tab import (
    CompetitionTeamsTab,
)
from src.ui.windows.competition_tabs.form_tab import (
    CompetitionFormTab,
)
from src.ui.windows.competition_tabs.home_away_tab import (
    CompetitionHomeAwayTab,
)
from src.ui.windows.competition_tabs.goal_timeline_tab import (
    CompetitionGoalTimelineTab,
)
from src.ui.windows.competition_tabs.goal_difference_tab import (
    CompetitionGoalDifferenceTab,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionWorkspace(QWidget):
    def __init__(self):
        super().__init__()

        self.competitions = []
        self.selected_competition_id = None
        self.competition_tabs = []

        self.setup_ui()
        self.connect_signals()
        self.load_competitions()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("🏆 Wettbewerbe")
        title.setObjectName("PageTitle")

        self.info_label = QLabel("")
        self.info_label.setObjectName("InfoLabel")

        content_splitter = QSplitter(
            Qt.Horizontal
        )

        sidebar_widget = self.create_sidebar()
        tabs_widget = self.create_tabs()

        content_splitter.addWidget(
            sidebar_widget
        )
        content_splitter.addWidget(
            tabs_widget
        )

        content_splitter.setStretchFactor(
            0,
            0,
        )
        content_splitter.setStretchFactor(
            1,
            1,
        )

        content_splitter.setSizes(
            [350, 1000]
        )

        main_layout.addWidget(title)
        main_layout.addWidget(
            self.info_label
        )
        main_layout.addWidget(
            content_splitter
        )

        self.setLayout(main_layout)

    def create_sidebar(self) -> QWidget:
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Wettbewerb suchen..."
        )

        self.competition_list = QListWidget()

        self.new_button = QPushButton(
            "➕ Neuer Wettbewerb"
        )

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(
            QLabel("Wettbewerbe")
        )
        sidebar_layout.addWidget(
            self.search
        )
        sidebar_layout.addWidget(
            self.competition_list
        )
        sidebar_layout.addWidget(
            self.new_button
        )

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(
            sidebar_layout
        )
        sidebar_widget.setMinimumWidth(320)
        sidebar_widget.setMaximumWidth(450)

        return sidebar_widget

    def create_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()

        self.overview_tab = CompetitionOverviewTab()
        self.teams_tab = CompetitionTeamsTab()
        self.schedule_tab = CompetitionScheduleTab()
        self.matches_tab = CompetitionMatchesTab()
        self.table_tab = CompetitionTableTab()
        self.home_table_tab = CompetitionHomeTableTab()
        self.away_table_tab = CompetitionAwayTableTab()
        self.form_tab = CompetitionFormTab()
        self.statistics_tab = CompetitionStatisticsTab()
        self.fairplay_tab = CompetitionFairplayTab()
        self.home_away_tab = CompetitionHomeAwayTab()
        self.goal_timeline_tab = CompetitionGoalTimelineTab()
        self.goal_difference_tab = CompetitionGoalDifferenceTab()

        self.register_tab(
            self.overview_tab,
            "📋 Übersicht",
        )

        self.register_tab(
            self.teams_tab,
            "👥 Teilnehmer",
        )

        self.register_tab(
            self.schedule_tab,
            "⚽ Spielplan",
        )

        self.register_tab(
            self.matches_tab,
            "🥅 Spiele",
        )

        self.register_tab(
            self.table_tab,
            "📊 Tabelle",
        )

        self.register_tab(
            self.home_table_tab,
            "🏠 Heim",
        )

        self.register_tab(
            self.away_table_tab,
            "✈️ Auswärts",
        )

        self.register_tab(
            self.form_tab,
            "📈 Form",
        )

        self.register_tab(
            self.home_away_tab,
            "📊 Vergleich",
        )

        self.register_tab(
            self.statistics_tab,
            "🏆 Torjäger",
        )

        self.register_tab(
            self.fairplay_tab,
            "🟨 Fairplay",
        )

        self.register_tab(
            self.goal_timeline_tab,
            "🔥 Torphasen",
        )

        self.register_tab(
            self.goal_difference_tab,
            "⚖️ Torverhältnis",
        )

        return self.tabs

    def register_tab(
        self,
        tab: QWidget,
        title: str,
    ):
        self.tabs.addTab(
            tab,
            title,
        )

        self.competition_tabs.append(
            tab
        )

    def connect_signals(self):
        self.search.textChanged.connect(
            self.filter_competitions
        )

        self.new_button.clicked.connect(
            self.new_competition
        )

        self.competition_list.currentItemChanged.connect(
            self.competition_changed
        )

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

    def load_competitions(self):
        previous_competition_id = (
            self.selected_competition_id
        )

        self.competitions.clear()
        self.competition_list.clear()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            repository = CompetitionRepository(
                connection
            )

            service = CompetitionService(
                repository
            )

            self.competitions = (
                service.get_all_competitions()
            )

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
                (
                    "Wettbewerbe konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

        finally:
            connection.close()

        selected_row = self.find_competition_row(
            previous_competition_id
        )

        if (
            selected_row < 0
            and self.competition_list.count() > 0
        ):
            selected_row = 0

        if selected_row >= 0:
            self.competition_list.setCurrentRow(
                selected_row
            )
        else:
            self.set_competition_for_tabs(
                None
            )

    def add_competition_item(
        self,
        connection: sqlite3.Connection,
        competition,
    ):
        display_text = self.format_competition(
            connection,
            competition,
        )

        item = QListWidgetItem(
            display_text
        )

        item.setData(
            Qt.UserRole,
            competition.competition_id,
        )

        self.competition_list.addItem(
            item
        )

    def filter_competitions(self):
        search_text = (
            self.search.text()
            .lower()
            .strip()
        )

        self.competition_list.clear()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            for competition in self.competitions:
                display_text = self.format_competition(
                    connection,
                    competition,
                )

                if search_text not in display_text.lower():
                    continue

                item = QListWidgetItem(
                    display_text
                )

                item.setData(
                    Qt.UserRole,
                    competition.competition_id,
                )

                self.competition_list.addItem(
                    item
                )

        finally:
            connection.close()

        if self.competition_list.count() > 0:
            self.competition_list.setCurrentRow(
                0
            )
        else:
            self.selected_competition_id = None

            self.set_competition_for_tabs(
                None
            )

    def competition_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ):
        if current is None:
            self.selected_competition_id = None

            self.set_competition_for_tabs(
                None
            )
            return

        competition_id = current.data(
            Qt.UserRole
        )

        if competition_id is None:
            self.selected_competition_id = None

            self.set_competition_for_tabs(
                None
            )
            return

        self.selected_competition_id = (
            competition_id
        )

        self.set_competition_for_tabs(
            competition_id
        )

    def set_competition_for_tabs(
        self,
        competition_id: int | None,
    ):
        for tab in self.competition_tabs:
            if hasattr(
                tab,
                "set_competition",
            ):
                tab.set_competition(
                    competition_id
                )

    def tab_changed(
        self,
        index: int,
    ):
        current_tab = self.tabs.widget(
            index
        )

        if hasattr(
            current_tab,
            "refresh",
        ):
            current_tab.refresh()

    def new_competition(self):
        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            league_repository = (
                LeagueRepository(connection)
            )

            leagues = (
                league_repository.get_all()
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    season_id,
                    name
                FROM seasons
                ORDER BY
                    start_date DESC,
                    name DESC
                """
            )

            seasons = cursor.fetchall()

            if not leagues:
                QMessageBox.warning(
                    self,
                    "Keine Ligen vorhanden",
                    (
                        "Bitte lege zuerst mindestens "
                        "eine Liga an."
                    ),
                )
                return

            if not seasons:
                QMessageBox.warning(
                    self,
                    "Keine Saisons vorhanden",
                    (
                        "Bitte lege zuerst mindestens "
                        "eine Saison an."
                    ),
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

            repository = CompetitionRepository(
                connection
            )

            service = CompetitionService(
                repository
            )

            competition_id = (
                service.create_competition(
                    name=data["name"],
                    league_id=data["league_id"],
                    season_id=data["season_id"],
                    active=data["active"],
                )
            )

            self.selected_competition_id = (
                competition_id
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Fehler",
                (
                    "Wettbewerb konnte nicht "
                    f"gespeichert werden:\n{error}"
                ),
            )
            return

        finally:
            connection.close()

        self.load_competitions()

    def find_competition_row(
        self,
        competition_id: int | None,
    ) -> int:
        if competition_id is None:
            return -1

        for row in range(
            self.competition_list.count()
        ):
            item = self.competition_list.item(
                row
            )

            if (
                item.data(Qt.UserRole)
                == competition_id
            ):
                return row

        return -1

    def format_competition(
        self,
        connection: sqlite3.Connection,
        competition,
    ) -> str:
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

        status = (
            "Aktiv"
            if competition.active
            else "Inaktiv"
        )

        return (
            f"{competition.name} | "
            f"{league_name} | "
            f"{season_name} | "
            f"{status}"
        )

    def refresh(self):
        self.load_competitions()