from dataclasses import dataclass


@dataclass(slots=True)
class ImportResult:
    competitions_created: int = 0
    clubs_created: int = 0
    teams_created: int = 0
    matches_created: int = 0
    matches_updated: int = 0

    @property
    def total_changes(self) -> int:
        return (
            self.competitions_created
            + self.clubs_created
            + self.teams_created
            + self.matches_created
            + self.matches_updated
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "competitions_created": self.competitions_created,
            "clubs_created": self.clubs_created,
            "teams_created": self.teams_created,
            "matches_created": self.matches_created,
            "matches_updated": self.matches_updated,
            "total_changes": self.total_changes,
        }