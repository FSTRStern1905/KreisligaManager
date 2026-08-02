from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.database.repository import Repository
from src.services.statistics.player_statistics_service import (
    PlayerStatisticsService,
)


class PlayersPage(QWidget):
    def __init__(
        self,
        repository: Repository,
    ) -> None:
        super().__init__()

        self.repository = repository
        self.connection = self._resolve_connection()
        self.statistics_service = PlayerStatisticsService(
            self.connection
        )

        self.players: list[dict] = []
        self.filtered_players: list[dict] = []
        self.current_player_id: int | None = None
        self.current_competition_id: int | None = None

        self.setup_ui()
        self.load_data()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(
            self
        )

        title = QLabel(
            "👤 Spieler"
        )
        title.setObjectName(
            "PageTitle"
        )

        subtitle = QLabel(
            "Spieler suchen, filtern und "
            "Saisonstatistiken anzeigen"
        )
        subtitle.setObjectName(
            "PageSubtitle"
        )

        main_layout.addWidget(
            title
        )
        main_layout.addWidget(
            subtitle
        )

        content_layout = QHBoxLayout()
        main_layout.addLayout(
            content_layout,
            1,
        )

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        content_layout.addWidget(
            left_panel,
            0,
        )
        content_layout.addWidget(
            right_panel,
            1,
        )

    def _create_left_panel(
        self,
    ) -> QWidget:
        panel = QFrame()
        panel.setObjectName(
            "SidebarCard"
        )
        panel.setMinimumWidth(
            320
        )
        panel.setMaximumWidth(
            420
        )

        layout = QVBoxLayout(
            panel
        )

        competition_label = QLabel(
            "Wettbewerb"
        )

        self.competition_combo = QComboBox()
        self.competition_combo.currentIndexChanged.connect(
            self._competition_changed
        )

        team_label = QLabel(
            "Mannschaft"
        )

        self.team_combo = QComboBox()
        self.team_combo.currentIndexChanged.connect(
            self.apply_filters
        )

        search_label = QLabel(
            "Suche"
        )

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Spielername suchen..."
        )
        self.search_input.textChanged.connect(
            self.apply_filters
        )

        self.player_count_label = QLabel(
            "0 Spieler"
        )
        self.player_count_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        self.player_list = QListWidget()
        self.player_list.currentItemChanged.connect(
            self._player_changed
        )

        layout.addWidget(
            competition_label
        )
        layout.addWidget(
            self.competition_combo
        )
        layout.addSpacing(
            8
        )
        layout.addWidget(
            team_label
        )
        layout.addWidget(
            self.team_combo
        )
        layout.addSpacing(
            8
        )
        layout.addWidget(
            search_label
        )
        layout.addWidget(
            self.search_input
        )
        layout.addWidget(
            self.player_count_label
        )
        layout.addWidget(
            self.player_list,
            1,
        )

        return panel

    def _create_right_panel(
        self,
    ) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(
            container
        )

        self.empty_label = QLabel(
            "Wähle links einen Spieler aus."
        )
        self.empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.profile_widget = QWidget()
        profile_layout = QVBoxLayout(
            self.profile_widget
        )

        self.player_name_label = QLabel(
            "-"
        )
        self.player_name_label.setObjectName(
            "SectionTitle"
        )

        self.player_meta_label = QLabel(
            "-"
        )

        profile_layout.addWidget(
            self.player_name_label
        )
        profile_layout.addWidget(
            self.player_meta_label
        )

        self.stats_frame = QFrame()
        self.stats_frame.setObjectName(
            "StatsCard"
        )

        stats_layout = QFormLayout(
            self.stats_frame
        )

        self.appearances_value = QLabel(
            "0"
        )
        self.starts_value = QLabel(
            "0"
        )
        self.substituted_in_value = QLabel(
            "0"
        )
        self.substituted_out_value = QLabel(
            "0"
        )
        self.unused_bench_value = QLabel(
            "0"
        )
        self.minutes_value = QLabel(
            "0"
        )
        self.average_minutes_value = QLabel(
            "0"
        )
        self.goals_value = QLabel(
            "0"
        )
        self.own_goals_value = QLabel(
            "0"
        )
        self.assists_value = QLabel(
            "0"
        )
        self.goals_per_90_value = QLabel(
            "0"
        )
        self.minutes_per_goal_value = QLabel(
            "-"
        )
        self.yellow_cards_value = QLabel(
            "0"
        )
        self.yellow_red_cards_value = QLabel(
            "0"
        )
        self.red_cards_value = QLabel(
            "0"
        )

        stats_layout.addRow(
            "Einsätze:",
            self.appearances_value,
        )
        stats_layout.addRow(
            "Startelf:",
            self.starts_value,
        )
        stats_layout.addRow(
            "Eingewechselt:",
            self.substituted_in_value,
        )
        stats_layout.addRow(
            "Ausgewechselt:",
            self.substituted_out_value,
        )
        stats_layout.addRow(
            "Ohne Einsatz:",
            self.unused_bench_value,
        )
        stats_layout.addRow(
            "Minuten:",
            self.minutes_value,
        )
        stats_layout.addRow(
            "Ø Minuten:",
            self.average_minutes_value,
        )
        stats_layout.addRow(
            "Tore:",
            self.goals_value,
        )
        stats_layout.addRow(
            "Eigentore:",
            self.own_goals_value,
        )
        stats_layout.addRow(
            "Vorlagen:",
            self.assists_value,
        )
        stats_layout.addRow(
            "Tore / 90:",
            self.goals_per_90_value,
        )
        stats_layout.addRow(
            "Minuten / Tor:",
            self.minutes_per_goal_value,
        )
        stats_layout.addRow(
            "Gelb:",
            self.yellow_cards_value,
        )
        stats_layout.addRow(
            "Gelb-Rot:",
            self.yellow_red_cards_value,
        )
        stats_layout.addRow(
            "Rot:",
            self.red_cards_value,
        )

        profile_layout.addWidget(
            self.stats_frame
        )

        history_title = QLabel(
            "Spielhistorie"
        )
        history_title.setObjectName(
            "SectionTitle"
        )

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(
            9
        )
        self.history_table.setHorizontalHeaderLabels(
            [
                "Spieltag",
                "Datum",
                "Begegnung",
                "Start",
                "Ein",
                "Aus",
                "Min.",
                "Tore",
                "Karten",
            ]
        )
        self.history_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.history_table.setAlternatingRowColors(
            True
        )

        profile_layout.addWidget(
            history_title
        )
        profile_layout.addWidget(
            self.history_table,
            1,
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(
            True
        )
        scroll.setWidget(
            self.profile_widget
        )

        layout.addWidget(
            self.empty_label,
            1,
        )
        layout.addWidget(
            scroll,
            1,
        )

        self.profile_widget.setVisible(
            False
        )

        return container

    def load_data(
        self,
    ) -> None:
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

    def refresh(
        self,
    ) -> None:
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

    def _load_competitions(
        self,
    ) -> None:
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

    def _load_teams(
        self,
    ) -> None:
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

            for team_id, name, short_name in cursor.fetchall():
                self.team_combo.addItem(
                    short_name or name,
                    int(team_id),
                )

        self.team_combo.blockSignals(
            False
        )

    def _load_players(
        self,
    ) -> None:
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
    ) -> None:
        search_text = (
            self.search_input.text()
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

        self._fill_player_list()

    def _fill_player_list(
        self,
    ) -> None:
        selected_player_id = (
            self.current_player_id
        )

        self.player_list.blockSignals(
            True
        )
        self.player_list.clear()

        for player in self.filtered_players:
            item = QListWidgetItem(
                (
                    f"{player['player_name']}\n"
                    f"{player['team_name']} · "
                    f"{player['position']}"
                )
            )
            item.setData(
                Qt.ItemDataRole.UserRole,
                player["player_id"],
            )
            self.player_list.addItem(
                item
            )

        self.player_list.blockSignals(
            False
        )

        self.player_count_label.setText(
            f"{len(self.filtered_players)} Spieler"
        )

        if selected_player_id is not None:
            self._select_player(
                selected_player_id
            )

        if (
            self.player_list.currentRow() < 0
            and self.player_list.count() > 0
        ):
            self.player_list.setCurrentRow(
                0
            )

        if self.player_list.count() == 0:
            self.current_player_id = None
            self._show_empty_state()

    def _competition_changed(
        self,
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

    def _player_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous

        if current is None:
            self.current_player_id = None
            self._show_empty_state()
            return

        player_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        if player_id is None:
            self.current_player_id = None
            self._show_empty_state()
            return

        self.current_player_id = int(
            player_id
        )

        self._load_player_profile(
            self.current_player_id
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
        self.history_table.setRowCount(
            len(history)
        )

        for row_index, match in enumerate(
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

            values = [
                matchday,
                match_date,
                encounter,
                (
                    "Ja"
                    if match["is_starting"]
                    else "Nein"
                ),
                (
                    str(match["minute_in"])
                    if match["was_substituted_in"]
                    else "-"
                ),
                (
                    str(match["minute_out"])
                    if match["was_substituted_out"]
                    else "-"
                ),
                str(match["minutes_played"]),
                str(match["goals"]),
                ", ".join(card_parts) or "-",
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    value
                )
                self.history_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.history_table.resizeColumnsToContents()

    def _show_empty_state(
        self,
    ) -> None:
        self.empty_label.setVisible(
            True
        )
        self.profile_widget.setVisible(
            False
        )
        self.history_table.setRowCount(
            0
        )

    def _select_player(
        self,
        player_id: int,
    ) -> None:
        for row in range(
            self.player_list.count()
        ):
            item = self.player_list.item(
                row
            )

            if item is None:
                continue

            if (
                item.data(
                    Qt.ItemDataRole.UserRole
                )
                == player_id
            ):
                self.player_list.setCurrentRow(
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