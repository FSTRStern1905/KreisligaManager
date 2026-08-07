from __future__ import annotations

import sqlite3

from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)
from src.services.statistics.form_service import (
    FormService,
)
from src.services.statistics.goal_timeline_service import (
    GoalTimelineService,
)
from src.services.statistics.home_away_service import (
    HomeAwayService,
)
from src.services.statistics.records_service import (
    RecordsService,
)
from src.services.statistics.streak_service import (
    StreakService,
)
from src.services.statistics_service import (
    StatisticsService,
)


class StatisticsUpdater:
    """
    Zentraler Einstiegspunkt für Statistik-Aktualisierungen.

    Match-Ebene:
    - PlayerMatchStats

    Wettbewerbsebene:
    - Tabelle
    - Torjäger
    - Spiel-/Torzähler
    - verschiedene Torschützen
    - Karten
    - Torphasen
    - Heim-/Auswärtsvergleich
    - Form der letzten 5 Spiele
    - Ergebnisserien
    - Rekorde
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

        self.player_match_stats_builder = (
            PlayerMatchStatsBuilder(
                connection
            )
        )

        self.statistics_service = (
            StatisticsService(
                connection
            )
        )

        self.goal_timeline_service = (
            GoalTimelineService(
                connection
            )
        )

        self.home_away_service = (
            HomeAwayService(
                connection
            )
        )

        self.form_service = (
            FormService(
                connection
            )
        )

        self.streak_service = (
            StreakService(
                connection
            )
        )

        self.records_service = (
            RecordsService(
                connection
            )
        )

    def update_match(
        self,
        match_id: int,
    ) -> dict:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        player_match_stats_result = (
            self.player_match_stats_builder.build(
                match_id
            )
        )

        return {
            "match_id": match_id,
            "player_match_stats": (
                player_match_stats_result
            ),
            "player_match_stats_created": int(
                player_match_stats_result.get(
                    "stats_created",
                    0,
                )
            ),
        }

    def update_competition(
        self,
        competition_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        competition_name = (
            self.statistics_service
            .get_competition_name(
                competition_id
            )
        )

        if competition_name is None:
            raise ValueError(
                "Der Wettbewerb wurde nicht gefunden."
            )

        table = (
            self.statistics_service
            .get_table(
                competition_id=competition_id,
                mode="all",
            )
        )

        top_scorers = (
            self.statistics_service
            .get_top_scorers(
                competition_id=competition_id,
            )
        )

        finished_matches = (
            self.statistics_service
            .get_finished_match_count(
                competition_id
            )
        )

        goals = (
            self.statistics_service
            .get_goal_count(
                competition_id
            )
        )

        scorers = (
            self.statistics_service
            .get_scorer_count(
                competition_id
            )
        )

        yellow_cards = (
            self.statistics_service
            .get_card_count(
                competition_id,
                "YELLOW_CARD",
            )
        )

        yellow_red_cards = (
            self.statistics_service
            .get_card_count(
                competition_id,
                "YELLOW_RED_CARD",
            )
        )

        red_cards = (
            self.statistics_service
            .get_card_count(
                competition_id,
                "RED_CARD",
            )
        )

        goal_timeline = (
            self.goal_timeline_service
            .get_goal_timeline(
                competition_id
            )
        )

        home_away = (
            self.home_away_service
            .get_comparison(
                competition_id
            )
        )

        form_table = (
            self.form_service
            .get_form_table(
                competition_id=competition_id,
                matches=5,
            )
        )

        team_streaks = (
            self.streak_service
            .get_team_streaks(
                competition_id
            )
        )

        streak_records = (
            self.streak_service
            .get_competition_records(
                competition_id
            )
        )

        records = (
            self.records_service
            .get_records(
                competition_id
            )
        )

        return {
            "competition_id": competition_id,
            "competition_name": competition_name,
            "finished_matches": finished_matches,
            "goals": goals,
            "different_scorers": scorers,
            "yellow_cards": yellow_cards,
            "yellow_red_cards": yellow_red_cards,
            "red_cards": red_cards,
            "cards_total": (
                yellow_cards
                + yellow_red_cards
                + red_cards
            ),
            "table": table,
            "top_scorers": top_scorers,
            "goal_timeline": goal_timeline,
            "home_away": home_away,
            "form_last_5": form_table,
            "team_streaks": team_streaks,
            "streak_records": streak_records,
            "records": records,
        }