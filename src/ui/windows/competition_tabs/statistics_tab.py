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


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionStatisticsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🏆 Torjäger")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.scorer_table = QTableWidget()
        self.scorer_table.setColumnCount(5)

        self.scorer_table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Spieler",
                "Mannschaft",
                "Position",
                "Tore",
            ]
        )

        self.scorer_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.scorer_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.scorer_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.scorer_table.setAlternatingRowColors(True)
        self.scorer_table.verticalHeader().setVisible(False)

        header = self.scorer_table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents,
        )

        self.refresh_button = QPushButton(
            "🔄 Torjäger aktualisieren"
        )
        self.refresh_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.scorer_table)
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
        self.scorer_table.setRowCount(0)

        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:
            competition_name = self._load_competition_name(
                cursor
            )

            if competition_name is None:
                self.clear_data()
                return

            scorers = self._load_scorers(cursor)

            self._show_scorers(scorers)

            total_goals = sum(
                scorer["goals"]
                for scorer in scorers
            )

            self.info_label.setText(
                f"{competition_name} | "
                f"{len(scorers)} Torschützen | "
                f"{total_goals} Tore"
            )

            self.refresh_button.setEnabled(True)

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Die Torjägerliste konnte nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def _load_competition_name(
        self,
        cursor: sqlite3.Cursor,
    ) -> str | None:
        cursor.execute(
            """
            SELECT name
            FROM competitions
            WHERE competition_id = ?
            """,
            (self.competition_id,),
        )

        result = cursor.fetchone()

        if result is None:
            return None

        return result[0]

    def _load_scorers(
        self,
        cursor: sqlite3.Cursor,
    ) -> list[dict]:
        cursor.execute(
            """
            SELECT
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.name,
                teams.short_name,
                COUNT(events.event_id) AS goal_count
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            INNER JOIN matches
                ON matches.match_id = events.match_id
            INNER JOIN players
                ON players.player_id = events.player_id
            INNER JOIN teams
                ON teams.team_id = events.team_id
            WHERE
                matches.competition_id = ?
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL'
                )
            GROUP BY
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.team_id,
                teams.name,
                teams.short_name
            ORDER BY
                goal_count DESC,
                players.last_name ASC,
                players.first_name ASC
            """,
            (self.competition_id,),
        )

        scorers = []

        for row in cursor.fetchall():
            first_name = row[1] or ""
            last_name = row[2] or ""

            player_name = (
                f"{first_name} {last_name}"
            ).strip()

            team_name = row[5] or row[4]

            scorers.append(
                {
                    "player_id": row[0],
                    "player_name": player_name,
                    "position": row[3] or "-",
                    "team_name": team_name,
                    "goals": row[6],
                }
            )

        return scorers

    def _show_scorers(
        self,
        scorers: list[dict],
    ):
        self.scorer_table.setRowCount(
            len(scorers)
        )

        current_position = 0
        previous_goals = None

        for row_index, scorer in enumerate(scorers):
            if scorer["goals"] != previous_goals:
                current_position = row_index + 1
                previous_goals = scorer["goals"]

            values = [
                current_position,
                scorer["player_name"],
                scorer["team_name"],
                scorer["position"],
                scorer["goals"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column_index in {
                    0,
                    3,
                    4,
                }:
                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                item.setData(
                    Qt.UserRole,
                    scorer["player_id"],
                )

                self.scorer_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.scorer_table.setRowCount(0)

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(False)