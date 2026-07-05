"""
database.py
------------

Zentrale SQLite-Datenbankverwaltung
KreisligaManager

Autor: Stefan Frick
"""

from pathlib import Path
import sqlite3
from sqlite3 import Connection
from typing import Optional


class Database:

    def __init__(self):

        self.db_folder = Path("data/database")
        self.db_folder.mkdir(parents=True, exist_ok=True)

        self.db_path = self.db_folder / "kreisligamanager.db"

        self.connection: Optional[Connection] = None

    def connect(self):

        if self.connection is None:

            self.connection = sqlite3.connect(self.db_path)

            self.connection.row_factory = sqlite3.Row

        return self.connection

    def cursor(self):

        return self.connect().cursor()

    def execute(self, sql: str, params: tuple = ()):

        cur = self.cursor()

        cur.execute(sql, params)

        self.connection.commit()

        return cur

    def query(self, sql: str, params: tuple = ()):

        cur = self.cursor()

        cur.execute(sql, params)

        return cur.fetchall()

    def executescript(self, script: str):

        self.connect().executescript(script)

        self.connection.commit()

    def close(self):

        if self.connection:

            self.connection.close()

            self.connection = None