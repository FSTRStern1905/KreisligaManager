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

from src.services.statistics.player_statistics_service import (
    PlayerStatisticsService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionPlayerOverviewTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="👤 Spielerstatistiken",
            refresh_button_text=(
                "🔄 Spielerstatistiken aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.appearances_tab = QWidget()
        self.minutes_tab = QWidget()
        self.scorer_tab = QWidget()
        self.efficiency_tab = QWidget()
        self.cards_tab = QWidget()

        self.appearances_table = QTableWidget()
        self.minutes_table = QTableWidget()
        self.scorer_table = QTableWidget()
        self.efficiency_table = QTableWidget()
        self.cards_table = QTableWidget()

        self.setup_appearances_tab()
        self.setup_minutes_tab()
        self.setup_scorer_tab()
        self.setup_efficiency_tab()
        self.setup_cards_tab()

        self.inner_tabs.addTab(
            self.appearances_tab,
            "Einsätze",
        )

        self.inner_tabs.addTab(
            self.minutes_tab,
            "Minuten",
        )

        self.inner_tabs.addTab(
            self.scorer_tab,
            "Scorer",
        )

        self.inner_tabs.addTab(
            self.efficiency_tab,
            "Effizienz",
        )

        self.inner_tabs.addTab(
            self.cards_tab,
            "Karten",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_appearances_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.appearances_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.appearances_table.setColumnCount(
            9
        )

        self.appearances_table.setHorizontalHeaderLabels(
            [
                "Spieler",
                "Mannschaft",
                "Pos.",
                "Kader",
                "Einsätze",
                "Startelf",
                "Eingewechselt",
                "Ausgewechselt",
                "Bank",
            ]
        )

        self._setup_table(
            self.appearances_table,
        )

        layout.addWidget(
            self.appearances_table
        )

    def setup_minutes_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.minutes_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.minutes_table.setColumnCount(
            7
        )

        self.minutes_table.setHorizontalHeaderLabels(
            [
                "Spieler",
                "Mannschaft",
                "Einsätze",
                "Minuten",
                "Ø Minuten",
                "Startelf",
                "Startelf %",
            ]
        )

        self._setup_table(
            self.minutes_table,
        )

        layout.addWidget(
            self.minutes_table
        )

    def setup_scorer_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.scorer_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.scorer_table.setColumnCount(
            9
        )

        self.scorer_table.setHorizontalHeaderLabels(
            [
                "Spieler",
                "Mannschaft",
                "Tore",
                "Assists",
                "Scorer",
                "Tore / 90",
                "Assists / 90",
                "Min. / Tor",
                "Minuten",
            ]
        )

        self._setup_table(
            self.scorer_table,
        )

        layout.addWidget(
            self.scorer_table
        )

    def setup_efficiency_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.efficiency_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.efficiency_table.setColumnCount(
            10
        )

        self.efficiency_table.setHorizontalHeaderLabels(
            [
                "Spieler",
                "Mannschaft",
                "Einsätze",
                "Minuten",
                "Tore",
                "Tore / Einsatz",
                "Tore / 90",
                "Min. / Tor",
                "Ø Minuten",
                "Startelf %",
            ]
        )

        self._setup_table(
            self.efficiency_table,
        )

        layout.addWidget(
            self.efficiency_table
        )

    def setup_cards_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.cards_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.cards_table.setColumnCount(
            7
        )

        self.cards_table.setHorizontalHeaderLabels(
            [
                "Spieler",
                "Mannschaft",
                "Einsätze",
                "Gelb",
                "Gelb-Rot",
                "Rot",
                "Karten gesamt",
            ]
        )

        self._setup_table(
            self.cards_table,
        )

        layout.addWidget(
            self.cards_table
        )

    @staticmethod
    def _setup_table(
        table: QTableWidget,
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
            if column in (
                0,
                1,
            ):
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

                service = PlayerStatisticsService(
                    connection
                )

                statistics = (
                    service.get_competition_statistics(
                        competition_id=self.competition_id,
                    )
                )

                self.populate_appearances_table(
                    statistics
                )

                self.populate_minutes_table(
                    statistics
                )

                self.populate_scorer_table(
                    statistics
                )

                self.populate_efficiency_table(
                    statistics
                )

                self.populate_cards_table(
                    statistics
                )

                players_with_appearances = [
                    player
                    for player in statistics
                    if int(
                        player[
                            "appearances"
                        ]
                    ) > 0
                ]

                top_appearance = (
                    self._get_max_player(
                        players_with_appearances,
                        "appearances",
                    )
                )

                top_minutes = (
                    self._get_max_player(
                        players_with_appearances,
                        "minutes_played",
                    )
                )

                top_scorer = (
                    self._get_max_player(
                        statistics,
                        "goals",
                    )
                )

                info_parts = [
                    competition_name,
                    (
                        f"{len(players_with_appearances)} Spieler "
                        "mit Einsatz"
                    ),
                ]

                if top_appearance is not None:
                    info_parts.append(
                        (
                            "Meiste Einsätze: "
                            f"{top_appearance['player_name']} "
                            f"– {top_appearance['appearances']}"
                        )
                    )

                if top_minutes is not None:
                    info_parts.append(
                        (
                            "Meiste Minuten: "
                            f"{top_minutes['player_name']} "
                            f"– {top_minutes['minutes_played']}"
                        )
                    )

                if (
                    top_scorer is not None
                    and int(
                        top_scorer[
                            "goals"
                        ]
                    ) > 0
                ):
                    info_parts.append(
                        (
                            "Meiste Tore: "
                            f"{top_scorer['player_name']} "
                            f"– {top_scorer['goals']}"
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
                    "Die Spielerstatistiken "
                    "konnten nicht geladen werden."
                ),
                error=error,
            )

    def populate_appearances_table(
        self,
        statistics: list[dict],
    ) -> None:
        filtered = [
            player
            for player in statistics
            if int(
                player[
                    "appearances"
                ]
            ) > 0
        ]

        rows = sorted(
            filtered,
            key=lambda player: (
                -int(
                    player[
                        "appearances"
                    ]
                ),
                -int(
                    player[
                        "starts"
                    ]
                ),
                -int(
                    player[
                        "minutes_played"
                    ]
                ),
                str(
                    player[
                        "player_name"
                    ]
                ).casefold(),
            ),
        )

        self.appearances_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, player in enumerate(
            rows
        ):
            values = [
                player["player_name"],
                player["team_name"],
                player["position"],
                player["squad_selections"],
                player["appearances"],
                player["starts"],
                player["substituted_in"],
                player["substituted_out"],
                player["unused_bench"],
            ]

            self._populate_row(
                table=self.appearances_table,
                row_index=row_index,
                player=player,
                values=values,
            )

    def populate_minutes_table(
        self,
        statistics: list[dict],
    ) -> None:
        filtered = [
            player
            for player in statistics
            if int(
                player[
                    "minutes_played"
                ]
            ) > 0
        ]

        rows = sorted(
            filtered,
            key=lambda player: (
                -int(
                    player[
                        "minutes_played"
                    ]
                ),
                -int(
                    player[
                        "appearances"
                    ]
                ),
                str(
                    player[
                        "player_name"
                    ]
                ).casefold(),
            ),
        )

        self.minutes_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, player in enumerate(
            rows
        ):
            values = [
                player["player_name"],
                player["team_name"],
                player["appearances"],
                player["minutes_played"],
                (
                    f"{player['average_minutes']:.1f}"
                ),
                player["starts"],
                (
                    f"{player['start_percentage']:.1f} %"
                ),
            ]

            self._populate_row(
                table=self.minutes_table,
                row_index=row_index,
                player=player,
                values=values,
            )

    def populate_scorer_table(
        self,
        statistics: list[dict],
    ) -> None:
        filtered = [
            player
            for player in statistics
            if (
                int(
                    player[
                        "goals"
                    ]
                ) > 0
                or int(
                    player[
                        "assists"
                    ]
                ) > 0
            )
        ]

        rows = sorted(
            filtered,
            key=lambda player: (
                -(
                    int(
                        player[
                            "goals"
                        ]
                    )
                    + int(
                        player[
                            "assists"
                        ]
                    )
                ),
                -int(
                    player[
                        "goals"
                    ]
                ),
                -int(
                    player[
                        "assists"
                    ]
                ),
                str(
                    player[
                        "player_name"
                    ]
                ).casefold(),
            ),
        )

        self.scorer_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, player in enumerate(
            rows
        ):
            scorer_points = (
                int(
                    player[
                        "goals"
                    ]
                )
                + int(
                    player[
                        "assists"
                    ]
                )
            )

            minutes_per_goal = (
                player[
                    "minutes_per_goal"
                ]
            )

            values = [
                player["player_name"],
                player["team_name"],
                player["goals"],
                player["assists"],
                scorer_points,
                (
                    f"{player['goals_per_90']:.2f}"
                ),
                (
                    f"{player['assists_per_90']:.2f}"
                ),
                (
                    f"{minutes_per_goal:.1f}"
                    if minutes_per_goal is not None
                    else "-"
                ),
                player["minutes_played"],
            ]

            self._populate_row(
                table=self.scorer_table,
                row_index=row_index,
                player=player,
                values=values,
            )

    def populate_efficiency_table(
        self,
        statistics: list[dict],
    ) -> None:
        filtered = [
            player
            for player in statistics
            if (
                int(
                    player.get(
                        "minutes_played",
                        0,
                    )
                ) >= 900
                and int(
                    player.get(
                        "goals",
                        0,
                    )
                ) > 0
            )
        ]

        rows = sorted(
            filtered,
            key=lambda player: (
                -float(
                    player.get(
                        "goals_per_90",
                        0.0,
                    )
                ),
                -int(
                    player.get(
                        "goals",
                        0,
                    )
                ),
                int(
                    player.get(
                        "minutes_played",
                        0,
                    )
                ),
                str(
                    player.get(
                        "player_name",
                        "",
                    )
                ).casefold(),
            ),
        )

        self.efficiency_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, player in enumerate(
            rows
        ):
            appearances = int(
                player.get(
                    "appearances",
                    0,
                )
            )

            goals = int(
                player.get(
                    "goals",
                    0,
                )
            )

            goals_per_appearance = (
                goals / appearances
                if appearances > 0
                else 0.0
            )

            minutes_per_goal = (
                player.get(
                    "minutes_per_goal"
                )
            )

            values = [
                player["player_name"],
                player["team_name"],
                appearances,
                player["minutes_played"],
                goals,
                f"{goals_per_appearance:.2f}",
                f"{player['goals_per_90']:.2f}",
                (
                    f"{minutes_per_goal:.1f}"
                    if minutes_per_goal is not None
                    else "-"
                ),
                f"{player['average_minutes']:.1f}",
                f"{player['start_percentage']:.1f} %",
            ]

            self._populate_row(
                table=self.efficiency_table,
                row_index=row_index,
                player=player,
                values=values,
            )

    def populate_cards_table(
        self,
        statistics: list[dict],
    ) -> None:
        filtered = [
            player
            for player in statistics
            if (
                int(
                    player[
                        "yellow_cards"
                    ]
                )
                + int(
                    player[
                        "yellow_red_cards"
                    ]
                )
                + int(
                    player[
                        "red_cards"
                    ]
                )
            ) > 0
        ]

        rows = sorted(
            filtered,
            key=lambda player: (
                -(
                    int(
                        player[
                            "yellow_cards"
                        ]
                    )
                    + int(
                        player[
                            "yellow_red_cards"
                        ]
                    )
                    + int(
                        player[
                            "red_cards"
                        ]
                    )
                ),
                -int(
                    player[
                        "red_cards"
                    ]
                ),
                -int(
                    player[
                        "yellow_red_cards"
                    ]
                ),
                -int(
                    player[
                        "yellow_cards"
                    ]
                ),
                str(
                    player[
                        "player_name"
                    ]
                ).casefold(),
            ),
        )

        self.cards_table.setRowCount(
            len(
                rows
            )
        )

        for row_index, player in enumerate(
            rows
        ):
            total_cards = (
                int(
                    player[
                        "yellow_cards"
                    ]
                )
                + int(
                    player[
                        "yellow_red_cards"
                    ]
                )
                + int(
                    player[
                        "red_cards"
                    ]
                )
            )

            values = [
                player["player_name"],
                player["team_name"],
                player["appearances"],
                player["yellow_cards"],
                player["yellow_red_cards"],
                player["red_cards"],
                total_cards,
            ]

            self._populate_row(
                table=self.cards_table,
                row_index=row_index,
                player=player,
                values=values,
            )

    @staticmethod
    def _populate_row(
        table: QTableWidget,
        row_index: int,
        player: dict,
        values: list,
    ) -> None:
        for column_index, value in enumerate(
            values
        ):
            item = QTableWidgetItem(
                str(
                    value
                )
            )

            if column_index not in (
                0,
                1,
                2,
            ):
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

            item.setData(
                Qt.ItemDataRole.UserRole,
                player[
                    "player_id"
                ],
            )

            table.setItem(
                row_index,
                column_index,
                item,
            )

    @staticmethod
    def _get_max_player(
        statistics: list[dict],
        key: str,
    ) -> dict | None:
        if not statistics:
            return None

        return max(
            statistics,
            key=lambda player: (
                int(
                    player.get(
                        key,
                        0,
                    )
                ),
                int(
                    player.get(
                        "minutes_played",
                        0,
                    )
                ),
                str(
                    player.get(
                        "player_name",
                        "",
                    )
                ),
            ),
        )

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "appearances_table",
        ):
            self.appearances_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "minutes_table",
        ):
            self.minutes_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "scorer_table",
        ):
            self.scorer_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "efficiency_table",
        ):
            self.efficiency_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "cards_table",
        ):
            self.cards_table.setRowCount(
                0
            )