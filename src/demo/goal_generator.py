import random
import sqlite3


class DemoGoalGenerator:
    GOAL_EVENT_CODE = "GOAL"

    def __init__(
        self,
        connection: sqlite3.Connection,
        seed: int = 2029,
    ):
        self.connection = connection
        self.cursor = connection.cursor()
        self.random = random.Random(seed)

    def generate_for_competition(
        self,
        competition_id: int,
    ) -> dict:
        event_type_id = self._get_event_type_id(
            self.GOAL_EVENT_CODE
        )

        matches = self._load_finished_matches(
            competition_id
        )

        if not matches:
            raise ValueError(
                "Für den Wettbewerb wurden keine "
                "beendeten Spiele gefunden."
            )

        match_ids = [
            match[0]
            for match in matches
        ]

        self._delete_existing_goals(
            match_ids,
            event_type_id,
        )

        generated_goal_count = 0

        for match in matches:
            match_id = match[0]
            home_team_id = match[1]
            away_team_id = match[2]
            home_goals = match[3]
            away_goals = match[4]

            generated_goal_count += self._generate_team_goals(
                match_id=match_id,
                team_id=home_team_id,
                goal_count=home_goals,
                event_type_id=event_type_id,
            )

            generated_goal_count += self._generate_team_goals(
                match_id=match_id,
                team_id=away_team_id,
                goal_count=away_goals,
                event_type_id=event_type_id,
            )

        self.connection.commit()

        return {
            "match_count": len(matches),
            "goal_count": generated_goal_count,
        }

    def _generate_team_goals(
        self,
        match_id: int,
        team_id: int,
        goal_count: int | None,
        event_type_id: int,
    ) -> int:
        if goal_count is None or goal_count <= 0:
            return 0

        players = self._load_goal_candidates(team_id)

        if not players:
            raise ValueError(
                f"Für Mannschaft {team_id} wurden "
                "keine Spieler gefunden."
            )

        used_minutes = set()

        for _ in range(goal_count):
            player_id = self._choose_scorer(players)
            minute = self._generate_unique_minute(
                used_minutes
            )

            self.cursor.execute(
                """
                INSERT INTO events (
                    match_id,
                    event_type_id,
                    minute,
                    second,
                    team_id,
                    player_id,
                    related_player_id,
                    value,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    event_type_id,
                    minute,
                    0,
                    team_id,
                    player_id,
                    None,
                    None,
                    "Automatisch erzeugtes Demo-Tor",
                ),
            )

        return goal_count

    def _load_finished_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                match_id,
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
            ORDER BY match_id
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def _load_goal_candidates(
        self,
        team_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                player_id,
                position
            FROM players
            WHERE
                team_id = ?
                AND is_active = 1
            ORDER BY player_id
            """,
            (team_id,),
        )

        return self.cursor.fetchall()

    def _choose_scorer(
        self,
        players: list[tuple],
    ) -> int:
        player_ids = []
        weights = []

        for player_id, position in players:
            player_ids.append(player_id)
            weights.append(
                self._position_weight(position)
            )

        return self.random.choices(
            player_ids,
            weights=weights,
            k=1,
        )[0]

    def _position_weight(
        self,
        position: str | None,
    ) -> int:
        weights = {
            "Torwart": 1,
            "Innenverteidiger": 3,
            "Außenverteidiger": 4,
            "Defensives Mittelfeld": 5,
            "Zentrales Mittelfeld": 7,
            "Offensives Mittelfeld": 10,
            "Flügel": 12,
            "Stürmer": 16,
        }

        return weights.get(position or "", 6)

    def _generate_unique_minute(
        self,
        used_minutes: set[int],
    ) -> int:
        while True:
            minute = self.random.randint(1, 90)

            if minute not in used_minutes:
                used_minutes.add(minute)
                return minute

    def _get_event_type_id(
        self,
        code: str,
    ) -> int:
        self.cursor.execute(
            """
            SELECT event_type_id
            FROM event_types
            WHERE code = ?
            """,
            (code,),
        )

        result = self.cursor.fetchone()

        if result is None:
            raise ValueError(
                f"Eventtyp '{code}' wurde nicht gefunden."
            )

        return result[0]

    def _delete_existing_goals(
        self,
        match_ids: list[int],
        event_type_id: int,
    ):
        if not match_ids:
            return

        placeholders = ",".join(
            "?"
            for _ in match_ids
        )

        self.cursor.execute(
            f"""
            DELETE FROM events
            WHERE
                event_type_id = ?
                AND match_id IN ({placeholders})
            """,
            (
                event_type_id,
                *match_ids,
            ),
        )