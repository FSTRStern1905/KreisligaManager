import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.home_away_service import (
    HomeAwayService,
)
from src.services.statistics_service import (
    StatisticsService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionHomeAwayTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel(
            "📊 Heim-/Auswärtsvergleich"
        )
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.table = QTableWidget()
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
            QAbstractItemView.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        for column in range(2, 9):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeToContents,
            )

        self.refresh_button = QPushButton(
            "🔄 Vergleich aktualisieren"
        )
        self.refresh_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.table)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def connect_signals(self):
        self.refresh_button.clicked.connect(
            self.load_data
        )

    def set_competition(
        self,
        competition_id: int | None,
    ):
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            statistics_service = StatisticsService(
                connection
            )

            comparison_service = HomeAwayService(
                connection
            )

            competition_name = (
                statistics_service.get_competition_name(
                    self.competition_id
                )
            )

            if competition_name is None:
                self.clear_data()
                return

            comparison = (
                comparison_service.get_comparison(
                    self.competition_id
                )
            )

            self.show_comparison(
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

            self.info_label.setText(
                f"{competition_name} | "
                f"{home_stronger_count} heimstärker | "
                f"{away_stronger_count} auswärtsstärker | "
                f"{balanced_count} ausgeglichen"
            )

            self.refresh_button.setEnabled(True)

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Der Heim-/Auswärtsvergleich "
                    "konnte nicht geladen werden:\n"
                    f"{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_comparison(
        self,
        comparison: list[dict],
    ):
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
                        Qt.AlignCenter
                    )

                item.setData(
                    Qt.UserRole,
                    team["team_id"],
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def format_signed_value(
        self,
        value: int,
    ) -> str:
        if value > 0:
            return f"+{value}"

        return str(value)

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.table.setRowCount(0)

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(False)