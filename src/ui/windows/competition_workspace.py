from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.widgets.card import Card
from src.ui.widgets.data_table import DataTable
from src.ui.widgets.page_header import PageHeader
from src.ui.widgets.primary_button import PrimaryButton
from src.ui.widgets.secondary_button import SecondaryButton
from src.ui.widgets.toolbar import Toolbar
from src.ui.windows.competition_tabs.match_center_tab import (
    CompetitionMatchCenterTab,
)
from src.ui.windows.competition_tabs.matches_tab import (
    CompetitionMatchesTab,
)
from src.ui.windows.competition_tabs.overview_tab import (
    CompetitionOverviewTab,
)
from src.ui.windows.competition_tabs.prediction_tab import (
    CompetitionPredictionTab,
)
from src.ui.windows.competition_tabs.schedule_tab import (
    CompetitionScheduleTab,
)
from src.ui.windows.competition_tabs.statistics_hub_tab import (
    CompetitionStatisticsHubTab,
)
from src.ui.windows.competition_tabs.table_tab import (
    CompetitionTableTab,
)
from src.ui.windows.competition_tabs.teams_tab import (
    CompetitionTeamsTab,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionWorkspace(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competitions = []
        self.filtered_competitions = []
        self.competition_filter_data = {}

        self.selected_competition_id: int | None = None
        self.competition_tabs: list[QWidget] = []

        self.setObjectName(
            "CompetitionWorkspace"
        )

        self.setup_ui()
        self.connect_signals()
        self.load_competitions()

    def setup_ui(
        self,
    ) -> None:
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
        )

        main_layout.setSpacing(
            Metrics.PAGE_SPACING
        )

        self.header = PageHeader(
            title="Wettbewerbe",
            subtitle=(
                "Wettbewerbe verwalten und "
                "Saisonverläufe analysieren"
            ),
        )

        self.toolbar = Toolbar(
            search_placeholder=(
                "Wettbewerb, Liga oder Saison suchen ..."
            )
        )

        self.refresh_button = SecondaryButton(
            "Aktualisieren"
        )

        self.new_button = PrimaryButton(
            "Neuer Wettbewerb"
        )

        self.toolbar.add_action(
            self.refresh_button
        )

        self.toolbar.add_action(
            self.new_button
        )

        self.filter_widget = QWidget()
        filter_layout = QHBoxLayout(
            self.filter_widget
        )
        filter_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        filter_layout.setSpacing(8)

        self.season_filter = QComboBox()
        self.season_filter.addItem(
            "Alle Saisons",
            None,
        )

        self.level_filter = QComboBox()
        self.level_filter.addItem(
            "Alle Liga-Level",
            None,
        )

        self.source_filter = QComboBox()
        self.source_filter.addItem(
            "Echte Daten",
            "real",
        )
        self.source_filter.addItem(
            "Alle Quellen",
            "all",
        )
        self.source_filter.addItem(
            "Demo",
            "demo",
        )
        self.source_filter.addItem(
            "Manuell",
            "manual",
        )

        filter_layout.addWidget(
            QLabel("Saison")
        )
        filter_layout.addWidget(
            self.season_filter
        )
        filter_layout.addSpacing(8)

        filter_layout.addWidget(
            QLabel("Liga-Level")
        )
        filter_layout.addWidget(
            self.level_filter
        )
        filter_layout.addSpacing(8)

        filter_layout.addWidget(
            QLabel("Quelle")
        )
        filter_layout.addWidget(
            self.source_filter
        )
        filter_layout.addStretch(1)

        content_layout = QHBoxLayout()

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            Metrics.CARD_SPACING
        )

        self.competition_card = Card(
            title="Wettbewerbsübersicht",
            icon="🏆",
        )

        self.competition_card.setMinimumWidth(
            440
        )

        self.competition_card.setMaximumWidth(
            580
        )

        self.competition_table = DataTable()

        self.competition_table.set_columns(
            (
                (
                    "name",
                    "Wettbewerb",
                ),
                (
                    "league",
                    "Liga",
                ),
                (
                    "season",
                    "Saison",
                ),
                (
                    "status",
                    "Status",
                ),
            )
        )

        self.competition_table.set_column_widths(
            {
                "league": 150,
                "season": 110,
                "status": 90,
            }
        )

        self.competition_table.stretch_column(
            "name"
        )

        self.competition_card.add_widget(
            self.competition_table,
            stretch=1,
        )

        self.workspace_card = Card(
            title="Wettbewerbsdetails",
            icon="📊",
        )

        self.tabs = self.create_tabs()

        self.workspace_card.add_widget(
            self.tabs,
            stretch=1,
        )

        content_layout.addWidget(
            self.competition_card,
            0,
        )

        content_layout.addWidget(
            self.workspace_card,
            1,
        )

        main_layout.addWidget(
            self.header
        )

        main_layout.addWidget(
            self.toolbar
        )

        main_layout.addWidget(
            self.filter_widget
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        self._apply_style()

    def create_tabs(
        self,
    ) -> QTabWidget:
        self.tabs = QTabWidget()

        self.tabs.setObjectName(
            "CompetitionTabs"
        )

        self.overview_tab = (
            CompetitionOverviewTab()
        )

        self.teams_tab = (
            CompetitionTeamsTab()
        )

        self.schedule_tab = (
            CompetitionScheduleTab()
        )

        self.matches_tab = (
            CompetitionMatchesTab()
        )

        self.table_tab = (
            CompetitionTableTab()
        )

        self.statistics_hub_tab = (
            CompetitionStatisticsHubTab()
        )

        self.prediction_tab = (
            CompetitionPredictionTab()
        )

        self.match_center_tab = (
            CompetitionMatchCenterTab()
        )

        self.register_tab(
            self.overview_tab,
            "Übersicht",
        )

        self.register_tab(
            self.teams_tab,
            "Teilnehmer",
        )

        self.register_tab(
            self.schedule_tab,
            "Spielplan",
        )

        self.register_tab(
            self.matches_tab,
            "Spiele",
        )

        self.register_tab(
            self.table_tab,
            "Tabelle",
        )

        self.register_tab(
            self.statistics_hub_tab,
            "Statistiken",
        )

        self.register_tab(
            self.prediction_tab,
            "🔮 Prognose",
        )

        self.register_tab(
            self.match_center_tab,
            "⚽ Match-Center",
        )

        return self.tabs

    def register_tab(
        self,
        tab: QWidget,
        title: str,
    ) -> None:
        self.tabs.addTab(
            tab,
            title,
        )

        self.competition_tabs.append(
            tab
        )

    def connect_signals(
        self,
    ) -> None:
        self.toolbar.search_bar.text_changed.connect(
            self.filter_competitions
        )

        self.season_filter.currentIndexChanged.connect(
            self._filters_changed
        )
        self.level_filter.currentIndexChanged.connect(
            self._filters_changed
        )
        self.source_filter.currentIndexChanged.connect(
            self._filters_changed
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.new_button.clicked.connect(
            self.new_competition
        )

        self.competition_table.itemSelectionChanged.connect(
            self.competition_changed
        )

        self.competition_table.row_activated.connect(
            self.competition_activated
        )

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

    def load_competitions(
        self,
    ) -> None:
        previous_competition_id = (
            self.selected_competition_id
        )

        self.competitions.clear()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            repository = (
                CompetitionRepository(
                    connection
                )
            )

            service = (
                CompetitionService(
                    repository
                )
            )

            self.competitions = (
                service.get_all_competitions()
            )

            self._load_filter_data(
                connection
            )
            self._populate_filters()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Wettbewerbe konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.competitions = []

        finally:
            connection.close()

        self.filter_competitions(
            self.toolbar.search_bar.text()
        )

        if previous_competition_id is not None:
            self._select_competition(
                previous_competition_id
            )

        if (
            self.competition_table.rowCount() > 0
            and self.competition_table.currentRow() < 0
        ):
            self.competition_table.selectRow(
                0
            )

        if (
            self.competition_table.rowCount()
            == 0
        ):
            self.selected_competition_id = (
                None
            )

            self.set_competition_for_tabs(
                None
            )

    def _filters_changed(
        self,
        _index: int = 0,
    ) -> None:
        self.filter_competitions(
            self.toolbar.search_bar.text()
        )

    def filter_competitions(
        self,
        search_text: str = "",
    ) -> None:
        normalized_search = (
            search_text
            .strip()
            .casefold()
        )

        season_filter = (
            self.season_filter.currentData()
        )
        level_filter = (
            self.level_filter.currentData()
        )
        source_filter = (
            self.source_filter.currentData()
        )

        rows = []

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            for competition in self.competitions:
                row = self._competition_row(
                    connection,
                    competition,
                )

                filter_data = (
                    self.competition_filter_data.get(
                        competition.competition_id,
                        {},
                    )
                )

                searchable_text = (
                    f"{row['name']} "
                    f"{row['league']} "
                    f"{row['season']} "
                    f"{row['status']}"
                ).casefold()

                if (
                    normalized_search
                    and normalized_search
                    not in searchable_text
                ):
                    continue

                if (
                    season_filter is not None
                    and row["season"]
                    != season_filter
                ):
                    continue

                if (
                    level_filter is not None
                    and filter_data.get(
                        "league_level"
                    )
                    != level_filter
                ):
                    continue

                source = filter_data.get(
                    "source",
                    "manual",
                )

                if (
                    source_filter == "real"
                    and source == "demo"
                ):
                    continue

                if (
                    source_filter == "demo"
                    and source != "demo"
                ):
                    continue

                if (
                    source_filter == "manual"
                    and source != "manual"
                ):
                    continue

                rows.append(row)

        finally:
            connection.close()

        self.filtered_competitions = rows

        self.competition_table.set_rows(
            rows,
            id_key="id",
        )

        if rows:
            self.competition_table.selectRow(
                0
            )

        else:
            self.selected_competition_id = None
            self.set_competition_for_tabs(
                None
            )

    def _load_filter_data(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.competition_filter_data.clear()

        cursor = connection.cursor()

        cursor.execute(
            "PRAGMA table_info(competitions)"
        )
        competition_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        has_source = (
            "source" in competition_columns
        )

        for competition in self.competitions:
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

            source = "manual"

            if has_source:
                cursor.execute(
                    """
                    SELECT source
                    FROM competitions
                    WHERE competition_id = ?
                    """,
                    (competition.competition_id,),
                )
                source_result = cursor.fetchone()

                if (
                    source_result is not None
                    and source_result[0]
                ):
                    source = str(
                        source_result[0]
                    ).strip().lower()

            self.competition_filter_data[
                competition.competition_id
            ] = {
                "season": season_name,
                "source": source,
                "league_level": (
                    self._league_level(
                        league_name,
                        competition.name,
                    )
                ),
            }

    def _populate_filters(
        self,
    ) -> None:
        current_season = (
            self.season_filter.currentData()
        )
        current_level = (
            self.level_filter.currentData()
        )

        seasons = sorted(
            {
                data["season"]
                for data in (
                    self.competition_filter_data
                    .values()
                )
                if data.get("season")
            },
            reverse=True,
        )

        levels = {
            data["league_level"]
            for data in (
                self.competition_filter_data
                .values()
            )
            if data.get("league_level")
        }

        level_order = (
            "Bundesliga",
            "2. Bundesliga",
            "3. Liga",
            "Regionalliga",
            "Oberliga",
            "Verbands-/Landesliga",
            "Bezirksliga",
            "Kreisliga",
            "Reserveklasse",
            "Jugend",
            "Sonstige",
        )

        self.season_filter.blockSignals(True)
        self.level_filter.blockSignals(True)

        self.season_filter.clear()
        self.season_filter.addItem(
            "Alle Saisons",
            None,
        )

        for season in seasons:
            self.season_filter.addItem(
                season,
                season,
            )

        self.level_filter.clear()
        self.level_filter.addItem(
            "Alle Liga-Level",
            None,
        )

        for level in level_order:
            if level in levels:
                self.level_filter.addItem(
                    level,
                    level,
                )

        self._restore_filter(
            self.season_filter,
            current_season,
        )
        self._restore_filter(
            self.level_filter,
            current_level,
        )

        self.season_filter.blockSignals(False)
        self.level_filter.blockSignals(False)

    @staticmethod
    def _restore_filter(
        combo: QComboBox,
        value,
    ) -> None:
        index = combo.findData(value)

        combo.setCurrentIndex(
            index
            if index >= 0
            else 0
        )

    @staticmethod
    def _league_level(
        league_name: str,
        competition_name: str,
    ) -> str:
        text = (
            f"{league_name} "
            f"{competition_name}"
        ).casefold()

        youth_terms = (
            "a-junior",
            "b-junior",
            "c-junior",
            "d-junior",
            "e-junior",
            "f-junior",
            "junioren",
            "juniorinnen",
            "jugend",
            "u19",
            "u18",
            "u17",
            "u16",
            "u15",
            "u14",
            "u13",
            "u12",
            "u11",
            "u10",
            "u9",
        )

        if any(
            term in text
            for term in youth_terms
        ):
            return "Jugend"

        if "2. bundesliga" in text:
            return "2. Bundesliga"

        if "bundesliga" in text:
            return "Bundesliga"

        if (
            "3. liga" in text
            or "3.liga" in text
        ):
            return "3. Liga"

        if "regionalliga" in text:
            return "Regionalliga"

        if "oberliga" in text:
            return "Oberliga"

        if any(
            term in text
            for term in (
                "verbandsliga",
                "landesliga",
                "rheinlandliga",
            )
        ):
            return "Verbands-/Landesliga"

        if "bezirksliga" in text:
            return "Bezirksliga"

        if any(
            term in text
            for term in (
                "kreisliga",
                "kreisklasse",
            )
        ):
            return "Kreisliga"

        if "reserveklasse" in text:
            return "Reserveklasse"

        return "Sonstige"

    def _competition_row(
        self,
        connection: sqlite3.Connection,
        competition,
    ) -> dict:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                name
            FROM leagues
            WHERE
                league_id = ?
            """,
            (
                competition.league_id,
            ),
        )

        league_result = (
            cursor.fetchone()
        )

        league_name = (
            league_result[0]
            if league_result is not None
            else "Keine Liga"
        )

        cursor.execute(
            """
            SELECT
                name
            FROM seasons
            WHERE
                season_id = ?
            """,
            (
                competition.season_id,
            ),
        )

        season_result = (
            cursor.fetchone()
        )

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

        return {
            "id": (
                competition.competition_id
            ),
            "name": (
                competition.name
            ),
            "league": league_name,
            "season": season_name,
            "status": status,
        }

    def competition_changed(
        self,
    ) -> None:
        competition_id = (
            self.competition_table.selected_row_id()
        )

        if competition_id is None:
            self.selected_competition_id = (
                None
            )

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

    def competition_activated(
        self,
        competition_id: int,
    ) -> None:
        self.selected_competition_id = (
            competition_id
        )

        self.set_competition_for_tabs(
            competition_id
        )

    def set_competition_for_tabs(
        self,
        competition_id: int | None,
    ) -> None:
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
    ) -> None:
        current_tab = (
            self.tabs.widget(
                index
            )
        )

        if current_tab is None:
            return

        if hasattr(
            current_tab,
            "refresh",
        ):
            current_tab.refresh()

    def new_competition(
        self,
    ) -> None:
        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            league_repository = (
                LeagueRepository(
                    connection
                )
            )

            leagues = (
                league_repository.get_all()
            )

            cursor = (
                connection.cursor()
            )

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

            seasons = (
                cursor.fetchall()
            )

            if not leagues:
                QMessageBox.warning(
                    self,
                    "Keine Ligen vorhanden",
                    (
                        "Bitte lege zuerst "
                        "mindestens eine Liga an."
                    ),
                )

                return

            if not seasons:
                QMessageBox.warning(
                    self,
                    "Keine Saisons vorhanden",
                    (
                        "Bitte lege zuerst "
                        "mindestens eine Saison an."
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

            repository = (
                CompetitionRepository(
                    connection
                )
            )

            service = (
                CompetitionService(
                    repository
                )
            )

            competition_id = (
                service.create_competition(
                    name=data[
                        "name"
                    ],
                    league_id=data[
                        "league_id"
                    ],
                    season_id=data[
                        "season_id"
                    ],
                    active=data[
                        "active"
                    ],
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

        if (
            self.selected_competition_id
            is not None
        ):
            self._select_competition(
                self.selected_competition_id
            )

    def _select_competition(
        self,
        competition_id: int,
    ) -> None:
        for row in range(
            self.competition_table.rowCount()
        ):
            item = (
                self.competition_table.item(
                    row,
                    0,
                )
            )

            if item is None:
                continue

            if (
                item.data(
                    self._user_role()
                )
                == competition_id
            ):
                self.competition_table.selectRow(
                    row
                )

                return

    @staticmethod
    def _user_role():
        from PySide6.QtCore import Qt

        return (
            Qt.ItemDataRole.UserRole
        )

    def refresh(
        self,
    ) -> None:
        self.load_competitions()

    def _apply_style(
        self,
    ) -> None:
        self.setStyleSheet(
            f"""
            QWidget#CompetitionWorkspace {{
                background-color:
                    {Colors.BACKGROUND};
            }}

            QTabWidget#CompetitionTabs::pane {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
                top:
                    -1px;
            }}

            QTabWidget#CompetitionStatisticsTabs::pane {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                border:
                    none;
                top:
                    -1px;
            }}

            QTabBar::tab {{
                background-color:
                    {Colors.BACKGROUND_ELEVATED};
                color:
                    {Colors.TEXT_SECONDARY};
                border:
                    none;
                padding:
                    9px 13px;
                margin-right:
                    2px;
            }}

            QTabBar::tab:hover {{
                background-color:
                    {Colors.CARD_BACKGROUND_HOVER};
                color:
                    {Colors.TEXT_PRIMARY};
            }}

            QTabBar::tab:selected {{
                background-color:
                    {Colors.TABLE_ROW_SELECTED};
                color:
                    {Colors.TEXT_PRIMARY};
            }}
            """
        )