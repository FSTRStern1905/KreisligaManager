from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.records_service import (
    RecordsService,
)
from src.services.statistics.team_records_extension_service import (
    TeamRecordsExtensionService,
)
from src.services.statistics.player_records_service import (
    PlayerRecordsService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionRecordsTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="🏆 Rekorde",
            refresh_button_text=(
                "🔄 Rekorde aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.matches_tab = QWidget()
        self.teams_tab = QWidget()
        self.home_away_tab = QWidget()
        self.streaks_tab = QWidget()
        self.players_tab = QWidget()

        self.matches_table = QTableWidget()
        self.teams_table = QTableWidget()
        self.home_away_table = QTableWidget()
        self.streaks_table = QTableWidget()
        self.players_table = QTableWidget()

        self.setup_matches_tab()
        self.setup_teams_tab()
        self.setup_home_away_tab()
        self.setup_streaks_tab()
        self.setup_players_tab()

        self.inner_tabs.addTab(
            self.matches_tab,
            "Spiele",
        )

        self.inner_tabs.addTab(
            self.teams_tab,
            "Mannschaften",
        )

        self.inner_tabs.addTab(
            self.home_away_tab,
            "Heim/Auswärts",
        )

        self.inner_tabs.addTab(
            self.streaks_tab,
            "Serien",
        )

        self.inner_tabs.addTab(
            self.players_tab,
            "Spieler",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_matches_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.matches_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.matches_table.setColumnCount(
            6
        )

        self.matches_table.setHorizontalHeaderLabels(
            [
                "Rekord",
                "Spiel",
                "Ergebnis",
                "Spieltag",
                "Datum",
                "Wert",
            ]
        )

        self._setup_table(
            self.matches_table,
            stretch_column=1,
        )

        layout.addWidget(
            self.matches_table
        )

    def setup_teams_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.teams_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.teams_table.setColumnCount(
            4
        )

        self.teams_table.setHorizontalHeaderLabels(
            [
                "Rekord",
                "Mannschaft",
                "Wert",
                "Spiele",
            ]
        )

        self._setup_table(
            self.teams_table,
            stretch_column=1,
        )

        layout.addWidget(
            self.teams_table
        )

    def setup_home_away_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.home_away_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.home_away_table.setColumnCount(
            4
        )

        self.home_away_table.setHorizontalHeaderLabels(
            [
                "Rekord",
                "Mannschaft",
                "Wert",
                "Spiele",
            ]
        )

        self._setup_table(
            self.home_away_table,
            stretch_column=1,
        )

        layout.addWidget(
            self.home_away_table
        )

    def setup_streaks_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.streaks_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.streaks_table.setColumnCount(
            6
        )

        self.streaks_table.setHorizontalHeaderLabels(
            [
                "Rekord",
                "Mannschaft",
                "Länge",
                "Von ST",
                "Bis ST",
                "Zeitraum",
            ]
        )

        self._setup_table(
            self.streaks_table,
            stretch_column=1,
        )

        layout.addWidget(
            self.streaks_table
        )

    def setup_players_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.players_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.players_table.setColumnCount(
            6
        )

        self.players_table.setHorizontalHeaderLabels(
            [
                "Rekord",
                "Spieler",
                "Mannschaft",
                "Wert",
                "Einsätze",
                "Minuten",
            ]
        )

        self._setup_table(
            self.players_table,
            stretch_column=1,
        )

        layout.addWidget(
            self.players_table
        )

    @staticmethod
    def _setup_table(
        table: QTableWidget,
        stretch_column: int,
    ) -> None:
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        table.setAlternatingRowColors(
            True
        )

        table.verticalHeader().setVisible(
            False
        )

        header = table.horizontalHeader()

        for column in range(
            table.columnCount()
        ):
            if column == stretch_column:
                header.setSectionResizeMode(
                    column,
                    QHeaderView.ResizeMode.Stretch,
                )
            else:
                header.setSectionResizeMode(
                    column,
                    QHeaderView.ResizeMode.ResizeToContents,
                )

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.clear_content()

        try:
            with self.database_connection() as connection:
                competition_name = (
                    self.get_competition_name(
                        connection
                    )
                )

                if competition_name is None:
                    self.clear_data()
                    return

                records_service = RecordsService(
                    connection
                )

                extension_service = (
                    TeamRecordsExtensionService(
                        connection
                    )
                )

                player_records_service = (
                    PlayerRecordsService(
                        connection
                    )
                )

                records = (
                    records_service.get_records(
                        self.competition_id
                    )
                )

                extended_records = (
                    extension_service.get_records(
                        self.competition_id
                    )
                )

                player_records = (
                    player_records_service.get_records(
                        self.competition_id
                    )
                )

                self.populate_matches_table(
                    records
                )

                self.populate_teams_table(
                    records,
                    extended_records,
                )

                self.populate_home_away_table(
                    extended_records
                )

                self.populate_streaks_table(
                    records
                )

                self.populate_players_table(
                    player_records
                )

                info_parts = [
                    competition_name
                ]

                biggest_win = records.get(
                    "biggest_win"
                )

                most_points = extended_records.get(
                    "most_points"
                )

                longest_unbeaten = records.get(
                    "longest_unbeaten_streak"
                )

                if biggest_win is not None:
                    info_parts.append(
                        (
                            "Höchster Sieg: "
                            f"{biggest_win['home_team_name']} "
                            f"{biggest_win['home_goals']}:"
                            f"{biggest_win['away_goals']} "
                            f"{biggest_win['away_team_name']}"
                        )
                    )

                if most_points is not None:
                    info_parts.append(
                        (
                            "Meiste Punkte: "
                            f"{most_points['team_name']} "
                            f"– {most_points['value']}"
                        )
                    )

                if longest_unbeaten is not None:
                    info_parts.append(
                        (
                            "Längste Ungeschlagen-Serie: "
                            f"{longest_unbeaten['team_name']} "
                            f"– {longest_unbeaten['length']} Spiele"
                        )
                    )

                self.set_info_text(
                    " | ".join(
                        info_parts
                    )
                )

                self.set_refresh_enabled(
                    True
                )

        except (
            sqlite3.Error,
            ValueError,
            KeyError,
        ) as error:
            self.handle_load_error(
                message=(
                    "Die Rekord-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_matches_table(
        self,
        records: dict,
    ) -> None:
        definitions = [
            (
                "Höchster Heimsieg",
                "biggest_home_win",
                "goal_difference",
            ),
            (
                "Höchster Auswärtssieg",
                "biggest_away_win",
                "goal_difference",
            ),
            (
                "Höchster Sieg",
                "biggest_win",
                "goal_difference",
            ),
            (
                "Torreichstes Spiel",
                "highest_scoring_match",
                "total_goals",
            ),
            (
                "Meiste Heimtore",
                "most_home_goals_match",
                "home_goals",
            ),
            (
                "Meiste Auswärtstore",
                "most_away_goals_match",
                "away_goals",
            ),
            (
                "Torreichstes Remis",
                "highest_scoring_draw",
                "total_goals",
            ),
        ]

        rows: list[tuple] = []

        for (
            label,
            key,
            value_key,
        ) in definitions:
            record = records.get(
                key
            )

            if record is None:
                continue

            match_text = (
                f"{record['home_team_name']} "
                f"- {record['away_team_name']}"
            )

            result_text = (
                f"{record['home_goals']}:"
                f"{record['away_goals']}"
            )

            matchday = record.get(
                "matchday"
            )

            match_date = record.get(
                "match_date"
            )

            value = record.get(
                value_key,
                "-",
            )

            rows.append(
                (
                    label,
                    match_text,
                    result_text,
                    (
                        matchday
                        if matchday is not None
                        else "-"
                    ),
                    (
                        match_date
                        if match_date
                        else "-"
                    ),
                    value,
                )
            )

        self.matches_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, values in enumerate(
            rows
        ):
            self._populate_row(
                table=self.matches_table,
                row_index=row_index,
                values=values,
                text_columns=(
                    0,
                    1,
                ),
            )

    def populate_teams_table(
        self,
        records: dict,
        extended_records: dict,
    ) -> None:
        rows: list[tuple] = []

        normal_definitions = [
            (
                "Beste Offensive",
                "best_offense",
            ),
            (
                "Beste Defensive",
                "best_defense",
            ),
            (
                "Schlechteste Offensive",
                "worst_offense",
            ),
            (
                "Schlechteste Defensive",
                "worst_defense",
            ),
            (
                "Meiste Siege",
                "most_wins",
            ),
            (
                "Meiste Remis",
                "most_draws",
            ),
            (
                "Meiste Niederlagen",
                "most_losses",
            ),
            (
                "Beste Tordifferenz",
                "best_goal_difference",
            ),
            (
                "Schlechteste Tordifferenz",
                "worst_goal_difference",
            ),
        ]

        for (
            label,
            key,
        ) in normal_definitions:
            record = records.get(
                key
            )

            if record is None:
                continue

            rows.append(
                (
                    label,
                    record["team_name"],
                    record["value"],
                    record["played"],
                )
            )

        extended_definitions = [
            (
                "Meiste Punkte",
                "most_points",
                "integer",
            ),
            (
                "Wenigste Punkte",
                "fewest_points",
                "integer",
            ),
            (
                "Beste Punkte / Spiel",
                "best_points_per_game",
                "float",
            ),
            (
                "Meiste Zu-Null-Spiele",
                "most_clean_sheets",
                "integer",
            ),
            (
                "Wenigste Zu-Null-Spiele",
                "fewest_clean_sheets",
                "integer",
            ),
            (
                "Beste Zu-Null-Quote",
                "best_clean_sheet_rate",
                "percentage",
            ),
        ]

        for (
            label,
            key,
            value_type,
        ) in extended_definitions:
            record = extended_records.get(
                key
            )

            if record is None:
                continue

            value = self._format_record_value(
                record.get(
                    "value",
                    0,
                ),
                value_type,
            )

            rows.append(
                (
                    label,
                    record["team_name"],
                    value,
                    record["played"],
                )
            )

        self.teams_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, values in enumerate(
            rows
        ):
            self._populate_row(
                table=self.teams_table,
                row_index=row_index,
                values=values,
                text_columns=(
                    0,
                    1,
                ),
            )

    def populate_home_away_table(
        self,
        records: dict,
    ) -> None:
        definitions = [
            (
                "Bestes Heimteam",
                "best_home_team",
                "integer",
            ),
            (
                "Schlechtestes Heimteam",
                "worst_home_team",
                "integer",
            ),
            (
                "Meiste Heimsiege",
                "most_home_wins",
                "integer",
            ),
            (
                "Beste Heimpunkte / Spiel",
                "best_home_points_per_game",
                "float",
            ),
            (
                "Bestes Auswärtsteam",
                "best_away_team",
                "integer",
            ),
            (
                "Schlechtestes Auswärtsteam",
                "worst_away_team",
                "integer",
            ),
            (
                "Meiste Auswärtssiege",
                "most_away_wins",
                "integer",
            ),
            (
                "Beste Auswärtspunkte / Spiel",
                "best_away_points_per_game",
                "float",
            ),
        ]

        rows: list[tuple] = []

        for (
            label,
            key,
            value_type,
        ) in definitions:
            record = records.get(
                key
            )

            if record is None:
                continue

            value = self._format_record_value(
                record.get(
                    "value",
                    0,
                ),
                value_type,
            )

            rows.append(
                (
                    label,
                    record["team_name"],
                    value,
                    record["played"],
                )
            )

        self.home_away_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, values in enumerate(
            rows
        ):
            self._populate_row(
                table=self.home_away_table,
                row_index=row_index,
                values=values,
                text_columns=(
                    0,
                    1,
                ),
            )

    def populate_streaks_table(
        self,
        records: dict,
    ) -> None:
        definitions = [
            (
                "Längste Siegesserie",
                "longest_win_streak",
            ),
            (
                "Längste Ungeschlagen-Serie",
                "longest_unbeaten_streak",
            ),
            (
                "Längste Niederlagenserie",
                "longest_loss_streak",
            ),
            (
                "Längste Sieglos-Serie",
                "longest_winless_streak",
            ),
            (
                "Längste Torserie",
                "longest_scoring_streak",
            ),
            (
                "Längste Zu-Null-Serie",
                "longest_clean_sheet_streak",
            ),
        ]

        rows: list[tuple] = []

        for (
            label,
            key,
        ) in definitions:
            record = records.get(
                key
            )

            if record is None:
                continue

            period = self._format_period(
                start_date=record.get(
                    "start_date"
                ),
                end_date=record.get(
                    "end_date"
                ),
            )

            rows.append(
                (
                    label,
                    record["team_name"],
                    record["length"],
                    (
                        record.get(
                            "start_matchday"
                        )
                        or "-"
                    ),
                    (
                        record.get(
                            "end_matchday"
                        )
                        or "-"
                    ),
                    period,
                )
            )

        self.streaks_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, values in enumerate(
            rows
        ):
            self._populate_row(
                table=self.streaks_table,
                row_index=row_index,
                values=values,
                text_columns=(
                    0,
                    1,
                    5,
                ),
            )

    def populate_players_table(
        self,
        records: dict,
    ) -> None:
        definitions = [
            ("Meiste Tore", "most_goals", "integer"),
            ("Meiste Startelf-Tore", "most_starter_goals", "integer"),
            ("Meiste Joker-Tore", "most_substitute_goals", "integer"),
            ("Meiste Tore in einem Spiel", "most_goals_in_match", "integer"),
            ("Meiste Mehrfach-Tor-Spiele", "most_multi_goal_matches", "integer"),
            ("Meiste Hattricks", "most_hattricks", "integer"),
            ("Meiste Spiele mit Tor", "most_scoring_matches", "integer"),
            ("Beste Tore / Einsatz (min. 10)", "best_goals_per_appearance", "float"),
            ("Beste Tore / 90 (min. 900 Min.)", "best_goals_per_90", "float"),
            ("Beste Minuten / Tor (min. 900 Min.)", "best_minutes_per_goal", "float"),
            ("Meiste Einsätze", "most_appearances", "integer"),
            ("Meiste Startelfeinsätze", "most_starts", "integer"),
            ("Meiste Spielminuten", "most_minutes", "integer"),
            ("Meiste Einwechslungen", "most_substituted_in", "integer"),
            ("Meiste Auswechslungen", "most_substituted_out", "integer"),
            ("Meiste Gelbe Karten", "most_yellow_cards", "integer"),
            ("Meiste Gelb-Rote Karten", "most_yellow_red_cards", "integer"),
            ("Meiste Rote Karten", "most_red_cards", "integer"),
            ("Meiste Karten / 90 (min. 900 Min.)", "most_cards_per_90", "float"),
            ("Meiste Zu-Null-Spiele", "most_clean_sheets", "integer"),
        ]

        rows: list[tuple] = []

        for label, key, value_type in definitions:
            record = records.get(key)

            if record is None:
                continue

            value = self._format_record_value(
                record.get("value", 0),
                value_type,
            )

            rows.append(
                (
                    label,
                    record["player_name"],
                    record["team_name"],
                    value,
                    record["appearances"],
                    record["minutes_played"],
                )
            )

        self.players_table.setRowCount(
            len(rows)
        )

        for row_index, values in enumerate(rows):
            self._populate_row(
                table=self.players_table,
                row_index=row_index,
                values=values,
                text_columns=(0, 1, 2),
            )

    @staticmethod
    def _format_record_value(
        value,
        value_type: str,
    ) -> str:
        if value_type == "percentage":
            return (
                f"{float(value):.1f} %"
            )

        if value_type == "float":
            return (
                f"{float(value):.2f}"
            )

        return str(
            int(
                value
            )
        )

    @staticmethod
    def _populate_row(
        table: QTableWidget,
        row_index: int,
        values: tuple,
        text_columns: tuple[int, ...],
    ) -> None:
        for column_index, value in enumerate(
            values
        ):
            item = QTableWidgetItem(
                str(
                    value
                )
            )

            if column_index not in text_columns:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

            table.setItem(
                row_index,
                column_index,
                item,
            )

    @staticmethod
    def _format_period(
        start_date,
        end_date,
    ) -> str:
        if (
            not start_date
            and not end_date
        ):
            return "-"

        if start_date == end_date:
            return str(
                start_date
            )

        return (
            f"{start_date or '-'} "
            f"bis "
            f"{end_date or '-'}"
        )

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "matches_table",
        ):
            self.matches_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "teams_table",
        ):
            self.teams_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "home_away_table",
        ):
            self.home_away_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "streaks_table",
        ):
            self.streaks_table.setRowCount(
                0
            )