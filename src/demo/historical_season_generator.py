from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

DEMO_PREFIX = "DEMO_HIST_"
RANDOM_SEED = 1905

TEAMS_PER_LEAGUE = 18
LEAGUE_LEVELS = 5
PROMOTION_PLACES = 2

REFERENCE_CLUB_NAME = "SV Grün-Weiß Höhenwald"
REFERENCE_TEAM_NAME = "SV Grün-Weiß Höhenwald"
REFERENCE_SHORT_NAME = "GW Höhenwald"


@dataclass(frozen=True)
class HistoricalSeason:
    name: str
    start_date: str
    end_date: str
    league_level: int
    final_position: int


HISTORY = [
    HistoricalSeason("2012/13", "2012-07-01", "2013-06-30", 5, 2),
    HistoricalSeason("2013/14", "2013-07-01", "2014-06-30", 4, 8),
    HistoricalSeason("2014/15", "2014-07-01", "2015-06-30", 4, 5),
    HistoricalSeason("2015/16", "2015-07-01", "2016-06-30", 4, 2),
    HistoricalSeason("2016/17", "2016-07-01", "2017-06-30", 3, 11),
    HistoricalSeason("2017/18", "2017-07-01", "2018-06-30", 3, 18),
    HistoricalSeason("2018/19", "2018-07-01", "2019-06-30", 4, 7),
    HistoricalSeason("2019/20", "2019-07-01", "2020-06-30", 4, 4),
    HistoricalSeason("2020/21", "2020-07-01", "2021-06-30", 4, 3),
    HistoricalSeason("2021/22", "2021-07-01", "2022-06-30", 4, 1),
    HistoricalSeason("2022/23", "2022-07-01", "2023-06-30", 3, 2),
    HistoricalSeason("2023/24", "2023-07-01", "2024-06-30", 2, 10),
    HistoricalSeason("2024/25", "2024-07-01", "2025-06-30", 2, 3),
    HistoricalSeason("2025/26", "2025-07-01", "2026-06-30", 1, 12),
]


LEAGUE_NAMES = {
    1: "Demo Bundesliga",
    2: "Demo 2. Bundesliga",
    3: "Demo 3. Liga",
    4: "Demo Regionalliga Südwest",
    5: "Demo Oberliga Südwest",
}


BASE_CLUBS = [
    ("SV Grün-Weiß Höhenwald", "GW Höhenwald", "Höhenwald"),
    ("FC Rot-Weiß Falkenberg", "RW Falkenberg", "Falkenberg"),
    ("TSV Blau-Weiß Kronau", "BW Kronau", "Kronau"),
    ("VfB Adlerstadt", "VfB Adlerstadt", "Adlerstadt"),
    ("SC Viktoria Rheinhain", "Viktoria Rheinhain", "Rheinhain"),
    ("FV Borussia Eichen", "Borussia Eichen", "Eichen"),
    ("SV Eintracht Sonnenberg", "E. Sonnenberg", "Sonnenberg"),
    ("FC Germania Westtal", "Germania Westtal", "Westtal"),
    ("TSG Fortuna Linden", "Fortuna Linden", "Linden"),
    ("SV Union Bergheim", "Union Bergheim", "Bergheim"),
    ("FC Olympia Nord", "Olympia Nord", "Nordstadt"),
    ("VfR Schwarz-Gelb Hohenfeld", "SG Hohenfeld", "Hohenfeld"),
    ("SC Alemannia Talheim", "Alemannia Talheim", "Talheim"),
    ("SV Preußen Waldstadt", "Preußen Waldstadt", "Waldstadt"),
    ("FC Concordia Mosel", "Concordia Mosel", "Moselstadt"),
    ("TSV Rheingold Süd", "Rheingold Süd", "Südstadt"),
    ("SV Blau-Rot Heide", "BR Heide", "Heide"),
    ("FC Sportfreunde Auen", "SF Auen", "Auen"),
]


PREFIXES = [
    "FC",
    "SV",
    "TSV",
    "VfB",
    "SC",
    "FV",
    "TSG",
    "VfR",
]

PLACES = [
    "Eberbach",
    "Westerfeld",
    "Rosenheim",
    "Birkental",
    "Hinterwald",
    "Neustadt",
    "Rheindorf",
    "Kirchberg",
    "Lauterbach",
    "Eichenau",
    "Steinheim",
    "Felsenberg",
    "Ahrtal",
    "Saarhöhe",
    "Mühlenstadt",
    "Waldkirchen",
    "Bergtal",
    "Hochwald",
    "Sonnenfeld",
    "Moselheim",
    "Riedlingen",
    "Tannenberg",
    "Silbertal",
    "Wiesengrund",
    "Erlenbach",
    "Lindenau",
    "Hohenrain",
    "Wiesenstadt",
    "Talburg",
    "Rheinau",
    "Waldbrunn",
    "Auenheim",
    "Kronenberg",
    "Burgheim",
    "Falkental",
    "Eichendorf",
    "Sonnenau",
    "Bergheim-Nord",
    "Rheintal",
    "Westerburg",
    "Heideck",
    "Mittelwald",
    "Nordtal",
    "Südheim",
    "Oberkirchen",
    "Unterfeld",
    "Felsenau",
    "Hunsrück",
    "Nahetal",
    "Ruwertal",
    "Saarburg",
    "Moseltal",
    "Eifelheim",
    "Waldhöhe",
    "Bergstadt",
    "Rheinberg",
    "Ahrweiler-Süd",
    "Westerwald",
    "Kylltal",
    "Liesertal",
    "Prümtal",
    "Salmhöhe",
    "Hochfels",
    "Talheim-West",
    "Waldstadt-Ost",
    "Rheinhöhe",
    "Sonnenberg-West",
    "Bergkirchen",
    "Eichenfeld",
    "Falkenau",
    "Lindental",
    "Mühlenberg",
]


class HistoricalSeasonGenerator:
    def __init__(
        self,
        database_path: Path = DATABASE_PATH,
    ) -> None:
        self.database_path = database_path
        self.random = random.Random(
            RANDOM_SEED
        )

    def run(
        self,
    ) -> None:
        if not self.database_path.exists():
            raise FileNotFoundError(
                "Datenbank nicht gefunden: "
                f"{self.database_path}"
            )

        connection = sqlite3.connect(
            self.database_path
        )
        connection.row_factory = sqlite3.Row

        try:
            connection.execute(
                "PRAGMA foreign_keys = ON;"
            )

            with connection:
                self._remove_previous_demo_data(
                    connection
                )

                team_ids = (
                    self._ensure_demo_clubs_and_teams(
                        connection
                    )
                )

                reference_team_id = team_ids[
                    REFERENCE_TEAM_NAME
                ]

                level_assignments = (
                    self._create_initial_level_assignments(
                        team_ids=team_ids,
                        reference_team_id=(
                            reference_team_id
                        ),
                    )
                )

                total_matches = 0
                total_competitions = 0

                for season_index, season in enumerate(
                    HISTORY
                ):
                    season_id = self._ensure_season(
                        connection=connection,
                        season=season,
                    )

                    level_assignments = (
                        self._force_reference_level(
                            level_assignments=level_assignments,
                            reference_team_id=(
                                reference_team_id
                            ),
                            target_level=(
                                season.league_level
                            ),
                        )
                    )

                    rankings_by_level: dict[
                        int,
                        list[int],
                    ] = {}

                    for level in range(
                        1,
                        LEAGUE_LEVELS + 1,
                    ):
                        league_id = self._ensure_league(
                            connection=connection,
                            season=season,
                            level=level,
                        )

                        competition_id = (
                            self._create_competition(
                                connection=connection,
                                season=season,
                                season_id=season_id,
                                league_id=league_id,
                                level=level,
                            )
                        )

                        league_team_ids = list(
                            level_assignments[
                                level
                            ]
                        )

                        ordered_team_ids = (
                            self._build_target_order(
                                team_ids=league_team_ids,
                                reference_team_id=(
                                    reference_team_id
                                ),
                                reference_position=(
                                    season.final_position
                                    if level
                                    == season.league_level
                                    else None
                                ),
                            )
                        )

                        rankings_by_level[
                            level
                        ] = ordered_team_ids

                        self._add_competition_teams(
                            connection=connection,
                            competition_id=(
                                competition_id
                            ),
                            team_ids=(
                                ordered_team_ids
                            ),
                        )

                        fixtures = (
                            self._generate_double_round_robin(
                                ordered_team_ids
                            )
                        )

                        self._create_matches(
                            connection=connection,
                            competition_id=(
                                competition_id
                            ),
                            season_id=season_id,
                            league_id=league_id,
                            season=season,
                            level=level,
                            ordered_team_ids=(
                                ordered_team_ids
                            ),
                            fixtures=fixtures,
                            season_index=season_index,
                        )

                        self._create_standings_from_matches(
                            connection=connection,
                            competition_id=(
                                competition_id
                            ),
                        )

                        self._create_team_season_metrics(
                            connection=connection,
                            competition_id=(
                                competition_id
                            ),
                            season_id=season_id,
                            ordered_team_ids=(
                                ordered_team_ids
                            ),
                            reference_team_id=(
                                reference_team_id
                            ),
                            season=season,
                            level=level,
                            season_index=season_index,
                        )

                        total_matches += sum(
                            len(round_matches)
                            for round_matches in fixtures
                        )
                        total_competitions += 1

                    if season_index < len(
                        HISTORY
                    ) - 1:
                        next_reference_level = (
                            HISTORY[
                                season_index + 1
                            ].league_level
                        )

                        level_assignments = (
                            self._create_next_season_assignments(
                                rankings_by_level=(
                                    rankings_by_level
                                ),
                                reference_team_id=(
                                    reference_team_id
                                ),
                                current_reference_level=(
                                    season.league_level
                                ),
                                next_reference_level=(
                                    next_reference_level
                                ),
                            )
                        )

            print(
                "Historische Demo-Ligapyramide "
                "erfolgreich erstellt."
            )
            print(
                f"Saisons: {len(HISTORY)}"
            )
            print(
                f"Ligen pro Saison: {LEAGUE_LEVELS}"
            )
            print(
                "Teams pro Liga: "
                f"{TEAMS_PER_LEAGUE}"
            )
            print(
                "Teams gesamt: "
                f"{TEAMS_PER_LEAGUE * LEAGUE_LEVELS}"
            )
            print(
                "Wettbewerbe gesamt: "
                f"{total_competitions}"
            )
            print(
                f"Spiele gesamt: {total_matches}"
            )
            print(
                "Team-Saison-Metriken: "
                f"{len(HISTORY) * TEAMS_PER_LEAGUE * LEAGUE_LEVELS}"
            )
            print(
                "Referenzverein: "
                f"{REFERENCE_CLUB_NAME}"
            )

        finally:
            connection.close()

    def _remove_previous_demo_data(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            DELETE FROM matches
            WHERE external_id LIKE ?;
            """,
            (
                f"{DEMO_PREFIX}MATCH_%",
            ),
        )

        connection.execute(
            """
            DELETE FROM competitions
            WHERE external_id LIKE ?;
            """,
            (
                f"{DEMO_PREFIX}COMP_%",
            ),
        )

        connection.execute(
            """
            DELETE FROM leagues
            WHERE external_id LIKE ?;
            """,
            (
                f"{DEMO_PREFIX}LEAGUE_%",
            ),
        )

    def _ensure_demo_clubs_and_teams(
        self,
        connection: sqlite3.Connection,
    ) -> dict[str, int]:
        clubs = list(
            BASE_CLUBS
        )

        required_count = (
            TEAMS_PER_LEAGUE
            * LEAGUE_LEVELS
        )

        generated_index = 0

        while len(clubs) < required_count:
            prefix = PREFIXES[
                generated_index
                % len(PREFIXES)
            ]

            place = PLACES[
                generated_index
                % len(PLACES)
            ]

            cycle = (
                generated_index
                // len(PLACES)
            )

            suffix = (
                ""
                if cycle == 0
                else f" {cycle + 1}"
            )

            club_name = (
                f"{prefix} {place}{suffix}"
            )

            short_name = (
                f"{prefix} {place[:12]}{suffix}"
            )

            city = (
                f"{place}{suffix}"
            )

            if all(
                existing[0] != club_name
                for existing in clubs
            ):
                clubs.append(
                    (
                        club_name,
                        short_name,
                        city,
                    )
                )

            generated_index += 1

        team_ids: dict[str, int] = {}

        for (
            club_name,
            short_name,
            city,
        ) in clubs:
            club_id = self._ensure_club(
                connection=connection,
                club_name=club_name,
                short_name=short_name,
                city=city,
            )

            team_id = self._ensure_team(
                connection=connection,
                club_id=club_id,
                team_name=club_name,
                short_name=short_name,
            )

            team_ids[
                club_name
            ] = team_id

        return team_ids

    def _ensure_club(
        self,
        connection: sqlite3.Connection,
        club_name: str,
        short_name: str,
        city: str,
    ) -> int:
        row = connection.execute(
            """
            SELECT club_id
            FROM clubs
            WHERE name = ?
            LIMIT 1;
            """,
            (
                club_name,
            ),
        ).fetchone()

        if row is not None:
            return int(
                row["club_id"]
            )

        cursor = connection.execute(
            """
            INSERT INTO clubs (
                association_id,
                name,
                short_name,
                city,
                country,
                founded,
                website,
                logo,
                external_id
            )
            VALUES (
                NULL,
                ?,
                ?,
                ?,
                'Deutschland',
                NULL,
                NULL,
                NULL,
                ?
            );
            """,
            (
                club_name,
                short_name,
                city,
                (
                    f"{DEMO_PREFIX}CLUB_"
                    f"{self._slug(club_name)}"
                ),
            ),
        )

        return int(
            cursor.lastrowid
        )

    def _ensure_team(
        self,
        connection: sqlite3.Connection,
        club_id: int,
        team_name: str,
        short_name: str,
    ) -> int:
        row = connection.execute(
            """
            SELECT team_id
            FROM teams
            WHERE
                club_id = ?
                AND name = ?
            LIMIT 1;
            """,
            (
                club_id,
                team_name,
            ),
        ).fetchone()

        if row is not None:
            return int(
                row["team_id"]
            )

        cursor = connection.execute(
            """
            INSERT INTO teams (
                club_id,
                name,
                short_name,
                team_number,
                coach,
                age_group,
                external_id
            )
            VALUES (
                ?,
                ?,
                ?,
                1,
                NULL,
                'Herren',
                ?
            );
            """,
            (
                club_id,
                team_name,
                short_name,
                (
                    f"{DEMO_PREFIX}TEAM_"
                    f"{self._slug(team_name)}"
                ),
            ),
        )

        return int(
            cursor.lastrowid
        )

    def _ensure_season(
        self,
        connection: sqlite3.Connection,
        season: HistoricalSeason,
    ) -> int:
        row = connection.execute(
            """
            SELECT season_id
            FROM seasons
            WHERE name = ?
            LIMIT 1;
            """,
            (
                season.name,
            ),
        ).fetchone()

        if row is not None:
            return int(
                row["season_id"]
            )

        cursor = connection.execute(
            """
            INSERT INTO seasons (
                name,
                start_date,
                end_date,
                external_id,
                active
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                0
            );
            """,
            (
                season.name,
                season.start_date,
                season.end_date,
                (
                    f"{DEMO_PREFIX}SEASON_"
                    f"{season.name.replace('/', '_')}"
                ),
            ),
        )

        return int(
            cursor.lastrowid
        )

    def _ensure_league(
        self,
        connection: sqlite3.Connection,
        season: HistoricalSeason,
        level: int,
    ) -> int:
        external_id = (
            f"{DEMO_PREFIX}LEAGUE_"
            f"L{level}_"
            f"{season.name.replace('/', '_')}"
        )

        row = connection.execute(
            """
            SELECT league_id
            FROM leagues
            WHERE external_id = ?
            LIMIT 1;
            """,
            (
                external_id,
            ),
        ).fetchone()

        if row is not None:
            return int(
                row["league_id"]
            )

        cursor = connection.execute(
            """
            INSERT INTO leagues (
                association_id,
                name,
                level,
                season_type,
                country,
                external_id
            )
            VALUES (
                NULL,
                ?,
                ?,
                'Liga',
                'Deutschland',
                ?
            );
            """,
            (
                LEAGUE_NAMES[
                    level
                ],
                level,
                external_id,
            ),
        )

        return int(
            cursor.lastrowid
        )

    def _create_competition(
        self,
        connection: sqlite3.Connection,
        season: HistoricalSeason,
        season_id: int,
        league_id: int,
        level: int,
    ) -> int:
        external_id = (
            f"{DEMO_PREFIX}COMP_"
            f"L{level}_"
            f"{season.name.replace('/', '_')}"
        )

        cursor = connection.execute(
            """
            INSERT INTO competitions (
                league_id,
                season_id,
                name,
                active,
                external_id,
                schedule_url,
                last_schedule_sync
            )
            VALUES (
                ?,
                ?,
                ?,
                0,
                ?,
                '',
                NULL
            );
            """,
            (
                league_id,
                season_id,
                (
                    f"{LEAGUE_NAMES[level]} "
                    f"{season.name}"
                ),
                external_id,
            ),
        )

        return int(
            cursor.lastrowid
        )

    def _create_initial_level_assignments(
        self,
        team_ids: dict[str, int],
        reference_team_id: int,
    ) -> dict[int, list[int]]:
        all_team_ids = list(
            team_ids.values()
        )

        all_team_ids.remove(
            reference_team_id
        )

        self.random.shuffle(
            all_team_ids
        )

        assignments: dict[
            int,
            list[int],
        ] = {
            level: []
            for level in range(
                1,
                LEAGUE_LEVELS + 1,
            )
        }

        assignments[5].append(
            reference_team_id
        )

        index = 0

        for level in range(
            1,
            LEAGUE_LEVELS + 1,
        ):
            needed = (
                TEAMS_PER_LEAGUE
                - len(
                    assignments[level]
                )
            )

            assignments[level].extend(
                all_team_ids[
                    index:index + needed
                ]
            )

            index += needed

        return assignments

    def _force_reference_level(
        self,
        level_assignments: dict[int, list[int]],
        reference_team_id: int,
        target_level: int,
    ) -> dict[int, list[int]]:
        assignments = {
            level: list(team_ids)
            for level, team_ids in (
                level_assignments.items()
            )
        }

        current_level = next(
            (
                level
                for level, team_ids in assignments.items()
                if reference_team_id in team_ids
            ),
            None,
        )

        if current_level is None:
            raise ValueError(
                "Referenzteam fehlt in Ligapyramide."
            )

        if current_level == target_level:
            return assignments

        swap_team_id = next(
            team_id
            for team_id in assignments[
                target_level
            ]
            if team_id != reference_team_id
        )

        assignments[
            current_level
        ].remove(
            reference_team_id
        )
        assignments[
            target_level
        ].remove(
            swap_team_id
        )

        assignments[
            target_level
        ].append(
            reference_team_id
        )
        assignments[
            current_level
        ].append(
            swap_team_id
        )

        return assignments

    def _build_target_order(
        self,
        team_ids: list[int],
        reference_team_id: int,
        reference_position: int | None,
    ) -> list[int]:
        candidates = list(
            team_ids
        )

        self.random.shuffle(
            candidates
        )

        if (
            reference_position is None
            or reference_team_id not in candidates
        ):
            return candidates

        candidates.remove(
            reference_team_id
        )

        position = max(
            1,
            min(
                reference_position,
                len(team_ids),
            ),
        )

        candidates.insert(
            position - 1,
            reference_team_id,
        )

        return candidates

    def _create_next_season_assignments(
        self,
        rankings_by_level: dict[int, list[int]],
        reference_team_id: int,
        current_reference_level: int,
        next_reference_level: int,
    ) -> dict[int, list[int]]:
        assignments = {
            level: list(
                rankings_by_level[level]
            )
            for level in range(
                1,
                LEAGUE_LEVELS + 1,
            )
        }

        for upper_level in range(
            1,
            LEAGUE_LEVELS,
        ):
            lower_level = (
                upper_level + 1
            )

            upper_ranking = rankings_by_level[
                upper_level
            ]
            lower_ranking = rankings_by_level[
                lower_level
            ]

            relegated = list(
                upper_ranking[
                    -PROMOTION_PLACES:
                ]
            )
            promoted = list(
                lower_ranking[
                    :PROMOTION_PLACES
                ]
            )

            if (
                current_reference_level
                == upper_level
                and next_reference_level
                == lower_level
            ):
                if reference_team_id not in relegated:
                    relegated[
                        -1
                    ] = reference_team_id

            elif (
                current_reference_level
                == lower_level
                and next_reference_level
                == upper_level
            ):
                if reference_team_id not in promoted:
                    promoted[
                        -1
                    ] = reference_team_id

            elif (
                current_reference_level
                in (
                    upper_level,
                    lower_level,
                )
                and next_reference_level
                == current_reference_level
            ):
                if reference_team_id in relegated:
                    replacement = next(
                        team_id
                        for team_id in reversed(
                            upper_ranking
                        )
                        if (
                            team_id
                            != reference_team_id
                            and team_id
                            not in relegated
                        )
                    )
                    relegated[
                        relegated.index(
                            reference_team_id
                        )
                    ] = replacement

                if reference_team_id in promoted:
                    replacement = next(
                        team_id
                        for team_id in lower_ranking
                        if (
                            team_id
                            != reference_team_id
                            and team_id
                            not in promoted
                        )
                    )
                    promoted[
                        promoted.index(
                            reference_team_id
                        )
                    ] = replacement

            for team_id in relegated:
                if team_id in assignments[
                    upper_level
                ]:
                    assignments[
                        upper_level
                    ].remove(
                        team_id
                    )

            for team_id in promoted:
                if team_id in assignments[
                    lower_level
                ]:
                    assignments[
                        lower_level
                    ].remove(
                        team_id
                    )

            assignments[
                upper_level
            ].extend(
                promoted
            )

            assignments[
                lower_level
            ].extend(
                relegated
            )

        return assignments

    def _add_competition_teams(
        self,
        connection: sqlite3.Connection,
        competition_id: int,
        team_ids: list[int],
    ) -> None:
        for team_id in team_ids:
            connection.execute(
                """
                INSERT INTO competition_teams (
                    competition_id,
                    team_id
                )
                VALUES (
                    ?,
                    ?
                );
                """,
                (
                    competition_id,
                    team_id,
                ),
            )

    def _generate_double_round_robin(
        self,
        team_ids: list[int],
    ) -> list[list[tuple[int, int]]]:
        teams = list(
            team_ids
        )

        if len(teams) % 2:
            teams.append(
                -1
            )

        team_count = len(
            teams
        )
        rotation = teams[:]
        rounds: list[
            list[
                tuple[int, int]
            ]
        ] = []

        for round_index in range(
            team_count - 1
        ):
            round_matches: list[
                tuple[int, int]
            ] = []

            for index in range(
                team_count // 2
            ):
                first = rotation[
                    index
                ]
                second = rotation[
                    team_count
                    - 1
                    - index
                ]

                if (
                    first == -1
                    or second == -1
                ):
                    continue

                if (
                    round_index + index
                ) % 2 == 0:
                    home_id = first
                    away_id = second
                else:
                    home_id = second
                    away_id = first

                round_matches.append(
                    (
                        home_id,
                        away_id,
                    )
                )

            rounds.append(
                round_matches
            )

            rotation = [
                rotation[0],
                rotation[-1],
                *rotation[1:-1],
            ]

        second_half = [
            [
                (
                    away_id,
                    home_id,
                )
                for (
                    home_id,
                    away_id,
                ) in round_matches
            ]
            for round_matches in rounds
        ]

        return (
            rounds
            + second_half
        )

    def _create_matches(
        self,
        connection: sqlite3.Connection,
        competition_id: int,
        season_id: int,
        league_id: int,
        season: HistoricalSeason,
        level: int,
        ordered_team_ids: list[int],
        fixtures: list[list[tuple[int, int]]],
        season_index: int,
    ) -> None:
        rank_by_team = {
            team_id: rank
            for rank, team_id in enumerate(
                ordered_team_ids,
                start=1,
            )
        }

        start_year = int(
            season.name.split(
                "/"
            )[0]
        )

        for matchday, matches in enumerate(
            fixtures,
            start=1,
        ):
            month_offset = (
                matchday - 1
            ) // 4

            month = (
                8 + month_offset
            )
            year = start_year

            while month > 12:
                month -= 12
                year += 1

            day = min(
                28,
                3
                + (
                    (
                        matchday - 1
                    )
                    % 4
                )
                * 7,
            )

            match_date = (
                f"{year:04d}-"
                f"{month:02d}-"
                f"{day:02d}"
            )

            for game_index, (
                home_id,
                away_id,
            ) in enumerate(
                matches
            ):
                home_rank = rank_by_team[
                    home_id
                ]
                away_rank = rank_by_team[
                    away_id
                ]

                home_goals, away_goals = (
                    self._deterministic_score(
                        home_rank=home_rank,
                        away_rank=away_rank,
                        matchday=matchday,
                    )
                )

                attendance = (
                    self._simulate_attendance(
                        league_level=level,
                        home_rank=home_rank,
                        away_rank=away_rank,
                        team_count=len(
                            ordered_team_ids
                        ),
                        season_index=season_index,
                    )
                )

                kickoff_hour = (
                    13
                    + (
                        game_index % 4
                    )
                )

                external_id = (
                    f"{DEMO_PREFIX}MATCH_"
                    f"L{level}_"
                    f"{season.name.replace('/', '_')}_"
                    f"{matchday:02d}_"
                    f"{home_id}_{away_id}"
                )

                connection.execute(
                    """
                    INSERT INTO matches (
                        competition_id,
                        season_id,
                        league_id,
                        matchday,
                        match_date,
                        kickoff_time,
                        home_team_id,
                        away_team_id,
                        attendance,
                        home_goals,
                        away_goals,
                        status,
                        detail_imported,
                        notes,
                        external_id
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        'finished', 0, ?, ?
                    );
                    """,
                    (
                        competition_id,
                        season_id,
                        league_id,
                        matchday,
                        match_date,
                        f"{kickoff_hour:02d}:30",
                        home_id,
                        away_id,
                        attendance,
                        home_goals,
                        away_goals,
                        (
                            "Historisches "
                            "Demo-Spiel"
                        ),
                        external_id,
                    ),
                )

    def _deterministic_score(
        self,
        home_rank: int,
        away_rank: int,
        matchday: int,
    ) -> tuple[int, int]:
        rank_difference = (
            away_rank
            - home_rank
        )

        if abs(
            rank_difference
        ) <= 1:
            if matchday % 3 == 0:
                return (
                    1,
                    1,
                )

        if rank_difference > 0:
            margin = min(
                4,
                1
                + abs(
                    rank_difference
                )
                // 5,
            )

            home_goals = (
                1
                + margin
            )
            away_goals = (
                0
                if margin >= 2
                else 1
            )

            return (
                home_goals,
                away_goals,
            )

        margin = min(
            4,
            1
            + abs(
                rank_difference
            )
            // 5,
        )

        away_goals = (
            1
            + margin
        )
        home_goals = (
            0
            if margin >= 2
            else 1
        )

        return (
            home_goals,
            away_goals,
        )

    def _create_standings_from_matches(
        self,
        connection: sqlite3.Connection,
        competition_id: int,
    ) -> None:
        team_rows = connection.execute(
            """
            SELECT team_id
            FROM competition_teams
            WHERE competition_id = ?;
            """,
            (
                competition_id,
            ),
        ).fetchall()

        table: dict[
            int,
            dict[str, int],
        ] = {}

        for row in team_rows:
            team_id = int(
                row["team_id"]
            )

            table[
                team_id
            ] = {
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "points": 0,
            }

        matches = connection.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished';
            """,
            (
                competition_id,
            ),
        ).fetchall()

        for match in matches:
            home_id = int(
                match["home_team_id"]
            )
            away_id = int(
                match["away_team_id"]
            )
            home_goals = int(
                match["home_goals"]
            )
            away_goals = int(
                match["away_goals"]
            )

            home = table[
                home_id
            ]
            away = table[
                away_id
            ]

            home[
                "played"
            ] += 1
            away[
                "played"
            ] += 1

            home[
                "goals_for"
            ] += home_goals
            home[
                "goals_against"
            ] += away_goals

            away[
                "goals_for"
            ] += away_goals
            away[
                "goals_against"
            ] += home_goals

            if home_goals > away_goals:
                home[
                    "wins"
                ] += 1
                home[
                    "points"
                ] += 3
                away[
                    "losses"
                ] += 1
            elif home_goals < away_goals:
                away[
                    "wins"
                ] += 1
                away[
                    "points"
                ] += 3
                home[
                    "losses"
                ] += 1
            else:
                home[
                    "draws"
                ] += 1
                away[
                    "draws"
                ] += 1
                home[
                    "points"
                ] += 1
                away[
                    "points"
                ] += 1

        ordered = sorted(
            table.items(),
            key=lambda item: (
                item[1][
                    "points"
                ],
                (
                    item[1][
                        "goals_for"
                    ]
                    - item[1][
                        "goals_against"
                    ]
                ),
                item[1][
                    "goals_for"
                ],
            ),
            reverse=True,
        )

        for position, (
            team_id,
            values,
        ) in enumerate(
            ordered,
            start=1,
        ):
            goal_difference = (
                values[
                    "goals_for"
                ]
                - values[
                    "goals_against"
                ]
            )

            connection.execute(
                """
                INSERT INTO standings (
                    competition_id,
                    team_id,
                    position,
                    played,
                    wins,
                    draws,
                    losses,
                    goals_for,
                    goals_against,
                    goal_difference,
                    points,
                    source
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'demo-history'
                );
                """,
                (
                    competition_id,
                    team_id,
                    position,
                    values[
                        "played"
                    ],
                    values[
                        "wins"
                    ],
                    values[
                        "draws"
                    ],
                    values[
                        "losses"
                    ],
                    values[
                        "goals_for"
                    ],
                    values[
                        "goals_against"
                    ],
                    goal_difference,
                    values[
                        "points"
                    ],
                ),
            )

    def _create_team_season_metrics(
        self,
        connection: sqlite3.Connection,
        competition_id: int,
        season_id: int,
        ordered_team_ids: list[int],
        reference_team_id: int,
        season: HistoricalSeason,
        level: int,
        season_index: int,
    ) -> None:
        for position, team_id in enumerate(
            ordered_team_ids,
            start=1,
        ):
            average_attendance = (
                self._get_average_attendance(
                    connection=connection,
                    competition_id=(
                        competition_id
                    ),
                    team_id=team_id,
                )
            )

            if team_id == reference_team_id:
                strengths = (
                    self._reference_strengths(
                        season_index=(
                            season_index
                        )
                    )
                )
            else:
                strengths = (
                    self._generic_strengths(
                        league_level=level,
                        position=position,
                        team_count=len(
                            ordered_team_ids
                        ),
                    )
                )

            connection.execute(
                """
                INSERT INTO team_season_metrics (
                    competition_id,
                    season_id,
                    team_id,
                    average_attendance,
                    goalkeeper_strength,
                    defense_strength,
                    midfield_strength,
                    attack_strength,
                    overall_strength,
                    source
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, 'demo-history'
                );
                """,
                (
                    competition_id,
                    season_id,
                    team_id,
                    average_attendance,
                    strengths[
                        "goalkeeper"
                    ],
                    strengths[
                        "defense"
                    ],
                    strengths[
                        "midfield"
                    ],
                    strengths[
                        "attack"
                    ],
                    strengths[
                        "overall"
                    ],
                ),
            )

    def _get_average_attendance(
        self,
        connection: sqlite3.Connection,
        competition_id: int,
        team_id: int,
    ) -> float:
        row = connection.execute(
            """
            SELECT AVG(attendance) AS average_attendance
            FROM matches
            WHERE
                competition_id = ?
                AND home_team_id = ?
                AND attendance IS NOT NULL;
            """,
            (
                competition_id,
                team_id,
            ),
        ).fetchone()

        if (
            row is None
            or row[
                "average_attendance"
            ] is None
        ):
            return 0.0

        return round(
            float(
                row[
                    "average_attendance"
                ]
            ),
            1,
        )

    def _reference_strengths(
        self,
        season_index: int,
    ) -> dict[str, float]:
        values = [
            (53, 51, 54, 56),
            (57, 56, 58, 60),
            (59, 58, 61, 63),
            (62, 61, 64, 67),
            (65, 64, 66, 69),
            (62, 61, 63, 64),
            (60, 59, 61, 62),
            (62, 62, 64, 65),
            (64, 65, 67, 68),
            (68, 69, 71, 73),
            (71, 72, 74, 76),
            (74, 75, 77, 79),
            (77, 79, 81, 83),
            (80, 81, 83, 85),
        ]

        goalkeeper, defense, midfield, attack = values[
            max(
                0,
                min(
                    season_index,
                    len(values) - 1,
                ),
            )
        ]

        overall = round(
            (
                goalkeeper
                + defense
                + midfield
                + attack
            )
            / 4.0,
            1,
        )

        return {
            "goalkeeper": float(
                goalkeeper
            ),
            "defense": float(
                defense
            ),
            "midfield": float(
                midfield
            ),
            "attack": float(
                attack
            ),
            "overall": overall,
        }

    def _generic_strengths(
        self,
        league_level: int,
        position: int,
        team_count: int,
    ) -> dict[str, float]:
        base_by_level = {
            1: 78.0,
            2: 72.0,
            3: 66.0,
            4: 60.0,
            5: 54.0,
        }

        base = base_by_level[
            league_level
        ]

        rank_factor = (
            (
                team_count
                - position
            )
            / (
                team_count - 1
            )
            - 0.5
        ) * 8.0

        overall_base = (
            base
            + rank_factor
        )

        goalkeeper = self._clamp_strength(
            overall_base
            + self.random.uniform(
                -2.5,
                2.5,
            )
        )
        defense = self._clamp_strength(
            overall_base
            + self.random.uniform(
                -2.5,
                2.5,
            )
        )
        midfield = self._clamp_strength(
            overall_base
            + self.random.uniform(
                -2.5,
                2.5,
            )
        )
        attack = self._clamp_strength(
            overall_base
            + self.random.uniform(
                -2.5,
                2.5,
            )
        )

        overall = round(
            (
                goalkeeper
                + defense
                + midfield
                + attack
            )
            / 4.0,
            1,
        )

        return {
            "goalkeeper": goalkeeper,
            "defense": defense,
            "midfield": midfield,
            "attack": attack,
            "overall": overall,
        }

    def _simulate_attendance(
        self,
        league_level: int,
        home_rank: int,
        away_rank: int,
        team_count: int,
        season_index: int,
    ) -> int:
        base_by_level = {
            1: 28000,
            2: 15000,
            3: 5500,
            4: 1800,
            5: 700,
        }

        base = base_by_level[
            league_level
        ]

        rank_quality = (
            (
                team_count
                - home_rank
                + 1
            )
            + (
                team_count
                - away_rank
                + 1
            )
        ) / (
            team_count * 2
        )

        strength_factor = (
            0.80
            + rank_quality * 0.45
        )

        growth_factor = (
            1.0
            + season_index
            * 0.012
        )

        random_factor = (
            self.random.uniform(
                0.80,
                1.20,
            )
        )

        return max(
            80,
            round(
                base
                * strength_factor
                * growth_factor
                * random_factor
            ),
        )

    @staticmethod
    def _clamp_strength(
        value: float,
    ) -> float:
        return round(
            max(
                1.0,
                min(
                    99.0,
                    value,
                ),
            ),
            1,
        )

    @staticmethod
    def _slug(
        value: str,
    ) -> str:
        allowed: list[str] = []

        for character in value.upper():
            if character.isalnum():
                allowed.append(
                    character
                )
            else:
                allowed.append(
                    "_"
                )

        result = "".join(
            allowed
        )

        while "__" in result:
            result = result.replace(
                "__",
                "_",
            )

        return result.strip(
            "_"
        )


def main() -> None:
    generator = HistoricalSeasonGenerator()
    generator.run()


if __name__ == "__main__":
    main()
