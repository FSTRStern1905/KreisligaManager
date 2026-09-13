from __future__ import annotations

import sqlite3

from src.services.statistics.lead_comeback_service import (
    LeadComebackService,
)


class DroppedPointsService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

    def get_statistics(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        service = LeadComebackService(
            self.connection
        )

        lead_statistics = service.get_statistics(
            competition_id
        )

        statistics = []

        for team in lead_statistics:
            statistics.append(
                {
                    "team_id": int(
                        team["team_id"]
                    ),
                    "team_name": team["team_name"],
                    "position": int(
                        team.get("position", 0)
                        or 0
                    ),
                    "matches_leading": int(
                        team.get(
                            "matches_leading",
                            0,
                        )
                    ),
                    "dropped_points": int(
                        team.get(
                            "dropped_points_after_leading",
                            0,
                        )
                    ),
                }
            )

        statistics.sort(
            key=lambda team: (
                -team["dropped_points"],
                -team["matches_leading"],
                team["position"] or 9999,
                team["team_name"].lower(),
            )
        )

        return statistics
