from __future__ import annotations

import sqlite3

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class PlayerMatchStatsRepository:
    COLUMNS = """
        player_match_stat_id,
        match_id,
        team_id,
        player_id,
        is_starting,
        was_substituted_in,
        was_substituted_out,
        minute_in,
        minute_out,
        minutes_played,
        goals,
        own_goals,
        assists,
        yellow_cards,
        yellow_red_cards,
        red_cards,
        clean_sheet,
        shirt_number,
        position,
        created_at,
        updated_at
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self._ensure_indexes()

    def get(
        self,
        match_id: int,
        player_id: int,
    ) -> PlayerMatchStat | None:
        self._validate_ids(
            match_id=match_id,
            team_id=1,
            player_id=player_id,
        )

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM player_match_stats
            WHERE
                match_id = ?
                AND player_id = ?
            LIMIT 1
            """,
            (
                match_id,
                player_id,
            ),
        )

        return self._row_to_model(
            self.cursor.fetchone()
        )

    def get_by_id(
        self,
        player_match_stat_id: int,
    ) -> PlayerMatchStat | None:
        if player_match_stat_id <= 0:
            raise ValueError(
                "Ungültige Spielerstatistik-ID."
            )

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM player_match_stats
            WHERE player_match_stat_id = ?
            LIMIT 1
            """,
            (player_match_stat_id,),
        )

        return self._row_to_model(
            self.cursor.fetchone()
        )

    def get_by_match(
        self,
        match_id: int,
    ) -> list[PlayerMatchStat]:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM player_match_stats
            WHERE match_id = ?
            ORDER BY
                team_id,
                is_starting DESC,
                shirt_number,
                player_id
            """,
            (match_id,),
        )

        return [
            self._row_to_model(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_match_and_team(
        self,
        match_id: int,
        team_id: int,
    ) -> list[PlayerMatchStat]:
        self._validate_ids(
            match_id=match_id,
            team_id=team_id,
            player_id=1,
        )

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM player_match_stats
            WHERE
                match_id = ?
                AND team_id = ?
            ORDER BY
                is_starting DESC,
                shirt_number,
                player_id
            """,
            (
                match_id,
                team_id,
            ),
        )

        return [
            self._row_to_model(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_player(
        self,
        player_id: int,
    ) -> list[PlayerMatchStat]:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM player_match_stats
            WHERE player_id = ?
            ORDER BY match_id DESC
            """,
            (player_id,),
        )

        return [
            self._row_to_model(row)
            for row in self.cursor.fetchall()
        ]

    def add(
        self,
        stat: PlayerMatchStat,
        commit: bool = True,
    ) -> int:
        self._validate_stat(stat)

        self.cursor.execute(
            """
            INSERT INTO player_match_stats (
                match_id,
                team_id,
                player_id,
                is_starting,
                was_substituted_in,
                was_substituted_out,
                minute_in,
                minute_out,
                minutes_played,
                goals,
                own_goals,
                assists,
                yellow_cards,
                yellow_red_cards,
                red_cards,
                clean_sheet,
                shirt_number,
                position
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            self._model_to_values(stat),
        )

        if commit:
            self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def update(
        self,
        stat: PlayerMatchStat,
        commit: bool = True,
    ) -> int:
        if stat.player_match_stat_id is None:
            raise ValueError(
                "Die Spielerstatistik besitzt keine ID."
            )

        if stat.player_match_stat_id <= 0:
            raise ValueError(
                "Ungültige Spielerstatistik-ID."
            )

        self._validate_stat(stat)

        self.cursor.execute(
            """
            UPDATE player_match_stats
            SET
                match_id = ?,
                team_id = ?,
                player_id = ?,
                is_starting = ?,
                was_substituted_in = ?,
                was_substituted_out = ?,
                minute_in = ?,
                minute_out = ?,
                minutes_played = ?,
                goals = ?,
                own_goals = ?,
                assists = ?,
                yellow_cards = ?,
                yellow_red_cards = ?,
                red_cards = ?,
                clean_sheet = ?,
                shirt_number = ?,
                position = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE player_match_stat_id = ?
            """,
            (
                *self._model_to_values(stat),
                stat.player_match_stat_id,
            ),
        )

        if self.cursor.rowcount == 0:
            raise ValueError(
                "Spielerstatistik wurde nicht gefunden."
            )

        if commit:
            self.connection.commit()

        return int(
            stat.player_match_stat_id
        )

    def upsert(
        self,
        stat: PlayerMatchStat,
        commit: bool = True,
    ) -> int:
        self._validate_stat(stat)

        self.cursor.execute(
            """
            INSERT INTO player_match_stats (
                match_id,
                team_id,
                player_id,
                is_starting,
                was_substituted_in,
                was_substituted_out,
                minute_in,
                minute_out,
                minutes_played,
                goals,
                own_goals,
                assists,
                yellow_cards,
                yellow_red_cards,
                red_cards,
                clean_sheet,
                shirt_number,
                position
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(match_id, player_id)
            DO UPDATE SET
                team_id = excluded.team_id,
                is_starting = excluded.is_starting,
                was_substituted_in =
                    excluded.was_substituted_in,
                was_substituted_out =
                    excluded.was_substituted_out,
                minute_in = excluded.minute_in,
                minute_out = excluded.minute_out,
                minutes_played = excluded.minutes_played,
                goals = excluded.goals,
                own_goals = excluded.own_goals,
                assists = excluded.assists,
                yellow_cards = excluded.yellow_cards,
                yellow_red_cards =
                    excluded.yellow_red_cards,
                red_cards = excluded.red_cards,
                clean_sheet = excluded.clean_sheet,
                shirt_number = excluded.shirt_number,
                position = excluded.position,
                updated_at = CURRENT_TIMESTAMP
            """,
            self._model_to_values(stat),
        )

        existing = self.get(
            match_id=stat.match_id,
            player_id=stat.player_id,
        )

        if existing is None:
            raise RuntimeError(
                "Spielerstatistik konnte nicht gespeichert werden."
            )

        if commit:
            self.connection.commit()

        return int(
            existing.player_match_stat_id
        )

    def replace_match(
        self,
        match_id: int,
        stats: list[PlayerMatchStat],
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        for stat in stats:
            if stat.match_id != match_id:
                raise ValueError(
                    "Eine Spielerstatistik gehört nicht "
                    "zum angegebenen Spiel."
                )

        try:
            self.delete_by_match(
                match_id=match_id,
                commit=False,
            )

            inserted = 0

            for stat in stats:
                stat.player_match_stat_id = None

                self.add(
                    stat=stat,
                    commit=False,
                )

                inserted += 1

            self.connection.commit()

            return inserted

        except Exception:
            self.connection.rollback()
            raise

    def delete(
        self,
        player_match_stat_id: int,
        commit: bool = True,
    ) -> int:
        if player_match_stat_id <= 0:
            raise ValueError(
                "Ungültige Spielerstatistik-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM player_match_stats
            WHERE player_match_stat_id = ?
            """,
            (player_match_stat_id,),
        )

        deleted = self.cursor.rowcount

        if commit:
            self.connection.commit()

        return deleted

    def delete_by_match(
        self,
        match_id: int,
        commit: bool = True,
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM player_match_stats
            WHERE match_id = ?
            """,
            (match_id,),
        )

        deleted = self.cursor.rowcount

        if commit:
            self.connection.commit()

        return deleted

    def count_by_match(
        self,
        match_id: int,
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM player_match_stats
            WHERE match_id = ?
            """,
            (match_id,),
        )

        return int(
            self.cursor.fetchone()[0]
        )

    def count_by_player(
        self,
        player_id: int,
    ) -> int:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM player_match_stats
            WHERE player_id = ?
            """,
            (player_id,),
        )

        return int(
            self.cursor.fetchone()[0]
        )

    def _ensure_indexes(
        self,
    ) -> None:
        self.cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_player_match_stats_unique_player
            ON player_match_stats(
                match_id,
                player_id
            )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_player_match_stats_match_team
            ON player_match_stats(
                match_id,
                team_id
            )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_player_match_stats_player
            ON player_match_stats(
                player_id
            )
            """
        )

        self.connection.commit()

    def _validate_stat(
        self,
        stat: PlayerMatchStat,
    ) -> None:
        self._validate_ids(
            match_id=stat.match_id,
            team_id=stat.team_id,
            player_id=stat.player_id,
        )

        self._validate_minute(
            value=stat.minute_in,
            field_name="Einwechselminute",
        )

        self._validate_minute(
            value=stat.minute_out,
            field_name="Auswechselminute",
        )

        if stat.minutes_played < 0:
            raise ValueError(
                "Die Spielminuten dürfen nicht negativ sein."
            )

        if (
            stat.minute_in is not None
            and stat.minute_out is not None
            and stat.minute_out < stat.minute_in
        ):
            raise ValueError(
                "Die Auswechselminute darf nicht vor "
                "der Einwechselminute liegen."
            )

        counters = {
            "Tore": stat.goals,
            "Eigentore": stat.own_goals,
            "Vorlagen": stat.assists,
            "Gelbe Karten": stat.yellow_cards,
            "Gelb-Rote Karten": stat.yellow_red_cards,
            "Rote Karten": stat.red_cards,
        }

        for name, value in counters.items():
            if value < 0:
                raise ValueError(
                    f"{name} dürfen nicht negativ sein."
                )

        if (
            stat.shirt_number is not None
            and stat.shirt_number < 0
        ):
            raise ValueError(
                "Die Rückennummer darf nicht negativ sein."
            )

    @staticmethod
    def _validate_ids(
        match_id: int,
        team_id: int,
        player_id: int,
    ) -> None:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

    @staticmethod
    def _validate_minute(
        value: int | None,
        field_name: str,
    ) -> None:
        if value is not None and value < 0:
            raise ValueError(
                f"{field_name} darf nicht negativ sein."
            )

    @staticmethod
    def _model_to_values(
        stat: PlayerMatchStat,
    ) -> tuple:
        return (
            stat.match_id,
            stat.team_id,
            stat.player_id,
            int(stat.is_starting),
            int(stat.was_substituted_in),
            int(stat.was_substituted_out),
            stat.minute_in,
            stat.minute_out,
            stat.minutes_played,
            stat.goals,
            stat.own_goals,
            stat.assists,
            stat.yellow_cards,
            stat.yellow_red_cards,
            stat.red_cards,
            int(stat.clean_sheet),
            stat.shirt_number,
            stat.position.strip(),
        )

    @staticmethod
    def _row_to_model(
        row: sqlite3.Row | tuple | None,
    ) -> PlayerMatchStat | None:
        if row is None:
            return None

        return PlayerMatchStat(
            player_match_stat_id=int(row[0]),
            match_id=int(row[1]),
            team_id=int(row[2]),
            player_id=int(row[3]),
            is_starting=bool(row[4]),
            was_substituted_in=bool(row[5]),
            was_substituted_out=bool(row[6]),
            minute_in=row[7],
            minute_out=row[8],
            minutes_played=int(row[9]),
            goals=int(row[10]),
            own_goals=int(row[11]),
            assists=int(row[12]),
            yellow_cards=int(row[13]),
            yellow_red_cards=int(row[14]),
            red_cards=int(row[15]),
            clean_sheet=bool(row[16]),
            shirt_number=row[17],
            position=row[18] or "",
            created_at=row[19],
            updated_at=row[20],
        )