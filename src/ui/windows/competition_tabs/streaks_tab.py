from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.streak_service import (
    StreakService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionStreaksTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="🔥 Serien",
            refresh_button_text=(
                "🔄 Serien aktualisieren"
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
                "Pos",
                "Mannschaft",
                "Aktuelle Serie",
                "Siegesserie",
                "Remisserie",
                "Niederlagenserie",
                "Ungeschlagen",
                "Sieglos",
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

        header = (
            self.table.horizontalHeader()
        )

        header.setStretchLastSection(
            True
        )

        header.setSectionResizeMode(
            0,
            header.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            header.ResizeMode.Stretch,
        )

        for column in range(
            2,
            8,
        ):
            header.setSectionResizeMode(
                column,
                header.ResizeMode.ResizeToContents,
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

                service = StreakService(
                    connection
                )

                streaks = (
                    service.get_streaks(
                        self.competition_id
                    )
                )

                self.populate_table(
                    streaks
                )

                longest_winning_team = (
                    self._get_team_with_max_value(
                        streaks,
                        "longest_win_streak",
                    )
                )

                longest_unbeaten_team = (
                    self._get_team_with_max_value(
                        streaks,
                        "longest_unbeaten_streak",
                    )
                )

                current_winning_team = (
                    self._get_current_streak_team(
                        streaks,
                        result="S",
                    )
                )

                current_losing_team = (
                    self._get_current_streak_team(
                        streaks,
                        result="N",
                    )
                )

                info_parts = [
                    competition_name
                ]

                if longest_winning_team is not None:
                    info_parts.append(
                        (
                            "Längste Siegesserie: "
                            f"{longest_winning_team['team_name']} "
                            "– "
                            f"{longest_winning_team['longest_win_streak']} "
                            "Spiele"
                        )
                    )

                if longest_unbeaten_team is not None:
                    info_parts.append(
                        (
                            "Längste Ungeschlagen-Serie: "
                            f"{longest_unbeaten_team['team_name']} "
                            "– "
                            f"{longest_unbeaten_team['longest_unbeaten_streak']} "
                            "Spiele"
                        )
                    )

                if current_winning_team is not None:
                    info_parts.append(
                        (
                            "🔥 Aktuell beste Siegesserie: "
                            f"{current_winning_team['team_name']} "
                            "– "
                            f"{current_winning_team['current_length']} "
                            f"{self._game_label(current_winning_team['current_length'])}"
                        )
                    )

                if current_losing_team is not None:
                    info_parts.append(
                        (
                            "🧊 Aktuell längste Niederlagenserie: "
                            f"{current_losing_team['team_name']} "
                            "– "
                            f"{current_losing_team['current_length']} "
                            f"{self._game_label(current_losing_team['current_length'])}"
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
                    "Die Serien konnten "
                    "nicht geladen werden."
                ),
                error=error,
            )

    def populate_table(
        self,
        streaks: list[dict],
    ) -> None:
        self.table.setRowCount(
            len(
                streaks
            )
        )

        for row_index, team in enumerate(
            streaks
        ):
            values = [
                (
                    team["position"]
                    if team["position"] is not None
                    else "-"
                ),
                team["team_name"],
                team["current_label"],
                team["longest_win_streak"],
                team["longest_draw_streak"],
                team["longest_loss_streak"],
                team["longest_unbeaten_streak"],
                team["longest_winless_streak"],
            ]

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

                if column_index == 2:
                    self._style_current_streak_item(
                        item,
                        team.get(
                            "current_result"
                        ),
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    @staticmethod
    def _style_current_streak_item(
        item: QTableWidgetItem,
        result: str | None,
    ) -> None:
        if result == "S":
            item.setForeground(
                QColor(
                    "#66bb6a"
                )
            )

        elif result == "U":
            item.setForeground(
                QColor(
                    "#f0a72f"
                )
            )

        elif result == "N":
            item.setForeground(
                QColor(
                    "#ef5350"
                )
            )

        else:
            item.setForeground(
                QColor(
                    "#9ca3af"
                )
            )

    @staticmethod
    def _get_team_with_max_value(
        streaks: list[dict],
        key: str,
    ) -> dict | None:
        if not streaks:
            return None

        return max(
            streaks,
            key=lambda team: (
                int(
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

    @staticmethod
    def _get_current_streak_team(
        streaks: list[dict],
        result: str,
    ) -> dict | None:
        candidates = [
            team
            for team in streaks
            if (
                team.get(
                    "current_result"
                )
                == result
                and int(
                    team.get(
                        "current_length",
                        0,
                    )
                )
                > 0
            )
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda team: (
                int(
                    team.get(
                        "current_length",
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

    @staticmethod
    def _game_label(
        count: int,
    ) -> str:
        if count == 1:
            return "Spiel"

        return "Spiele"

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