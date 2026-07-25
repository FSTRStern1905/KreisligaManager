import sqlite3

from src.database.models.association import Association


class AssociationRepository:

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_by_name(
        self,
        name: str,
    ) -> Association | None:

        self.cursor.execute(
            """
            SELECT
                association_id,
                name,
                country,
                short_name,
                active
            FROM associations
            WHERE name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (name.strip(),),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return Association(
            association_id=row[0],
            name=row[1],
            country=row[2],
            short_name=row[3] or "",
            active=bool(row[4]),
        )

    def add(
        self,
        association: Association,
    ) -> int:

        self.cursor.execute(
            """
            INSERT INTO associations
            (
                name,
                country,
                short_name,
                active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                association.name,
                association.country,
                association.short_name,
                int(association.active),
            ),
        )

        self.connection.commit()

        return int(self.cursor.lastrowid)

    def get_or_create(
        self,
        association: Association,
    ) -> int:

        existing = self.get_by_name(
            association.name
        )

        if existing is not None:
            return int(existing.association_id)

        return self.add(association)