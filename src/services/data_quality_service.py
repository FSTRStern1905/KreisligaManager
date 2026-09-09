from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field


@dataclass
class DataQualityMetric:
    key: str
    label: str
    available: int
    expected: int
    percent: float | None
    note: str = ""


@dataclass
class CompetitionDataQuality:
    competition_id: int
    competition_name: str
    season_name: str
    sources: list[str] = field(
        default_factory=list
    )
    total_matches: int = 0
    completed_matches: int = 0
    detail_imported_matches: int = 0
    latest_matchday: int | None = None
    metrics: list[DataQualityMetric] = field(
        default_factory=list
    )
    overall_percent: float | None = None

    @property
    def source_text(self) -> str:
        if not self.sources:
            return "Unbekannt"

        return " · ".join(
            self.sources
        )

    @property
    def quality_label(self) -> str:
        if self.overall_percent is None:
            return "Nicht bewertet"

        if self.overall_percent >= 90.0:
            return "Gut"

        if self.overall_percent >= 70.0:
            return "Teilweise"

        return "Lückenhaft"

    @property
    def data_status_text(self) -> str:
        if self.total_matches <= 0:
            return (
                f"{self.season_name} · "
                "keine Spiele"
            )

        match_text = (
            f"{self.completed_matches}/"
            f"{self.total_matches} Spiele"
        )

        if self.latest_matchday is not None:
            return (
                f"{self.season_name} · "
                f"ST {self.latest_matchday} · "
                f"{match_text}"
            )

        return (
            f"{self.season_name} · "
            f"{match_text}"
        )


class DataQualityService:
    """
    Ermittelt die Datenabdeckung eines Wettbewerbs.

    Wichtig:
    Die Prozentwerte messen Vollständigkeit/Abdeckung,
    nicht die inhaltliche Richtigkeit der Quelle.

    Detailmetriken werden nur auf Spiele bezogen, die
    als detail_imported markiert sind. Dadurch wird ein
    absichtlich nur grob importierter Spielplan nicht
    fälschlich als schlechte Detailqualität bewertet.
    """

    GOAL_CODES = (
        "GOAL",
        "OWN_GOAL",
        "PENALTY_GOAL",
    )

    CARD_CODES = (
        "YELLOW_CARD",
        "YELLOW_RED_CARD",
        "RED_CARD",
    )

    SUBSTITUTION_CODES = (
        "SUBSTITUTION",
        "SUBSTITUTION_IN",
        "SUBSTITUTION_OUT",
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def get_competition_quality(
        self,
        competition_id: int,
    ) -> CompetitionDataQuality:
        competition = self._get_competition(
            competition_id
        )

        if competition is None:
            raise ValueError(
                "Wettbewerb nicht gefunden: "
                f"{competition_id}"
            )

        match_summary = self._get_match_summary(
            competition_id
        )

        total_matches = int(
            match_summary["total_matches"]
            or 0
        )

        completed_matches = int(
            match_summary["completed_matches"]
            or 0
        )

        detail_matches = int(
            match_summary["detail_matches"]
            or 0
        )

        latest_matchday = (
            match_summary["latest_matchday"]
        )

        metrics: list[
            DataQualityMetric
        ] = []

        metrics.append(
            self._build_results_metric(
                competition_id=competition_id,
                completed_matches=completed_matches,
            )
        )

        if detail_matches > 0:
            metrics.extend(
                self._build_detail_metrics(
                    competition_id=competition_id,
                    detail_matches=detail_matches,
                )
            )

        overall_percent = (
            self._calculate_overall(
                metrics
            )
        )

        return CompetitionDataQuality(
            competition_id=competition_id,
            competition_name=str(
                competition["competition_name"]
            ),
            season_name=str(
                competition["season_name"]
            ),
            sources=self._detect_sources(
                competition_id
            ),
            total_matches=total_matches,
            completed_matches=completed_matches,
            detail_imported_matches=detail_matches,
            latest_matchday=(
                int(latest_matchday)
                if latest_matchday is not None
                else None
            ),
            metrics=metrics,
            overall_percent=overall_percent,
        )

    def _get_competition(
        self,
        competition_id: int,
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            """
            SELECT
                competitions.name
                    AS competition_name,
                seasons.name
                    AS season_name,
                competitions.schedule_url
                    AS schedule_url
            FROM competitions
            INNER JOIN seasons
                ON seasons.season_id =
                   competitions.season_id
            WHERE competitions.competition_id = ?
            """,
            (
                competition_id,
            ),
        ).fetchone()

    def _get_match_summary(
        self,
        competition_id: int,
    ) -> sqlite3.Row:
        return self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_matches,

                SUM(
                    CASE
                        WHEN home_goals IS NOT NULL
                         AND away_goals IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS completed_matches,

                SUM(
                    CASE
                        WHEN detail_imported = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS detail_matches,

                MAX(
                    CASE
                        WHEN home_goals IS NOT NULL
                         AND away_goals IS NOT NULL
                        THEN matchday
                        ELSE NULL
                    END
                ) AS latest_matchday
            FROM matches
            WHERE competition_id = ?
            """,
            (
                competition_id,
            ),
        ).fetchone()

    def _build_results_metric(
        self,
        competition_id: int,
        completed_matches: int,
    ) -> DataQualityMetric:
        total_matches = self._scalar(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE competition_id = ?
            """,
            (
                competition_id,
            ),
        )

        return self._metric(
            key="results",
            label="Ergebnisse",
            available=completed_matches,
            expected=total_matches,
            note="Spiele mit eingetragenem Endergebnis",
        )

    def _build_detail_metrics(
        self,
        competition_id: int,
        detail_matches: int,
    ) -> list[DataQualityMetric]:
        expected_team_sides = (
            detail_matches * 2
        )

        lineup_team_sides = self._scalar(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    lineups.match_id,
                    lineups.team_id
                FROM lineups
                INNER JOIN matches
                    ON matches.match_id =
                       lineups.match_id
                WHERE
                    matches.competition_id = ?
                    AND matches.detail_imported = 1
            )
            """,
            (
                competition_id,
            ),
        )

        stats_team_sides = self._scalar(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    player_match_stats.match_id,
                    player_match_stats.team_id
                FROM player_match_stats
                INNER JOIN matches
                    ON matches.match_id =
                       player_match_stats.match_id
                WHERE
                    matches.competition_id = ?
                    AND matches.detail_imported = 1
            )
            """,
            (
                competition_id,
            ),
        )

        formation_team_sides = self._scalar(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    match_formations.match_id,
                    match_formations.team_id
                FROM match_formations
                INNER JOIN matches
                    ON matches.match_id =
                       match_formations.match_id
                WHERE
                    matches.competition_id = ?
                    AND matches.detail_imported = 1
            )
            """,
            (
                competition_id,
            ),
        )

        return [
            self._metric(
                key="lineups",
                label="Aufstellungen",
                available=lineup_team_sides,
                expected=expected_team_sides,
                note=(
                    "Mannschaftsseiten mit "
                    "Aufstellungsdaten"
                ),
            ),
            self._metric(
                key="player_stats",
                label="Spielerdetails",
                available=stats_team_sides,
                expected=expected_team_sides,
                note=(
                    "Mannschaftsseiten mit "
                    "Spielerstatistiken"
                ),
            ),
            self._metric(
                key="formations",
                label="Formationen",
                available=formation_team_sides,
                expected=expected_team_sides,
                note=(
                    "Mannschaftsseiten mit "
                    "Formation"
                ),
            ),
            self._build_goal_assignment_metric(
                competition_id
            ),
            self._build_card_assignment_metric(
                competition_id
            ),
        ]

    def _build_goal_assignment_metric(
        self,
        competition_id: int,
    ) -> DataQualityMetric:
        placeholders = ",".join(
            "?"
            for _ in self.GOAL_CODES
        )

        params = (
            competition_id,
            *self.GOAL_CODES,
        )

        row = self.connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_events,
                SUM(
                    CASE
                        WHEN events.player_id
                             IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS assigned_events
            FROM events
            INNER JOIN matches
                ON matches.match_id =
                   events.match_id
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            WHERE
                matches.competition_id = ?
                AND matches.detail_imported = 1
                AND event_types.code
                    IN ({placeholders})
            """,
            params,
        ).fetchone()

        total_events = int(
            row["total_events"]
            or 0
        )

        assigned_events = int(
            row["assigned_events"]
            or 0
        )

        if total_events <= 0:
            return DataQualityMetric(
                key="goal_assignment",
                label="Torschützen",
                available=0,
                expected=0,
                percent=None,
                note=(
                    "Keine Torereignisse in "
                    "Detailspielen vorhanden"
                ),
            )

        return self._metric(
            key="goal_assignment",
            label="Torschützen",
            available=assigned_events,
            expected=total_events,
            note=(
                "Torereignisse mit "
                "Spielerzuordnung"
            ),
        )

    def _build_card_assignment_metric(
        self,
        competition_id: int,
    ) -> DataQualityMetric:
        placeholders = ",".join(
            "?"
            for _ in self.CARD_CODES
        )

        params = (
            competition_id,
            *self.CARD_CODES,
        )

        row = self.connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_events,
                SUM(
                    CASE
                        WHEN events.player_id
                             IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS assigned_events
            FROM events
            INNER JOIN matches
                ON matches.match_id =
                   events.match_id
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            WHERE
                matches.competition_id = ?
                AND matches.detail_imported = 1
                AND event_types.code
                    IN ({placeholders})
            """,
            params,
        ).fetchone()

        total_events = int(
            row["total_events"]
            or 0
        )

        assigned_events = int(
            row["assigned_events"]
            or 0
        )

        if total_events <= 0:
            return DataQualityMetric(
                key="card_assignment",
                label="Karten",
                available=0,
                expected=0,
                percent=None,
                note=(
                    "Keine Kartenereignisse in "
                    "Detailspielen vorhanden"
                ),
            )

        return self._metric(
            key="card_assignment",
            label="Karten",
            available=assigned_events,
            expected=total_events,
            note=(
                "Kartenereignisse mit "
                "Spielerzuordnung"
            ),
        )

    def _detect_sources(
        self,
        competition_id: int,
    ) -> list[str]:
        sources: list[str] = []

        standing_sources = self.connection.execute(
            """
            SELECT DISTINCT source
            FROM standings
            WHERE
                competition_id = ?
                AND source IS NOT NULL
                AND TRIM(source) <> ''
            ORDER BY source
            """,
            (
                competition_id,
            ),
        ).fetchall()

        for row in standing_sources:
            self._append_source(
                sources,
                row["source"],
            )

        competition = self._get_competition(
            competition_id
        )

        if competition is not None:
            schedule_url = str(
                competition["schedule_url"]
                or ""
            ).lower()

            if "fussball.de" in schedule_url:
                self._append_source(
                    sources,
                    "FUSSBALL.DE",
                )

            if "fupa.net" in schedule_url:
                self._append_source(
                    sources,
                    "FuPa",
                )

        external_match_count = self._scalar(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE
                competition_id = ?
                AND external_id IS NOT NULL
                AND TRIM(external_id) <> ''
            """,
            (
                competition_id,
            ),
        )

        if (
            not sources
            and external_match_count > 0
        ):
            sources.append(
                "Importierte Spieldaten"
            )

        if not sources:
            sources.append(
                "Lokal / manuell"
            )

        return sources

    def _append_source(
        self,
        sources: list[str],
        value: object,
    ) -> None:
        source = str(
            value
            or ""
        ).strip()

        if not source:
            return

        normalized = source.lower()

        if normalized in {
            "fussball.de",
            "fussball_de",
            "fussballde",
        }:
            display = "FUSSBALL.DE"
        elif normalized in {
            "fupa",
            "fupa.net",
        }:
            display = "FuPa"
        elif normalized in {
            "manual",
            "manuell",
        }:
            display = "Manuell"
        else:
            display = source

        if display not in sources:
            sources.append(
                display
            )

    def _calculate_overall(
        self,
        metrics: list[DataQualityMetric],
    ) -> float | None:
        percentages = [
            metric.percent
            for metric in metrics
            if metric.percent is not None
        ]

        if not percentages:
            return None

        return round(
            sum(percentages)
            / len(percentages),
            1,
        )

    def _metric(
        self,
        key: str,
        label: str,
        available: int,
        expected: int,
        note: str = "",
    ) -> DataQualityMetric:
        if expected <= 0:
            percent = None
        else:
            percent = round(
                min(
                    100.0,
                    (
                        available
                        / expected
                    )
                    * 100.0,
                ),
                1,
            )

        return DataQualityMetric(
            key=key,
            label=label,
            available=available,
            expected=expected,
            percent=percent,
            note=note,
        )

    def _scalar(
        self,
        sql: str,
        params: tuple = (),
    ) -> int:
        row = self.connection.execute(
            sql,
            params,
        ).fetchone()

        if row is None:
            return 0

        return int(
            row[0]
            or 0
        )
