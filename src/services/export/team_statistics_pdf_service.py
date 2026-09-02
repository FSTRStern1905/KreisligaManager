from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from src.services.export.team_pdf_export_service import (
    TeamPdfExportService,
)
from src.services.statistics.form_service import (
    FormService,
)
from src.services.statistics_service import (
    StatisticsService,
)


class TeamStatisticsPdfService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.statistics_service = (
            StatisticsService(
                connection
            )
        )

        self.form_service = FormService(
            connection
        )

        self.team_export_service = (
            TeamPdfExportService(
                connection
            )
        )

    def build_report_data(
        self,
        competition_id: int,
        team_id: int,
        selected_sections: list[str],
    ) -> dict[str, Any]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        team = (
            self.team_export_service
            .validate_team_selection(
                competition_id=competition_id,
                team_id=team_id,
            )
        )

        competition = (
            self._get_competition_meta(
                competition_id
            )
        )

        if competition is None:
            raise ValueError(
                "Der Wettbewerb wurde nicht gefunden."
            )

        sections: dict[str, Any] = {}

        if "overview" in selected_sections:
            sections[
                "overview"
            ] = self._build_overview_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "table_form" in selected_sections:
            sections[
                "table_form"
            ] = self._build_table_form_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        return {
            "team_name": team[
                "team_name"
            ],
            "competition_name": competition[
                "competition_name"
            ],
            "season_name": competition[
                "season_name"
            ],
            "generated_at": datetime.now(),
            "selected_sections": list(
                selected_sections
            ),
            "sections": sections,
        }

    def _build_overview_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        overall_table = (
            self.statistics_service.get_table(
                competition_id=competition_id,
                mode="all",
            )
        )

        team_row = self._find_team_row(
            overall_table,
            team_id,
        )

        if team_row is None:
            return {
                "text": (
                    "Für diese Mannschaft sind "
                    "keine Tabellenwerte vorhanden."
                )
            }

        position = (
            self._get_position(
                overall_table,
                team_id,
            )
        )

        played = int(
            team_row.get(
                "played",
                0,
            )
        )

        points = int(
            team_row.get(
                "points",
                0,
            )
        )

        goals_for = int(
            team_row.get(
                "goals_for",
                0,
            )
        )

        goals_against = int(
            team_row.get(
                "goals_against",
                0,
            )
        )

        goal_difference = int(
            team_row.get(
                "goal_difference",
                (
                    goals_for
                    - goals_against
                ),
            )
        )

        points_per_match = (
            points / played
            if played > 0
            else 0.0
        )

        goals_per_match = (
            goals_for / played
            if played > 0
            else 0.0
        )

        goals_against_per_match = (
            goals_against / played
            if played > 0
            else 0.0
        )

        recent_form = (
            self._get_recent_form(
                competition_id=competition_id,
                team_id=team_id,
                limit=5,
            )
        )

        form_text = (
            " ".join(
                recent_form
            )
            if recent_form
            else "-"
        )

        return {
            "keyfacts": [
                (
                    f"Tabellenplatz: "
                    f"{position if position is not None else '-'}"
                ),
                (
                    f"Punkte: {points}"
                ),
                (
                    f"Tordifferenz: "
                    f"{self._format_signed(goal_difference)}"
                ),
                (
                    f"Form: {form_text}"
                ),
            ],
            "facts": {
                "Tabellenplatz":
                    position
                    if position is not None
                    else "-",
                "Spiele":
                    played,
                "Siege":
                    int(
                        team_row.get(
                            "wins",
                            0,
                        )
                    ),
                "Unentschieden":
                    int(
                        team_row.get(
                            "draws",
                            0,
                        )
                    ),
                "Niederlagen":
                    int(
                        team_row.get(
                            "losses",
                            0,
                        )
                    ),
                "Punkte":
                    points,
                "Punkte / Spiel":
                    round(
                        points_per_match,
                        2,
                    ),
                "Tore":
                    goals_for,
                "Gegentore":
                    goals_against,
                "Tordifferenz":
                    self._format_signed(
                        goal_difference
                    ),
                "Tore / Spiel":
                    round(
                        goals_per_match,
                        2,
                    ),
                "Gegentore / Spiel":
                    round(
                        goals_against_per_match,
                        2,
                    ),
                "Form letzte 5":
                    form_text,
            },
        }

    def _build_table_form_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        home_table = (
            self.statistics_service.get_table(
                competition_id=competition_id,
                mode="home",
            )
        )

        away_table = (
            self.statistics_service.get_table(
                competition_id=competition_id,
                mode="away",
            )
        )

        form_table = (
            self.form_service.get_form_table(
                competition_id=competition_id,
                matches=5,
            )
        )

        home_row = self._find_team_row(
            home_table,
            team_id,
        )

        away_row = self._find_team_row(
            away_table,
            team_id,
        )

        form_row = self._find_team_row(
            form_table,
            team_id,
        )

        home_position = (
            self._get_position(
                home_table,
                team_id,
            )
        )

        away_position = (
            self._get_position(
                away_table,
                team_id,
            )
        )

        form_position = (
            self._get_position(
                form_table,
                team_id,
            )
        )

        blocks: list[dict[str, Any]] = []

        if home_row is not None:
            blocks.append(
                {
                    "title": "Heimbilanz",
                    "facts": self._row_to_facts(
                        row=home_row,
                        position=home_position,
                        position_label="Heimplatz",
                    ),
                }
            )

        if away_row is not None:
            blocks.append(
                {
                    "title": "Auswärtsbilanz",
                    "facts": self._row_to_facts(
                        row=away_row,
                        position=away_position,
                        position_label="Auswärtsplatz",
                    ),
                }
            )

        if form_row is not None:
            recent_form = (
                self._get_recent_form(
                    competition_id=competition_id,
                    team_id=team_id,
                    limit=5,
                )
            )

            form_facts = (
                self._row_to_facts(
                    row=form_row,
                    position=form_position,
                    position_label="Formplatz",
                )
            )

            form_facts[
                "Letzte 5"
            ] = (
                " ".join(
                    recent_form
                )
                if recent_form
                else "-"
            )

            blocks.append(
                {
                    "title": "Form letzte 5 Spiele",
                    "facts": form_facts,
                }
            )

        return {
            "blocks": blocks,
        }

    def _get_competition_meta(
        self,
        competition_id: int,
    ) -> dict[str, str] | None:
        self.cursor.execute(
            """
            SELECT
                competitions.name,
                seasons.name
            FROM competitions
            INNER JOIN seasons
                ON seasons.season_id =
                   competitions.season_id
            WHERE
                competitions.competition_id = ?
            LIMIT 1;
            """,
            (
                competition_id,
            ),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return {
            "competition_name": str(
                row[0]
            ),
            "season_name": str(
                row[1]
            ),
        }

    def _get_recent_form(
        self,
        competition_id: int,
        team_id: int,
        limit: int = 5,
    ) -> list[str]:
        self.cursor.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
                AND (
                    home_team_id = ?
                    OR away_team_id = ?
                )
            ORDER BY
                matchday DESC,
                match_id DESC
            LIMIT ?;
            """,
            (
                competition_id,
                team_id,
                team_id,
                limit,
            ),
        )

        results: list[str] = []

        for row in self.cursor.fetchall():
            home_team_id = int(
                row[0]
            )

            away_team_id = int(
                row[1]
            )

            home_goals = int(
                row[2]
            )

            away_goals = int(
                row[3]
            )

            if team_id == home_team_id:
                goals_for = home_goals
                goals_against = away_goals
            elif team_id == away_team_id:
                goals_for = away_goals
                goals_against = home_goals
            else:
                continue

            if goals_for > goals_against:
                results.append(
                    "S"
                )
            elif goals_for < goals_against:
                results.append(
                    "N"
                )
            else:
                results.append(
                    "U"
                )

        results.reverse()

        return results

    @staticmethod
    def _find_team_row(
        rows: list[dict],
        team_id: int,
    ) -> dict | None:
        for row in rows:
            if int(
                row.get(
                    "team_id",
                    0,
                )
            ) == team_id:
                return row

        return None

    @staticmethod
    def _get_position(
        rows: list[dict],
        team_id: int,
    ) -> int | None:
        for position, row in enumerate(
            rows,
            start=1,
        ):
            if int(
                row.get(
                    "team_id",
                    0,
                )
            ) == team_id:
                return position

        return None

    @staticmethod
    def _row_to_facts(
        row: dict,
        position: int | None,
        position_label: str,
    ) -> dict[str, Any]:
        played = int(
            row.get(
                "played",
                0,
            )
        )

        points = int(
            row.get(
                "points",
                0,
            )
        )

        goals_for = int(
            row.get(
                "goals_for",
                0,
            )
        )

        goals_against = int(
            row.get(
                "goals_against",
                0,
            )
        )

        goal_difference = int(
            row.get(
                "goal_difference",
                (
                    goals_for
                    - goals_against
                ),
            )
        )

        return {
            position_label:
                position
                if position is not None
                else "-",
            "Spiele":
                played,
            "Siege":
                int(
                    row.get(
                        "wins",
                        0,
                    )
                ),
            "Remis":
                int(
                    row.get(
                        "draws",
                        0,
                    )
                ),
            "Niederlagen":
                int(
                    row.get(
                        "losses",
                        0,
                    )
                ),
            "Punkte":
                points,
            "Punkte / Spiel":
                round(
                    (
                        points / played
                        if played > 0
                        else 0.0
                    ),
                    2,
                ),
            "Tore":
                goals_for,
            "Gegentore":
                goals_against,
            "Tordifferenz":
                TeamStatisticsPdfService
                ._format_signed(
                    goal_difference
                ),
        }

    @staticmethod
    def _format_signed(
        value: int,
    ) -> str:
        if value > 0:
            return (
                f"+{value}"
            )

        return str(
            value
        )
