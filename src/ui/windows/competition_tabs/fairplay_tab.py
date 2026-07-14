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

from src.services.statistics_service import StatisticsService


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionFairplayTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🟨 Fairplay")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.fairplay_table = QTableWidget()
        self.fairplay_table.setColumnCount(6)

        self.fairplay_table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Mannschaft",
                "Gelb",
                "Gelb-Rot",
                "Rot",
                "Strafpunkte",
            ]
        )

        self.fairplay_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.fairplay_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.fairplay_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.fairplay_table.setAlternatingRowColors(True)
        self.fairplay_table.verticalHeader().setVisible(False)

        header = self.fairplay_table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        for column in range(2, 6):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeToContents,
            )

        self.refresh_button = QPushButton(
            "🔄 Fairplay aktualisieren"
        )
        self.refresh_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.fairplay_table)
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
        self.fairplay_table.setRowCount(0)

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            service = StatisticsService(
                connection
            )

            competition_name = (
                service.get_competition_name(
                    self.competition_id
                )
            )

            if competition_name is None:
                self.clear_data()
                return

            fairplay_rows = (
                service.get_fairplay_table(
                    self.competition_id
                )
            )

            yellow_cards = service.get_card_count(
                self.competition_id,
                "YELLOW_CARD",
            )

            yellow_red_cards = (
                service.get_card_count(
                    self.competition_id,
                    "YELLOW_RED_CARD",
                )
            )

            red_cards = service.get_card_count(
                self.competition_id,
                "RED_CARD",
            )

            self.show_fairplay_table(
                fairplay_rows
            )

            self.info_label.setText(
                f"{competition_name} | "
                f"{yellow_cards} Gelbe | "
                f"{yellow_red_cards} Gelb-Rote | "
                f"{red_cards} Rote Karten"
            )

            self.refresh_button.setEnabled(True)

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die Fairplay-Tabelle konnte "
                    f"nicht geladen werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def show_fairplay_table(
        self,
        fairplay_rows: list[dict],
    ):
        self.fairplay_table.setRowCount(
            len(fairplay_rows)
        )

        current_position = 0
        previous_points = None

        for row_index, team in enumerate(
            fairplay_rows
        ):
            if (
                team["fairplay_points"]
                != previous_points
            ):
                current_position = row_index + 1
                previous_points = (
                    team["fairplay_points"]
                )

            values = [
                current_position,
                team["team_name"],
                team["yellow_cards"],
                team["yellow_red_cards"],
                team["red_cards"],
                team["fairplay_points"],
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

                self.fairplay_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.fairplay_table.setRowCount(0)

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(False)