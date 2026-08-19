from __future__ import annotations

import sqlite3
from dataclasses import dataclass


GOAL_EVENT_CODES = (
    "GOAL",
    "PENALTY_GOAL",
    "OWN_GOAL",
)


@dataclass(frozen=True)
class LivetickerCompleteness:
    match_id: int
    matchday: int | None
    external_id: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    imported_home_goals: int
    imported_away_goals: int

    @property
    def expected_goals(self) -> int:
        return self.home_goals + self.away_goals

    @property
    def imported_goals(self) -> int:
        return (
            self.imported_home_goals
            + self.imported_away_goals
        )

    @property
    def missing_goals(self) -> int:
        return max(
            0,
            self.expected_goals - self.imported_goals,
        )

    @property
    def extra_goals(self) -> int:
        return max(
            0,
            self.imported_goals - self.expected_goals,
        )

    @property
    def is_complete(self) -> bool:
        return (
            self.home_goals == self.imported_home_goals
            and self.away_goals == self.imported_away_goals
        )

    @property
    def status(self) -> str:
        return "COMPLETE" if self.is_complete else "INCOMPLETE"


class LivetickerCompletenessService:

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def get_all(
        self,
    ) -> list[LivetickerCompleteness]:
        rows = self.connection.execute(
            """
            SELECT
                m.match_id,
                m.matchday,
                m.external_id,
                m.home_team_id,
                m.away_team_id,
                ht.name AS home_team,
                at.name AS away_team,
                m.home_goals,
                m.away_goals,

                SUM(
                    CASE
                        WHEN et.code IN (
                            'GOAL',
                            'PENALTY_GOAL',
                            'OWN_GOAL'
                        )
                        AND e.team_id = m.home_team_id
                        THEN 1
                        ELSE 0
                    END
                ) AS imported_home_goals,

                SUM(
                    CASE
                        WHEN et.code IN (
                            'GOAL',
                            'PENALTY_GOAL',
                            'OWN_GOAL'
                        )
                        AND e.team_id = m.away_team_id
                        THEN 1
                        ELSE 0
                    END
                ) AS imported_away_goals

            FROM matches AS m

            INNER JOIN teams AS ht
                ON ht.team_id = m.home_team_id

            INNER JOIN teams AS at
                ON at.team_id = m.away_team_id

            LEFT JOIN events AS e
                ON e.match_id = m.match_id

            LEFT JOIN event_types AS et
                ON et.event_type_id = e.event_type_id

            WHERE
                m.detail_imported = 1
                AND m.home_goals IS NOT NULL
                AND m.away_goals IS NOT NULL

            GROUP BY
                m.match_id,
                m.matchday,
                m.external_id,
                m.home_team_id,
                m.away_team_id,
                ht.name,
                at.name,
                m.home_goals,
                m.away_goals

            ORDER BY
                m.matchday,
                m.match_id
            """
        ).fetchall()

        return [
            LivetickerCompleteness(
                match_id=int(row["match_id"]),
                matchday=row["matchday"],
                external_id=str(
                    row["external_id"] or ""
                ),
                home_team=str(row["home_team"]),
                away_team=str(row["away_team"]),
                home_goals=int(row["home_goals"]),
                away_goals=int(row["away_goals"]),
                imported_home_goals=int(
                    row["imported_home_goals"] or 0
                ),
                imported_away_goals=int(
                    row["imported_away_goals"] or 0
                ),
            )
            for row in rows
        ]

    def get_incomplete(
        self,
    ) -> list[LivetickerCompleteness]:
        return [
            result
            for result in self.get_all()
            if not result.is_complete
        ]