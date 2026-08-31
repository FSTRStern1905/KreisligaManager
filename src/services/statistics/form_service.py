from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class FormService(TableService):
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        super().__init__(
            connection
        )

    def get_form_table(
        self,
        competition_id: int,
        matches: int = 5,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if matches <= 0:
            raise ValueError(
                "Die Anzahl der Formspiele muss größer als 0 sein."
            )

        standings = self._create_empty_table(
            competition_id
        )

        recent_matches = (
            self._load_recent_matches(
                competition_id=competition_id,
                match_count=matches,
            )
        )

        for match in recent_matches:
            self._apply_match_result(
                standings=standings,
                match=match,
                mode="all",
            )

        self._calculate_goal_differences(
            standings
        )

        form_sequences = (
            self.get_form_sequences(
                competition_id=competition_id,
                matches=matches,
            )
        )

        for row in standings.values():
            team_id = int(
                row["team_id"]
            )

            sequence = form_sequences.get(
                team_id,
                [],
            )

            row["form"] = sequence

            row["form_text"] = (
                " ".join(
                    sequence
                )
            )

        return self._sort_table(
            standings
        )

    def get_form_sequences(
        self,
        competition_id: int,
        matches: int = 5,
    ) -> dict[int, list[str]]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if matches <= 0:
            raise ValueError(
                "Die Anzahl der Formspiele muss größer als 0 sein."
            )

        rows = self._load_sequence_matches(
            competition_id
        )

        sequences: dict[
            int,
            list[str],
        ] = {}

        for row in rows:
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

            home_result = self._result_code(
                goals_for=home_goals,
                goals_against=away_goals,
            )

            away_result = self._result_code(
                goals_for=away_goals,
                goals_against=home_goals,
            )

            sequences.setdefault(
                home_team_id,
                [],
            ).append(
                home_result
            )

            sequences.setdefault(
                away_team_id,
                [],
            ).append(
                away_result
            )

        for team_id in list(
            sequences.keys()
        ):
            sequences[team_id] = (
                sequences[
                    team_id
                ][-matches:]
            )

        return sequences

    def _load_recent_matches(
        self,
        competition_id: int,
        match_count: int,
    ) -> list[tuple]:
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

            ORDER BY
                matchday DESC,
                match_date DESC,
                match_id DESC
            """,
            (competition_id,),
        )

        matches = self.cursor.fetchall()

        team_matches: dict[
            int,
            int,
        ] = {}

        result: list[tuple] = []

        for match in matches:
            home_team = int(
                match[0]
            )

            away_team = int(
                match[1]
            )

            home_count = team_matches.get(
                home_team,
                0,
            )

            away_count = team_matches.get(
                away_team,
                0,
            )

            if (
                home_count >= match_count
                and away_count >= match_count
            ):
                continue

            result.append(
                match
            )

            if home_count < match_count:
                team_matches[
                    home_team
                ] = (
                    home_count + 1
                )

            if away_count < match_count:
                team_matches[
                    away_team
                ] = (
                    away_count + 1
                )

        result.reverse()

        return result

    def _load_sequence_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
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

            ORDER BY
                matchday ASC,
                match_date ASC,
                match_id ASC
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    @staticmethod
    def _result_code(
        goals_for: int,
        goals_against: int,
    ) -> str:
        if goals_for > goals_against:
            return "S"

        if goals_for < goals_against:
            return "N"

        return "U"