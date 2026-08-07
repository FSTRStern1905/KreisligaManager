from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.dialogs.club_dialog import ClubDialog
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


class ClubsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.clubs: list[tuple] = []
        self.filtered_clubs: list[tuple] = []

        self.setObjectName(
            "ClubsPage"
        )

        self.setup_ui()
        self.connect_signals()
        self.load_clubs()

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
            title="Vereine",
            subtitle=(
                "Vereine durchsuchen und "
                "verwalten"
            ),
        )

        self.toolbar = Toolbar(
            search_placeholder=(
                "Verein, Kurzname oder Ort suchen ..."
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
            "Neuer Verein"
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
            title="Vereinsübersicht",
            icon="🏟",
        )

        self.table = DataTable()

        self.table.set_columns(
            (
                ("name", "Verein"),
                ("short_name", "Kurzname"),
                ("city", "Ort"),
            )
        )

        self.table.set_column_widths(
            {
                "short_name": 140,
                "city": 220,
            }
        )

        self.table.stretch_column(
            "name"
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
            self.new_club
        )

        self.edit_button.clicked.connect(
            self.edit_selected_club
        )

        self.delete_button.clicked.connect(
            self.delete_selected_club
        )

        self.refresh_button.clicked.connect(
            self.load_clubs
        )

        self.toolbar.search_bar.text_changed.connect(
            self.filter_clubs
        )

        self.table.row_activated.connect(
            self.edit_club_by_id
        )

    def load_clubs(self) -> None:
        self.clubs.clear()

        if not DATABASE_PATH.exists():
            self.filtered_clubs = []
            self._render_clubs()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    club_id,
                    name,
                    short_name,
                    city
                FROM clubs
                ORDER BY name ASC
                """
            )

            self.clubs = cursor.fetchall()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Vereine konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.clubs = []

        finally:
            connection.close()

        self.filter_clubs(
            self.toolbar.search_bar.text()
        )

    def filter_clubs(
        self,
        search_text: str = "",
    ) -> None:
        normalized_search = (
            search_text
            .lower()
            .strip()
        )

        if not normalized_search:
            self.filtered_clubs = list(
                self.clubs
            )
        else:
            self.filtered_clubs = [
                club
                for club in self.clubs
                if normalized_search
                in self._club_search_text(
                    club
                )
            ]

        self._render_clubs()

    def _render_clubs(self) -> None:
        rows = []

        for club in self.filtered_clubs:
            (
                club_id,
                name,
                short_name,
                city,
            ) = club

            rows.append(
                {
                    "id": club_id,
                    "name": name or "",
                    "short_name": short_name or "",
                    "city": city or "",
                }
            )

        self.table.set_rows(
            rows,
            id_key="id",
        )

    @staticmethod
    def _club_search_text(
        club: tuple,
    ) -> str:
        (
            _club_id,
            name,
            short_name,
            city,
        ) = club

        return (
            f"{name or ''} "
            f"{short_name or ''} "
            f"{city or ''}"
        ).lower()

    def new_club(self) -> None:
        dialog = ClubDialog(
            self
        )

        if not dialog.exec():
            return

        data = dialog.get_data()

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO clubs (
                    name,
                    short_name,
                    city
                )
                VALUES (?, ?, ?)
                """,
                (
                    data["name"],
                    data["short_name"],
                    data["city"],
                ),
            )

            connection.commit()

            self.load_clubs()

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Verein existiert bereits",
                (
                    "Dieser Verein ist bereits "
                    "vorhanden."
                ),
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Verein konnte nicht "
                    f"gespeichert werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def edit_selected_club(self) -> None:
        club_id = self.table.selected_row_id()

        if club_id is None:
            QMessageBox.information(
                self,
                "Kein Verein ausgewählt",
                (
                    "Bitte zuerst einen Verein "
                    "auswählen."
                ),
            )
            return

        self.edit_club_by_id(
            club_id
        )

    def edit_club_by_id(
        self,
        club_id: int,
    ) -> None:
        club = self._get_club_by_id(
            club_id
        )

        if club is None:
            QMessageBox.warning(
                self,
                "Verein nicht gefunden",
                (
                    "Der ausgewählte Verein "
                    "konnte nicht gefunden werden."
                ),
            )
            return

        dialog = ClubDialog(
            self
        )

        if hasattr(
            dialog,
            "set_data",
        ):
            dialog.set_data(
                {
                    "name": club[1] or "",
                    "short_name": club[2] or "",
                    "city": club[3] or "",
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
            cursor.execute(
                """
                UPDATE clubs
                SET
                    name = ?,
                    short_name = ?,
                    city = ?
                WHERE club_id = ?
                """,
                (
                    data["name"],
                    data["short_name"],
                    data["city"],
                    club_id,
                ),
            )

            connection.commit()
            self.load_clubs()

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Verein existiert bereits",
                (
                    "Ein Verein mit diesen Daten "
                    "ist bereits vorhanden."
                ),
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Verein konnte nicht "
                    f"aktualisiert werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def delete_selected_club(self) -> None:
        club_id = self.table.selected_row_id()

        if club_id is None:
            QMessageBox.information(
                self,
                "Kein Verein ausgewählt",
                (
                    "Bitte zuerst einen Verein "
                    "auswählen."
                ),
            )
            return

        club = self._get_club_by_id(
            club_id
        )

        if club is None:
            return

        result = QMessageBox.question(
            self,
            "Verein löschen",
            (
                f"Soll der Verein\n\n"
                f"{club[1]}\n\n"
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
                DELETE FROM clubs
                WHERE club_id = ?
                """,
                (
                    club_id,
                ),
            )

            connection.commit()
            self.load_clubs()

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Verein kann nicht gelöscht werden",
                (
                    "Der Verein wird noch von "
                    "anderen Datensätzen verwendet."
                ),
            )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Verein konnte nicht "
                    f"gelöscht werden:\n{error}"
                ),
            )

        finally:
            connection.close()

    def _get_club_by_id(
        self,
        club_id: int,
    ) -> tuple | None:
        for club in self.clubs:
            if club[0] == club_id:
                return club

        return None

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#ClubsPage {{
                background-color:
                    {Colors.BACKGROUND};
            }}
            """
        )