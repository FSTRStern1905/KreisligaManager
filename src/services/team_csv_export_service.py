from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path
from typing import Any


class TeamCsvExportService:
    """CSV-Export aller verfügbaren Mannschaftsdaten eines Wettbewerbs."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def export_team(
        self,
        competition_id: int,
        team_id: int,
        destination_root: str | Path = "exports/csv",
    ) -> Path:
        if competition_id <= 0:
            raise ValueError("Ungültige Wettbewerb-ID.")
        if team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")

        context = self._load_context(competition_id, team_id)

        destination = (
            Path(destination_root)
            / self._safe_name(context["season_name"])
            / self._safe_name(context["competition_name"])
            / self._safe_name(context["team_name"])
        )
        destination.mkdir(parents=True, exist_ok=True)

        match_ids = self._load_match_ids(competition_id, team_id)
        player_ids = self._load_player_ids(team_id, match_ids)

        self._export_metadata(destination, context, len(match_ids), len(player_ids))
        self._export_team(destination, team_id)
        self._export_competition(destination, competition_id)
        self._export_matches(destination, competition_id, team_id)
        self._export_players(destination, player_ids)
        self._export_table_by_matches(
            destination,
            "player_match_stats",
            "player_match_stats.csv",
            match_ids,
            {"team_id": team_id},
        )
        self._export_events(destination, match_ids, team_id)
        self._export_table_by_matches(
            destination,
            "lineups",
            "lineups.csv",
            match_ids,
            {"team_id": team_id},
        )
        self._export_table_by_matches(
            destination,
            "match_formations",
            "match_formations.csv",
            match_ids,
            {"team_id": team_id},
        )
        self._export_table_by_matches(
            destination,
            "weather",
            "weather.csv",
            match_ids,
        )
        self._export_table_filtered(
            destination,
            "standings",
            "standings.csv",
            {"competition_id": competition_id, "team_id": team_id},
        )
        self._export_team_season_metrics(
            destination,
            competition_id,
            team_id,
            int(context["season_id"]),
        )
        self._export_table_filtered(
            destination,
            "staff",
            "staff.csv",
            {"team_id": team_id},
        )
        self._export_table_filtered(
            destination,
            "competition_teams",
            "competition_team.csv",
            {"competition_id": competition_id, "team_id": team_id},
        )

        return destination

    def _load_context(self, competition_id: int, team_id: int) -> sqlite3.Row:
        row = self.connection.execute(
            """
            SELECT
                c.competition_id,
                c.name AS competition_name,
                c.season_id,
                s.name AS season_name,
                c.league_id,
                l.name AS league_name,
                t.team_id,
                t.name AS team_name,
                t.club_id,
                cl.name AS club_name
            FROM competitions AS c
            INNER JOIN seasons AS s
                ON s.season_id = c.season_id
            LEFT JOIN leagues AS l
                ON l.league_id = c.league_id
            INNER JOIN competition_teams AS ct
                ON ct.competition_id = c.competition_id
            INNER JOIN teams AS t
                ON t.team_id = ct.team_id
            LEFT JOIN clubs AS cl
                ON cl.club_id = t.club_id
            WHERE
                c.competition_id = ?
                AND t.team_id = ?
            LIMIT 1
            """,
            (competition_id, team_id),
        ).fetchone()

        if row is None:
            raise ValueError("Mannschaft ist dem Wettbewerb nicht zugeordnet.")

        return row

    def _load_match_ids(self, competition_id: int, team_id: int) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT match_id
            FROM matches
            WHERE
                competition_id = ?
                AND (home_team_id = ? OR away_team_id = ?)
            ORDER BY matchday, match_date, kickoff_time, match_id
            """,
            (competition_id, team_id, team_id),
        ).fetchall()

        return [int(row["match_id"]) for row in rows]

    def _load_player_ids(self, team_id: int, match_ids: list[int]) -> list[int]:
        player_ids: set[int] = set()

        if self._table_exists("players") and "team_id" in self._table_columns("players"):
            rows = self.connection.execute(
                "SELECT player_id FROM players WHERE team_id = ?",
                (team_id,),
            ).fetchall()
            player_ids.update(
                int(row["player_id"])
                for row in rows
                if row["player_id"] is not None
            )

        if not match_ids:
            return sorted(player_ids)

        placeholders = self._placeholders(len(match_ids))

        for table_name in ("lineups", "player_match_stats", "events"):
            if not self._table_exists(table_name):
                continue

            columns = self._table_columns(table_name)
            if "match_id" not in columns or "player_id" not in columns:
                continue

            sql = (
                f"SELECT DISTINCT player_id FROM {self._quote_identifier(table_name)} "
                f"WHERE match_id IN ({placeholders}) AND player_id IS NOT NULL"
            )
            params: list[Any] = list(match_ids)

            if "team_id" in columns:
                sql += " AND team_id = ?"
                params.append(team_id)

            rows = self.connection.execute(sql, tuple(params)).fetchall()
            player_ids.update(
                int(row["player_id"])
                for row in rows
                if row["player_id"] is not None
            )

        return sorted(player_ids)

    def _export_metadata(
        self,
        destination: Path,
        context: sqlite3.Row,
        match_count: int,
        player_count: int,
    ) -> None:
        rows = [
            {"key": "competition_id", "value": context["competition_id"]},
            {"key": "competition_name", "value": context["competition_name"]},
            {"key": "season_id", "value": context["season_id"]},
            {"key": "season_name", "value": context["season_name"]},
            {"key": "league_id", "value": context["league_id"]},
            {"key": "league_name", "value": context["league_name"]},
            {"key": "team_id", "value": context["team_id"]},
            {"key": "team_name", "value": context["team_name"]},
            {"key": "club_id", "value": context["club_id"]},
            {"key": "club_name", "value": context["club_name"]},
            {"key": "match_count", "value": match_count},
            {"key": "player_count", "value": player_count},
        ]
        self._write_csv(destination / "00_metadata.csv", rows, ["key", "value"])

    def _export_team(self, destination: Path, team_id: int) -> None:
        rows = self.connection.execute(
            """
            SELECT
                t.*,
                cl.name AS club_name,
                cl.short_name AS club_short_name,
                cl.city AS club_city
            FROM teams AS t
            LEFT JOIN clubs AS cl ON cl.club_id = t.club_id
            WHERE t.team_id = ?
            """,
            (team_id,),
        ).fetchall()
        self._write_rows(destination / "team.csv", rows)

    def _export_competition(self, destination: Path, competition_id: int) -> None:
        rows = self.connection.execute(
            """
            SELECT
                c.*,
                s.name AS season_name,
                s.start_date AS season_start_date,
                s.end_date AS season_end_date,
                l.name AS league_name,
                l.level AS league_level
            FROM competitions AS c
            INNER JOIN seasons AS s ON s.season_id = c.season_id
            LEFT JOIN leagues AS l ON l.league_id = c.league_id
            WHERE c.competition_id = ?
            """,
            (competition_id,),
        ).fetchall()
        self._write_rows(destination / "competition.csv", rows)

    def _export_matches(
        self,
        destination: Path,
        competition_id: int,
        team_id: int,
    ) -> None:
        rows = self.connection.execute(
            """
            SELECT
                m.*,
                home.name AS home_team_name,
                away.name AS away_team_name,
                CASE WHEN m.home_team_id = ? THEN 'home' ELSE 'away' END
                    AS selected_team_role,
                CASE WHEN m.home_team_id = ? THEN away.name ELSE home.name END
                    AS opponent_name
            FROM matches AS m
            INNER JOIN teams AS home ON home.team_id = m.home_team_id
            INNER JOIN teams AS away ON away.team_id = m.away_team_id
            WHERE
                m.competition_id = ?
                AND (m.home_team_id = ? OR m.away_team_id = ?)
            ORDER BY m.matchday, m.match_date, m.kickoff_time, m.match_id
            """,
            (team_id, team_id, competition_id, team_id, team_id),
        ).fetchall()
        self._write_rows(destination / "matches.csv", rows)

    def _export_players(self, destination: Path, player_ids: list[int]) -> None:
        if not self._table_exists("players"):
            return

        if not player_ids:
            self._write_empty_table_csv(destination, "players", "players.csv")
            return

        placeholders = self._placeholders(len(player_ids))
        rows = self.connection.execute(
            f"""
            SELECT *
            FROM players
            WHERE player_id IN ({placeholders})
            ORDER BY last_name, first_name, player_id
            """,
            tuple(player_ids),
        ).fetchall()
        self._write_rows(destination / "players.csv", rows)

    def _export_events(
        self,
        destination: Path,
        match_ids: list[int],
        selected_team_id: int,
    ) -> None:
        if not self._table_exists("events"):
            return

        if not match_ids:
            self._write_empty_table_csv(destination, "events", "events.csv")
            return

        placeholders = self._placeholders(len(match_ids))
        rows = self.connection.execute(
            f"""
            SELECT
                e.*,
                et.code AS event_type_code,
                et.name AS event_type_name,
                p.first_name AS player_first_name,
                p.last_name AS player_last_name,
                rp.first_name AS related_player_first_name,
                rp.last_name AS related_player_last_name,
                t.name AS event_team_name,
                CASE
                    WHEN e.team_id = ? THEN 'own'
                    WHEN e.team_id IS NULL THEN 'unknown'
                    ELSE 'opponent'
                END AS relation_to_selected_team
            FROM events AS e
            LEFT JOIN event_types AS et ON et.event_type_id = e.event_type_id
            LEFT JOIN players AS p ON p.player_id = e.player_id
            LEFT JOIN players AS rp ON rp.player_id = e.related_player_id
            LEFT JOIN teams AS t ON t.team_id = e.team_id
            WHERE e.match_id IN ({placeholders})
            ORDER BY e.match_id, e.minute, e.second, e.event_id
            """,
            (selected_team_id, *match_ids),
        ).fetchall()
        self._write_rows(destination / "events.csv", rows)

    def _export_team_season_metrics(
        self,
        destination: Path,
        competition_id: int,
        team_id: int,
        season_id: int,
    ) -> None:
        table_name = "team_season_metrics"
        if not self._table_exists(table_name):
            return

        columns = self._table_columns(table_name)
        filters: dict[str, Any] = {}

        if "competition_id" in columns:
            filters["competition_id"] = competition_id
        if "team_id" in columns:
            filters["team_id"] = team_id
        if "season_id" in columns and "competition_id" not in columns:
            filters["season_id"] = season_id

        self._export_table_filtered(
            destination,
            table_name,
            "team_season_metrics.csv",
            filters,
        )

    def _export_table_by_matches(
        self,
        destination: Path,
        table_name: str,
        file_name: str,
        match_ids: list[int],
        filters: dict[str, Any] | None = None,
    ) -> None:
        if not self._table_exists(table_name):
            return

        columns = self._table_columns(table_name)
        if "match_id" not in columns:
            return

        if not match_ids:
            self._write_empty_table_csv(destination, table_name, file_name)
            return

        placeholders = self._placeholders(len(match_ids))
        sql = (
            f"SELECT * FROM {self._quote_identifier(table_name)} "
            f"WHERE match_id IN ({placeholders})"
        )
        params: list[Any] = list(match_ids)

        for column, value in (filters or {}).items():
            if column not in columns:
                continue
            sql += f" AND {self._quote_identifier(column)} = ?"
            params.append(value)

        sql += " ORDER BY match_id"
        rows = self.connection.execute(sql, tuple(params)).fetchall()
        self._write_rows(destination / file_name, rows, columns)

    def _export_table_filtered(
        self,
        destination: Path,
        table_name: str,
        file_name: str,
        filters: dict[str, Any],
    ) -> None:
        if not self._table_exists(table_name):
            return

        columns = self._table_columns(table_name)
        usable = {key: value for key, value in filters.items() if key in columns}

        sql = f"SELECT * FROM {self._quote_identifier(table_name)}"
        params: list[Any] = []

        if usable:
            clauses = []
            for column, value in usable.items():
                clauses.append(f"{self._quote_identifier(column)} = ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(clauses)

        rows = self.connection.execute(sql, tuple(params)).fetchall()
        self._write_rows(destination / file_name, rows, columns)

    def _write_empty_table_csv(
        self,
        destination: Path,
        table_name: str,
        file_name: str,
    ) -> None:
        self._write_csv(
            destination / file_name,
            [],
            self._table_columns(table_name),
        )

    def _write_rows(
        self,
        file_path: Path,
        rows: list[sqlite3.Row],
        fallback_columns: list[str] | None = None,
    ) -> None:
        if rows:
            fieldnames = list(rows[0].keys())
            dictionaries = [dict(row) for row in rows]
        else:
            fieldnames = fallback_columns or []
            dictionaries = []

        self._write_csv(file_path, dictionaries, fieldnames)

    @staticmethod
    def _write_csv(
        file_path: Path,
        rows: list[dict[str, Any]],
        fieldnames: list[str],
    ) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
                delimiter=";",
                extrasaction="ignore",
            )

            if fieldnames:
                writer.writeheader()

            for row in rows:
                writer.writerow(
                    {key: "" if value is None else value for key, value in row.items()}
                )

    def _table_exists(self, table_name: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            LIMIT 1
            """,
            (table_name,),
        ).fetchone()
        return row is not None

    def _table_columns(self, table_name: str) -> list[str]:
        rows = self.connection.execute(
            f"PRAGMA table_info({self._quote_identifier(table_name)})"
        ).fetchall()
        return [str(row["name"]) for row in rows]

    @staticmethod
    def _placeholders(count: int) -> str:
        return ",".join("?" for _ in range(count))

    @staticmethod
    def _quote_identifier(value: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError(f"Ungültiger SQL-Bezeichner: {value}")
        return f'"{value}"'

    @staticmethod
    def _safe_name(value: Any) -> str:
        text = str(value or "").strip()
        text = re.sub(r'[<>:"/\\|?*]+', "_", text)
        text = re.sub(r"\s+", " ", text)
        text = text.rstrip(". ")
        return text or "unbekannt"
