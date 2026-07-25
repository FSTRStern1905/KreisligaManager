from src.database.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository):

    TABLE = "teams"
    ID = "team_id"

    def get_all(self) -> list[dict]:
        return self.fetch_all(
            self.TABLE,
            order_by="name ASC",
        )

    def get(
        self,
        team_id: int,
    ) -> dict | None:
        return self.fetch_by_id(
            self.TABLE,
            self.ID,
            team_id,
        )

    def get_by_name(
        self,
        club_id: int,
        name: str,
    ) -> dict | None:
        normalized_name = name.strip()

        if club_id <= 0:
            raise ValueError(
                "Ungültige Vereins-ID."
            )

        if not normalized_name:
            return None

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM teams
            WHERE
                club_id = ?
                AND name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (
                club_id,
                normalized_name,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def get_by_external_id(
        self,
        external_id: str,
    ) -> dict | None:
        normalized_external_id = external_id.strip()

        if not normalized_external_id:
            return None

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM teams
            WHERE external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def get_by_club(
        self,
        club_id: int,
    ) -> list[dict]:
        if club_id <= 0:
            raise ValueError(
                "Ungültige Vereins-ID."
            )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM teams
            WHERE club_id = ?
            ORDER BY
                team_number ASC,
                name ASC
            """,
            (club_id,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def add(
        self,
        club_id: int,
        name: str,
        short_name: str = "",
        team_number: int | None = None,
        coach: str = "",
        age_group: str = "",
        external_id: str = "",
    ) -> int:
        normalized_name = name.strip()

        if club_id <= 0:
            raise ValueError(
                "Ungültige Vereins-ID."
            )

        if not normalized_name:
            raise ValueError(
                "Der Mannschaftsname darf nicht leer sein."
            )

        if (
            team_number is not None
            and team_number <= 0
        ):
            raise ValueError(
                "Die Mannschaftsnummer muss größer als 0 sein."
            )

        return self.insert(
            self.TABLE,
            {
                "club_id": club_id,
                "name": normalized_name,
                "short_name": short_name.strip(),
                "team_number": team_number,
                "coach": coach.strip(),
                "age_group": age_group.strip(),
                "external_id": external_id.strip() or None,
            },
        )

    def get_or_create(
        self,
        club_id: int,
        name: str,
        short_name: str = "",
        team_number: int | None = None,
        coach: str = "",
        age_group: str = "",
        external_id: str = "",
    ) -> int:
        normalized_name = name.strip()
        normalized_external_id = external_id.strip()

        if club_id <= 0:
            raise ValueError(
                "Ungültige Vereins-ID."
            )

        if not normalized_name:
            raise ValueError(
                "Der Mannschaftsname darf nicht leer sein."
            )

        existing_team = None

        if normalized_external_id:
            existing_team = self.get_by_external_id(
                normalized_external_id
            )

        if existing_team is None:
            existing_team = self.get_by_name(
                club_id=club_id,
                name=normalized_name,
            )

        if existing_team is not None:
            return int(
                existing_team[self.ID]
            )

        team_id = self.add(
            club_id=club_id,
            name=normalized_name,
            short_name=short_name,
            team_number=team_number,
            coach=coach,
            age_group=age_group,
            external_id=normalized_external_id,
        )

        self.connection.commit()

        return team_id

    def update(
        self,
        team_id: int,
        club_id: int,
        name: str,
        short_name: str = "",
        team_number: int | None = None,
        coach: str = "",
        age_group: str = "",
        external_id: str = "",
    ) -> int:
        normalized_name = name.strip()

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        if club_id <= 0:
            raise ValueError(
                "Ungültige Vereins-ID."
            )

        if not normalized_name:
            raise ValueError(
                "Der Mannschaftsname darf nicht leer sein."
            )

        if (
            team_number is not None
            and team_number <= 0
        ):
            raise ValueError(
                "Die Mannschaftsnummer muss größer als 0 sein."
            )

        return super().update(
            self.TABLE,
            self.ID,
            team_id,
            {
                "club_id": club_id,
                "name": normalized_name,
                "short_name": short_name.strip(),
                "team_number": team_number,
                "coach": coach.strip(),
                "age_group": age_group.strip(),
                "external_id": external_id.strip() or None,
            },
        )

    def delete(
        self,
        team_id: int,
    ) -> int:
        return super().delete(
            self.TABLE,
            self.ID,
            team_id,
        )

    def search(
        self,
        text: str,
    ) -> list[dict]:
        search_text = text.strip()

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                teams.*,
                clubs.name AS club_name
            FROM teams
            INNER JOIN clubs
                ON clubs.club_id = teams.club_id
            WHERE
                teams.name LIKE ?
                OR teams.short_name LIKE ?
                OR teams.coach LIKE ?
                OR clubs.name LIKE ?
            ORDER BY
                teams.name ASC
            """,
            (
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
            ),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]