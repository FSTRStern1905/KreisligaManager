from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.dialogs.team_dialog import TeamDialog
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.widgets.card import Card
from src.ui.widgets.data_table import DataTable
from src.ui.widgets.page_header import PageHeader
from src.ui.widgets.primary_button import PrimaryButton
from src.ui.widgets.secondary_button import SecondaryButton
from src.ui.widgets.toolbar import Toolbar


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class TeamsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.teams: list[tuple] = []
        self.filtered_teams: list[tuple] = []

        self.setObjectName(
            "TeamsPage"
        )

        self.setup_ui()
        self.connect_signals()
        self.load_teams()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
            Metrics.PAGE_MARGIN,
        )

        layout.setSpacing(
            Metrics.PAGE_SPACING
        )

        self.header = PageHeader(
            title="Mannschaften",
            subtitle=(
                "Mannschaften durchsuchen "
                "und verwalten"
            ),
        )

        self.toolbar = Toolbar(
            search_placeholder=(
                "Mannschaft oder Verein suchen ..."
            )
        )

        self.refresh_button = SecondaryButton(
            "Aktualisieren"
        )

        self.edit_button = SecondaryButton(
            "Bearbeiten"
        )

        self.delete_button = SecondaryButton(
            "Löschen"
        )

        self.new_button = PrimaryButton(
            "Neue Mannschaft"
        )

        self.toolbar.add_action(
            self.refresh_button
        )

        self.toolbar.add_action(
            self.edit_button
        )

        self.toolbar.add_action(
            self.delete_button
        )

        self.toolbar.add_action(
            self.new_button
        )

        self.list_card = Card(
            title="Mannschaftsübersicht",
            icon="👥",
        )

        self.table = DataTable()

        self.table.set_columns(
            (
                ("team_name", "Mannschaft"),
                ("club_name", "Verein"),
                ("short_name", "Kurzname"),
                ("team_number", "Nr."),
            )
        )

        self.table.set_column_widths(
            {
                "club_name": 280,
                "short_name": 180,
                "team_number": 90,
            }
        )

        self.table.stretch_column(
            "team_name"
        )

        self.list_card.add_widget(
            self.table,
            stretch=1,
        )

        layout.addWidget(
            self.header
        )

        layout.addWidget(
            self.toolbar
        )

        layout.addWidget(
            self.list_card,
            1,
        )

        self._apply_style()

    def connect_signals(self) -> None:
        self.new_button.clicked.connect(
            self.new_team
        )

        self.refresh_button.clicked.connect(
            self.load_teams
        )

        self.edit_button.clicked.connect(
            self.edit_selected_team
        )

        self.delete_button.clicked.connect(
            self.delete_selected_team
        )

        self.toolbar.search_bar.text_changed.connect(
            self.filter_teams
        )

        self.table.row_activated.connect(
            self.edit_team_by_id
        )

    def load_teams(self) -> None:
        self.teams.clear()

        if not DATABASE_PATH.exists():
            self.filtered_teams = []
            self._render_teams()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    teams.team_id,
                    teams.name,
                    teams.short_name,
                    teams.team_number,
                    clubs.name
                FROM teams
                INNER JOIN clubs
                    ON teams.club_id = clubs.club_id
                ORDER BY
                    clubs.name ASC,
                    teams.team_number ASC
                """
            )

            self.teams = cursor.fetchall()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Mannschaften konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.teams = []

        finally:
            connection.close()

        self.filter_teams(
            self.toolbar.search_bar.text()
        )

    def filter_teams(
        self,
        search_text: str = "",
    ) -> None:
        normalized_search = (
            search_text
            .lower()
            .strip()
        )

        if not normalized_search:
            self.filtered_teams = list(
                self.teams
            )
        else:
            self.filtered_teams = [
                team
                for team in self.teams
                if normalized_search
                in self._team_search_text(
                    team
                )
            ]

        self._render_teams()

    def _render_teams(self) -> None:
        rows = []

        for team in self.filtered_teams:
            (
                team_id,
                team_name,
                short_name,
                team_number,
                club_name,
            ) = team

            rows.append(
                {
                    "id": team_id,
                    "team_name": (
                        short_name
                        or team_name
                        or ""
                    ),
                    "club_name": (
                        club_name
                        or ""
                    ),
                    "short_name": (
                        short_name
                        or ""
                    ),
                    "team_number": (
                        team_number
                        if team_number is not None
                        else ""
                    ),
                }
            )

        self.table.set_rows(
            rows,
            id_key="id",
        )

    @staticmethod
    def _team_search_text(
        team: tuple,
    ) -> str:
        (
            _team_id,
            team_name,
            short_name,
            team_number,
            club_name,
        ) = team

        return (
            f"{team_name or ''} "
            f"{short_name or ''} "
            f"{team_number or ''} "
            f"{club_name or ''}"
        ).lower()

    def new_team(self) -> None:
        clubs = self.load_clubs_for_dialog()

        if not clubs:
            QMessageBox.warning(
                self,
                "Keine Vereine vorhanden",
                (
                    "Bitte lege zuerst mindestens "
                    "einen Verein an."
                ),
            )
            return

        dialog = TeamDialog(
            clubs,
            self,
        )

        if not dialog.exec():
            return

        data = dialog.get_data()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            club_name = self.get_club_name(
                cursor,
                data["club_id"],
            )

            cursor.execute(
                """
                INSERT INTO teams (
                    club_id,
                    name,
                    short_name,
                    team_number
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    data["club_id"],
                    club_name,
                    data["team_name"],
                    data["team_number"],
                ),
            )

            connection.commit()
            self.load_teams()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Mannschaft konnte nicht "
                    f"gespeichert werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def edit_selected_team(self) -> None:
        team_id = self.table.selected_row_id()

        if team_id is None:
            QMessageBox.information(
                self,
                "Keine Mannschaft ausgewählt",
                (
                    "Bitte zuerst eine Mannschaft "
                    "auswählen."
                ),
            )
            return

        self.edit_team_by_id(
            team_id
        )

    def edit_team_by_id(
        self,
        team_id: int,
    ) -> None:
        team = self._get_team_by_id(
            team_id
        )

        if team is None:
            QMessageBox.warning(
                self,
                "Mannschaft nicht gefunden",
                (
                    "Die ausgewählte Mannschaft "
                    "konnte nicht gefunden werden."
                ),
            )
            return

        clubs = self.load_clubs_for_dialog()

        if not clubs:
            return

        dialog = TeamDialog(
            clubs,
            self,
        )

        if hasattr(
            dialog,
            "set_data",
        ):
            (
                _team_id,
                _team_name,
                short_name,
                team_number,
                club_name,
            ) = team

            club_id = self._get_club_id_by_name(
                club_name
            )

            dialog.set_data(
                {
                    "club_id": club_id,
                    "team_name": short_name or "",
                    "team_number": (
                        team_number
                        if team_number is not None
                        else 1
                    ),
                }
            )

        if not dialog.exec():
            return

        data = dialog.get_data()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            club_name = self.get_club_name(
                cursor,
                data["club_id"],
            )

            cursor.execute(
                """
                UPDATE teams
                SET
                    club_id = ?,
                    name = ?,
                    short_name = ?,
                    team_number = ?
                WHERE team_id = ?
                """,
                (
                    data["club_id"],
                    club_name,
                    data["team_name"],
                    data["team_number"],
                    team_id,
                ),
            )

            connection.commit()
            self.load_teams()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Mannschaft konnte nicht "
                    f"aktualisiert werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def delete_selected_team(self) -> None:
        team_id = self.table.selected_row_id()

        if team_id is None:
            QMessageBox.information(
                self,
                "Keine Mannschaft ausgewählt",
                (
                    "Bitte zuerst eine Mannschaft "
                    "auswählen."
                ),
            )
            return

        team = self._get_team_by_id(
            team_id
        )

        if team is None:
            return

        display_name = (
            team[2]
            or team[1]
            or "Mannschaft"
        )

        result = QMessageBox.question(
            self,
            "Mannschaft löschen",
            (
                f"Soll die Mannschaft\n\n"
                f"{display_name}\n\n"
                "wirklich gelöscht werden?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM teams
                WHERE team_id = ?
                """,
                (
                    team_id,
                ),
            )

            connection.commit()
            self.load_teams()

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Mannschaft kann nicht gelöscht werden",
                (
                    "Die Mannschaft wird noch von "
                    "anderen Datensätzen verwendet."
                ),
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Mannschaft konnte nicht "
                    f"gelöscht werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def load_clubs_for_dialog(
        self,
    ) -> list[tuple]:
        if not DATABASE_PATH.exists():
            return []

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    club_id,
                    name
                FROM clubs
                ORDER BY name ASC
                """
            )

            return cursor.fetchall()

        except sqlite3.Error:
            return []

        finally:
            connection.close()

    @staticmethod
    def get_club_name(
        cursor: sqlite3.Cursor,
        club_id: int,
    ) -> str:
        cursor.execute(
            """
            SELECT name
            FROM clubs
            WHERE club_id = ?
            """,
            (
                club_id,
            ),
        )

        result = cursor.fetchone()

        if result is None:
            raise ValueError(
                "Verein wurde nicht gefunden."
            )

        return str(
            result[0]
        )

    def _get_club_id_by_name(
        self,
        club_name: str,
    ) -> int | None:
        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT club_id
                FROM clubs
                WHERE name = ?
                LIMIT 1
                """,
                (
                    club_name,
                ),
            )

            result = cursor.fetchone()

            if result is None:
                return None

            return int(
                result[0]
            )

        finally:
            connection.close()

    def _get_team_by_id(
        self,
        team_id: int,
    ) -> tuple | None:
        for team in self.teams:
            if team[0] == team_id:
                return team

        return None

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#TeamsPage {{
                background-color:
                    {Colors.BACKGROUND};
            }}
            """
        )