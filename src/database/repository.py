import sqlite3


class Repository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def insert(self, table: str, values: dict) -> int:
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        self.cursor.execute(sql, tuple(values.values()))
        self.connection.commit()

        return self.cursor.lastrowid

    def fetch_all(self, table: str, where: str = None, params: tuple = ()) -> list[dict]:
        sql = f"SELECT * FROM {table}"

        if where:
            sql += f" WHERE {where}"

        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

    def fetch_one(self, table: str, where: str, params: tuple = ()) -> dict | None:
        sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"

        self.cursor.execute(sql, params)
        row = self.cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def update(self, table: str, values: dict, where: str, params: tuple = ()) -> int:
        set_clause = ", ".join([f"{column} = ?" for column in values.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        all_params = tuple(values.values()) + params

        self.cursor.execute(sql, all_params)
        self.connection.commit()

        return self.cursor.rowcount

    def delete(self, table: str, where: str, params: tuple = ()) -> int:
        sql = f"DELETE FROM {table} WHERE {where}"

        self.cursor.execute(sql, params)
        self.connection.commit()

        return self.cursor.rowcount

    def count(self, table: str) -> int:
        sql = f"SELECT COUNT(*) AS total FROM {table}"

        self.cursor.execute(sql)
        row = self.cursor.fetchone()

        return row["total"]

    def exists(self, table: str, where: str, params: tuple = ()) -> bool:
        sql = f"SELECT 1 FROM {table} WHERE {where} LIMIT 1"

        self.cursor.execute(sql, params)
        row = self.cursor.fetchone()

        return row is not None