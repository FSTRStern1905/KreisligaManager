from __future__ import annotations

from src.database.database import Database
from src.database.repositories.event_repository import (
    EventRepository,
)
from src.database.repositories.lineup_repository import (
    LineupRepository,
)
from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.database.repositories.referee_repository import (
    RefereeRepository,
)
from src.database.repositories.stadium_repository import (
    StadiumRepository,
)
from src.validator.snapshot_builder import (
    SnapshotBuilder,
)
from src.validator.snapshot_loader import (
    SnapshotLoader,
)


MATCH_EXTERNAL_ID = (
    "02TNB07C34000000VS5489BUVSSD35NB"
)


def main() -> None:

    database = Database(
        database_name="kreisligamanager_test.db",
    )

    connection = database.connect()

    try:

        loader = SnapshotLoader(
            match_repository=MatchRepository(
                connection
            ),
            player_repository=PlayerRepository(
                connection
            ),
            lineup_repository=LineupRepository(
                connection
            ),
            event_repository=EventRepository(
                connection
            ),
            referee_repository=RefereeRepository(
                connection
            ),
            stadium_repository=StadiumRepository(
                connection
            ),
        )

        builder = SnapshotBuilder(
            loader=loader,
        )

        snapshot = (
            builder.build_by_external_id(
                MATCH_EXTERNAL_ID
            )
        )

        print()
        print("=" * 60)
        print("MATCH SNAPSHOT")
        print("=" * 60)

        print(
            f"Heim: {snapshot.home_team}"
        )

        print(
            f"Auswärts: {snapshot.away_team}"
        )

        print(
            f"Ergebnis: "
            f"{snapshot.home_goals}:"
            f"{snapshot.away_goals}"
        )

        print(
            f"Halbzeit: "
            f"{snapshot.halftime_home}:"
            f"{snapshot.halftime_away}"
        )

        print(
            f"Heimspieler: "
            f"{len(snapshot.home_players)}"
        )

        print(
            f"Auswärtsspieler: "
            f"{len(snapshot.away_players)}"
        )

        print(
            f"Events: "
            f"{len(snapshot.events)}"
        )

    finally:

        database.close()


if __name__ == "__main__":
    main()