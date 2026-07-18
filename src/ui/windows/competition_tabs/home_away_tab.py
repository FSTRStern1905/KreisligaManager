import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.services.statistics.home_away_service import (
    HomeAwayService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class CompetitionHomeAwayTab(
    BaseStatisticsTab
):
    def __init__(self):
        super().__init__(
            title="📊 Heim-/Auswärtsvergleich",
            refresh_button_text=(
                "🔄 Vergleich aktualisieren"
            ),
        )

        self.table = QTableWidget()
        self.setup_table()

        self.add_content_widget(
            self.table,
            stretch=1,
        )

        self.clear_data()

    def setup_table(self) -> None:
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Mannschaft",
                "Gesamt",
                "Heim",
                "Auswärts",
                "Δ Punkte",
                "Heim-Diff",
                "Auswärts-Diff",
                "Δ Diff",
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

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(2, 9):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

    def load_data(self) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.table.setRowCount(0)

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

                service = HomeAwayService(
                    connection
                )

                comparison = (
                    service.get_comparison(
                        self.competition_id
                    )
                )

                self.populate_table(
                    comparison
                )

                home_stronger_count = sum(
                    1
                    for team in comparison
                    if team["point_difference"] > 0
                )

                away_stronger_count = sum(
                    1
                    for team in comparison
                    if team["point_difference"] < 0
                )

                balanced_count = sum(
                    1
                    for team in comparison
                    if team["point_difference"] == 0
                )

                self.set_info_text(
                    f"{competition_name} | "
                    f"{home_stronger_count} heimstärker | "
                    f"{away_stronger_count} auswärtsstärker | "
                    f"{balanced_count} ausgeglichen"
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
                    "Der Heim-/Auswärtsvergleich "
                    "konnte nicht geladen werden."
                ),
                error=error,
            )

    def populate_table(
        self,
        comparison: list[dict],
    ) -> None:
        self.table.setRowCount(
            len(comparison)
        )

        for row_index, team in enumerate(
            comparison
        ):
            values = [
                row_index + 1,
                team["team_name"],
                team["overall_points"],
                team["home_points"],
                team["away_points"],
                self.format_signed_value(
                    team["point_difference"]
                ),
                self.format_signed_value(
                    team["home_goal_difference"]
                ),
                self.format_signed_value(
                    team["away_goal_difference"]
                ),
                self.format_signed_value(
                    team[
                        "goal_difference_difference"
                    ]
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                if column_index != 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    team["team_id"],
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    @staticmethod
    def format_signed_value(
        value: int,
    ) -> str:
        if value > 0:
            return f"+{value}"

        return str(value)

    def clear_content(self) -> None:
        if not hasattr(
            self,
            "table",
        ):
            return

        self.table.setRowCount(0)