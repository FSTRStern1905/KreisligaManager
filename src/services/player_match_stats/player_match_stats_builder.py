from __future__ import annotations

import sqlite3

from src.database.repositories.event_repository import (
    EventRepository,
)
from src.database.repositories.lineup_repository import (
    LineupRepository,
)
from src.database.repositories.player_match_stats_repository import (
    PlayerMatchStatsRepository,
)
from src.services.player_match_stats.event_mapper import (
    EventMapper,
)
from src.services.player_match_stats.lineup_mapper import (
    LineupMapper,
)
from src.services.player_match_stats.minutes_calculator import (
    MinutesCalculator,
)


class PlayerMatchStatsBuilder:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

        self.event_repository = EventRepository(
            connection
        )

        self.lineup_repository = LineupRepository(
            connection
        )

        self.player_match_stats_repository = (
            PlayerMatchStatsRepository(
                connection
            )
        )

        self.lineup_mapper = LineupMapper()
        self.event_mapper = EventMapper()
        self.minutes_calculator = (
            MinutesCalculator()
        )

    def build(
        self,
        match_id: int,
    ) -> dict:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        lineups = (
            self.lineup_repository
            .get_by_match(match_id)
        )

        if not lineups:
            return {
                "match_id": match_id,
                "lineups_found": 0,
                "events_found": 0,
                "stats_created": 0,
            }

        events = (
            self.event_repository
            .get_by_match(match_id)
        )

        stats = self.lineup_mapper.build(
            lineups
        )

        self.event_mapper.apply(
            stats=stats,
            events=events,
        )

        self.minutes_calculator.apply(
            stats=stats
        )

        try:
            stats_created = (
                self.player_match_stats_repository
                .replace_match(
                    match_id=match_id,
                    stats=stats,
                )
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        return {
            "match_id": match_id,
            "lineups_found": len(lineups),
            "events_found": len(events),
            "stats_created": stats_created,
        }