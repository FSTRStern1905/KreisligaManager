from src.database.repository import Repository


class ClubImportService:
    def __init__(
        self,
        repository: Repository,
    ):
        self.repository = repository

    def import_clubs(
        self,
        clubs: list[dict],
    ) -> tuple[int, int]:
        imported = 0
        skipped = 0

        for club in clubs:
            club_id = club["club_id"].strip()

            existing = self.repository.find_one(
                "club",
                club_id=club_id,
            )

            if existing:
                skipped += 1
                continue

            self.repository.insert(
                "club",
                {
                    "club_id": club_id,
                    "club_name": club["club_name"].strip(),
                    "club_short_name": club["club_short_name"].strip(),
                    "association": club["association"].strip(),
                    "country": club["country"].strip(),
                },
            )

            imported += 1

        return imported, skipped