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

from src.services.statistics.lead_comeback_service import (
    LeadComebackService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionLeadComebackTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="🔄 Führung / Rückstand",
            refresh_button_text=(
                "🔄 Führung/Rückstand aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.trailing_tab = QWidget()
        self.leading_tab = QWidget()

        self.trailing_table = QTableWidget()
        self.leading_table = QTableWidget()

        self.setup_trailing_tab()
        self.setup_leading_tab()

        self.inner_tabs.addTab(
            self.trailing_tab,
            "Rückstand",
        )

        self.inner_tabs.addTab(
            self.leading_tab,
            "Führung",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

    def setup_trailing_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.trailing_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.trailing_table.setColumnCount(
            7
        )

        self.trailing_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Rückstand",
                "Gedreht",
                "Remis gerettet",
                "Pkt. nach Rückstand",
                "Comeback %",
            ]
        )

        self._setup_table(
            self.trailing_table,
            column_count=7,
        )

        layout.addWidget(
            self.trailing_table
        )

    def setup_leading_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.leading_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.leading_table.setColumnCount(
            8
        )

        self.leading_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Führung",
                "Führung gehalten",
                "Remis nach Führung",
                "Niederlage nach Führung",
                "Führung verspielt",
                "Verspielte Punkte",
            ]
        )

        self._setup_table(
            self.leading_table,
            column_count=8,
        )

        layout.addWidget(
            self.leading_table
        )

    def _setup_table(
        self,
        table: QTableWidget,
        column_count: int,
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

        header = (
            table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(
            2,
            column_count,
        ):
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

        self.trailing_table.setRowCount(
            0
        )

        self.leading_table.setRowCount(
            0
        )

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

                service = LeadComebackService(
                    connection
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                self.populate_trailing_table(
                    statistics
                )

                self.populate_leading_table(
                    statistics
                )

                comeback_king = (
                    self._get_max_team(
                        statistics,
                        "points_after_trailing",
                    )
                )

                safest_lead = (
                    self._get_max_team(
                        statistics,
                        "lead_win_percentage",
                    )
                )

                most_dropped_points = (
                    self._get_max_team(
                        statistics,
                        "dropped_points_after_leading",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if comeback_king is not None:
                    info_parts.append(
                        (
                            "Comeback-König: "
                            f"{comeback_king['team_name']} "
                            "– "
                            f"{comeback_king['points_after_trailing']} Punkte"
                        )
                    )

                if safest_lead is not None:
                    info_parts.append(
                        (
                            "Sicherste Führung: "
                            f"{safest_lead['team_name']} "
                            "– "
                            f"{safest_lead['lead_win_percentage']:.1f} %"
                        )
                    )

                if most_dropped_points is not None:
                    info_parts.append(
                        (
                            "Meiste verspielte Punkte: "
                            f"{most_dropped_points['team_name']} "
                            "– "
                            f"{most_dropped_points['dropped_points_after_leading']}"
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
        ) as error:
            self.handle_load_error(
                message=(
                    "Die Führung-/Rückstand-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_trailing_table(
        self,
        statistics: list[dict],
    ) -> None:
        sorted_statistics = sorted(
            statistics,
            key=lambda team: (
                -int(
                    team[
                        "points_after_trailing"
                    ]
                ),
                -float(
                    team[
                        "comeback_percentage"
                    ]
                ),
                int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            ),
        )

        self.trailing_table.setRowCount(
            len(
                sorted_statistics
            )
        )

        for row_index, team in enumerate(
            sorted_statistics
        ):
            values = [
                team["position"],
                team["team_name"],
                team["matches_trailing"],
                team["wins_after_trailing"],
                team["draws_after_trailing"],
                team["points_after_trailing"],
                (
                    f"{team['comeback_percentage']:.1f} %"
                ),
            ]

            self._populate_row(
                table=self.trailing_table,
                row_index=row_index,
                team=team,
                values=values,
            )

    def populate_leading_table(
        self,
        statistics: list[dict],
    ) -> None:
        sorted_statistics = sorted(
            statistics,
            key=lambda team: (
                -float(
                    team[
                        "lead_win_percentage"
                    ]
                ),
                int(
                    team[
                        "dropped_points_after_leading"
                    ]
                ),
                int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            ),
        )

        self.leading_table.setRowCount(
            len(
                sorted_statistics
            )
        )

        for row_index, team in enumerate(
            sorted_statistics
        ):
            leadership_lost = (
                int(
                    team[
                        "draws_after_leading"
                    ]
                )
                + int(
                    team[
                        "losses_after_leading"
                    ]
                )
            )

            values = [
                team["position"],
                team["team_name"],
                team["matches_leading"],
                team["wins_after_leading"],
                team["draws_after_leading"],
                team["losses_after_leading"],
                leadership_lost,
                team["dropped_points_after_leading"],
            ]

            self._populate_row(
                table=self.leading_table,
                row_index=row_index,
                team=team,
                values=values,
            )

    @staticmethod
    def _populate_row(
        table: QTableWidget,
        row_index: int,
        team: dict,
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

            if column_index != 1:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

            item.setData(
                Qt.ItemDataRole.UserRole,
                team["team_id"],
            )

            table.setItem(
                row_index,
                column_index,
                item,
            )

    @staticmethod
    def _get_max_team(
        statistics: list[dict],
        key: str,
    ) -> dict | None:
        if not statistics:
            return None

        return max(
            statistics,
            key=lambda team: (
                float(
                    team.get(
                        key,
                        0,
                    )
                ),
                -int(
                    team.get(
                        "position",
                        9999,
                    )
                    or 9999
                ),
            ),
        )

    def clear_content(
        self,
    ) -> None:
        if hasattr(
            self,
            "trailing_table",
        ):
            self.trailing_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "leading_table",
        ):
            self.leading_table.setRowCount(
                0
            )