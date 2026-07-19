import re
import sqlite3
from typing import Any


class Repository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def insert(
        self,
        table: str,
        values: dict[str, Any],
    ) -> int:
        self._validate_identifier(table)

        if not values:
            raise ValueError(
                "Für den INSERT wurden keine Werte übergeben."
            )

        self._validate_identifiers(values.keys())

        columns = ", ".join(values.keys())
        placeholders = ", ".join(
            ["?"] * len(values)
        )

        sql = (
            f"INSERT INTO {table} "
            f"({columns}) "
            f"VALUES ({placeholders})"
        )

        self.cursor.execute(
            sql,
            tuple(values.values()),
        )
        self.connection.commit()

        return self.cursor.lastrowid

    def fetch_all(
        self,
        table: str,
        where: str | None = None,
        params: tuple = (),
    ) -> list[dict]:
        self._validate_identifier(table)

        sql = f"SELECT * FROM {table}"

        if where:
            sql += f" WHERE {where}"

        self.cursor.execute(
            sql,
            params,
        )

        rows = self.cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def fetch_one(
        self,
        table: str,
        where: str,
        params: tuple = (),
    ) -> dict | None:
        self._validate_identifier(table)

        sql = (
            f"SELECT * FROM {table} "
            f"WHERE {where} "
            f"LIMIT 1"
        )

        self.cursor.execute(
            sql,
            params,
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def find_all(
        self,
        table: str,
        **filters: Any,
    ) -> list[dict]:
        where, params = self._build_filters(
            filters
        )

        return self.fetch_all(
            table=table,
            where=where,
            params=params,
        )

    def find_one(
        self,
        table: str,
        **filters: Any,
    ) -> dict | None:
        where, params = self._build_filters(
            filters
        )

        if not where:
            raise ValueError(
                "find_one benötigt mindestens einen Filter."
            )

        return self.fetch_one(
            table=table,
            where=where,
            params=params,
        )

    def update(
        self,
        table: str,
        values: dict[str, Any],
        where: str,
        params: tuple = (),
    ) -> int:
        self._validate_identifier(table)

        if not values:
            raise ValueError(
                "Für das UPDATE wurden keine Werte übergeben."
            )

        if not where:
            raise ValueError(
                "Ein UPDATE ohne WHERE-Bedingung ist nicht erlaubt."
            )

        self._validate_identifiers(values.keys())

        set_clause = ", ".join(
            f"{column} = ?"
            for column in values
        )

        sql = (
            f"UPDATE {table} "
            f"SET {set_clause} "
            f"WHERE {where}"
        )

        all_params = (
            tuple(values.values())
            + params
        )

        self.cursor.execute(
            sql,
            all_params,
        )
        self.connection.commit()

        return self.cursor.rowcount

    def update_by(
        self,
        table: str,
        values: dict[str, Any],
        **filters: Any,
    ) -> int:
        where, params = self._build_filters(
            filters
        )

        if not where:
            raise ValueError(
                "update_by benötigt mindestens einen Filter."
            )

        return self.update(
            table=table,
            values=values,
            where=where,
            params=params,
        )

    def delete(
        self,
        table: str,
        where: str,
        params: tuple = (),
    ) -> int:
        self._validate_identifier(table)

        if not where:
            raise ValueError(
                "Ein DELETE ohne WHERE-Bedingung ist nicht erlaubt."
            )

        sql = (
            f"DELETE FROM {table} "
            f"WHERE {where}"
        )

        self.cursor.execute(
            sql,
            params,
        )
        self.connection.commit()

        return self.cursor.rowcount

    def delete_by(
        self,
        table: str,
        **filters: Any,
    ) -> int:
        where, params = self._build_filters(
            filters
        )

        if not where:
            raise ValueError(
                "delete_by benötigt mindestens einen Filter."
            )

        return self.delete(
            table=table,
            where=where,
            params=params,
        )

    def count(
        self,
        table: str,
        where: str | None = None,
        params: tuple = (),
    ) -> int:
        self._validate_identifier(table)

        sql = (
            f"SELECT COUNT(*) AS total "
            f"FROM {table}"
        )

        if where:
            sql += f" WHERE {where}"

        self.cursor.execute(
            sql,
            params,
        )

        row = self.cursor.fetchone()

        return int(row["total"])

    def count_by(
        self,
        table: str,
        **filters: Any,
    ) -> int:
        where, params = self._build_filters(
            filters
        )

        return self.count(
            table=table,
            where=where,
            params=params,
        )

    def exists(
        self,
        table: str,
        where: str | None = None,
        params: tuple = (),
        **filters: Any,
    ) -> bool:
        self._validate_identifier(table)

        if filters:
            if where:
                raise ValueError(
                    "where und Filter können nicht gleichzeitig "
                    "verwendet werden."
                )

            where, params = self._build_filters(
                filters
            )

        if not where:
            raise ValueError(
                "exists benötigt mindestens eine Bedingung."
            )

        sql = (
            f"SELECT 1 FROM {table} "
            f"WHERE {where} "
            f"LIMIT 1"
        )

        self.cursor.execute(
            sql,
            params,
        )

        return self.cursor.fetchone() is not None

    def upsert(
        self,
        table: str,
        values: dict[str, Any],
        key: str,
    ) -> tuple[str, int]:
        self._validate_identifier(table)
        self._validate_identifier(key)

        if key not in values:
            raise ValueError(
                f"Der Schlüssel '{key}' fehlt in den Werten."
            )

        key_value = values[key]

        existing = self.find_one(
            table,
            **{
                key: key_value,
            },
        )

        if existing:
            update_values = {
                column: value
                for column, value in values.items()
                if column != key
            }

            if not update_values:
                return "unchanged", 0

            affected_rows = self.update_by(
                table,
                update_values,
                **{
                    key: key_value,
                },
            )

            return "updated", affected_rows

        row_id = self.insert(
            table,
            values,
        )

        return "inserted", row_id

    def _build_filters(
        self,
        filters: dict[str, Any],
    ) -> tuple[str | None, tuple]:
        if not filters:
            return None, ()

        self._validate_identifiers(
            filters.keys()
        )

        clauses: list[str] = []
        params: list[Any] = []

        for column, value in filters.items():
            if value is None:
                clauses.append(
                    f"{column} IS NULL"
                )
            else:
                clauses.append(
                    f"{column} = ?"
                )
                params.append(value)

        where = " AND ".join(clauses)

        return where, tuple(params)

    def _validate_identifiers(
        self,
        identifiers,
    ) -> None:
        for identifier in identifiers:
            self._validate_identifier(
                identifier
            )

    @staticmethod
    def _validate_identifier(
        identifier: str,
    ) -> None:
        if not isinstance(identifier, str):
            raise TypeError(
                "Tabellen- und Spaltennamen müssen Text sein."
            )

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            identifier,
        ):
            raise ValueError(
                f"Ungültiger Tabellen- oder Spaltenname: "
                f"{identifier}"
            )