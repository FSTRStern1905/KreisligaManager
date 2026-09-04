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

        if "results" in selected_sections:
            sections[
                "results"
            ] = self._build_results_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "goals" in selected_sections:
            sections[
                "goals"
            ] = self._build_goals_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "match_flow" in selected_sections:
            sections[
                "match_flow"
            ] = self._build_match_flow_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "players" in selected_sections:
            sections[
                "players"
            ] = self._build_players_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "records" in selected_sections:
            sections[
                "records"
            ] = self._build_records_section(
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

    def _build_results_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        matches = self._get_team_matches(
            competition_id=competition_id,
            team_id=team_id,
        )

        if not matches:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "abgeschlossenen Spiele vorhanden."
                )
            }

        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0
        result_rows: list[list[Any]] = []

        for match in matches:
            (
                _match_id,
                matchday,
                match_date,
                home_team_id,
                _away_team_id,
                home_team_name,
                away_team_name,
                home_goals,
                away_goals,
            ) = match

            is_home = int(home_team_id) == team_id
            team_goals = int(home_goals if is_home else away_goals)
            opponent_goals = int(away_goals if is_home else home_goals)

            goals_for += team_goals
            goals_against += opponent_goals

            if team_goals > opponent_goals:
                result_code = "S"
                wins += 1
            elif team_goals < opponent_goals:
                result_code = "N"
                losses += 1
            else:
                result_code = "U"
                draws += 1

            result_rows.append(
                [
                    matchday if matchday is not None else "-",
                    match_date if match_date else "-",
                    f"{home_team_name} - {away_team_name}",
                    f"{home_goals}:{away_goals}",
                    result_code,
                ]
            )

        played = len(matches)

        return {
            "keyfacts": [
                f"{wins} Siege",
                f"{draws} Remis",
                f"{losses} Niederlagen",
                f"Torbilanz: {goals_for}:{goals_against}",
            ],
            "facts": {
                "Spiele": played,
                "Siege": wins,
                "Remis": draws,
                "Niederlagen": losses,
                "Siegquote %": round(wins / played * 100, 1) if played else 0.0,
                "Tore": goals_for,
                "Gegentore": goals_against,
                "Tordifferenz": self._format_signed(goals_for - goals_against),
            },
            "tables": [
                {
                    "title": "Letzte 10 Spiele",
                    "headers": ["ST", "Datum", "Spiel", "Ergebnis", "W/U/N"],
                    "rows": result_rows[-10:],
                }
            ],
        }

    def _build_goals_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        intervals = [
            (0, 15, "0–15"),
            (16, 30, "16–30"),
            (31, 45, "31–45"),
            (46, 60, "46–60"),
            (61, 75, "61–75"),
            (76, 90, "76–90"),
        ]

        phase_rows: list[list[Any]] = []
        total_for = 0
        total_against = 0

        for start_minute, end_minute, label in intervals:
            goals_for = self._count_goal_events(
                competition_id=competition_id,
                team_id=team_id,
                start_minute=start_minute,
                end_minute=end_minute,
                for_team=True,
            )
            goals_against = self._count_goal_events(
                competition_id=competition_id,
                team_id=team_id,
                start_minute=start_minute,
                end_minute=end_minute,
                for_team=False,
            )

            total_for += goals_for
            total_against += goals_against
            phase_rows.append(
                [
                    label,
                    goals_for,
                    goals_against,
                    self._format_signed(goals_for - goals_against),
                ]
            )

        first_half_for = sum(int(row[1]) for row in phase_rows[:3])
        first_half_against = sum(int(row[2]) for row in phase_rows[:3])
        second_half_for = total_for - first_half_for
        second_half_against = total_against - first_half_against
        strongest_phase = max(phase_rows, key=lambda row: int(row[1]), default=None)

        return {
            "keyfacts": [
                f"{total_for} Tore",
                f"{total_against} Gegentore",
                f"Tordifferenz: {self._format_signed(total_for - total_against)}",
                (
                    f"Stärkste Torphase: {strongest_phase[0]}"
                    if strongest_phase
                    else "Stärkste Torphase: -"
                ),
            ],
            "facts": {
                "Tore 1. HZ": first_half_for,
                "Gegentore 1. HZ": first_half_against,
                "Tore 2. HZ": second_half_for,
                "Gegentore 2. HZ": second_half_against,
                "Frühe Tore 0–15": phase_rows[0][1],
                "Späte Tore 76–90": phase_rows[-1][1],
                "Frühe Gegentore 0–15": phase_rows[0][2],
                "Späte Gegentore 76–90": phase_rows[-1][2],
            },
            "tables": [
                {
                    "title": "Torphasen",
                    "headers": ["Minute", "Tore", "Gegentore", "Bilanz"],
                    "rows": phase_rows,
                }
            ],
        }

    def _build_match_flow_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        matches = self._get_team_matches(
            competition_id=competition_id,
            team_id=team_id,
        )

        took_lead = 0
        conceded_first = 0
        wins_after_lead = 0
        draws_after_lead = 0
        losses_after_lead = 0
        wins_after_conceding = 0
        draws_after_conceding = 0
        losses_after_conceding = 0
        goalless_matches = 0

        for match in matches:
            (
                match_id,
                _matchday,
                _match_date,
                home_team_id,
                _away_team_id,
                _home_team_name,
                _away_team_name,
                home_goals,
                away_goals,
            ) = match

            opening_team_id = self._get_opening_goal_team(int(match_id))
            is_home = int(home_team_id) == team_id
            team_goals = int(home_goals if is_home else away_goals)
            opponent_goals = int(away_goals if is_home else home_goals)

            if opening_team_id is None:
                goalless_matches += 1
                continue

            if int(opening_team_id) == team_id:
                took_lead += 1
                if team_goals > opponent_goals:
                    wins_after_lead += 1
                elif team_goals < opponent_goals:
                    losses_after_lead += 1
                else:
                    draws_after_lead += 1
            else:
                conceded_first += 1
                if team_goals > opponent_goals:
                    wins_after_conceding += 1
                elif team_goals < opponent_goals:
                    losses_after_conceding += 1
                else:
                    draws_after_conceding += 1

        return {
            "keyfacts": [
                f"{took_lead}× erstes Tor erzielt",
                f"{conceded_first}× erstes Tor kassiert",
                f"Siege nach Führung: {wins_after_lead}",
                f"Comeback-Siege: {wins_after_conceding}",
            ],
            "blocks": [
                {
                    "title": "Nach eigener Führung",
                    "facts": {
                        "Führungen": took_lead,
                        "Siege": wins_after_lead,
                        "Remis": draws_after_lead,
                        "Niederlagen": losses_after_lead,
                        "Führung gehalten %": round(
                            wins_after_lead / took_lead * 100,
                            1,
                        ) if took_lead else 0.0,
                    },
                },
                {
                    "title": "Nach erstem Gegentor",
                    "facts": {
                        "Rückstände": conceded_first,
                        "Siege": wins_after_conceding,
                        "Remis": draws_after_conceding,
                        "Niederlagen": losses_after_conceding,
                        "Punkte gerettet %": round(
                            (wins_after_conceding + draws_after_conceding)
                            / conceded_first
                            * 100,
                            1,
                        ) if conceded_first else 0.0,
                    },
                },
            ],
            "facts": {
                "Spiele ohne Tor": goalless_matches,
            },
        }

    def _build_players_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        self.cursor.execute(
            """
            SELECT
                players.first_name,
                players.last_name,
                COALESCE(NULLIF(player_match_stats.position, ''), players.position, '') AS position,
                SUM(
                    CASE
                        WHEN player_match_stats.is_starting = 1
                          OR player_match_stats.was_substituted_in = 1
                          OR player_match_stats.minutes_played > 0
                        THEN 1 ELSE 0
                    END
                ) AS appearances,
                SUM(player_match_stats.is_starting) AS starts,
                SUM(player_match_stats.minutes_played) AS minutes_played,
                SUM(player_match_stats.goals) AS goals,
                SUM(player_match_stats.assists) AS assists,
                SUM(player_match_stats.yellow_cards) AS yellow_cards,
                SUM(player_match_stats.yellow_red_cards) AS yellow_red_cards,
                SUM(player_match_stats.red_cards) AS red_cards
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id = player_match_stats.match_id
            INNER JOIN players
                ON players.player_id = player_match_stats.player_id
            WHERE
                matches.competition_id = ?
                AND player_match_stats.team_id = ?
            GROUP BY
                player_match_stats.player_id,
                players.first_name,
                players.last_name,
                COALESCE(
                    NULLIF(
                        player_match_stats.position,
                        ''
                    ),
                    players.position,
                    ''
                )
            ORDER BY
                goals DESC,
                assists DESC,
                minutes_played DESC,
                appearances DESC,
                players.last_name,
                players.first_name;
            """,
            (competition_id, team_id),
        )

        rows = self.cursor.fetchall()

        if not rows:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "Spielerstatistiken vorhanden."
                )
            }

        player_rows: list[list[Any]] = []

        for row in rows:
            first_name = str(row[0] or "").strip()
            last_name = str(row[1] or "").strip()
            player_name = f"{first_name} {last_name}".strip()

            player_rows.append(
                [
                    player_name,
                    str(row[2] or "-"),
                    int(row[3] or 0),
                    int(row[4] or 0),
                    int(row[5] or 0),
                    int(row[6] or 0),
                    int(row[7] or 0),
                    int(row[8] or 0),
                    int(row[9] or 0),
                    int(row[10] or 0),
                ]
            )

        top_scorer = max(player_rows, key=lambda row: (int(row[5]), int(row[6])))
        most_minutes = max(player_rows, key=lambda row: int(row[4]))

        return {
            "keyfacts": [
                f"Top-Torschütze: {top_scorer[0]} ({top_scorer[5]} Tore)",
                f"Meiste Minuten: {most_minutes[0]} ({most_minutes[4]})",
                f"{len(player_rows)} Spieler mit Statistikdaten",
            ],
            "tables": [
                {
                    "title": "Spielerübersicht",
                    "headers": [
                        "Spieler", "Pos.", "Eins.", "Start", "Min.",
                        "Tore", "Assists", "Gelb", "G-R", "Rot",
                    ],
                    "rows": player_rows[:25],
                }
            ],
        }

    def _build_records_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        matches = self._get_team_matches(
            competition_id=competition_id,
            team_id=team_id,
        )

        if not matches:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "Rekorddaten vorhanden."
                )
            }

        best_win = None
        worst_loss = None
        highest_scoring = None
        clean_sheets = 0
        scoreless = 0

        for match in matches:
            (
                _match_id,
                matchday,
                match_date,
                home_team_id,
                _away_team_id,
                home_team_name,
                away_team_name,
                home_goals,
                away_goals,
            ) = match

            is_home = int(home_team_id) == team_id
            goals_for = int(home_goals if is_home else away_goals)
            goals_against = int(away_goals if is_home else home_goals)
            difference = goals_for - goals_against
            total_goals = goals_for + goals_against

            record = (
                difference,
                total_goals,
                matchday,
                match_date,
                home_team_name,
                away_team_name,
                home_goals,
                away_goals,
            )

            if goals_against == 0:
                clean_sheets += 1
            if goals_for == 0:
                scoreless += 1

            if difference > 0 and (best_win is None or difference > best_win[0]):
                best_win = record
            if difference < 0 and (worst_loss is None or difference < worst_loss[0]):
                worst_loss = record
            if highest_scoring is None or total_goals > highest_scoring[1]:
                highest_scoring = record

        record_rows: list[list[Any]] = []

        if best_win is not None:
            record_rows.append(self._record_to_row("Höchster Sieg", best_win))
        if worst_loss is not None:
            record_rows.append(self._record_to_row("Höchste Niederlage", worst_loss))
        if highest_scoring is not None:
            record_rows.append(self._record_to_row("Torreichstes Spiel", highest_scoring))

        return {
            "keyfacts": [
                f"Zu Null: {clean_sheets}",
                f"Ohne eigenes Tor: {scoreless}",
            ],
            "facts": {
                "Zu-Null-Spiele": clean_sheets,
                "Spiele ohne eigenes Tor": scoreless,
            },
            "tables": [
                {
                    "title": "Team-Rekorde",
                    "headers": ["Rekord", "ST", "Datum", "Spiel", "Ergebnis", "Wert"],
                    "rows": record_rows,
                }
            ],
        }

    def _get_team_matches(
        self,
        competition_id: int,
        team_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                matches.match_id,
                matches.matchday,
                matches.match_date,
                matches.home_team_id,
                matches.away_team_id,
                home_teams.name,
                away_teams.name,
                matches.home_goals,
                matches.away_goals
            FROM matches
            INNER JOIN teams AS home_teams
                ON home_teams.team_id = matches.home_team_id
            INNER JOIN teams AS away_teams
                ON away_teams.team_id = matches.away_team_id
            WHERE
                matches.competition_id = ?
                AND matches.status = 'finished'
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL
                AND (
                    matches.home_team_id = ?
                    OR matches.away_team_id = ?
                )
            ORDER BY
                matches.matchday,
                matches.match_date,
                matches.match_id;
            """,
            (competition_id, team_id, team_id),
        )

        return list(self.cursor.fetchall())

    def _count_goal_events(
        self,
        competition_id: int,
        team_id: int,
        start_minute: int,
        end_minute: int,
        for_team: bool,
    ) -> int:
        operator = "=" if for_team else "!="

        self.cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id = events.event_type_id
            INNER JOIN matches
                ON matches.match_id = events.match_id
            WHERE
                matches.competition_id = ?
                AND matches.status = 'finished'
                AND event_types.code IN ('GOAL', 'PENALTY_GOAL', 'OWN_GOAL')
                AND events.team_id {operator} ?
                AND events.team_id IS NOT NULL
                AND (
                    matches.home_team_id = ?
                    OR matches.away_team_id = ?
                )
                AND CAST(
                    CASE
                        WHEN instr(CAST(events.minute AS TEXT), '+') > 0
                        THEN substr(
                            CAST(events.minute AS TEXT),
                            1,
                            instr(CAST(events.minute AS TEXT), '+') - 1
                        )
                        ELSE CAST(events.minute AS TEXT)
                    END
                    AS INTEGER
                ) BETWEEN ? AND ?;
            """,
            (
                competition_id,
                team_id,
                team_id,
                team_id,
                start_minute,
                end_minute,
            ),
        )

        row = self.cursor.fetchone()
        return int(row[0] or 0)

    def _get_opening_goal_team(
        self,
        match_id: int,
    ) -> int | None:
        self.cursor.execute(
            """
            SELECT events.team_id
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id = events.event_type_id
            WHERE
                events.match_id = ?
                AND event_types.code IN ('GOAL', 'PENALTY_GOAL', 'OWN_GOAL')
                AND events.team_id IS NOT NULL
            ORDER BY
                CAST(
                    CASE
                        WHEN instr(CAST(events.minute AS TEXT), '+') > 0
                        THEN substr(
                            CAST(events.minute AS TEXT),
                            1,
                            instr(CAST(events.minute AS TEXT), '+') - 1
                        )
                        ELSE CAST(events.minute AS TEXT)
                    END
                    AS INTEGER
                ),
                events.event_id
            LIMIT 1;
            """,
            (match_id,),
        )

        row = self.cursor.fetchone()
        return int(row[0]) if row is not None else None

    @staticmethod
    def _record_to_row(
        label: str,
        record: tuple,
    ) -> list[Any]:
        (
            difference,
            total_goals,
            matchday,
            match_date,
            home_team_name,
            away_team_name,
            home_goals,
            away_goals,
        ) = record

        value = total_goals if label == "Torreichstes Spiel" else difference

        return [
            label,
            matchday if matchday is not None else "-",
            match_date if match_date else "-",
            f"{home_team_name} - {away_team_name}",
            f"{home_goals}:{away_goals}",
            (
                int(value)
                if label == "Torreichstes Spiel"
                else TeamStatisticsPdfService._format_signed(int(value))
            ),
        ]

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
