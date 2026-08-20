from __future__ import annotations

import sqlite3

from src.services.validation.validation_result import (
    ValidationCheck,
    ValidationResult,
)


class ImportValidationService:
    CARD_EVENT_CODES = (
        "YELLOW_CARD",
        "YELLOW_RED_CARD",
        "RED_CARD",
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def validate(
        self,
        competition_id: int | None = None,
    ) -> ValidationResult:
        if competition_id is not None and competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        result = ValidationResult()

        result.add_check(
            self._check_integrity(
                competition_id
            )
        )
        result.add_check(
            self._check_goals(
                competition_id
            )
        )
        result.add_check(
            self._check_lineups(
                competition_id
            )
        )
        result.add_check(
            self._check_minutes(
                competition_id
            )
        )
        result.add_check(
            self._check_cards(
                competition_id
            )
        )

        return result

    def _check_integrity(
        self,
        competition_id: int | None,
    ) -> ValidationCheck:
        errors: list[str] = []
        warnings: list[str] = []

        duplicate_stats = self._fetch_all(
            """
            SELECT
                player_match_stats.match_id,
                player_match_stats.player_id,
                COUNT(*)
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id
            WHERE
                (? IS NULL OR matches.competition_id = ?)
            GROUP BY
                player_match_stats.match_id,
                player_match_stats.player_id
            HAVING COUNT(*) > 1
            ORDER BY
                player_match_stats.match_id,
                player_match_stats.player_id;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        for match_id, player_id, count in duplicate_stats:
            errors.append(
                "Doppelter Spielerstatistik-Datensatz: "
                f"Spiel {match_id}, Spieler {player_id}, "
                f"{count} Einträge."
            )

        orphan_events = self._fetch_value(
            """
            SELECT COUNT(*)
            FROM events
            LEFT JOIN matches
                ON matches.match_id = events.match_id
            WHERE matches.match_id IS NULL;
            """
        )

        if orphan_events > 0:
            errors.append(
                f"{orphan_events} Events besitzen "
                "kein gültiges Spiel."
            )

        orphan_stats = self._fetch_value(
            """
            SELECT COUNT(*)
            FROM player_match_stats
            LEFT JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id
            LEFT JOIN teams
                ON teams.team_id =
                    player_match_stats.team_id
            LEFT JOIN players
                ON players.player_id =
                    player_match_stats.player_id
            WHERE
                matches.match_id IS NULL
                OR teams.team_id IS NULL
                OR players.player_id IS NULL;
            """
        )

        if orphan_stats > 0:
            errors.append(
                f"{orphan_stats} Spielerstatistiken "
                "besitzen ungültige Referenzen."
            )

        matches_without_competition = self._fetch_value(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE competition_id IS NULL;
            """
        )

        if matches_without_competition > 0:
            warnings.append(
                f"{matches_without_competition} Spiele "
                "besitzen keinen Wettbewerb."
            )

        return ValidationCheck(
            name="Datenintegrität",
            passed=not errors,
            warnings=warnings,
            errors=errors,
        )

    def _check_goals(
        self,
        competition_id: int | None,
    ) -> ValidationCheck:
        errors: list[str] = []
        warnings: list[str] = []

        rows = self._fetch_all(
            """
            SELECT
                matches.match_id,
                home_teams.name,
                away_teams.name,
                COALESCE(matches.home_goals, 0),
                COALESCE(matches.away_goals, 0),

                COALESCE(
                    (
                        SELECT COUNT(*)
                        FROM events
                        INNER JOIN event_types
                            ON event_types.event_type_id =
                                events.event_type_id
                        WHERE
                            events.match_id = matches.match_id
                            AND event_types.code IN (
                                'GOAL',
                                'PENALTY_GOAL',
                                'OWN_GOAL'
                            )
                    ),
                    0
                ) AS event_goals,

                COALESCE(
                    (
                        SELECT
                            SUM(
                                player_match_stats.goals
                                + player_match_stats.own_goals
                            )
                        FROM player_match_stats
                        WHERE
                            player_match_stats.match_id =
                                matches.match_id
                    ),
                    0
                ) AS stat_goals

            FROM matches

            INNER JOIN teams AS home_teams
                ON home_teams.team_id =
                    matches.home_team_id

            INNER JOIN teams AS away_teams
                ON away_teams.team_id =
                    matches.away_team_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL

            ORDER BY matches.match_id;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        for (
            match_id,
            home_name,
            away_name,
            home_goals,
            away_goals,
            event_goals,
            stat_goals,
        ) in rows:
            match_goals = int(home_goals) + int(away_goals)

            if int(event_goals) < match_goals:
                missing_goals = (
                    match_goals - int(event_goals)
                )

                warnings.append(
                    f"Spiel {match_id}: {home_name} - "
                    f"{away_name}; Liveticker unvollständig: "
                    f"Ergebnis enthält {match_goals} Tore, "
                    f"Events enthalten {event_goals}. "
                    f"Es fehlen {missing_goals} Tor-Events."
                )

            elif int(event_goals) > match_goals:
                errors.append(
                    f"Spiel {match_id}: {home_name} - "
                    f"{away_name}; Events enthalten mehr Tore "
                    f"als das offizielle Ergebnis: "
                    f"Ergebnis={match_goals}, "
                    f"Events={event_goals}."
                )

            if int(stat_goals) != int(event_goals):
                warnings.append(
                    f"Spiel {match_id}: Events enthalten "
                    f"{event_goals} Tore, "
                    f"player_match_stats enthalten "
                    f"{stat_goals}."
                )

        if not rows:
            warnings.append(
                "Keine abgeschlossenen Spiele mit "
                "Ergebnis gefunden."
            )

        return ValidationCheck(
            name="Tore und Endergebnisse",
            passed=not errors,
            warnings=warnings,
            errors=errors,
        )

    def _check_lineups(
        self,
        competition_id: int | None,
    ) -> ValidationCheck:
        errors: list[str] = []
        warnings: list[str] = []

        rows = self._fetch_all(
            """
            SELECT
                player_match_stats.match_id,
                player_match_stats.team_id,
                teams.name,
                SUM(player_match_stats.is_starting)
                    AS starters,
                SUM(
                    player_match_stats.was_substituted_in
                ) AS substitutions_in,
                SUM(
                    player_match_stats.was_substituted_out
                ) AS substitutions_out,
                COUNT(*) AS squad_size

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            INNER JOIN teams
                ON teams.team_id =
                    player_match_stats.team_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1

            GROUP BY
                player_match_stats.match_id,
                player_match_stats.team_id,
                teams.name

            ORDER BY
                player_match_stats.match_id,
                player_match_stats.team_id;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        for (
            match_id,
            team_id,
            team_name,
            starters,
            substitutions_in,
            substitutions_out,
            squad_size,
        ) in rows:
            del team_id

            starters = int(starters or 0)
            substitutions_in = int(
                substitutions_in or 0
            )
            substitutions_out = int(
                substitutions_out or 0
            )
            squad_size = int(squad_size or 0)

            if starters != 11:
                errors.append(
                    f"Spiel {match_id}, {team_name}: "
                    f"{starters} Startspieler statt 11."
                )

            if substitutions_in != substitutions_out:
                warnings.append(
                    f"Spiel {match_id}, {team_name}: "
                    f"{substitutions_in} Einwechslungen, "
                    f"{substitutions_out} Auswechslungen."
                )

            if squad_size < starters:
                errors.append(
                    f"Spiel {match_id}, {team_name}: "
                    "Kadergröße kleiner als Startelf."
                )

            if squad_size > 30:
                warnings.append(
                    f"Spiel {match_id}, {team_name}: "
                    f"ungewöhnlich großer Kader "
                    f"mit {squad_size} Spielern."
                )

        if not rows:
            warnings.append(
                "Keine Aufstellungs- oder "
                "Spielerstatistikdaten gefunden."
            )

        return ValidationCheck(
            name="Aufstellungen und Wechsel",
            passed=not errors,
            warnings=warnings,
            errors=errors,
        )

    def _check_minutes(
        self,
        competition_id: int | None,
    ) -> ValidationCheck:
        errors: list[str] = []
        warnings: list[str] = []

        invalid_rows = self._fetch_all(
            """
            SELECT
                player_match_stats.player_match_stat_id,
                player_match_stats.match_id,
                player_match_stats.player_id,
                players.first_name,
                players.last_name,
                player_match_stats.minute_in,
                player_match_stats.minute_out,
                player_match_stats.minutes_played

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            INNER JOIN players
                ON players.player_id =
                    player_match_stats.player_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1
                AND (
                    player_match_stats.minutes_played < 0
                    OR player_match_stats.minutes_played > 120
                    OR (
                        player_match_stats.minute_in IS NOT NULL
                        AND player_match_stats.minute_in < 0
                    )
                    OR (
                        player_match_stats.minute_out IS NOT NULL
                        AND player_match_stats.minute_out < 0
                    )
                    OR (
                        player_match_stats.minute_in IS NOT NULL
                        AND player_match_stats.minute_out IS NOT NULL
                        AND player_match_stats.minute_out
                            < player_match_stats.minute_in
                    )
                )

            ORDER BY
                player_match_stats.match_id,
                player_match_stats.player_id;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        for row in invalid_rows:
            (
                stat_id,
                match_id,
                player_id,
                first_name,
                last_name,
                minute_in,
                minute_out,
                minutes_played,
            ) = row

            player_name = (
                f"{first_name or ''} "
                f"{last_name or ''}"
            ).strip()

            errors.append(
                f"Statistik {stat_id}, Spiel {match_id}, "
                f"Spieler {player_name or player_id}: "
                f"minute_in={minute_in}, "
                f"minute_out={minute_out}, "
                f"minutes_played={minutes_played}."
            )

        team_minutes = self._fetch_all(
            """
            SELECT
                player_match_stats.match_id,
                teams.name,
                SUM(player_match_stats.minutes_played)
                    AS total_minutes

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            INNER JOIN teams
                ON teams.team_id =
                    player_match_stats.team_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1

            GROUP BY
                player_match_stats.match_id,
                player_match_stats.team_id,
                teams.name

            HAVING
                SUM(player_match_stats.is_starting) = 11
                AND SUM(
                    player_match_stats.minutes_played
                ) != 990

            ORDER BY
                player_match_stats.match_id,
                player_match_stats.team_id;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        for (
            match_id,
            team_name,
            total_minutes,
        ) in team_minutes:
            warnings.append(
                f"Spiel {match_id}, {team_name}: "
                f"{total_minutes} Mannschaftsminuten "
                "statt 990."
            )

        return ValidationCheck(
            name="Einsatzminuten",
            passed=not errors,
            warnings=warnings,
            errors=errors,
        )

    def _check_cards(
        self,
        competition_id: int | None,
    ) -> ValidationCheck:
        errors: list[str] = []
        warnings: list[str] = []

        event_counts = self._load_card_event_counts(
            competition_id
        )
        stat_counts = self._load_card_stat_counts(
            competition_id
        )

        stat_key_by_code = {
            "YELLOW_CARD": "yellow_cards",
            "YELLOW_RED_CARD": "yellow_red_cards",
            "RED_CARD": "red_cards",
        }

        for code in self.CARD_EVENT_CODES:
            event_count = event_counts.get(
                code,
                0,
            )

            stat_count = stat_counts.get(
                stat_key_by_code[code],
                0,
            )

            if event_count != stat_count:
                warnings.append(
                    f"{code}: Events={event_count}, "
                    f"player_match_stats={stat_count}."
                )

        card_events_without_player = self._fetch_all(
            """
            SELECT
                event_types.code,
                COUNT(*)

            FROM events

            INNER JOIN event_types
                ON event_types.event_type_id =
                    events.event_type_id

            INNER JOIN matches
                ON matches.match_id =
                    events.match_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1
                AND event_types.code IN (
                    'YELLOW_CARD',
                    'YELLOW_RED_CARD',
                    'RED_CARD'
                )
                AND events.player_id IS NULL

            GROUP BY event_types.code

            ORDER BY event_types.code;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        for code, count in card_events_without_player:
            warnings.append(
                f"{count} {code}-Events besitzen "
                "keine Spielerzuordnung."
            )

        return ValidationCheck(
            name="Karten",
            passed=not errors,
            warnings=warnings,
            errors=errors,
        )

    def _load_card_event_counts(
        self,
        competition_id: int | None,
    ) -> dict[str, int]:
        rows = self._fetch_all(
            """
            SELECT
                event_types.code,
                COUNT(*)

            FROM events

            INNER JOIN event_types
                ON event_types.event_type_id =
                    events.event_type_id

            INNER JOIN matches
                ON matches.match_id =
                    events.match_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1
                AND event_types.code IN (
                    'YELLOW_CARD',
                    'YELLOW_RED_CARD',
                    'RED_CARD'
                )

            GROUP BY event_types.code;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        return {
            str(code): int(count)
            for code, count in rows
        }

    def _load_card_stat_counts(
        self,
        competition_id: int | None,
    ) -> dict[str, int]:
        row = self._fetch_one(
            """
            SELECT
                COALESCE(
                    SUM(
                        player_match_stats.yellow_cards
                    ),
                    0
                ),
                COALESCE(
                    SUM(
                        player_match_stats.yellow_red_cards
                    ),
                    0
                ),
                COALESCE(
                    SUM(
                        player_match_stats.red_cards
                    ),
                    0
                )

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            WHERE
                (? IS NULL OR matches.competition_id = ?)
                AND matches.detail_imported = 1;
            """,
            (
                competition_id,
                competition_id,
            ),
        )

        if row is None:
            return {
                "yellow_cards": 0,
                "yellow_red_cards": 0,
                "red_cards": 0,
            }

        return {
            "yellow_cards": int(row[0] or 0),
            "yellow_red_cards": int(row[1] or 0),
            "red_cards": int(row[2] or 0),
        }

    def _fetch_value(
        self,
        query: str,
        parameters: tuple = (),
    ) -> int:
        self.cursor.execute(
            query,
            parameters,
        )

        row = self.cursor.fetchone()

        if row is None:
            return 0

        return int(
            row[0] or 0
        )

    def _fetch_one(
        self,
        query: str,
        parameters: tuple = (),
    ) -> sqlite3.Row | tuple | None:
        self.cursor.execute(
            query,
            parameters,
        )

        return self.cursor.fetchone()

    def _fetch_all(
        self,
        query: str,
        parameters: tuple = (),
    ) -> list[sqlite3.Row | tuple]:
        self.cursor.execute(
            query,
            parameters,
        )

        return self.cursor.fetchall()