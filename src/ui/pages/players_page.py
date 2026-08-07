from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.database.repository import Repository
from src.services.statistics.player_statistics_service import (
    PlayerStatisticsService,
)
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography
from src.ui.widgets.card import Card
from src.ui.widgets.data_table import DataTable
from src.ui.widgets.page_header import PageHeader
from src.ui.widgets.secondary_button import SecondaryButton
from src.ui.widgets.toolbar import Toolbar


class PlayersPage(QWidget):
    def __init__(
        self,
        repository: Repository,
    ) -> None:
        super().__init__()

        self.repository = repository
        self.connection = self._resolve_connection()

        self.statistics_service = (
            PlayerStatisticsService(
                self.connection
            )
        )

        self.players: list[dict] = []
        self.filtered_players: list[dict] = []

        self.current_player_id: int | None = None
        self.current_competition_id: int | None = None

        self.setObjectName(
            "PlayersPage"
        )

        self.setup_ui()
        self.load_data()

    def setup_ui(self) -> None:
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
            title="Spieler",
            subtitle=(
                "Spieler suchen, filtern und "
                "Saisonstatistiken anzeigen"
            ),
        )

        self.toolbar = Toolbar(
            search_placeholder=(
                "Spielername suchen ..."
            )
        )

        self.refresh_button = SecondaryButton(
            "Aktualisieren"
        )

        self.toolbar.add_action(
            self.refresh_button
        )

        self.filter_card = Card(
            title="Filter",
            icon="⚙",
        )

        filter_layout = QHBoxLayout()

        filter_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        filter_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        competition_group = self._create_filter_group(
            "Wettbewerb"
        )

        self.competition_combo = QComboBox()
        self.competition_combo.setObjectName(
            "PlayerFilterCombo"
        )

        competition_group.layout().addWidget(
            self.competition_combo
        )

        team_group = self._create_filter_group(
            "Mannschaft"
        )

        self.team_combo = QComboBox()
        self.team_combo.setObjectName(
            "PlayerFilterCombo"
        )

        team_group.layout().addWidget(
            self.team_combo
        )

        self.player_count_label = QLabel(
            "0 Spieler"
        )

        self.player_count_label.setObjectName(
            "PlayerCountLabel"
        )

        self.player_count_label.setFont(
            Typography.body()
        )

        self.player_count_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        filter_layout.addWidget(
            competition_group,
            1,
        )

        filter_layout.addWidget(
            team_group,
            1,
        )

        filter_layout.addStretch(
            1
        )

        filter_layout.addWidget(
            self.player_count_label
        )

        self.filter_card.add_layout(
            filter_layout
        )

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

        self.player_card = Card(
            title="Spielerübersicht",
            icon="👤",
        )

        self.player_card.setMinimumWidth(
            430
        )

        self.player_card.setMaximumWidth(
            560
        )

        self.player_table = DataTable()

        self.player_table.set_columns(
            (
                ("player_name", "Spieler"),
                ("position", "Position"),
                ("team_name", "Mannschaft"),
            )
        )

        self.player_table.set_column_widths(
            {
                "position": 110,
                "team_name": 180,
            }
        )

        self.player_table.stretch_column(
            "player_name"
        )

        self.player_card.add_widget(
            self.player_table,
            stretch=1,
        )

        self.profile_card = Card(
            title="Spielerprofil",
            icon="📊",
        )

        self._create_profile_content()

        content_layout.addWidget(
            self.player_card,
            0,
        )

        content_layout.addWidget(
            self.profile_card,
            1,
        )

        main_layout.addWidget(
            self.header
        )

        main_layout.addWidget(
            self.toolbar
        )

        main_layout.addWidget(
            self.filter_card
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        self._connect_signals()
        self._apply_style()

    def _create_filter_group(
        self,
        title: str,
    ) -> QWidget:
        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            Metrics.SPACING_XXS
        )

        label = QLabel(
            title
        )

        label.setObjectName(
            "FilterLabel"
        )

        label.setFont(
            Typography.small()
        )

        layout.addWidget(
            label
        )

        return widget

    def _create_profile_content(
        self,
    ) -> None:
        self.empty_label = QLabel(
            "Wähle einen Spieler aus."
        )

        self.empty_label.setObjectName(
            "PlayerEmptyState"
        )

        self.empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.profile_widget = QWidget()

        profile_layout = QVBoxLayout(
            self.profile_widget
        )

        profile_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        profile_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self.player_name_label = QLabel(
            "-"
        )

        self.player_name_label.setObjectName(
            "PlayerName"
        )

        self.player_name_label.setFont(
            Typography.heading()
        )

        self.player_meta_label = QLabel(
            "-"
        )

        self.player_meta_label.setObjectName(
            "PlayerMeta"
        )

        self.player_meta_label.setFont(
            Typography.body()
        )

        profile_layout.addWidget(
            self.player_name_label
        )

        profile_layout.addWidget(
            self.player_meta_label
        )

        self.stats_card = Card(
            title="Saisonstatistik",
        )

        stats_layout = QGridLayout()

        stats_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        stats_layout.setHorizontalSpacing(
            Metrics.SPACING_LARGE
        )

        stats_layout.setVerticalSpacing(
            Metrics.SPACING_SMALL
        )

        self.appearances_value = self._stat_value()
        self.starts_value = self._stat_value()
        self.substituted_in_value = self._stat_value()
        self.substituted_out_value = self._stat_value()
        self.unused_bench_value = self._stat_value()
        self.minutes_value = self._stat_value()
        self.average_minutes_value = self._stat_value()
        self.goals_value = self._stat_value()
        self.own_goals_value = self._stat_value()
        self.assists_value = self._stat_value()
        self.goals_per_90_value = self._stat_value()
        self.minutes_per_goal_value = self._stat_value("-")
        self.yellow_cards_value = self._stat_value()
        self.yellow_red_cards_value = self._stat_value()
        self.red_cards_value = self._stat_value()

        stats = (
            ("Einsätze", self.appearances_value),
            ("Startelf", self.starts_value),
            ("Eingewechselt", self.substituted_in_value),
            ("Ausgewechselt", self.substituted_out_value),
            ("Ohne Einsatz", self.unused_bench_value),
            ("Minuten", self.minutes_value),
            ("Ø Minuten", self.average_minutes_value),
            ("Tore", self.goals_value),
            ("Eigentore", self.own_goals_value),
            ("Vorlagen", self.assists_value),
            ("Tore / 90", self.goals_per_90_value),
            ("Minuten / Tor", self.minutes_per_goal_value),
            ("Gelb", self.yellow_cards_value),
            ("Gelb-Rot", self.yellow_red_cards_value),
            ("Rot", self.red_cards_value),
        )

        for index, (
            label_text,
            value_label,
        ) in enumerate(stats):
            row = index // 3
            column = index % 3

            cell = QWidget()

            cell_layout = QVBoxLayout(
                cell
            )

            cell_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            cell_layout.setSpacing(
                Metrics.SPACING_XXS
            )

            label = QLabel(
                label_text
            )

            label.setObjectName(
                "StatLabel"
            )

            label.setFont(
                Typography.small()
            )

            cell_layout.addWidget(
                label
            )

            cell_layout.addWidget(
                value_label
            )

            stats_layout.addWidget(
                cell,
                row,
                column,
            )

        self.stats_card.add_layout(
            stats_layout
        )

        profile_layout.addWidget(
            self.stats_card
        )

        self.history_card = Card(
            title="Spielhistorie",
        )

        self.history_table = DataTable()

        self.history_table.set_columns(
            (
                ("matchday", "ST"),
                ("match_date", "Datum"),
                ("encounter", "Begegnung"),
                ("start", "Start"),
                ("minute_in", "Ein"),
                ("minute_out", "Aus"),
                ("minutes", "Min."),
                ("goals", "Tore"),
                ("cards", "Karten"),
            )
        )

        self.history_table.set_column_widths(
            {
                "matchday": 60,
                "match_date": 100,
                "start": 70,
                "minute_in": 60,
                "minute_out": 60,
                "minutes": 70,
                "goals": 70,
                "cards": 100,
            }
        )

        self.history_table.stretch_column(
            "encounter"
        )

        self.history_card.add_widget(
            self.history_table,
            stretch=1,
        )

        profile_layout.addWidget(
            self.history_card,
            1,
        )

        self.profile_card.add_widget(
            self.empty_label,
            stretch=1,
        )

        self.profile_card.add_widget(
            self.profile_widget,
            stretch=1,
        )

        self.profile_widget.setVisible(
            False
        )

    def _stat_value(
        self,
        value: str = "0",
    ) -> QLabel:
        label = QLabel(
            value
        )

        label.setObjectName(
            "StatValue"
        )

        label.setFont(
            Typography.subtitle()
        )

        return label

    def _connect_signals(self) -> None:
        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.toolbar.search_bar.text_changed.connect(
            self.apply_filters
        )

        self.competition_combo.currentIndexChanged.connect(
            self._competition_changed
        )

        self.team_combo.currentIndexChanged.connect(
            self.apply_filters
        )

        self.player_table.itemSelectionChanged.connect(
            self._player_selection_changed
        )

        self.player_table.row_activated.connect(
            self._load_player_profile
        )

    def load_data(self) -> None:
        try:
            self._load_competitions()
            self._load_teams()
            self._load_players()
            self.apply_filters()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                str(error),
            )

    def refresh(self) -> None:
        selected_competition_id = (
            self.current_competition_id
        )

        selected_player_id = (
            self.current_player_id
        )

        self.load_data()

        if selected_competition_id is not None:
            self._select_combo_data(
                self.competition_combo,
                selected_competition_id,
            )

        if selected_player_id is not None:
            self._select_player(
                selected_player_id
            )

    def _load_competitions(self) -> None:
        self.competition_combo.blockSignals(
            True
        )

        self.competition_combo.clear()

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                competition_id,
                name
            FROM competitions
            ORDER BY
                name COLLATE NOCASE,
                competition_id;
            """
        )

        for competition_id, name in cursor.fetchall():
            self.competition_combo.addItem(
                name or f"Wettbewerb {competition_id}",
                int(competition_id),
            )

        self.competition_combo.blockSignals(
            False
        )

        if self.competition_combo.count() > 0:
            self.competition_combo.setCurrentIndex(
                0
            )

            self.current_competition_id = int(
                self.competition_combo.currentData()
            )
        else:
            self.current_competition_id = None

    def _load_teams(self) -> None:
        self.team_combo.blockSignals(
            True
        )

        self.team_combo.clear()

        self.team_combo.addItem(
            "Alle Mannschaften",
            None,
        )

        if self.current_competition_id is not None:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT
                    teams.team_id,
                    teams.name,
                    teams.short_name
                FROM competition_teams
                INNER JOIN teams
                    ON teams.team_id =
                        competition_teams.team_id
                WHERE
                    competition_teams.competition_id = ?
                ORDER BY
                    teams.name COLLATE NOCASE;
                """,
                (
                    self.current_competition_id,
                ),
            )

            for (
                team_id,
                name,
                short_name,
            ) in cursor.fetchall():
                self.team_combo.addItem(
                    short_name or name,
                    int(team_id),
                )

        self.team_combo.blockSignals(
            False
        )

    def _load_players(self) -> None:
        self.players = []

        if self.current_competition_id is None:
            return

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT DISTINCT
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.team_id,
                teams.name,
                teams.short_name
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id
            INNER JOIN players
                ON players.player_id =
                    player_match_stats.player_id
            INNER JOIN teams
                ON teams.team_id =
                    player_match_stats.team_id
            WHERE
                matches.competition_id = ?
            ORDER BY
                players.last_name COLLATE NOCASE,
                players.first_name COLLATE NOCASE,
                teams.name COLLATE NOCASE;
            """,
            (
                self.current_competition_id,
            ),
        )

        for row in cursor.fetchall():
            first_name = row[1] or ""
            last_name = row[2] or ""

            self.players.append(
                {
                    "player_id": int(row[0]),
                    "player_name": (
                        f"{first_name} {last_name}"
                    ).strip(),
                    "position": row[3] or "-",
                    "team_id": int(row[4]),
                    "team_name": row[6] or row[5],
                }
            )

    def apply_filters(
        self,
        *_args,
    ) -> None:
        search_text = (
            self.toolbar.search_bar.text()
            .strip()
            .casefold()
        )

        team_id = self.team_combo.currentData()

        self.filtered_players = [
            player
            for player in self.players
            if (
                (
                    not search_text
                    or search_text
                    in player["player_name"].casefold()
                )
                and (
                    team_id is None
                    or player["team_id"] == team_id
                )
            )
        ]

        self._fill_player_table()

    def _fill_player_table(self) -> None:
        selected_player_id = (
            self.current_player_id
        )

        rows = [
            {
                "id": player["player_id"],
                "player_name": player["player_name"],
                "position": player["position"],
                "team_name": player["team_name"],
            }
            for player in self.filtered_players
        ]

        self.player_table.set_rows(
            rows,
            id_key="id",
        )

        count = len(
            self.filtered_players
        )

        self.player_count_label.setText(
            f"{count} "
            f"{'Spieler' if count == 1 else 'Spieler'}"
        )

        if selected_player_id is not None:
            self._select_player(
                selected_player_id
            )

        if (
            self.player_table.rowCount() > 0
            and self.player_table.currentRow() < 0
        ):
            self.player_table.selectRow(
                0
            )

        if self.player_table.rowCount() == 0:
            self.current_player_id = None
            self._show_empty_state()

    def _competition_changed(
        self,
        *_args,
    ) -> None:
        competition_id = (
            self.competition_combo.currentData()
        )

        self.current_competition_id = (
            int(competition_id)
            if competition_id is not None
            else None
        )

        self.current_player_id = None

        self._load_teams()
        self._load_players()
        self.apply_filters()

    def _player_selection_changed(
        self,
    ) -> None:
        player_id = (
            self.player_table.selected_row_id()
        )

        if player_id is None:
            self.current_player_id = None
            self._show_empty_state()
            return

        self.current_player_id = player_id

        self._load_player_profile(
            player_id
        )

    def _load_player_profile(
        self,
        player_id: int,
    ) -> None:
        if self.current_competition_id is None:
            self._show_empty_state()
            return

        statistics = (
            self.statistics_service
            .get_player_statistics(
                competition_id=(
                    self.current_competition_id
                ),
                player_id=player_id,
            )
        )

        if statistics is None:
            self._show_empty_state()
            return

        history = (
            self.statistics_service
            .get_player_match_history(
                competition_id=(
                    self.current_competition_id
                ),
                player_id=player_id,
            )
        )

        self.current_player_id = player_id

        self.player_name_label.setText(
            statistics["player_name"]
        )

        self.player_meta_label.setText(
            (
                f"{statistics['team_name']} · "
                f"{statistics['position']}"
            )
        )

        self.appearances_value.setText(
            str(statistics["appearances"])
        )

        self.starts_value.setText(
            str(statistics["starts"])
        )

        self.substituted_in_value.setText(
            str(statistics["substituted_in"])
        )

        self.substituted_out_value.setText(
            str(statistics["substituted_out"])
        )

        self.unused_bench_value.setText(
            str(statistics["unused_bench"])
        )

        self.minutes_value.setText(
            str(statistics["minutes_played"])
        )

        self.average_minutes_value.setText(
            str(statistics["average_minutes"])
        )

        self.goals_value.setText(
            str(statistics["goals"])
        )

        self.own_goals_value.setText(
            str(statistics["own_goals"])
        )

        self.assists_value.setText(
            str(statistics["assists"])
        )

        self.goals_per_90_value.setText(
            str(statistics["goals_per_90"])
        )

        minutes_per_goal = (
            statistics["minutes_per_goal"]
        )

        self.minutes_per_goal_value.setText(
            (
                str(minutes_per_goal)
                if minutes_per_goal is not None
                else "-"
            )
        )

        self.yellow_cards_value.setText(
            str(statistics["yellow_cards"])
        )

        self.yellow_red_cards_value.setText(
            str(statistics["yellow_red_cards"])
        )

        self.red_cards_value.setText(
            str(statistics["red_cards"])
        )

        self._fill_history_table(
            history
        )

        self.empty_label.setVisible(
            False
        )

        self.profile_widget.setVisible(
            True
        )

    def _fill_history_table(
        self,
        history: list[dict],
    ) -> None:
        rows = []

        for index, match in enumerate(
            history
        ):
            matchday = (
                str(match["matchday"])
                if match["matchday"] is not None
                else "-"
            )

            match_date = (
                str(match["match_date"])
                if match["match_date"] is not None
                else "-"
            )

            encounter = (
                f"{match['home_team_name']} "
                f"{match['home_goals']}:"
                f"{match['away_goals']} "
                f"{match['away_team_name']}"
            )

            card_parts = []

            if match["yellow_cards"] > 0:
                card_parts.append(
                    f"Gelb {match['yellow_cards']}"
                )

            if match["yellow_red_cards"] > 0:
                card_parts.append(
                    f"GR {match['yellow_red_cards']}"
                )

            if match["red_cards"] > 0:
                card_parts.append(
                    f"Rot {match['red_cards']}"
                )

            rows.append(
                {
                    "id": index,
                    "matchday": matchday,
                    "match_date": match_date,
                    "encounter": encounter,
                    "start": (
                        "Ja"
                        if match["is_starting"]
                        else "Nein"
                    ),
                    "minute_in": (
                        str(match["minute_in"])
                        if match["was_substituted_in"]
                        else "-"
                    ),
                    "minute_out": (
                        str(match["minute_out"])
                        if match["was_substituted_out"]
                        else "-"
                    ),
                    "minutes": str(
                        match["minutes_played"]
                    ),
                    "goals": str(
                        match["goals"]
                    ),
                    "cards": (
                        ", ".join(card_parts)
                        or "-"
                    ),
                }
            )

        self.history_table.set_rows(
            rows,
            id_key="id",
        )

    def _show_empty_state(self) -> None:
        self.empty_label.setVisible(
            True
        )

        self.profile_widget.setVisible(
            False
        )

        self.history_table.clear_rows()

    def _select_player(
        self,
        player_id: int,
    ) -> None:
        for row in range(
            self.player_table.rowCount()
        ):
            item = self.player_table.item(
                row,
                0,
            )

            if item is None:
                continue

            if (
                item.data(
                    Qt.ItemDataRole.UserRole
                )
                == player_id
            ):
                self.player_table.selectRow(
                    row
                )
                return

    @staticmethod
    def _select_combo_data(
        combo: QComboBox,
        value: int,
    ) -> None:
        index = combo.findData(
            value
        )

        if index >= 0:
            combo.setCurrentIndex(
                index
            )

    def _resolve_connection(
        self,
    ) -> sqlite3.Connection:
        connection = getattr(
            self.repository,
            "connection",
            None,
        )

        if isinstance(
            connection,
            sqlite3.Connection,
        ):
            return connection

        database = getattr(
            self.repository,
            "database",
            None,
        )

        database_connection = getattr(
            database,
            "connection",
            None,
        )

        if isinstance(
            database_connection,
            sqlite3.Connection,
        ):
            return database_connection

        raise RuntimeError(
            "Die Datenbankverbindung konnte "
            "nicht aus dem Repository gelesen werden."
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#PlayersPage {{
                background-color:
                    {Colors.BACKGROUND};
            }}

            QLabel#FilterLabel {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel#PlayerCountLabel {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QComboBox#PlayerFilterCombo {{
                min-height:
                    {Metrics.INPUT_HEIGHT}px;
                background-color:
                    {Colors.INPUT_BACKGROUND};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.INPUT_BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
                padding-left:
                    {Metrics.INPUT_PADDING_HORIZONTAL}px;
                padding-right:
                    {Metrics.INPUT_PADDING_HORIZONTAL}px;
            }}

            QComboBox#PlayerFilterCombo:hover {{
                background-color:
                    {Colors.INPUT_BACKGROUND_HOVER};
                border-color:
                    {Colors.BORDER_LIGHT};
            }}

            QComboBox#PlayerFilterCombo::drop-down {{
                border:
                    none;
                width:
                    28px;
            }}

            QComboBox#PlayerFilterCombo QAbstractItemView {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                selection-background-color:
                    {Colors.TABLE_ROW_SELECTED};
                selection-color:
                    {Colors.TEXT_PRIMARY};
            }}

            QLabel#PlayerEmptyState {{
                color:
                    {Colors.TEXT_MUTED};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel#PlayerName {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel#PlayerMeta {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel#StatLabel {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel#StatValue {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
                border:
                    none;
            }}
            """
        )