import sqlite3
from typing import Any


class BaseRepository:
    """
    Basisklasse für alle Repositories.
    Enthält allgemeine CRUD-Funktionen.
    """

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def fetch_all(self, table: str, order_by: str | None = None) -> list[dict]:
        sql = f"SELECT * FROM {table}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        cursor = self.connection.cursor()
        cursor.execute(sql)

        return [dict(row) for row in cursor.fetchall()]

    def fetch_by_id(
        self,
        table: str,
        id_column: str,
        record_id: int
    ) -> dict | None:

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            SELECT *
            FROM {table}
            WHERE {id_column}=?
            LIMIT 1
            """,
            (record_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def insert(self, table: str, values: dict[str, Any]) -> int:

        columns = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))

        sql = f"""
        INSERT INTO {table}
        ({columns})
        VALUES
        ({placeholders})
        """

        cursor = self.connection.cursor()

        cursor.execute(
            sql,
            tuple(values.values())
        )

        self.connection.commit()

        return cursor.lastrowid

    def update(
        self,
        table: str,
        id_column: str,
        record_id: int,
        values: dict[str, Any]
    ) -> int:

        set_clause = ", ".join(
            [f"{column}=?" for column in values.keys()]
        )

        sql = f"""
        UPDATE {table}
        SET {set_clause}
        WHERE {id_column}=?
        """

        params = tuple(values.values()) + (record_id,)

        cursor = self.connection.cursor()

        cursor.execute(
            sql,
            params
        )

        self.connection.commit()

        return cursor.rowcount

    def delete(
        self,
        table: str,
        id_column: str,
        record_id: int
    ) -> int:

        sql = f"""
        DELETE FROM {table}
        WHERE {id_column}=?
        """

        cursor = self.connection.cursor()

        cursor.execute(
            sql,
            (record_id,)
        )

        self.connection.commit()

        return cursor.rowcount

    def count(self, table: str) -> int:

        cursor = self.connection.cursor()

        cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        )

        return cursor.fetchone()[0]

    def exists(
        self,
        table: str,
        column: str,
        value: Any
    ) -> bool:

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            SELECT 1
            FROM {table}
            WHERE {column}=?
            LIMIT 1
            """,
            (value,)
        )

        return cursor.fetchone() is not None