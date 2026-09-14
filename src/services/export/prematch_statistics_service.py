from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from src.services.export.team_statistics_pdf_service import (
    TeamStatisticsPdfService,
)


class PrematchStatisticsService:
    REPORT_SECTIONS = [
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

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.team_statistics_service = (
            TeamStatisticsPdfService(
                connection
            )
        )

    def build_comparison_data(
        self,
        competition_id: int,
        team_a_id: int,
        team_b_id: int,
    ) -> dict[str, Any]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if team_a_id <= 0 or team_b_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        if team_a_id == team_b_id:
            raise ValueError(
                "Für den Prematch-Report müssen "
                "zwei unterschiedliche Mannschaften "
                "ausgewählt werden."
            )

        team_a = self._build_team_data(
            competition_id=competition_id,
            team_id=team_a_id,
        )

        team_b = self._build_team_data(
            competition_id=competition_id,
            team_id=team_b_id,
        )

        return {
            "competition_id":
                competition_id,
            "competition_name":
                team_a.get(
                    "competition_name",
                    "",
                ),
            "season_name":
                team_a.get(
                    "season_name",
                    "",
                ),
            "generated_at":
                datetime.now(),
            "team_a":
                team_a,
            "team_b":
                team_b,
            "venue_comparison":
                self._build_venue_comparison(
                    team_a=team_a,
                    team_b=team_b,
                ),
            "headline_comparison":
                self._build_headline_comparison(
                    team_a=team_a,
                    team_b=team_b,
                ),
            "strength_matchups":
                self._build_strength_matchups(
                    team_a=team_a,
                    team_b=team_b,
                ),
        }

    def _build_team_data(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict[str, Any]:
        report = (
            self.team_statistics_service
            .build_report_data(
                competition_id=competition_id,
                team_id=team_id,
                selected_sections=list(
                    self.REPORT_SECTIONS
                ),
                report_type="full",
            )
        )

        return {
            "team_id":
                team_id,
            "team_name":
                report.get(
                    "team_name",
                    "",
                ),
            "competition_name":
                report.get(
                    "competition_name",
                    "",
                ),
            "season_name":
                report.get(
                    "season_name",
                    "",
                ),
            "sections":
                report.get(
                    "sections",
                    {},
                ),
        }

    def _build_venue_comparison(
        self,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> dict[str, Any]:
        team_a_table_form = self._section(
            team_a,
            "table_form",
        )
        team_b_table_form = self._section(
            team_b,
            "table_form",
        )

        home = self._find_block(
            team_a_table_form,
            "Heimbilanz",
        )
        away = self._find_block(
            team_b_table_form,
            "Auswärtsbilanz",
        )

        return {
            "team_a_label":
                "Heimbilanz",
            "team_a":
                home,
            "team_b_label":
                "Auswärtsbilanz",
            "team_b":
                away,
        }

    def _build_headline_comparison(
        self,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> list[dict[str, Any]]:
        overview_a = self._facts(
            self._section(
                team_a,
                "overview",
            )
        )
        overview_b = self._facts(
            self._section(
                team_b,
                "overview",
            )
        )

        patterns_a = self._facts(
            self._section(
                team_a,
                "patterns",
            )
        )
        patterns_b = self._facts(
            self._section(
                team_b,
                "patterns",
            )
        )

        attack_a = self._facts(
            self._section(
                team_a,
                "attack_defense",
            )
        )
        attack_b = self._facts(
            self._section(
                team_b,
                "attack_defense",
            )
        )

        consistency_a = self._facts(
            self._section(
                team_a,
                "consistency",
            )
        )
        consistency_b = self._facts(
            self._section(
                team_b,
                "consistency",
            )
        )

        rows = [
            self._comparison_row(
                "Tabellenplatz",
                overview_a.get(
                    "Tabellenplatz",
                    "-",
                ),
                overview_b.get(
                    "Tabellenplatz",
                    "-",
                ),
            ),
            self._comparison_row(
                "Punkte / Spiel",
                overview_a.get(
                    "Punkte / Spiel",
                    0.0,
                ),
                overview_b.get(
                    "Punkte / Spiel",
                    0.0,
                ),
            ),
            self._comparison_row(
                "Form letzte 5",
                overview_a.get(
                    "Form letzte 5",
                    "-",
                ),
                overview_b.get(
                    "Form letzte 5",
                    "-",
                ),
            ),
            self._comparison_row(
                "Tore / Spiel",
                overview_a.get(
                    "Tore / Spiel",
                    0.0,
                ),
                overview_b.get(
                    "Tore / Spiel",
                    0.0,
                ),
            ),
            self._comparison_row(
                "Gegentore / Spiel",
                overview_a.get(
                    "Gegentore / Spiel",
                    0.0,
                ),
                overview_b.get(
                    "Gegentore / Spiel",
                    0.0,
                ),
            ),
            self._comparison_row(
                "Beide treffen %",
                patterns_a.get(
                    "Beide treffen %",
                    0.0,
                ),
                patterns_b.get(
                    "Beide treffen %",
                    0.0,
                ),
            ),
            self._comparison_row(
                "Over 2,5 %",
                patterns_a.get(
                    "Over 2,5 %",
                    0.0,
                ),
                patterns_b.get(
                    "Over 2,5 %",
                    0.0,
                ),
            ),
            self._comparison_row(
                "Mit eigenem Tor %",
                attack_a.get(
                    "Mit eigenem Tor %",
                    0.0,
                ),
                attack_b.get(
                    "Mit eigenem Tor %",
                    0.0,
                ),
            ),
            self._comparison_row(
                "Zu Null %",
                attack_a.get(
                    "Zu Null %",
                    0.0,
                ),
                attack_b.get(
                    "Zu Null %",
                    0.0,
                ),
            ),
            self._comparison_row(
                "PPG-Spanne",
                consistency_a.get(
                    "PPG-Spanne",
                    consistency_a.get(
                        "PPG Spread",
                        0.0,
                    ),
                ),
                consistency_b.get(
                    "PPG-Spanne",
                    consistency_b.get(
                        "PPG Spread",
                        0.0,
                    ),
                ),
            ),
        ]

        return rows

    def _build_strength_matchups(
        self,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> dict[str, Any]:
        profile_a = self._section(
            team_a,
            "strengths_weaknesses",
        )
        profile_b = self._section(
            team_b,
            "strengths_weaknesses",
        )

        strengths_a = list(
            profile_a.get(
                "strengths",
                [],
            )
        )
        weaknesses_a = list(
            profile_a.get(
                "weaknesses",
                [],
            )
        )
        strengths_b = list(
            profile_b.get(
                "strengths",
                [],
            )
        )
        weaknesses_b = list(
            profile_b.get(
                "weaknesses",
                [],
            )
        )

        return {
            "team_a_strengths":
                strengths_a,
            "team_a_weaknesses":
                weaknesses_a,
            "team_b_strengths":
                strengths_b,
            "team_b_weaknesses":
                weaknesses_b,
            "team_a_attack_points":
                self._pair_profiles(
                    strengths=strengths_a,
                    opponent_weaknesses=weaknesses_b,
                ),
            "team_b_attack_points":
                self._pair_profiles(
                    strengths=strengths_b,
                    opponent_weaknesses=weaknesses_a,
                ),
        }

    @staticmethod
    def _pair_profiles(
        strengths: list[dict[str, Any]],
        opponent_weaknesses: list[
            dict[str, Any]
        ],
    ) -> list[dict[str, Any]]:
        pairs: list[dict[str, Any]] = []

        max_rows = max(
            len(
                strengths
            ),
            len(
                opponent_weaknesses
            ),
        )

        for index in range(
            max_rows
        ):
            strength = (
                strengths[
                    index
                ]
                if index < len(
                    strengths
                )
                else None
            )
            weakness = (
                opponent_weaknesses[
                    index
                ]
                if index < len(
                    opponent_weaknesses
                )
                else None
            )

            pairs.append(
                {
                    "strength":
                        strength,
                    "opponent_weakness":
                        weakness,
                }
            )

        return pairs

    @staticmethod
    def _comparison_row(
        label: str,
        team_a_value: Any,
        team_b_value: Any,
    ) -> dict[str, Any]:
        return {
            "label":
                label,
            "team_a":
                team_a_value,
            "team_b":
                team_b_value,
        }

    @staticmethod
    def _section(
        team: dict[str, Any],
        name: str,
    ) -> dict[str, Any]:
        sections = team.get(
            "sections",
            {},
        )

        section = sections.get(
            name,
            {},
        )

        return (
            section
            if isinstance(
                section,
                dict,
            )
            else {}
        )

    @staticmethod
    def _facts(
        section: dict[str, Any],
    ) -> dict[str, Any]:
        facts = section.get(
            "facts",
            {},
        )

        return (
            facts
            if isinstance(
                facts,
                dict,
            )
            else {}
        )

    @staticmethod
    def _find_block(
        section: dict[str, Any],
        title: str,
    ) -> dict[str, Any]:
        blocks = section.get(
            "blocks",
            [],
        )

        if not isinstance(
            blocks,
            list,
        ):
            return {}

        for block in blocks:
            if not isinstance(
                block,
                dict,
            ):
                continue

            if str(
                block.get(
                    "title",
                    "",
                )
            ) == title:
                return block

        return {}
