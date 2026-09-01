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

from src.services.statistics.halftime_result_service import (
    HalftimeResultService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionHalftimeResultTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⏸ Halbzeit → Endstand",
            refresh_button_text=(
                "🔄 Halbzeitstatistik aktualisieren"
            ),
        )

        self.inner_tabs = QTabWidget()

        self.leading_tab = QWidget()
        self.drawing_tab = QWidget()
        self.trailing_tab = QWidget()

        self.leading_table = QTableWidget()
        self.drawing_table = QTableWidget()
        self.trailing_table = QTableWidget()

        self.setup_leading_tab()
        self.setup_drawing_tab()
        self.setup_trailing_tab()

        self.inner_tabs.addTab(
            self.leading_tab,
            "HZ-Führung",
        )

        self.inner_tabs.addTab(
            self.drawing_tab,
            "HZ-Remis",
        )

        self.inner_tabs.addTab(
            self.trailing_tab,
            "HZ-Rückstand",
        )

        self.add_content_widget(
            self.inner_tabs,
            stretch=1,
        )

        self.clear_data()

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
                "HZ-Führung",
                "Danach Sieg",
                "Danach Remis",
                "Danach Niederlage",
                "Siegquote %",
                "Verspielte Punkte",
            ]
        )

        self._setup_table(
            self.leading_table,
            8,
        )

        layout.addWidget(
            self.leading_table
        )

    def setup_drawing_tab(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self.drawing_tab
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.drawing_table.setColumnCount(
            8
        )

        self.drawing_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "HZ-Remis",
                "Danach Sieg",
                "Danach Remis",
                "Danach Niederlage",
                "Siegquote %",
                "Punkte danach",
            ]
        )

        self._setup_table(
            self.drawing_table,
            8,
        )

        layout.addWidget(
            self.drawing_table
        )

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
            8
        )

        self.trailing_table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "HZ-Rückstand",
                "Noch Sieg",
                "Noch Remis",
                "Niederlage",
                "Comeback %",
                "Punkte danach",
            ]
        )

        self._setup_table(
            self.trailing_table,
            8,
        )

        layout.addWidget(
            self.trailing_table
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

        self.leading_table.setRowCount(
            0
        )

        self.drawing_table.setRowCount(
            0
        )

        self.trailing_table.setRowCount(
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

                service = HalftimeResultService(
                    connection
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                self.populate_leading_table(
                    statistics
                )

                self.populate_drawing_table(
                    statistics
                )

                self.populate_trailing_table(
                    statistics
                )

                best_lead_team = (
                    self._get_max_team(
                        statistics,
                        "lead_conversion_percentage",
                    )
                )

                best_comeback_team = (
                    self._get_max_team(
                        statistics,
                        "points_after_halftime_trail",
                    )
                )

                best_draw_team = (
                    self._get_max_team(
                        statistics,
                        "win_percentage_after_halftime_draw",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_lead_team is not None:
                    info_parts.append(
                        (
                            "Beste HZ-Führung: "
                            f"{best_lead_team['team_name']} "
                            "– "
                            f"{best_lead_team['lead_conversion_percentage']:.1f} %"
                        )
                    )

                if best_comeback_team is not None:
                    info_parts.append(
                        (
                            "Bestes HZ-Comeback-Team: "
                            f"{best_comeback_team['team_name']} "
                            "– "
                            f"{best_comeback_team['points_after_halftime_trail']} Punkte"
                        )
                    )

                if best_draw_team is not None:
                    info_parts.append(
                        (
                            "Stärkstes Team nach HZ-Remis: "
                            f"{best_draw_team['team_name']} "
                            "– "
                            f"{best_draw_team['win_percentage_after_halftime_draw']:.1f} % Siege"
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
                    "Die Halbzeitstatistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
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
                        "lead_conversion_percentage"
                    ]
                ),
                int(
                    team[
                        "dropped_points_after_halftime_lead"
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
            values = [
                team["position"],
                team["team_name"],
                team["leading_at_halftime"],
                team["wins_after_halftime_lead"],
                team["draws_after_halftime_lead"],
                team["losses_after_halftime_lead"],
                (
                    f"{team['lead_conversion_percentage']:.1f} %"
                ),
                team["dropped_points_after_halftime_lead"],
            ]

            self._populate_row(
                self.leading_table,
                row_index,
                team,
                values,
            )

    def populate_drawing_table(
        self,
        statistics: list[dict],
    ) -> None:
        sorted_statistics = sorted(
            statistics,
            key=lambda team: (
                -float(
                    team[
                        "win_percentage_after_halftime_draw"
                    ]
                ),
                -int(
                    team[
                        "points_after_halftime_draw"
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

        self.drawing_table.setRowCount(
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
                team["drawing_at_halftime"],
                team["wins_after_halftime_draw"],
                team["draws_after_halftime_draw"],
                team["losses_after_halftime_draw"],
                (
                    f"{team['win_percentage_after_halftime_draw']:.1f} %"
                ),
                team["points_after_halftime_draw"],
            ]

            self._populate_row(
                self.drawing_table,
                row_index,
                team,
                values,
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
                        "points_after_halftime_trail"
                    ]
                ),
                -float(
                    team[
                        "halftime_comeback_percentage"
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
                team["trailing_at_halftime"],
                team["wins_after_halftime_trail"],
                team["draws_after_halftime_trail"],
                team["losses_after_halftime_trail"],
                (
                    f"{team['halftime_comeback_percentage']:.1f} %"
                ),
                team["points_after_halftime_trail"],
            ]

            self._populate_row(
                self.trailing_table,
                row_index,
                team,
                values,
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
        valid_statistics = [
            team
            for team in statistics
            if int(
                team.get(
                    "matches_with_halftime",
                    0,
                )
            ) > 0
        ]

        if not valid_statistics:
            return None

        return max(
            valid_statistics,
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
            "leading_table",
        ):
            self.leading_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "drawing_table",
        ):
            self.drawing_table.setRowCount(
                0
            )

        if hasattr(
            self,
            "trailing_table",
        ):
            self.trailing_table.setRowCount(
                0
            )