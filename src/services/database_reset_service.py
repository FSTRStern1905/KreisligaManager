from __future__ import annotations

import sqlite3


class DatabaseResetService:
    RESET_TABLES = (
        "player_match_stats",
        "events",
        "lineups",
        "match_formations",
        "weather",
        "staff",
        "standings",
        "competition_teams",
        "matches",
        "players",
        "referees",
        "stadiums",
        "formations",
        "teams",
        "clubs",
        "competitions",
        "leagues",
        "seasons",
        "associations",
        "countries",
    )

    PRESERVED_TABLES = (
        "event_types",
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def reset(
        self,
    ) -> dict:
        existing_tables = self._get_existing_tables()

        tables_to_reset = [
            table_name
            for table_name in self.RESET_TABLES
            if table_name in existing_tables
        ]

        counts_before = self._get_table_counts(
            tables_to_reset
        )

        foreign_keys_enabled = (
            self._foreign_keys_enabled()
        )

        try:
            self.cursor.execute(
                "PRAGMA foreign_keys = OFF;"
            )

            for table_name in tables_to_reset:
                self.cursor.execute(
                    f'DELETE FROM "{table_name}";'
                )

            self._reset_sequences(
                tables_to_reset
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        finally:
            if foreign_keys_enabled:
                self.cursor.execute(
                    "PRAGMA foreign_keys = ON;"
                )

        counts_after = self._get_table_counts(
            tables_to_reset
        )

        deleted_rows = sum(
            counts_before.values()
        )

        return {
            "tables_reset": len(
                tables_to_reset
            ),
            "rows_deleted": deleted_rows,
            "counts_before": counts_before,
            "counts_after": counts_after,
            "preserved_tables": list(
                self.PRESERVED_TABLES
            ),
        }

    def preview(
        self,
    ) -> dict:
        existing_tables = self._get_existing_tables()

        tables_to_reset = [
            table_name
            for table_name in self.RESET_TABLES
            if table_name in existing_tables
        ]

        counts = self._get_table_counts(
            tables_to_reset
        )

        return {
            "tables": tables_to_reset,
            "counts": counts,
            "total_rows": sum(
                counts.values()
            ),
            "preserved_tables": list(
                self.PRESERVED_TABLES
            ),
        }

    def is_empty(
        self,
    ) -> bool:
        preview = self.preview()

        return preview["total_rows"] == 0

    def _get_existing_tables(
        self,
    ) -> set[str]:
        self.cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE
                type = 'table'
                AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        )

        return {
            str(row[0])
            for row in self.cursor.fetchall()
        }

    def _get_table_counts(
        self,
        table_names: list[str],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}

        for table_name in table_names:
            self.cursor.execute(
                f'SELECT COUNT(*) FROM "{table_name}";'
            )

            row = self.cursor.fetchone()

            counts[table_name] = (
                int(row[0])
                if row is not None
                else 0
            )

        return counts

    def _reset_sequences(
        self,
        table_names: list[str],
    ) -> None:
        if not self._sqlite_sequence_exists():
            return

        placeholders = ", ".join(
            "?"
            for _ in table_names
        )

        if not placeholders:
            return

        self.cursor.execute(
            f"""
            DELETE FROM sqlite_sequence
            WHERE name IN ({placeholders});
            """,
            tuple(table_names),
        )

    def _sqlite_sequence_exists(
        self,
    ) -> bool:
        self.cursor.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE
                type = 'table'
                AND name = 'sqlite_sequence'
            LIMIT 1;
            """
        )

        return self.cursor.fetchone() is not None

    def _foreign_keys_enabled(
        self,
    ) -> bool:
        self.cursor.execute(
            "PRAGMA foreign_keys;"
        )

        row = self.cursor.fetchone()

        if row is None:
            return False

        return bool(
            row[0]
        )