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
from src.services.statistics.streak_service import (
    StreakService,
)
from src.services.statistics.lead_comeback_service import (
    LeadComebackService,
)
from src.services.statistics.half_goal_service import (
    HalfGoalService,
)
from src.services.statistics.halftime_result_service import (
    HalftimeResultService,
)
from src.services.statistics.table_progress_service import (
    TableProgressService,
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

        self.table_progress_service = (
            TableProgressService(
                connection
            )
        )

        self.streak_service = StreakService(
            connection
        )

        self.lead_comeback_service = (
            LeadComebackService(
                connection
            )
        )

        self.half_goal_service = HalfGoalService(
            connection
        )

        self.halftime_result_service = (
            HalftimeResultService(
                connection
            )
        )

    def build_report_data(
        self,
        competition_id: int,
        team_id: int,
        selected_sections: list[str],
        report_type: str = "short",
    ) -> dict[str, Any]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        if report_type not in {
            "short",
            "full",
        }:
            raise ValueError(
                "Ungültiger Berichtstyp."
            )

        is_full_report = (
            report_type == "full"
        )

        if is_full_report:
            selected_sections = [
                "overview",
                "table_form",
                "results",
                "goals",
                "match_flow",
                "patterns",
                "control",
                "halftime_phases",
                "consistency",
                "attack_defense",
                "strengths_weaknesses",
                "season_progress",
                "players",
                "discipline",
                "streaks",
                "records",
            ]

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
                include_all=is_full_report,
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

        if "patterns" in selected_sections:
            sections[
                "patterns"
            ] = self._build_patterns_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "control" in selected_sections:
            sections[
                "control"
            ] = self._build_control_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "halftime_phases" in selected_sections:
            sections[
                "halftime_phases"
            ] = self._build_halftime_phases_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "consistency" in selected_sections:
            sections[
                "consistency"
            ] = self._build_consistency_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "attack_defense" in selected_sections:
            sections["attack_defense"] = self._build_attack_defense_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "strengths_weaknesses" in selected_sections:
            sections[
                "strengths_weaknesses"
            ] = self._build_strengths_weaknesses_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "players" in selected_sections:
            sections[
                "players"
            ] = self._build_players_section(
                competition_id=competition_id,
                team_id=team_id,
                include_all=is_full_report,
            )

        if "season_progress" in selected_sections:
            sections[
                "season_progress"
            ] = self._build_season_progress_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "discipline" in selected_sections:
            sections[
                "discipline"
            ] = self._build_discipline_section(
                competition_id=competition_id,
                team_id=team_id,
            )

        if "streaks" in selected_sections:
            sections[
                "streaks"
            ] = self._build_streaks_section(
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
            "report_type": report_type,
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
        include_all: bool = False,
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
                    "title": (
                        "Alle Spiele"
                        if include_all
                        else "Letzte 10 Spiele"
                    ),
                    "headers": ["ST", "Datum", "Spiel", "Ergebnis", "W/U/N"],
                    "rows": (
                        result_rows
                        if include_all
                        else result_rows[-10:]
                    ),
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

    def _build_patterns_section(
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
                    "Spielmuster-Daten vorhanden."
                )
            }

        played = len(
            matches
        )

        clean_sheets = 0
        scoreless = 0
        both_scored = 0

        over_15 = 0
        over_25 = 0
        over_35 = 0

        one_goal_wins = 0
        multi_goal_wins = 0
        one_goal_losses = 0
        multi_goal_losses = 0
        draws = 0

        scored_first = 0
        conceded_first = 0
        no_opening_goal = 0

        scorelines: dict[
            str,
            int,
        ] = {}

        total_goals_in_matches = 0

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

            is_home = (
                int(
                    home_team_id
                )
                == team_id
            )

            goals_for = int(
                home_goals
                if is_home
                else away_goals
            )
            goals_against = int(
                away_goals
                if is_home
                else home_goals
            )

            total_goals = (
                goals_for
                + goals_against
            )

            total_goals_in_matches += (
                total_goals
            )

            if goals_against == 0:
                clean_sheets += 1

            if goals_for == 0:
                scoreless += 1

            if (
                goals_for > 0
                and goals_against > 0
            ):
                both_scored += 1

            if total_goals >= 2:
                over_15 += 1

            if total_goals >= 3:
                over_25 += 1

            if total_goals >= 4:
                over_35 += 1

            difference = (
                goals_for
                - goals_against
            )

            if difference > 0:
                if difference == 1:
                    one_goal_wins += 1
                else:
                    multi_goal_wins += 1

            elif difference < 0:
                if difference == -1:
                    one_goal_losses += 1
                else:
                    multi_goal_losses += 1

            else:
                draws += 1

            scoreline = (
                f"{goals_for}:{goals_against}"
            )

            scorelines[
                scoreline
            ] = (
                scorelines.get(
                    scoreline,
                    0,
                )
                + 1
            )

            opening_team_id = (
                self._get_opening_goal_team(
                    int(
                        match_id
                    )
                )
            )

            if opening_team_id is None:
                no_opening_goal += 1
            elif int(
                opening_team_id
            ) == team_id:
                scored_first += 1
            else:
                conceded_first += 1

        def percentage(
            value: int,
        ) -> float:
            return round(
                (
                    value
                    / played
                    * 100
                )
                if played
                else 0.0,
                1,
            )

        common_scorelines = sorted(
            scorelines.items(),
            key=lambda item: (
                -item[
                    1
                ],
                item[
                    0
                ],
            ),
        )[:5]

        scoreline_rows = [
            [
                scoreline,
                count,
                percentage(
                    count
                ),
            ]
            for scoreline, count
            in common_scorelines
        ]

        return {
            "keyfacts": [
                (
                    f"{clean_sheets} Zu-Null-Spiele"
                ),
                (
                    f"{both_scored}× beide Teams getroffen"
                ),
                (
                    f"{scored_first}× erstes Tor erzielt"
                ),
                (
                    f"{over_25}× mindestens 3 Tore im Spiel"
                ),
            ],
            "facts": {
                "Spiele":
                    played,
                "Zu Null":
                    clean_sheets,
                "Zu Null %":
                    percentage(
                        clean_sheets
                    ),
                "Ohne eigenes Tor":
                    scoreless,
                "Ohne eigenes Tor %":
                    percentage(
                        scoreless
                    ),
                "Beide treffen":
                    both_scored,
                "Beide treffen %":
                    percentage(
                        both_scored
                    ),
                "Over 1,5":
                    over_15,
                "Over 1,5 %":
                    percentage(
                        over_15
                    ),
                "Over 2,5":
                    over_25,
                "Over 2,5 %":
                    percentage(
                        over_25
                    ),
                "Over 3,5":
                    over_35,
                "Over 3,5 %":
                    percentage(
                        over_35
                    ),
                "Erstes Tor erzielt":
                    scored_first,
                "Erstes Tor erzielt %":
                    percentage(
                        scored_first
                    ),
                "Erstes Tor kassiert":
                    conceded_first,
                "Erstes Tor kassiert %":
                    percentage(
                        conceded_first
                    ),
                "Ohne Toreröffnung":
                    no_opening_goal,
                "Ø Gesamttore / Spiel":
                    round(
                        total_goals_in_matches
                        / played,
                        2,
                    )
                    if played
                    else 0.0,
            },
            "blocks": [
                {
                    "title":
                        "Ergebnismargen",
                    "facts": {
                        "Siege mit 1 Tor":
                            one_goal_wins,
                        "Siege mit 2+ Toren":
                            multi_goal_wins,
                        "Remis":
                            draws,
                        "Niederlagen mit 1 Tor":
                            one_goal_losses,
                        "Niederlagen mit 2+ Toren":
                            multi_goal_losses,
                    },
                },
                {
                    "title":
                        "Toreröffnung",
                    "facts": {
                        "Selbst eröffnet":
                            scored_first,
                        "Gegner eröffnet":
                            conceded_first,
                        "Kein Tor":
                            no_opening_goal,
                    },
                },
            ],
            "charts": {
                "goal_thresholds": [
                    {
                        "label":
                            "Over 1,5",
                        "count":
                            over_15,
                        "percentage":
                            percentage(
                                over_15
                            ),
                    },
                    {
                        "label":
                            "Over 2,5",
                        "count":
                            over_25,
                        "percentage":
                            percentage(
                                over_25
                            ),
                    },
                    {
                        "label":
                            "Over 3,5",
                        "count":
                            over_35,
                        "percentage":
                            percentage(
                                over_35
                            ),
                    },
                    {
                        "label":
                            "Beide treffen",
                        "count":
                            both_scored,
                        "percentage":
                            percentage(
                                both_scored
                            ),
                    },
                ],
                "result_margins": [
                    {
                        "label":
                            "Sieg +1",
                        "count":
                            one_goal_wins,
                    },
                    {
                        "label":
                            "Sieg +2 oder mehr",
                        "count":
                            multi_goal_wins,
                    },
                    {
                        "label":
                            "Remis",
                        "count":
                            draws,
                    },
                    {
                        "label":
                            "Niederlage -1",
                        "count":
                            one_goal_losses,
                    },
                    {
                        "label":
                            "Niederlage -2 oder mehr",
                        "count":
                            multi_goal_losses,
                    },
                ],
            },
            "tables": [
                {
                    "title":
                        "Häufigste Ergebnisse",
                    "headers": [
                        "Ergebnis",
                        "Anzahl",
                        "Anteil %",
                    ],
                    "rows":
                        scoreline_rows,
                }
            ],
        }

    def _build_control_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        statistics = (
            self.lead_comeback_service
            .get_statistics(
                competition_id
            )
        )

        team_row = self._find_team_row(
            statistics,
            team_id,
        )

        if team_row is None:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "Daten zu Führung und Rückstand vorhanden."
                )
            }

        matches_leading = int(
            team_row.get(
                "matches_leading",
                0,
            )
            or 0
        )
        wins_after_leading = int(
            team_row.get(
                "wins_after_leading",
                0,
            )
            or 0
        )
        draws_after_leading = int(
            team_row.get(
                "draws_after_leading",
                0,
            )
            or 0
        )
        losses_after_leading = int(
            team_row.get(
                "losses_after_leading",
                0,
            )
            or 0
        )

        matches_trailing = int(
            team_row.get(
                "matches_trailing",
                0,
            )
            or 0
        )
        wins_after_trailing = int(
            team_row.get(
                "wins_after_trailing",
                0,
            )
            or 0
        )
        draws_after_trailing = int(
            team_row.get(
                "draws_after_trailing",
                0,
            )
            or 0
        )
        losses_after_trailing = int(
            team_row.get(
                "losses_after_trailing",
                0,
            )
            or 0
        )

        points_after_trailing = int(
            team_row.get(
                "points_after_trailing",
                0,
            )
            or 0
        )
        dropped_points = int(
            team_row.get(
                "dropped_points_after_leading",
                0,
            )
            or 0
        )

        lead_win_percentage = float(
            team_row.get(
                "lead_win_percentage",
                0.0,
            )
            or 0.0
        )
        comeback_percentage = float(
            team_row.get(
                "comeback_percentage",
                0.0,
            )
            or 0.0
        )

        potential_points_from_leads = (
            matches_leading
            * 3
        )
        secured_points_from_leads = (
            wins_after_leading
            * 3
            + draws_after_leading
        )

        lead_conversion_percentage = (
            round(
                secured_points_from_leads
                / potential_points_from_leads
                * 100,
                1,
            )
            if potential_points_from_leads
            else 0.0
        )

        recovered_matches = (
            wins_after_trailing
            + draws_after_trailing
        )

        return {
            "keyfacts": [
                (
                    f"{matches_leading}× in Führung"
                ),
                (
                    f"{dropped_points} Punkte "
                    "nach Führung liegen gelassen"
                ),
                (
                    f"{matches_trailing}× in Rückstand"
                ),
                (
                    f"{points_after_trailing} Punkte "
                    "nach Rückstand geholt"
                ),
            ],
            "facts": {
                "Führungen":
                    matches_leading,
                "Siege nach Führung":
                    wins_after_leading,
                "Remis nach Führung":
                    draws_after_leading,
                "Niederlagen nach Führung":
                    losses_after_leading,
                "Führungen gewonnen %":
                    round(
                        lead_win_percentage,
                        1,
                    ),
                "Punktepotenzial aus Führungen":
                    potential_points_from_leads,
                "Punkte aus Führungen":
                    secured_points_from_leads,
                "Punkte nach Führung verloren":
                    dropped_points,
                "Punktausbeute aus Führungen %":
                    lead_conversion_percentage,
                "Rückstände":
                    matches_trailing,
                "Siege nach Rückstand":
                    wins_after_trailing,
                "Remis nach Rückstand":
                    draws_after_trailing,
                "Niederlagen nach Rückstand":
                    losses_after_trailing,
                "Gerettete Spiele":
                    recovered_matches,
                "Comeback-Quote %":
                    round(
                        comeback_percentage,
                        1,
                    ),
                "Punkte nach Rückstand":
                    points_after_trailing,
            },
            "charts": {
                "lead_outcomes": [
                    {
                        "label":
                            "Sieg",
                        "count":
                            wins_after_leading,
                    },
                    {
                        "label":
                            "Remis",
                        "count":
                            draws_after_leading,
                    },
                    {
                        "label":
                            "Niederlage",
                        "count":
                            losses_after_leading,
                    },
                ],
                "trailing_outcomes": [
                    {
                        "label":
                            "Sieg",
                        "count":
                            wins_after_trailing,
                    },
                    {
                        "label":
                            "Remis",
                        "count":
                            draws_after_trailing,
                    },
                    {
                        "label":
                            "Niederlage",
                        "count":
                            losses_after_trailing,
                    },
                ],
                "points_balance": [
                    {
                        "label":
                            "Punkte aus Führungen",
                        "value":
                            secured_points_from_leads,
                    },
                    {
                        "label":
                            "Verlorene Punkte",
                        "value":
                            dropped_points,
                    },
                    {
                        "label":
                            "Punkte nach Rückstand",
                        "value":
                            points_after_trailing,
                    },
                ],
            },
            "blocks": [
                {
                    "title":
                        "Führung verwalten",
                    "facts": {
                        "Führungen":
                            matches_leading,
                        "Gewonnen":
                            wins_after_leading,
                        "Nicht gewonnen":
                            (
                                draws_after_leading
                                + losses_after_leading
                            ),
                        "Punkteausbeute %":
                            lead_conversion_percentage,
                    },
                },
                {
                    "title":
                        "Rückstand reparieren",
                    "facts": {
                        "Rückstände":
                            matches_trailing,
                        "Gerettete Spiele":
                            recovered_matches,
                        "Comeback-Siege":
                            wins_after_trailing,
                        "Gerettete Punkte":
                            points_after_trailing,
                    },
                },
            ],
        }

    def _build_halftime_phases_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        half_goal_rows = (
            self.half_goal_service
            .get_statistics(
                competition_id
            )
        )
        halftime_rows = (
            self.halftime_result_service
            .get_statistics(
                competition_id
            )
        )

        half_goal_row = self._find_team_row(
            half_goal_rows,
            team_id,
        )
        halftime_row = self._find_team_row(
            halftime_rows,
            team_id,
        )

        if (
            half_goal_row is None
            and halftime_row is None
        ):
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "Halbzeit- und Spielphasen-Daten vorhanden."
                )
            }

        half_goal_row = (
            half_goal_row
            or {}
        )
        halftime_row = (
            halftime_row
            or {}
        )

        first_for = int(
            half_goal_row.get(
                "first_half_goals",
                0,
            )
            or 0
        )
        second_for = int(
            half_goal_row.get(
                "second_half_goals",
                0,
            )
            or 0
        )
        first_against = int(
            half_goal_row.get(
                "first_half_goals_against",
                0,
            )
            or 0
        )
        second_against = int(
            half_goal_row.get(
                "second_half_goals_against",
                0,
            )
            or 0
        )

        first_balance = (
            first_for
            - first_against
        )
        second_balance = (
            second_for
            - second_against
        )

        matches_with_halftime = int(
            halftime_row.get(
                "matches_with_halftime",
                0,
            )
            or 0
        )

        leading = int(
            halftime_row.get(
                "leading_at_halftime",
                0,
            )
            or 0
        )
        drawing = int(
            halftime_row.get(
                "drawing_at_halftime",
                0,
            )
            or 0
        )
        trailing = int(
            halftime_row.get(
                "trailing_at_halftime",
                0,
            )
            or 0
        )

        wins_lead = int(
            halftime_row.get(
                "wins_after_halftime_lead",
                0,
            )
            or 0
        )
        draws_lead = int(
            halftime_row.get(
                "draws_after_halftime_lead",
                0,
            )
            or 0
        )
        losses_lead = int(
            halftime_row.get(
                "losses_after_halftime_lead",
                0,
            )
            or 0
        )

        wins_draw = int(
            halftime_row.get(
                "wins_after_halftime_draw",
                0,
            )
            or 0
        )
        draws_draw = int(
            halftime_row.get(
                "draws_after_halftime_draw",
                0,
            )
            or 0
        )
        losses_draw = int(
            halftime_row.get(
                "losses_after_halftime_draw",
                0,
            )
            or 0
        )

        wins_trail = int(
            halftime_row.get(
                "wins_after_halftime_trail",
                0,
            )
            or 0
        )
        draws_trail = int(
            halftime_row.get(
                "draws_after_halftime_trail",
                0,
            )
            or 0
        )
        losses_trail = int(
            halftime_row.get(
                "losses_after_halftime_trail",
                0,
            )
            or 0
        )

        points_after_trail = int(
            halftime_row.get(
                "points_after_halftime_trail",
                0,
            )
            or 0
        )
        dropped_after_lead = int(
            halftime_row.get(
                "dropped_points_after_halftime_lead",
                0,
            )
            or 0
        )

        lead_conversion = float(
            halftime_row.get(
                "lead_conversion_percentage",
                0.0,
            )
            or 0.0
        )
        comeback_percentage = float(
            halftime_row.get(
                "halftime_comeback_percentage",
                0.0,
            )
            or 0.0
        )
        win_after_draw_percentage = float(
            halftime_row.get(
                "win_percentage_after_halftime_draw",
                0.0,
            )
            or 0.0
        )

        total_for = (
            first_for
            + second_for
        )
        total_against = (
            first_against
            + second_against
        )

        second_for_pct = (
            round(
                second_for
                / total_for
                * 100,
                1,
            )
            if total_for
            else 0.0
        )
        second_against_pct = (
            round(
                second_against
                / total_against
                * 100,
                1,
            )
            if total_against
            else 0.0
        )

        return {
            "keyfacts": [
                (
                    f"1. Halbzeit: "
                    f"{first_for}:{first_against} Tore"
                ),
                (
                    f"2. Halbzeit: "
                    f"{second_for}:{second_against} Tore"
                ),
                (
                    f"{leading}× Halbzeitführung"
                ),
                (
                    f"{points_after_trail} Punkte "
                    "nach Halbzeitrückstand"
                ),
            ],
            "facts": {
                "Spiele mit Halbzeitstand":
                    matches_with_halftime,
                "Tore 1. HZ":
                    first_for,
                "Gegentore 1. HZ":
                    first_against,
                "Bilanz 1. HZ":
                    first_balance,
                "Tore 2. HZ":
                    second_for,
                "Gegentore 2. HZ":
                    second_against,
                "Bilanz 2. HZ":
                    second_balance,
                "Tore in 2. HZ %":
                    second_for_pct,
                "Gegentore in 2. HZ %":
                    second_against_pct,
                "Halbzeitführung":
                    leading,
                "Halbzeitremis":
                    drawing,
                "Halbzeitrückstand":
                    trailing,
                "Führung gehalten %":
                    round(
                        lead_conversion,
                        1,
                    ),
                "Verlorene Punkte nach HZ-Führung":
                    dropped_after_lead,
                "Comeback-Quote nach HZ %":
                    round(
                        comeback_percentage,
                        1,
                    ),
                "Punkte nach HZ-Rückstand":
                    points_after_trail,
                "Siegquote nach HZ-Remis %":
                    round(
                        win_after_draw_percentage,
                        1,
                    ),
            },
            "charts": {
                "half_goals": [
                    {
                        "label": "1. Halbzeit",
                        "goals_for": first_for,
                        "goals_against": first_against,
                        "balance": first_balance,
                    },
                    {
                        "label": "2. Halbzeit",
                        "goals_for": second_for,
                        "goals_against": second_against,
                        "balance": second_balance,
                    },
                ],
                "halftime_states": [
                    {
                        "label": "Führung",
                        "count": leading,
                    },
                    {
                        "label": "Remis",
                        "count": drawing,
                    },
                    {
                        "label": "Rückstand",
                        "count": trailing,
                    },
                ],
                "after_halftime_lead": [
                    {
                        "label": "Sieg",
                        "count": wins_lead,
                    },
                    {
                        "label": "Remis",
                        "count": draws_lead,
                    },
                    {
                        "label": "Niederlage",
                        "count": losses_lead,
                    },
                ],
                "after_halftime_draw": [
                    {
                        "label": "Sieg",
                        "count": wins_draw,
                    },
                    {
                        "label": "Remis",
                        "count": draws_draw,
                    },
                    {
                        "label": "Niederlage",
                        "count": losses_draw,
                    },
                ],
                "after_halftime_trail": [
                    {
                        "label": "Sieg",
                        "count": wins_trail,
                    },
                    {
                        "label": "Remis",
                        "count": draws_trail,
                    },
                    {
                        "label": "Niederlage",
                        "count": losses_trail,
                    },
                ],
            },
            "blocks": [
                {
                    "title":
                        "Vor der Pause",
                    "facts": {
                        "Tore":
                            first_for,
                        "Gegentore":
                            first_against,
                        "Tordifferenz":
                            self._format_signed(
                                first_balance
                            ),
                    },
                },
                {
                    "title":
                        "Nach der Pause",
                    "facts": {
                        "Tore":
                            second_for,
                        "Gegentore":
                            second_against,
                        "Tordifferenz":
                            self._format_signed(
                                second_balance
                            ),
                    },
                },
                {
                    "title":
                        "Halbzeit → Endstand",
                    "facts": {
                        "Führung gehalten %":
                            round(
                                lead_conversion,
                                1,
                            ),
                        "Comeback-Quote %":
                            round(
                                comeback_percentage,
                                1,
                            ),
                        "Punkte nach Rückstand":
                            points_after_trail,
                        "Verlorene Punkte":
                            dropped_after_lead,
                    },
                },
            ],
        }

    def _build_consistency_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        matches = self._get_team_matches(
            competition_id=competition_id,
            team_id=team_id,
        )

        team_matches: list[dict[str, Any]] = []

        for match in matches:
            (
                _match_id,
                matchday,
                _match_date,
                home_team_id,
                away_team_id,
                _home_team_name,
                _away_team_name,
                home_goals,
                away_goals,
            ) = match

            home_team_id = int(
                home_team_id
            )
            away_team_id = int(
                away_team_id
            )
            home_goals = int(
                home_goals
            )
            away_goals = int(
                away_goals
            )

            if home_team_id == team_id:
                goals_for = home_goals
                goals_against = away_goals
            else:
                goals_for = away_goals
                goals_against = home_goals

            goal_difference = (
                goals_for
                - goals_against
            )

            if goal_difference > 0:
                points = 3
                result = "S"
            elif goal_difference == 0:
                points = 1
                result = "U"
            else:
                points = 0
                result = "N"

            team_matches.append(
                {
                    "matchday": int(
                        matchday
                        or 0
                    ),
                    "goals_for":
                        goals_for,
                    "goals_against":
                        goals_against,
                    "goal_difference":
                        goal_difference,
                    "total_goals":
                        goals_for
                        + goals_against,
                    "points":
                        points,
                    "result":
                        result,
                }
            )

        played = len(
            team_matches
        )

        if played <= 0:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "abgeschlossenen Spiele vorhanden."
                )
            }

        close_matches = sum(
            1
            for row in team_matches
            if abs(
                int(
                    row[
                        "goal_difference"
                    ]
                )
            ) <= 1
        )
        one_goal_matches = sum(
            1
            for row in team_matches
            if abs(
                int(
                    row[
                        "goal_difference"
                    ]
                )
            ) == 1
        )
        draws = sum(
            1
            for row in team_matches
            if int(
                row[
                    "goal_difference"
                ]
            ) == 0
        )
        clear_wins = sum(
            1
            for row in team_matches
            if int(
                row[
                    "goal_difference"
                ]
            ) >= 2
        )
        clear_losses = sum(
            1
            for row in team_matches
            if int(
                row[
                    "goal_difference"
                ]
            ) <= -2
        )

        goal_differences = [
            int(
                row[
                    "goal_difference"
                ]
            )
            for row in team_matches
        ]
        total_goals = [
            int(
                row[
                    "total_goals"
                ]
            )
            for row in team_matches
        ]

        average_goal_difference = (
            sum(
                goal_differences
            )
            / played
        )
        average_total_goals = (
            sum(
                total_goals
            )
            / played
        )

        gd_variance = (
            sum(
                (
                    value
                    - average_goal_difference
                )
                ** 2
                for value
                in goal_differences
            )
            / played
        )
        gd_stddev = (
            gd_variance
            ** 0.5
        )

        goal_variance = (
            sum(
                (
                    value
                    - average_total_goals
                )
                ** 2
                for value
                in total_goals
            )
            / played
        )
        total_goal_stddev = (
            goal_variance
            ** 0.5
        )

        close_match_pct = round(
            close_matches
            / played
            * 100,
            1,
        )

        block_size = 5
        form_blocks: list[dict[str, Any]] = []

        for start in range(
            0,
            played,
            block_size,
        ):
            block = team_matches[
                start:
                start + block_size
            ]

            if not block:
                continue

            points = sum(
                int(
                    row[
                        "points"
                    ]
                )
                for row in block
            )
            goals_for = sum(
                int(
                    row[
                        "goals_for"
                    ]
                )
                for row in block
            )
            goals_against = sum(
                int(
                    row[
                        "goals_against"
                    ]
                )
                for row in block
            )

            first_game = (
                start
                + 1
            )
            last_game = (
                start
                + len(
                    block
                )
            )

            form_blocks.append(
                {
                    "label": (
                        f"Sp. {first_game}–{last_game}"
                    ),
                    "games": len(
                        block
                    ),
                    "points":
                        points,
                    "ppg": round(
                        points
                        / len(
                            block
                        ),
                        2,
                    ),
                    "goal_difference": (
                        goals_for
                        - goals_against
                    ),
                }
            )

        ppg_values = [
            float(
                row[
                    "ppg"
                ]
            )
            for row in form_blocks
        ]

        ppg_spread = (
            round(
                max(
                    ppg_values
                )
                - min(
                    ppg_values
                ),
                2,
            )
            if ppg_values
            else 0.0
        )

        best_block = (
            max(
                form_blocks,
                key=lambda row: (
                    float(
                        row[
                            "ppg"
                        ]
                    ),
                    int(
                        row[
                            "goal_difference"
                        ]
                    ),
                ),
            )
            if form_blocks
            else None
        )
        worst_block = (
            min(
                form_blocks,
                key=lambda row: (
                    float(
                        row[
                            "ppg"
                        ]
                    ),
                    int(
                        row[
                            "goal_difference"
                        ]
                    ),
                ),
            )
            if form_blocks
            else None
        )

        if gd_stddev < 1.15:
            volatility_label = (
                "niedrig"
            )
        elif gd_stddev < 1.75:
            volatility_label = (
                "mittel"
            )
        else:
            volatility_label = (
                "hoch"
            )

        return {
            "keyfacts": [
                (
                    f"{close_matches} von {played} "
                    "Spielen waren knapp"
                ),
                (
                    f"{clear_wins} klare Siege"
                ),
                (
                    f"{clear_losses} klare Niederlagen"
                ),
                (
                    f"Ergebnisstreuung: "
                    f"{gd_stddev:.2f}"
                ),
            ],
            "facts": {
                "Spiele":
                    played,
                "Knappe Spiele":
                    close_matches,
                "Knappe Spiele %":
                    close_match_pct,
                "Ein-Tor-Spiele":
                    one_goal_matches,
                "Remis":
                    draws,
                "Klare Siege":
                    clear_wins,
                "Klare Niederlagen":
                    clear_losses,
                "Ø Tordifferenz":
                    round(
                        average_goal_difference,
                        2,
                    ),
                "Streuung Tordifferenz":
                    round(
                        gd_stddev,
                        2,
                    ),
                "Volatilität":
                    volatility_label,
                "Ø Gesamttore":
                    round(
                        average_total_goals,
                        2,
                    ),
                "Streuung Gesamttore":
                    round(
                        total_goal_stddev,
                        2,
                    ),
                "PPG-Spannweite":
                    ppg_spread,
            },
            "charts": {
                "result_margins": [
                    {
                        "label":
                            "Klare Siege",
                        "count":
                            clear_wins,
                    },
                    {
                        "label":
                            "Ein-Tor-Siege",
                        "count":
                            sum(
                                1
                                for row
                                in team_matches
                                if int(
                                    row[
                                        "goal_difference"
                                    ]
                                ) == 1
                            ),
                    },
                    {
                        "label":
                            "Remis",
                        "count":
                            draws,
                    },
                    {
                        "label":
                            "Ein-Tor-Niederlagen",
                        "count":
                            sum(
                                1
                                for row
                                in team_matches
                                if int(
                                    row[
                                        "goal_difference"
                                    ]
                                ) == -1
                            ),
                    },
                    {
                        "label":
                            "Klare Niederlagen",
                        "count":
                            clear_losses,
                    },
                ],
                "form_blocks":
                    form_blocks,
            },
            "best_block":
                best_block,
            "worst_block":
                worst_block,
        }

    def _build_attack_defense_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        matches = self._get_team_matches(
            competition_id=competition_id,
            team_id=team_id,
        )
        rows = []

        for match in matches:
            (
                _match_id, _matchday, _match_date,
                home_team_id, away_team_id,
                _home_name, _away_name,
                home_goals, away_goals,
            ) = match

            home_team_id = int(home_team_id)
            away_team_id = int(away_team_id)
            home_goals = int(home_goals)
            away_goals = int(away_goals)

            if home_team_id == team_id:
                gf, ga = home_goals, away_goals
            elif away_team_id == team_id:
                gf, ga = away_goals, home_goals
            else:
                continue

            points = 3 if gf > ga else 1 if gf == ga else 0
            rows.append({"gf": gf, "ga": ga, "points": points})

        played = len(rows)
        if not played:
            return {"text": "Keine abgeschlossenen Spiele vorhanden."}

        def bucket(value: int) -> str:
            return "0" if value == 0 else "1" if value == 1 else "2" if value == 2 else "3+"

        attack = {k: {"games": 0, "points": 0, "wins": 0} for k in ("0", "1", "2", "3+")}
        defense = {k: 0 for k in ("0", "1", "2", "3+")}

        for row in rows:
            a = bucket(row["gf"])
            d = bucket(row["ga"])
            attack[a]["games"] += 1
            attack[a]["points"] += row["points"]
            attack[a]["wins"] += int(row["points"] == 3)
            defense[d] += 1

        attack_rows = []
        for label in ("0", "1", "2", "3+"):
            data = attack[label]
            games = data["games"]
            attack_rows.append({
                "label": label,
                "games": games,
                "ppg": round(data["points"] / games, 2) if games else 0.0,
                "win_percentage": round(data["wins"] / games * 100, 1) if games else 0.0,
            })

        defense_rows = [{
            "label": label,
            "games": defense[label],
            "percentage": round(defense[label] / played * 100, 1),
        } for label in ("0", "1", "2", "3+")]

        scored = sum(r["gf"] > 0 for r in rows)
        multi = sum(r["gf"] >= 2 for r in rows)
        clean = sum(r["ga"] == 0 for r in rows)
        max_one = sum(r["ga"] <= 1 for r in rows)
        three_against = sum(r["ga"] >= 3 for r in rows)

        by_label = {r["label"]: r for r in attack_rows}

        return {
            "keyfacts": [
                f"{scored} von {played} Spielen mit eigenem Tor",
                f"{multi}× mindestens 2 Tore",
                f"{clean}× zu Null",
                f"{three_against}× mindestens 3 Gegentore",
            ],
            "facts": {
                "Spiele": played,
                "Mit eigenem Tor": scored,
                "Mit eigenem Tor %": round(scored / played * 100, 1),
                "Mind. 2 eigene Tore": multi,
                "Mind. 2 eigene Tore %": round(multi / played * 100, 1),
                "Zu Null": clean,
                "Zu Null %": round(clean / played * 100, 1),
                "Max. 1 Gegentor": max_one,
                "Max. 1 Gegentor %": round(max_one / played * 100, 1),
                "Mind. 3 Gegentore": three_against,
                "Mind. 3 Gegentore %": round(three_against / played * 100, 1),
                "PPG bei 1 Tor": by_label["1"]["ppg"],
                "PPG bei 2 Toren": by_label["2"]["ppg"],
                "PPG bei 3+ Toren": by_label["3+"]["ppg"],
                "Siegquote bei 1 Tor %": by_label["1"]["win_percentage"],
                "Siegquote bei 2 Toren %": by_label["2"]["win_percentage"],
                "Siegquote bei 3+ Toren %": by_label["3+"]["win_percentage"],
            },
            "charts": {
                "attack_output": attack_rows,
                "defense_output": defense_rows,
            },
        }

    def _build_strengths_weaknesses_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        overview = self._build_overview_section(
            competition_id=competition_id,
            team_id=team_id,
        )
        table_form = self._build_table_form_section(
            competition_id=competition_id,
            team_id=team_id,
        )
        patterns = self._build_patterns_section(
            competition_id=competition_id,
            team_id=team_id,
        )
        control = self._build_control_section(
            competition_id=competition_id,
            team_id=team_id,
        )
        halftime = self._build_halftime_phases_section(
            competition_id=competition_id,
            team_id=team_id,
        )
        consistency = self._build_consistency_section(
            competition_id=competition_id,
            team_id=team_id,
        )
        attack_defense = self._build_attack_defense_section(
            competition_id=competition_id,
            team_id=team_id,
        )

        overview_facts = overview.get(
            "facts",
            {},
        )
        pattern_facts = patterns.get(
            "facts",
            {},
        )
        control_facts = control.get(
            "facts",
            {},
        )
        halftime_facts = halftime.get(
            "facts",
            {},
        )
        consistency_facts = consistency.get(
            "facts",
            {},
        )
        attack_facts = attack_defense.get(
            "facts",
            {},
        )

        strengths: list[dict[str, Any]] = []
        weaknesses: list[dict[str, Any]] = []
        game_patterns: list[dict[str, Any]] = []

        def number(
            mapping: dict[str, Any],
            key: str,
        ) -> float:
            value = mapping.get(
                key,
                0,
            )
            try:
                return float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                return 0.0

        def add(
            target: list[dict[str, Any]],
            score: float,
            title: str,
            metric: str,
            text: str,
            source: str,
        ) -> None:
            target.append(
                {
                    "score": round(
                        float(score),
                        2,
                    ),
                    "title": title,
                    "metric": metric,
                    "text": text,
                    "source": source,
                }
            )

        home_facts: dict[str, Any] = {}
        away_facts: dict[str, Any] = {}
        form_facts: dict[str, Any] = {}

        for block in table_form.get(
            "blocks",
            [],
        ):
            title = str(
                block.get(
                    "title",
                    "",
                )
            )
            facts = block.get(
                "facts",
                {},
            )

            if title == "Heimbilanz":
                home_facts = facts
            elif title == "Auswärtsbilanz":
                away_facts = facts
            elif title == "Form letzte 5 Spiele":
                form_facts = facts

        home_ppg = number(
            home_facts,
            "Punkte / Spiel",
        )
        away_ppg = number(
            away_facts,
            "Punkte / Spiel",
        )
        form_ppg = number(
            form_facts,
            "Punkte / Spiel",
        )

        goals_per_game = number(
            overview_facts,
            "Tore / Spiel",
        )
        goals_against_per_game = number(
            overview_facts,
            "Gegentore / Spiel",
        )

        scored_pct = number(
            attack_facts,
            "Mit eigenem Tor %",
        )
        multi_goal_pct = number(
            attack_facts,
            "Mind. 2 eigene Tore %",
        )
        clean_sheet_pct = number(
            attack_facts,
            "Zu Null %",
        )
        max_one_against_pct = number(
            attack_facts,
            "Max. 1 Gegentor %",
        )
        three_plus_against_pct = number(
            attack_facts,
            "Mind. 3 Gegentore %",
        )
        ppg_two_goals = number(
            attack_facts,
            "PPG bei 2 Toren",
        )
        ppg_three_plus = number(
            attack_facts,
            "PPG bei 3+ Toren",
        )

        scored_first_pct = number(
            pattern_facts,
            "Erstes Tor erzielt %",
        )
        conceded_first_pct = number(
            pattern_facts,
            "Erstes Tor kassiert %",
        )
        btts_pct = number(
            pattern_facts,
            "Beide treffen %",
        )
        over_25_pct = number(
            pattern_facts,
            "Over 2,5 %",
        )

        lead_yield = number(
            control_facts,
            "Punktausbeute aus Führungen %",
        )
        dropped_points = number(
            control_facts,
            "Punkte nach Führung verloren",
        )
        matches_leading = number(
            control_facts,
            "Führungen",
        )
        comeback_pct = number(
            control_facts,
            "Comeback-Quote %",
        )
        points_after_trailing = number(
            control_facts,
            "Punkte nach Rückstand",
        )

        first_half_balance = number(
            halftime_facts,
            "Bilanz 1. HZ",
        )
        second_half_balance = number(
            halftime_facts,
            "Bilanz 2. HZ",
        )
        halftime_lead_conversion = number(
            halftime_facts,
            "Führung gehalten %",
        )
        halftime_comeback = number(
            halftime_facts,
            "Comeback-Quote nach HZ %",
        )

        close_match_pct = number(
            consistency_facts,
            "Knappe Spiele %",
        )
        ppg_spread = number(
            consistency_facts,
            "PPG-Spannweite",
        )
        volatility = str(
            consistency_facts.get(
                "Volatilität",
                "-",
            )
        )

        # --------------------------------------------------
        # STÄRKEN
        # --------------------------------------------------
        if home_ppg > away_ppg:
            difference = (
                home_ppg
                - away_ppg
            )
            add(
                strengths,
                55
                + difference * 25,
                "Heimvorteil",
                (
                    f"{home_ppg:.2f} vs. "
                    f"{away_ppg:.2f} Pkt./Spiel"
                ),
                (
                    "Die Punkteausbeute zuhause liegt "
                    "spürbar über dem Auswärtswert."
                ),
                "Heim-/Auswärtsbilanz",
            )
        elif away_ppg > home_ppg:
            difference = (
                away_ppg
                - home_ppg
            )
            add(
                strengths,
                55
                + difference * 25,
                "Auswärtsstärke",
                (
                    f"{away_ppg:.2f} vs. "
                    f"{home_ppg:.2f} Pkt./Spiel"
                ),
                (
                    "Auswärts wird aktuell mehr Ertrag "
                    "pro Spiel erzielt als zuhause."
                ),
                "Heim-/Auswärtsbilanz",
            )

        if form_ppg > 0:
            add(
                strengths,
                35
                + form_ppg * 20,
                "Aktuelle Form",
                f"{form_ppg:.2f} Pkt./Spiel",
                (
                    "Die letzten fünf Spiele liefern "
                    "einen aktuellen Leistungsindikator."
                ),
                "Form letzte 5",
            )

        add(
            strengths,
            scored_pct,
            "Trefferkonstanz",
            f"{scored_pct:.1f} %",
            (
                "Anteil der Spiele, in denen mindestens "
                "ein eigenes Tor erzielt wurde."
            ),
            "Offensivprofil",
        )

        add(
            strengths,
            multi_goal_pct
            + 10,
            "Mehrfach-Torgefahr",
            f"{multi_goal_pct:.1f} %",
            (
                "Anteil der Spiele mit mindestens "
                "zwei eigenen Treffern."
            ),
            "Offensivprofil",
        )

        add(
            strengths,
            clean_sheet_pct
            + 15,
            "Zu-Null-Potenzial",
            f"{clean_sheet_pct:.1f} %",
            (
                "Anteil der Spiele ohne Gegentor."
            ),
            "Defensivprofil",
        )

        add(
            strengths,
            max_one_against_pct,
            "Defensive Begrenzung",
            f"{max_one_against_pct:.1f} %",
            (
                "So häufig blieb die Mannschaft bei "
                "höchstens einem Gegentor."
            ),
            "Defensivprofil",
        )

        add(
            strengths,
            lead_yield,
            "Führungen verwerten",
            f"{lead_yield:.1f} %",
            (
                "Punktausbeute aus Spielen, in denen "
                "die Mannschaft mindestens einmal führte."
            ),
            "Spielkontrolle",
        )

        add(
            strengths,
            comeback_pct
            + 10,
            "Comeback-Fähigkeit",
            f"{comeback_pct:.1f} %",
            (
                f"Nach Rückständen wurden insgesamt "
                f"{int(points_after_trailing)} Punkte geholt."
            ),
            "Spielkontrolle",
        )

        add(
            strengths,
            halftime_lead_conversion,
            "Halbzeitführungen nutzen",
            f"{halftime_lead_conversion:.1f} %",
            (
                "Anteil der Halbzeitführungen, die "
                "anschließend in einen Sieg umgewandelt wurden."
            ),
            "Halbzeiten",
        )

        half_improvement = (
            second_half_balance
            - first_half_balance
        )
        if half_improvement > 0:
            add(
                strengths,
                50
                + min(
                    half_improvement * 4,
                    35,
                ),
                "Steigerung nach der Pause",
                (
                    f"{first_half_balance:+.0f} → "
                    f"{second_half_balance:+.0f}"
                ),
                (
                    "Die Torbilanz der zweiten Halbzeit "
                    "ist besser als vor der Pause."
                ),
                "Halbzeiten",
            )

        add(
            strengths,
            min(
                100,
                ppg_two_goals
                / 3
                * 100,
            ),
            "Ertrag bei zwei Toren",
            f"{ppg_two_goals:.2f} Pkt./Spiel",
            (
                "Punkteausbeute in Spielen mit genau "
                "zwei eigenen Treffern."
            ),
            "Offensivprofil",
        )

        add(
            strengths,
            min(
                100,
                ppg_three_plus
                / 3
                * 100,
            ),
            "Ertrag bei 3+ Toren",
            f"{ppg_three_plus:.2f} Pkt./Spiel",
            (
                "Punkteausbeute in Spielen mit mindestens "
                "drei eigenen Treffern."
            ),
            "Offensivprofil",
        )

        # --------------------------------------------------
        # SCHWÄCHEN
        # --------------------------------------------------
        add(
            weaknesses,
            max(
                0,
                100
                - scored_pct,
            )
            + 25,
            "Spiele ohne eigenen Treffer",
            f"{100 - scored_pct:.1f} %",
            (
                "In diesem Anteil der Spiele blieb "
                "die Mannschaft ohne eigenes Tor."
            ),
            "Offensivprofil",
        )

        add(
            weaknesses,
            max(
                0,
                100
                - clean_sheet_pct,
            ),
            "Seltene Zu-Null-Spiele",
            f"{clean_sheet_pct:.1f} % zu Null",
            (
                "Die Defensive hält nur selten ein "
                "komplettes Spiel ohne Gegentor."
            ),
            "Defensivprofil",
        )

        add(
            weaknesses,
            three_plus_against_pct
            + 30,
            "Hohe Gegentorlast",
            f"{three_plus_against_pct:.1f} % mit 3+ GT",
            (
                "In diesem Anteil der Spiele wurden "
                "mindestens drei Gegentore kassiert."
            ),
            "Defensivprofil",
        )

        add(
            weaknesses,
            max(
                0,
                goals_against_per_game
                - 1
            )
            * 45
            + 35,
            "Gegentore pro Spiel",
            f"{goals_against_per_game:.2f}",
            (
                "Die durchschnittliche Gegentorzahl "
                "belastet die Ergebniswahrscheinlichkeit."
            ),
            "Leistung & Tabelle",
        )

        add(
            weaknesses,
            conceded_first_pct
            + 10,
            "Häufig zuerst im Rückstand",
            f"{conceded_first_pct:.1f} %",
            (
                "So häufig erzielte der Gegner den "
                "ersten Treffer des Spiels."
            ),
            "Spielmuster",
        )

        dropped_per_lead = (
            dropped_points
            / matches_leading
            if matches_leading > 0
            else 0.0
        )
        add(
            weaknesses,
            min(
                100,
                dropped_per_lead
                * 45
                + 25,
            ),
            "Punkte nach Führung verloren",
            (
                f"{int(dropped_points)} Punkte"
            ),
            (
                "Trotz zwischenzeitlicher Führung "
                "ging ein Teil des möglichen Ertrags verloren."
            ),
            "Spielkontrolle",
        )

        add(
            weaknesses,
            max(
                0,
                100
                - comeback_pct,
            ),
            "Rückstände schwer zu reparieren",
            f"{comeback_pct:.1f} % Comeback-Quote",
            (
                "Nach einem Rückstand gelingt nur "
                "begrenzt noch ein Punktgewinn."
            ),
            "Spielkontrolle",
        )

        add(
            weaknesses,
            max(
                0,
                100
                - halftime_lead_conversion,
            )
            + 10,
            "Halbzeitführungen nicht sicher",
            f"{halftime_lead_conversion:.1f} %",
            (
                "Nicht jede Führung zur Pause wird "
                "bis zum Sieg gebracht."
            ),
            "Halbzeiten",
        )

        add(
            weaknesses,
            max(
                0,
                100
                - halftime_comeback,
            ),
            "Halbzeitrückstände problematisch",
            f"{halftime_comeback:.1f} %",
            (
                "Nach Rückstand zur Pause werden "
                "nur begrenzt Spiele gerettet."
            ),
            "Halbzeiten",
        )

        add(
            weaknesses,
            min(
                100,
                ppg_spread
                * 45
                + 20,
            ),
            "Formschwankungen",
            f"{ppg_spread:.2f} Pkt./Spiel",
            (
                "Die Punkteausbeute schwankt zwischen "
                "den Saisonabschnitten deutlich."
            ),
            "Konstanz & Volatilität",
        )

        if away_ppg + 0.25 < home_ppg:
            add(
                weaknesses,
                60
                + (
                    home_ppg
                    - away_ppg
                )
                * 20,
                "Auswärtsschwäche",
                f"{away_ppg:.2f} Pkt./Spiel",
                (
                    "Die Auswärtsausbeute fällt deutlich "
                    "gegenüber den Heimspielen ab."
                ),
                "Heim-/Auswärtsbilanz",
            )

        if home_ppg + 0.25 < away_ppg:
            add(
                weaknesses,
                60
                + (
                    away_ppg
                    - home_ppg
                )
                * 20,
                "Heimschwäche",
                f"{home_ppg:.2f} Pkt./Spiel",
                (
                    "Die Heimausbeute fällt deutlich "
                    "gegenüber den Auswärtsspielen ab."
                ),
                "Heim-/Auswärtsbilanz",
            )

        # --------------------------------------------------
        # SPIELMUSTER
        # --------------------------------------------------
        add(
            game_patterns,
            abs(
                btts_pct
                - 50
            )
            + 30,
            (
                "Beide Teams treffen häufig"
                if btts_pct >= 50
                else "Beide Teams treffen eher selten"
            ),
            f"{btts_pct:.1f} %",
            (
                "Beschreibt, wie häufig beide Mannschaften "
                "im selben Spiel mindestens einmal treffen."
            ),
            "Spielmuster",
        )

        add(
            game_patterns,
            abs(
                over_25_pct
                - 50
            )
            + 30,
            (
                "Torreiche Spielstruktur"
                if over_25_pct >= 50
                else "Eher torarme Spielstruktur"
            ),
            f"{over_25_pct:.1f} % Over 2,5",
            (
                "Anteil der Spiele mit mindestens "
                "drei Treffern insgesamt."
            ),
            "Spielmuster",
        )

        add(
            game_patterns,
            abs(
                scored_first_pct
                - conceded_first_pct
            )
            + 35,
            (
                "Gegner eröffnet häufiger"
                if conceded_first_pct > scored_first_pct
                else "Eigene Toreröffnung häufiger"
            ),
            (
                f"{scored_first_pct:.1f} % / "
                f"{conceded_first_pct:.1f} %"
            ),
            (
                "Vergleich zwischen eigenem ersten Treffer "
                "und erstem Gegentor."
            ),
            "Spielmuster",
        )

        add(
            game_patterns,
            abs(
                close_match_pct
                - 50
            )
            + 35,
            (
                "Viele enge Spiele"
                if close_match_pct >= 50
                else "Viele deutliche Entscheidungen"
            ),
            f"{close_match_pct:.1f} %",
            (
                "Anteil der Remis und Spiele mit "
                "höchstens einem Tor Unterschied."
            ),
            "Konstanz & Volatilität",
        )

        second_half_goals = number(
            halftime_facts,
            "Tore 2. HZ",
        )
        first_half_goals = number(
            halftime_facts,
            "Tore 1. HZ",
        )

        if (
            first_half_goals
            + second_half_goals
        ) > 0:
            second_half_share = (
                second_half_goals
                / (
                    first_half_goals
                    + second_half_goals
                )
                * 100
            )

            add(
                game_patterns,
                abs(
                    second_half_share
                    - 50
                )
                + 35,
                (
                    "Offensiv stärker nach der Pause"
                    if second_half_share >= 50
                    else "Offensiv stärker vor der Pause"
                ),
                f"{second_half_share:.1f} % der Tore",
                (
                    "Anteil der eigenen Treffer, die "
                    "in der zweiten Halbzeit fallen."
                ),
                "Halbzeiten",
            )

        home_away_gap = abs(
            home_ppg
            - away_ppg
        )
        if (
            home_ppg > 0
            or away_ppg > 0
        ):
            add(
                game_patterns,
                35
                + home_away_gap * 25,
                "Heim-/Auswärtsgefälle",
                (
                    f"{home_ppg:.2f} / "
                    f"{away_ppg:.2f} Pkt./Spiel"
                ),
                (
                    "Zeigt, wie stark sich die Punkteausbeute "
                    "zwischen Heim- und Auswärtsspielen unterscheidet."
                ),
                "Heim-/Auswärtsbilanz",
            )

        if volatility != "-":
            volatility_score = {
                "niedrig": 45,
                "mittel": 60,
                "hoch": 80,
            }.get(
                volatility.lower(),
                50,
            )

            add(
                game_patterns,
                volatility_score,
                f"Volatilität: {volatility}",
                f"PPG-Spannweite {ppg_spread:.2f}",
                (
                    "Beschreibt die Schwankung zwischen "
                    "verschiedenen Saisonabschnitten."
                ),
                "Konstanz & Volatilität",
            )

        strengths.sort(
            key=lambda item: (
                -float(
                    item[
                        "score"
                    ]
                ),
                item[
                    "title"
                ],
            )
        )
        weaknesses.sort(
            key=lambda item: (
                -float(
                    item[
                        "score"
                    ]
                ),
                item[
                    "title"
                ],
            )
        )
        game_patterns.sort(
            key=lambda item: (
                -float(
                    item[
                        "score"
                    ]
                ),
                item[
                    "title"
                ],
            )
        )

        strengths = strengths[:3]
        weaknesses = weaknesses[:3]
        game_patterns = game_patterns[:3]

        return {
            "keyfacts": [
                (
                    f"{len(strengths)} Stärken"
                ),
                (
                    f"{len(weaknesses)} Schwächen"
                ),
                (
                    f"{len(game_patterns)} Spielmuster"
                ),
            ],
            "strengths":
                strengths,
            "weaknesses":
                weaknesses,
            "patterns":
                game_patterns,
        }

    def _build_players_section(
        self,
        competition_id: int,
        team_id: int,
        include_all: bool = False,
    ) -> dict[str, Any]:
        self.cursor.execute(
            """
            SELECT
                players.first_name,
                players.last_name,
                COALESCE(
                    NULLIF(
                        player_match_stats.position,
                        ''
                    ),
                    players.position,
                    ''
                ) AS position,
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
            (
                competition_id,
                team_id,
            ),
        )

        rows = self.cursor.fetchall()

        if not rows:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "Spielerstatistiken vorhanden."
                )
            }

        consolidated: dict[str, dict[str, Any]] = {}

        for row in rows:
            first_name = str(
                row[0] or ""
            ).strip()
            last_name = str(
                row[1] or ""
            ).strip()

            player_name = " ".join(
                part
                for part in (
                    first_name,
                    last_name,
                )
                if part
            ).strip()

            if self._is_report_placeholder_player(
                player_name
            ):
                continue

            normalized_name = (
                self._normalize_player_name(
                    player_name
                )
            )

            if not normalized_name:
                continue

            position = str(
                row[2] or ""
            ).strip()

            values = {
                "appearances": int(
                    row[3] or 0
                ),
                "starts": int(
                    row[4] or 0
                ),
                "minutes": int(
                    row[5] or 0
                ),
                "goals": int(
                    row[6] or 0
                ),
                "assists": int(
                    row[7] or 0
                ),
                "yellow": int(
                    row[8] or 0
                ),
                "yellow_red": int(
                    row[9] or 0
                ),
                "red": int(
                    row[10] or 0
                ),
            }

            if normalized_name not in consolidated:
                consolidated[
                    normalized_name
                ] = {
                    "name": player_name,
                    "position": (
                        position
                        if position
                        else "-"
                    ),
                    **values,
                }
                continue

            player = consolidated[
                normalized_name
            ]

            if (
                player.get(
                    "position",
                    "-"
                )
                in {
                    "",
                    "-",
                }
                and position
            ):
                player[
                    "position"
                ] = position

            for key, value in values.items():
                player[
                    key
                ] = int(
                    player.get(
                        key,
                        0,
                    )
                ) + value

        player_rows: list[list[Any]] = []

        for player in consolidated.values():
            statistical_total = (
                int(player["appearances"])
                + int(player["starts"])
                + int(player["minutes"])
                + int(player["goals"])
                + int(player["assists"])
                + int(player["yellow"])
                + int(player["yellow_red"])
                + int(player["red"])
            )

            if statistical_total <= 0:
                continue

            player_rows.append(
                [
                    player["name"],
                    player.get(
                        "position",
                        "-"
                    )
                    or "-",
                    int(player["appearances"]),
                    int(player["starts"]),
                    int(player["minutes"]),
                    int(player["goals"]),
                    int(player["assists"]),
                    int(player["yellow"]),
                    int(player["yellow_red"]),
                    int(player["red"]),
                ]
            )

        if not player_rows:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "verwertbaren Spielerstatistiken vorhanden."
                )
            }

        player_rows.sort(
            key=lambda row: (
                -int(row[5]),
                -int(row[6]),
                -int(row[4]),
                -int(row[2]),
                str(row[0]).casefold(),
            )
        )

        top_scorer = max(
            player_rows,
            key=lambda row: (
                int(row[5]),
                int(row[6]),
                int(row[4]),
            ),
        )

        most_minutes = max(
            player_rows,
            key=lambda row: (
                int(row[4]),
                int(row[2]),
            ),
        )

        return {
            "keyfacts": [
                (
                    "Top-Torschütze: "
                    f"{top_scorer[0]} "
                    f"({top_scorer[5]} Tore)"
                ),
                (
                    "Meiste Minuten: "
                    f"{most_minutes[0]} "
                    f"({most_minutes[4]})"
                ),
                (
                    f"{len(player_rows)} Spieler "
                    "mit Statistikdaten"
                ),
            ],
            "tables": [
                {
                    "title": "Spielerübersicht",
                    "headers": [
                        "Spieler",
                        "Pos.",
                        "Eins.",
                        "Start",
                        "Min.",
                        "Tore",
                        "Assists",
                        "Gelb",
                        "G-R",
                        "Rot",
                    ],
                    "rows": (
                        player_rows
                        if include_all
                        else player_rows[:25]
                    ),
                }
            ],
        }

    def _build_season_progress_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        team_progress = (
            self.table_progress_service
            .get_team_progress(
                competition_id=competition_id,
                team_id=team_id,
            )
        )

        if not team_progress:
            return {
                "text": (
                    "Für diese Mannschaft ist kein "
                    "Saisonverlauf vorhanden."
                )
            }

        progress = list(
            team_progress.get(
                "progress",
                [],
            )
        )

        if not progress:
            return {
                "text": (
                    "Für diese Mannschaft ist kein "
                    "Saisonverlauf vorhanden."
                )
            }

        points_rows: list[list[Any]] = []
        position_rows: list[list[Any]] = []
        points_chart: list[dict[str, Any]] = []
        position_chart: list[dict[str, Any]] = []

        previous_points = 0

        for row in progress:
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
            position = int(
                row.get(
                    "position",
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
            gained_points = (
                points - previous_points
            )

            if gained_points >= 3:
                result_code = "S"
            elif gained_points == 1:
                result_code = "U"
            else:
                result_code = "N"

            points_rows.append(
                [
                    played,
                    points,
                    result_code,
                    goals_for,
                    goals_against,
                    self._format_signed(
                        goals_for - goals_against
                    ),
                ]
            )

            position_rows.append(
                [
                    played,
                    position,
                    points,
                ]
            )

            points_chart.append(
                {
                    "played": played,
                    "points": points,
                    "result": result_code,
                }
            )

            position_chart.append(
                {
                    "played": played,
                    "position": position,
                }
            )

            previous_points = points

        latest = progress[-1]

        return {
            "keyfacts": [
                (
                    f"{int(latest.get('played', 0))} "
                    "absolvierte Spiele"
                ),
                (
                    f"{int(latest.get('points', 0))} Punkte"
                ),
                (
                    "Aktueller Tabellenplatz: "
                    f"{int(latest.get('position', 0))}"
                ),
            ],
            "charts": {
                "points_progress": points_chart,
                "position_progress": position_chart,
            },
            "tables": [
                {
                    "title": "Punkteentwicklung",
                    "headers": [
                        "Spiel",
                        "Punkte",
                        "W/U/N",
                        "Tore",
                        "Gegentore",
                        "Tordiff.",
                    ],
                    "rows": points_rows,
                },
                {
                    "title": "Platzierungsverlauf",
                    "headers": [
                        "Spiel",
                        "Platz",
                        "Punkte",
                    ],
                    "rows": position_rows,
                },
            ],
        }

    def _build_discipline_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        self.cursor.execute(
            """
            SELECT
                players.first_name,
                players.last_name,
                SUM(
                    player_match_stats.yellow_cards
                ) AS yellow_cards,
                SUM(
                    player_match_stats.yellow_red_cards
                ) AS yellow_red_cards,
                SUM(
                    player_match_stats.red_cards
                ) AS red_cards
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id =
                   player_match_stats.match_id
            INNER JOIN players
                ON players.player_id =
                   player_match_stats.player_id
            WHERE
                matches.competition_id = ?
                AND player_match_stats.team_id = ?
            GROUP BY
                player_match_stats.player_id,
                players.first_name,
                players.last_name
            HAVING
                SUM(
                    player_match_stats.yellow_cards
                ) > 0
                OR SUM(
                    player_match_stats.yellow_red_cards
                ) > 0
                OR SUM(
                    player_match_stats.red_cards
                ) > 0
            ORDER BY
                yellow_cards DESC,
                yellow_red_cards DESC,
                red_cards DESC,
                players.last_name,
                players.first_name;
            """,
            (
                competition_id,
                team_id,
            ),
        )

        rows = self.cursor.fetchall()

        consolidated: dict[
            str,
            dict[str, Any],
        ] = {}

        for row in rows:
            name = " ".join(
                part
                for part in (
                    str(row[0] or "").strip(),
                    str(row[1] or "").strip(),
                )
                if part
            ).strip()

            if self._is_report_placeholder_player(
                name
            ):
                continue

            normalized_name = (
                self._normalize_player_name(
                    name
                )
            )

            if not normalized_name:
                continue

            player = consolidated.setdefault(
                normalized_name,
                {
                    "name": name,
                    "yellow": 0,
                    "yellow_red": 0,
                    "red": 0,
                },
            )

            player["yellow"] += int(
                row[2] or 0
            )
            player["yellow_red"] += int(
                row[3] or 0
            )
            player["red"] += int(
                row[4] or 0
            )

        player_rows: list[list[Any]] = []
        yellow_total = 0
        yellow_red_total = 0
        red_total = 0

        sorted_players = sorted(
            consolidated.values(),
            key=lambda player: (
                -int(player["yellow"]),
                -int(player["yellow_red"]),
                -int(player["red"]),
                str(player["name"]).casefold(),
            ),
        )

        for player in sorted_players:
            yellow = int(
                player["yellow"]
            )
            yellow_red = int(
                player["yellow_red"]
            )
            red = int(
                player["red"]
            )

            if (
                yellow <= 0
                and yellow_red <= 0
                and red <= 0
            ):
                continue

            yellow_total += yellow
            yellow_red_total += yellow_red
            red_total += red

            player_rows.append(
                [
                    player["name"],
                    yellow,
                    yellow_red,
                    red,
                ]
            )

        return {
            "facts": {
                "Gelbe Karten":
                    yellow_total,
                "Gelb-Rote Karten":
                    yellow_red_total,
                "Rote Karten":
                    red_total,
                "Spieler mit Karten":
                    len(player_rows),
            },
            "tables": [
                {
                    "title":
                        "Karten nach Spielern",
                    "headers": [
                        "Spieler",
                        "Gelb",
                        "Gelb-Rot",
                        "Rot",
                    ],
                    "rows":
                        player_rows,
                }
            ],
        }

    def _build_streaks_section(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        streaks = self.streak_service.get_streaks(
            competition_id
        )

        team_streak = self._find_team_row(
            streaks,
            team_id,
        )

        if team_streak is None:
            return {
                "text": (
                    "Für diese Mannschaft sind keine "
                    "Seriendaten vorhanden."
                )
            }

        return {
            "keyfacts": [
                str(
                    team_streak.get(
                        "current_label",
                        "Keine aktuelle Serie",
                    )
                    or "Keine aktuelle Serie"
                ),
                (
                    "Längste Siegesserie: "
                    f"{int(team_streak.get('longest_win_streak', 0))}"
                ),
                (
                    "Längste Serie ohne Niederlage: "
                    f"{int(team_streak.get('longest_unbeaten_streak', 0))}"
                ),
            ],
            "facts": {
                "Aktuelle Serie": (
                    team_streak.get(
                        "current_label",
                        "-",
                    )
                    or "-"
                ),
                "Siegesserie max.": int(
                    team_streak.get(
                        "longest_win_streak",
                        0,
                    )
                ),
                "Remisserie max.": int(
                    team_streak.get(
                        "longest_draw_streak",
                        0,
                    )
                ),
                "Niederlagenserie max.": int(
                    team_streak.get(
                        "longest_loss_streak",
                        0,
                    )
                ),
                "Ungeschlagen max.": int(
                    team_streak.get(
                        "longest_unbeaten_streak",
                        0,
                    )
                ),
                "Sieglos max.": int(
                    team_streak.get(
                        "longest_winless_streak",
                        0,
                    )
                ),
            },
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
    def _normalize_player_name(
        player_name: str,
    ) -> str:
        return " ".join(
            str(
                player_name
            ).split()
        ).casefold()

    @staticmethod
    def _is_report_placeholder_player(
        player_name: str,
    ) -> bool:
        normalized = (
            TeamStatisticsPdfService
            ._normalize_player_name(
                player_name
            )
        )

        if not normalized:
            return True

        if normalized == "unbekannt":
            return True

        if normalized.startswith(
            "unbekannt "
        ):
            return True

        return False

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
