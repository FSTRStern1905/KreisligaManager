import sqlite3

from src.database.models.association import Association


class AssociationRepository:

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def _get_or_create_country_id(
        self,
        country_name: str,
    ) -> int:
        normalized_name = country_name.strip() or "Deutschland"

        self.cursor.execute(
            """
            SELECT country_id
            FROM countries
            WHERE name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (normalized_name,),
        )

        row = self.cursor.fetchone()

        if row is not None:
            return int(row[0])

        iso_code = "DE" if normalized_name.casefold() == "deutschland" else ""

        self.cursor.execute(
            """
            INSERT INTO countries (name, iso_code)
            VALUES (?, ?)
            """,
            (normalized_name, iso_code),
        )

        self.connection.commit()
        return int(self.cursor.lastrowid)

    def get_by_name(
        self,
        name: str,
    ) -> Association | None:
        normalized_name = name.strip()

        if not normalized_name:
            return None

        self.cursor.execute(
            """
            SELECT
                associations.association_id,
                associations.country_id,
                associations.name,
                associations.short_name,
                countries.name
            FROM associations
            INNER JOIN countries
                ON countries.country_id = associations.country_id
            WHERE associations.name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (normalized_name,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return Association(
            association_id=row[0],
            country_id=row[1],
            name=row[2],
            short_name=row[3] or "",
            country=row[4] or "Deutschland",
        )

    def add(
        self,
        association: Association,
    ) -> int:
        normalized_name = association.name.strip()

        if not normalized_name:
            raise ValueError(
                "Der Verbandsname darf nicht leer sein."
            )

        country_id = association.country_id

        if country_id is None:
            country_id = self._get_or_create_country_id(
                association.country
            )

        self.cursor.execute(
            """
            INSERT INTO associations
            (
                country_id,
                name,
                short_name
            )
            VALUES (?, ?, ?)
            """,
            (
                country_id,
                normalized_name,
                association.short_name.strip(),
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
            if existing.association_id is None:
                raise ValueError(
                    "Der vorhandene Verband besitzt keine ID."
                )

            return int(existing.association_id)

        return self.add(association)
