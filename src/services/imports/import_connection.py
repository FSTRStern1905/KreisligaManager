from __future__ import annotations

import sqlite3


class ImportConnection(sqlite3.Connection):
    """
    SQLite-Verbindung für atomare Importvorgänge.

    Während eines Imports dürfen Repositories weiterhin
    connection.commit() aufrufen. Diese Aufrufe werden jedoch
    zurückgehalten, damit der komplette Import als eine einzige
    Transaktion behandelt werden kann.

    Erst final_commit() schreibt die Änderungen dauerhaft.

    Bei einem Fehler kann rollback() dadurch den gesamten
    Import zurücksetzen.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        self._commit_locked = True

    def commit(self) -> None:
        """
        Absichtliche No-Op-Methode während des Imports.

        Repository-interne commit()-Aufrufe dürfen die
        Gesamttransaktion nicht vorzeitig abschließen.
        """
        if not self._commit_locked:
            super().commit()

    def final_commit(self) -> None:
        """
        Schließt den vollständigen Import dauerhaft ab.
        """
        self._commit_locked = False

        try:
            super().commit()
        finally:
            self._commit_locked = True

    def rollback(self) -> None:
        """
        Setzt sämtliche noch nicht final bestätigten
        Änderungen des Importvorgangs zurück.
        """
        super().rollback()

    @property
    def commit_locked(self) -> bool:
        return self._commit_locked


def create_import_connection(
    database_path: str,
) -> ImportConnection:
    connection = sqlite3.connect(
        database_path,
        factory=ImportConnection,
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )

    return connection