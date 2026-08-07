from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography
from src.ui.widgets.card import Card
from src.ui.widgets.data_table import DataTable
from src.ui.widgets.page_header import PageHeader
from src.ui.widgets.secondary_button import SecondaryButton
from src.ui.widgets.toolbar import Toolbar


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class MatchesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.matches: list[dict] = []
        self.filtered_matches: list[dict] = []

        self.setObjectName(
            "MatchesPage"
        )

        self.setup_ui()
        self.connect_signals()
        self.load_matches()

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
            title="Spiele",
            subtitle=(
                "Spielplan durchsuchen und "
                "Ergebnisse überblicken"
            ),
        )

        self.toolbar = Toolbar(
            search_placeholder=(
                "Team, Spieltag, Status oder Ergebnis suchen ..."
            )
        )

        self.refresh_button = SecondaryButton(
            "Aktualisieren"
        )

        self.toolbar.add_action(
            self.refresh_button
        )

        self.overview_card = Card(
            title="Spielübersicht",
            icon="⚽",
        )

        self.info_label = QLabel(
            "0 Spieltage · 0 Spiele"
        )

        self.info_label.setObjectName(
            "MatchesInfoLabel"
        )

        self.info_label.setFont(
            Typography.small()
        )

        self.table = DataTable()

        self.table.set_columns(
            (
                ("matchday", "ST"),
                ("date", "Datum"),
                ("time", "Uhrzeit"),
                ("home", "Heim"),
                ("result", "Ergebnis"),
                ("away", "Gast"),
                ("status", "Status"),
            )
        )

        self.table.set_column_widths(
            {
                "matchday": 70,
                "date": 110,
                "time": 90,
                "result": 95,
                "status": 120,
            }
        )

        self.table.stretch_column(
            "home"
        )

        self.table.stretch_column(
            "away"
        )

        self.overview_card.add_widget(
            self.info_label
        )

        self.overview_card.add_widget(
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
            self.overview_card,
            1,
        )

        self._apply_style()

    def connect_signals(self) -> None:
        self.refresh_button.clicked.connect(
            self.load_matches
        )

        self.toolbar.search_bar.text_changed.connect(
            self.filter_matches
        )

    def load_matches(self) -> None:
        self.matches.clear()

        if not DATABASE_PATH.exists():
            self.filtered_matches = []
            self._render_matches()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    m.match_id,
                    m.matchday,
                    m.match_date,
                    m.kickoff_time,
                    h.name,
                    h.short_name,
                    a.name,
                    a.short_name,
                    m.home_goals,
                    m.away_goals,
                    m.status
                FROM matches m
                JOIN teams h
                    ON h.team_id = m.home_team_id
                JOIN teams a
                    ON a.team_id = m.away_team_id
                ORDER BY
                    CASE
                        WHEN m.match_date IS NULL THEN 1
                        ELSE 0
                    END,
                    m.match_date,
                    m.kickoff_time,
                    m.matchday,
                    m.match_id
                """
            )

            rows = cursor.fetchall()

            for row in rows:
                (
                    match_id,
                    matchday,
                    match_date,
                    kickoff_time,
                    home_name,
                    home_short,
                    away_name,
                    away_short,
                    home_goals,
                    away_goals,
                    status,
                ) = row

                home_display = (
                    home_short
                    or home_name
                    or "-"
                )

                away_display = (
                    away_short
                    or away_name
                    or "-"
                )

                result = self._format_result(
                    home_goals,
                    away_goals,
                )

                self.matches.append(
                    {
                        "id": int(match_id),
                        "matchday": (
                            str(matchday)
                            if matchday is not None
                            else "-"
                        ),
                        "date": self._format_date(
                            match_date
                        ),
                        "time": self._format_time(
                            kickoff_time
                        ),
                        "home": home_display,
                        "home_full": home_name or "",
                        "away": away_display,
                        "away_full": away_name or "",
                        "result": result,
                        "status": self._format_status(
                            status
                        ),
                        "status_raw": status or "",
                    }
                )

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Spiele konnten nicht "
                    f"geladen werden:\n{error}"
                ),
            )

            self.matches = []

        finally:
            connection.close()

        self.filter_matches(
            self.toolbar.search_bar.text()
        )

    def filter_matches(
        self,
        search_text: str = "",
    ) -> None:
        normalized_search = (
            search_text
            .strip()
            .casefold()
        )

        if not normalized_search:
            self.filtered_matches = list(
                self.matches
            )
        else:
            self.filtered_matches = [
                match
                for match in self.matches
                if normalized_search
                in self._search_text(
                    match
                )
            ]

        self._render_matches()

    def _render_matches(self) -> None:
        rows = [
            {
                "id": match["id"],
                "matchday": match["matchday"],
                "date": match["date"],
                "time": match["time"],
                "home": match["home"],
                "result": match["result"],
                "away": match["away"],
                "status": match["status"],
            }
            for match in self.filtered_matches
        ]

        self.table.set_rows(
            rows,
            id_key="id",
        )

        matchdays = {
            match["matchday"]
            for match in self.filtered_matches
            if match["matchday"] != "-"
        }

        match_count = len(
            self.filtered_matches
        )

        total_count = len(
            self.matches
        )

        if match_count == total_count:
            self.info_label.setText(
                (
                    f"{len(matchdays)} Spieltage · "
                    f"{match_count} Spiele"
                )
            )
        else:
            self.info_label.setText(
                (
                    f"{len(matchdays)} Spieltage · "
                    f"{match_count} von "
                    f"{total_count} Spielen"
                )
            )

    @staticmethod
    def _search_text(
        match: dict,
    ) -> str:
        return (
            f"{match['matchday']} "
            f"{match['date']} "
            f"{match['time']} "
            f"{match['home']} "
            f"{match['home_full']} "
            f"{match['away']} "
            f"{match['away_full']} "
            f"{match['result']} "
            f"{match['status']} "
            f"{match['status_raw']}"
        ).casefold()

    @staticmethod
    def _format_result(
        home_goals,
        away_goals,
    ) -> str:
        if (
            home_goals is None
            or away_goals is None
        ):
            return "- : -"

        return (
            f"{home_goals} : "
            f"{away_goals}"
        )

    @staticmethod
    def _format_date(
        value,
    ) -> str:
        if value is None:
            return "-"

        text = str(value).strip()

        if not text:
            return "-"

        if len(text) >= 10:
            parts = text[:10].split("-")

            if len(parts) == 3:
                year, month, day = parts

                if (
                    len(year) == 4
                    and len(month) == 2
                    and len(day) == 2
                ):
                    return (
                        f"{day}.{month}.{year}"
                    )

        return text

    @staticmethod
    def _format_time(
        value,
    ) -> str:
        if value is None:
            return "-"

        text = str(value).strip()

        if not text:
            return "-"

        if len(text) >= 5:
            return text[:5]

        return text

    @staticmethod
    def _format_status(
        status,
    ) -> str:
        normalized = (
            str(status or "")
            .strip()
            .casefold()
        )

        status_map = {
            "scheduled": "Geplant",
            "finished": "Beendet",
            "cancelled": "Abgesagt",
            "canceled": "Abgesagt",
            "postponed": "Verlegt",
            "live": "Live",
            "in_progress": "Live",
        }

        return status_map.get(
            normalized,
            status or "-",
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#MatchesPage {{
                background-color:
                    {Colors.BACKGROUND};
            }}

            QLabel#MatchesInfoLabel {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
                border:
                    none;
            }}
            """
        )