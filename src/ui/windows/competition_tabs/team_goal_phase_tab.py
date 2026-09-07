from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.team_goal_phase_service import (
    TeamGoalPhaseService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionTeamGoalPhaseTab(
    BaseStatisticsTab
):
    """
    Früh-/Spät-Analyse mit stärkerer visueller Gewichtung.

    Ziel:
    - weniger Zahlenfriedhof
    - Prozentwerte direkt als Balken lesbar
    - positive / negative Auffälligkeiten schnell erkennbar
    - Datenbasis transparent benennen
    """

    EARLY_COLOR = "#6f767f"
    LATE_COLOR = "#2f9e44"
    CONCEDED_COLOR = "#d94848"

    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⏱ Früh / Spät",
            refresh_button_text=(
                "🔄 Torphasen aktualisieren"
            ),
        )

        self.table = QTableWidget()

        self.setup_table()

        self.add_content_widget(
            self.table,
            stretch=1,
        )

        self.clear_data()

    def setup_table(
        self,
    ) -> None:
        self.table.setColumnCount(
            8
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Tab.",
                "Mannschaft",
                "Tore 0–15",
                "Frühe Tore",
                "Tore 76–90",
                "Späte Tore",
                "Späte Gegentore",
                "Bilanz 76–90",
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setSortingEnabled(
            False
        )

        self.table.setToolTip(
            (
                "Frühe Tore: Anteil der eigenen Tore in Minute 0–15.\n"
                "Späte Tore: Anteil der eigenen Tore in Minute 76–90.\n"
                "Späte Gegentore: Anteil der Gegentore in Minute 76–90.\n"
                "Bilanz 76–90: eigene Tore minus Gegentore in dieser Phase."
            )
        )

        header = (
            self.table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Fixed,
        )

        self.table.setColumnWidth(
            2,
            78,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Fixed,
        )

        self.table.setColumnWidth(
            4,
            78,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.Fixed,
        )

        self.table.setColumnWidth(
            7,
            84,
        )

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.table.setRowCount(
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

                service = TeamGoalPhaseService(
                    connection
                )

                statistics = (
                    service.get_statistics(
                        self.competition_id
                    )
                )

                self.populate_table(
                    statistics
                )

                best_late_team = (
                    self._get_best_team(
                        statistics,
                        "late_goal_percentage",
                    )
                )

                worst_late_team = (
                    self._get_best_team(
                        statistics,
                        "late_conceded_percentage",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if best_late_team is not None:
                    info_parts.append(
                        (
                            "🟢 Spätstärkstes Team: "
                            f"{best_late_team['team_name']} "
                            "· "
                            f"{best_late_team['late_goal_percentage']:.1f} %"
                        )
                    )

                if worst_late_team is not None:
                    info_parts.append(
                        (
                            "🔴 Anfällig spät: "
                            f"{worst_late_team['team_name']} "
                            "· "
                            f"{worst_late_team['late_conceded_percentage']:.1f} %"
                        )
                    )

                info_parts.append(
                    "Quelle: importierte Spieldaten"
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
                    "Die Früh-/Spät-Statistik "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_table(
        self,
        statistics: list[dict],
    ) -> None:
        self.table.setRowCount(
            len(
                statistics
            )
        )

        for row_index, team in enumerate(
            statistics
        ):
            team_id = int(
                team["team_id"]
            )

            position_item = (
                self._create_center_item(
                    team["position"],
                    team_id,
                )
            )

            team_item = QTableWidgetItem(
                str(
                    team["team_name"]
                )
            )
            team_item.setData(
                Qt.ItemDataRole.UserRole,
                team_id,
            )

            early_goals_item = (
                self._create_center_item(
                    team["early_goals"],
                    team_id,
                )
            )

            late_goals_item = (
                self._create_center_item(
                    team["late_goals"],
                    team_id,
                )
            )

            late_balance = int(
                team["late_balance"]
            )

            late_balance_text = (
                f"+{late_balance}"
                if late_balance > 0
                else str(
                    late_balance
                )
            )

            late_balance_item = (
                self._create_center_item(
                    late_balance_text,
                    team_id,
                )
            )

            self._style_balance_item(
                late_balance_item,
                late_balance,
            )

            self.table.setItem(
                row_index,
                0,
                position_item,
            )

            self.table.setItem(
                row_index,
                1,
                team_item,
            )

            self.table.setItem(
                row_index,
                2,
                early_goals_item,
            )

            self.table.setCellWidget(
                row_index,
                3,
                self._create_percentage_bar(
                    value=float(
                        team[
                            "early_goal_percentage"
                        ]
                    ),
                    color=self.EARLY_COLOR,
                    tooltip=(
                        "Anteil aller eigenen Tore "
                        "in Minute 0–15"
                    ),
                ),
            )

            self.table.setItem(
                row_index,
                4,
                late_goals_item,
            )

            self.table.setCellWidget(
                row_index,
                5,
                self._create_percentage_bar(
                    value=float(
                        team[
                            "late_goal_percentage"
                        ]
                    ),
                    color=self.LATE_COLOR,
                    tooltip=(
                        "Anteil aller eigenen Tore "
                        "in Minute 76–90"
                    ),
                ),
            )

            self.table.setCellWidget(
                row_index,
                6,
                self._create_percentage_bar(
                    value=float(
                        team[
                            "late_conceded_percentage"
                        ]
                    ),
                    color=self.CONCEDED_COLOR,
                    tooltip=(
                        "Anteil aller Gegentore "
                        "in Minute 76–90"
                    ),
                ),
            )

            self.table.setItem(
                row_index,
                7,
                late_balance_item,
            )

        self.table.resizeRowsToContents()

    @staticmethod
    def _create_center_item(
        value: object,
        team_id: int,
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(
            str(
                value
            )
        )

        item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        item.setData(
            Qt.ItemDataRole.UserRole,
            team_id,
        )

        return item

    @staticmethod
    def _create_percentage_bar(
        value: float,
        color: str,
        tooltip: str,
    ) -> QProgressBar:
        normalized_value = max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

        bar = QProgressBar()

        bar.setRange(
            0,
            1000,
        )

        bar.setValue(
            int(
                round(
                    normalized_value * 10
                )
            )
        )

        bar.setFormat(
            f"{normalized_value:.1f} %"
        )

        bar.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        bar.setTextVisible(
            True
        )

        bar.setToolTip(
            tooltip
        )

        bar.setMinimumHeight(
            22
        )

        bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid #3a3f46;
                border-radius: 4px;
                background-color: #202327;
                color: #f2f2f2;
                text-align: center;
                font-weight: 600;
            }}

            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
            """
        )

        return bar

    @staticmethod
    def _style_balance_item(
        item: QTableWidgetItem,
        value: int,
    ) -> None:
        if value > 0:
            item.setForeground(
                QColor(
                    "#55b96b"
                )
            )

        elif value < 0:
            item.setForeground(
                QColor(
                    "#e05a5a"
                )
            )

        else:
            item.setForeground(
                QColor(
                    "#d4a72c"
                )
            )

    @staticmethod
    def _get_best_team(
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
                        0.0,
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
        if not hasattr(
            self,
            "table",
        ):
            return

        self.table.setRowCount(
            0
        )
