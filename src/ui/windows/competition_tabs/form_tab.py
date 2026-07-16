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

from src.services.statistics.form_service import (
    FormService,
)
from src.services.statistics_service import (
    StatisticsService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionFormTab(QWidget):

    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):

        layout = QVBoxLayout()

        title = QLabel(
            "📈 Formtabelle"
        )
        title.setObjectName(
            "PageTitle"
        )

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName(
            "InfoLabel"
        )

        self.table = QTableWidget()

        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Mannschaft",
                "Sp",
                "S",
                "U",
                "N",
                "Tore",
                "Diff",
                "Pkt",
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

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = (
            self.table.horizontalHeader()
        )

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
            "🔄 Form aktualisieren"
        )

        self.refresh_button.setEnabled(
            False
        )

        layout.addWidget(title)
        layout.addWidget(
            self.info_label
        )
        layout.addWidget(
            self.table
        )
        layout.addWidget(
            self.refresh_button
        )

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

            statistics_service = (
                StatisticsService(
                    connection
                )
            )

            form_service = FormService(
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

            standings = (
                form_service.get_form_table(
                    competition_id=self.competition_id,
                    matches=5,
                )
            )

            self.show_standings(
                standings
            )

            self.info_label.setText(
                (
                    f"{competition_name} | "
                    "Letzte 5 Spiele"
                )
            )

            self.refresh_button.setEnabled(
                True
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:

            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die Formtabelle "
                    "konnte nicht geladen "
                    f"werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:

            connection.close()

    def show_standings(
        self,
        standings: list[dict],
    ):

        self.table.setRowCount(
            len(standings)
        )

        for row_index, team in enumerate(
            standings
        ):

            goal_text = (
                f"{team['goals_for']}:"
                f"{team['goals_against']}"
            )

            goal_difference = (
                f"+{team['goal_difference']}"
                if team["goal_difference"] > 0
                else str(
                    team["goal_difference"]
                )
            )

            values = [
                row_index + 1,
                team["team_name"],
                team["played"],
                team["wins"],
                team["draws"],
                team["losses"],
                goal_text,
                goal_difference,
                team["points"],
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
        def show_standings(
        self,
        standings: list[dict],
    ):

                self.table.setRowCount(
                len(standings)
        )

        for row_index, team in enumerate(
            standings
        ):

            goal_text = (
                f"{team['goals_for']}:"
                f"{team['goals_against']}"
            )

            goal_difference = (
                f"+{team['goal_difference']}"
                if team["goal_difference"] > 0
                else str(
                    team["goal_difference"]
                )
            )

            values = [
                row_index + 1,
                team["team_name"],
                team["played"],
                team["wins"],
                team["draws"],
                team["losses"],
                goal_text,
                goal_difference,
                team["points"],
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

    def refresh(self):

        self.load_data()

    def clear_data(self):

        self.table.setRowCount(0)

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(
            False
        )