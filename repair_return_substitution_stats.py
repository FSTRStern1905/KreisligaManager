from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)
from src.services.player_match_stats.event_mapper import (
    EventMapper,
)


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

BACKUP_DIR = Path(
    "data/database/backups"
)

COMPETITION_ID = 1


def create_backup() -> Path:
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / (
            "kreisligamanager_before_"
            "return_substitution_stats_fix_"
            f"{timestamp}.db"
        )
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    return backup_path


def get_candidate_rows(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.player_match_stat_id,
            pms.match_id,
            pms.team_id,
            pms.player_id,
            p.first_name,
            p.last_name,
            pms.is_starting,
            pms.was_substituted_in,
            pms.was_substituted_out,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played,

            (
                SELECT COUNT(*)
                FROM events AS e
                INNER JOIN event_types AS et
                    ON et.event_type_id =
                        e.event_type_id
                WHERE
                    e.match_id = pms.match_id
                    AND e.player_id = pms.player_id
                    AND et.code IN (
                        'SUBSTITUTION_IN',
                        'SUBSTITUTION_OUT'
                    )
            ) AS own_substitution_events

        FROM player_match_stats AS pms

        INNER JOIN matches AS m
            ON m.match_id = pms.match_id

        INNER JOIN players AS p
            ON p.player_id = pms.player_id

        WHERE
            m.competition_id = ?
            AND m.detail_imported = 1
            AND (
                (
                    SELECT COUNT(*)
                    FROM events AS e
                    INNER JOIN event_types AS et
                        ON et.event_type_id =
                            e.event_type_id
                    WHERE
                        e.match_id = pms.match_id
                        AND e.player_id = pms.player_id
                        AND et.code IN (
                            'SUBSTITUTION_IN',
                            'SUBSTITUTION_OUT'
                        )
                ) >= 2

                OR (
                    pms.is_starting = 1
                    AND COALESCE(
                        pms.minute_in,
                        -1
                    ) != 0
                )

                OR (
                    pms.minute_in IS NOT NULL
                    AND pms.minute_out IS NOT NULL
                    AND pms.minute_out
                        < pms.minute_in
                )

                OR pms.minutes_played < 0

                OR pms.minutes_played > 90
            )

        ORDER BY
            pms.match_id,
            pms.team_id,
            pms.player_id
        """,
        (COMPETITION_ID,),
    ).fetchall()


def get_player_events(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT
            e.event_id,
            e.match_id,
            e.team_id,
            e.player_id,
            e.related_player_id,
            e.minute,
            et.code AS event_type_code
        FROM events AS e

        INNER JOIN event_types AS et
            ON et.event_type_id =
                e.event_type_id

        WHERE
            e.match_id = ?
            AND e.player_id = ?

        ORDER BY
            e.minute,
            e.event_id
        """,
        (
            match_id,
            player_id,
        ),
    ).fetchall()

    return [
        {
            "event_id": int(
                row["event_id"]
            ),
            "match_id": int(
                row["match_id"]
            ),
            "team_id": (
                int(row["team_id"])
                if row["team_id"] is not None
                else None
            ),
            "player_id": (
                int(row["player_id"])
                if row["player_id"] is not None
                else None
            ),
            "related_player_id": (
                int(row["related_player_id"])
                if row["related_player_id"]
                is not None
                else None
            ),
            "minute": (
                int(row["minute"])
                if row["minute"] is not None
                else None
            ),
            "event_type_code": str(
                row["event_type_code"]
            ),
        }
        for row in rows
    ]


def build_stat_for_recalculation(
    row: sqlite3.Row,
) -> PlayerMatchStat:
    return PlayerMatchStat(
        player_match_stat_id=int(
            row["player_match_stat_id"]
        ),
        match_id=int(
            row["match_id"]
        ),
        team_id=int(
            row["team_id"]
        ),
        player_id=int(
            row["player_id"]
        ),
        is_starting=bool(
            row["is_starting"]
        ),
        was_substituted_in=False,
        was_substituted_out=False,
        minute_in=(
            0
            if bool(row["is_starting"])
            else None
        ),
        minute_out=(
            90
            if bool(row["is_starting"])
            else None
        ),
        minutes_played=(
            90
            if bool(row["is_starting"])
            else 0
        ),
        goals=0,
        own_goals=0,
        assists=0,
        yellow_cards=0,
        yellow_red_cards=0,
        red_cards=0,
        clean_sheet=False,
        shirt_number=None,
        position="",
    )


def stat_snapshot(
    row: sqlite3.Row,
) -> dict:
    return {
        "is_starting": int(
            row["is_starting"] or 0
        ),
        "was_substituted_in": int(
            row["was_substituted_in"] or 0
        ),
        "was_substituted_out": int(
            row["was_substituted_out"] or 0
        ),
        "minute_in": row["minute_in"],
        "minute_out": row["minute_out"],
        "minutes_played": int(
            row["minutes_played"] or 0
        ),
    }


def calculated_snapshot(
    stat: PlayerMatchStat,
) -> dict:
    return {
        "is_starting": int(
            bool(stat.is_starting)
        ),
        "was_substituted_in": int(
            bool(stat.was_substituted_in)
        ),
        "was_substituted_out": int(
            bool(stat.was_substituted_out)
        ),
        "minute_in": stat.minute_in,
        "minute_out": stat.minute_out,
        "minutes_played": int(
            stat.minutes_played
        ),
    }


def validate_calculated_stat(
    stat: PlayerMatchStat,
) -> list[str]:
    errors: list[str] = []

    if (
        stat.is_starting
        and stat.minute_in != 0
    ):
        errors.append(
            "Starter hat minute_in != 0."
        )

    if stat.minutes_played < 0:
        errors.append(
            "minutes_played < 0."
        )

    if stat.minutes_played > 90:
        errors.append(
            "minutes_played > 90."
        )

    if (
        stat.minute_in is not None
        and stat.minute_in < 0
    ):
        errors.append(
            "minute_in < 0."
        )

    if (
        stat.minute_out is not None
        and stat.minute_out < 0
    ):
        errors.append(
            "minute_out < 0."
        )

    if (
        stat.minute_in is not None
        and stat.minute_out is not None
        and stat.minute_out
            < stat.minute_in
    ):
        errors.append(
            "minute_out < minute_in."
        )

    return errors


def update_time_fields(
    connection: sqlite3.Connection,
    stat: PlayerMatchStat,
) -> None:
    connection.execute(
        """
        UPDATE player_match_stats
        SET
            was_substituted_in = ?,
            was_substituted_out = ?,
            minute_in = ?,
            minute_out = ?,
            minutes_played = ?
        WHERE
            player_match_stat_id = ?
        """,
        (
            int(
                bool(stat.was_substituted_in)
            ),
            int(
                bool(stat.was_substituted_out)
            ),
            stat.minute_in,
            stat.minute_out,
            int(
                stat.minutes_played
            ),
            int(
                stat.player_match_stat_id
            ),
        ),
    )


def get_updated_row(
    connection: sqlite3.Connection,
    stat_id: int,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            player_match_stat_id,
            match_id,
            team_id,
            player_id,
            is_starting,
            was_substituted_in,
            was_substituted_out,
            minute_in,
            minute_out,
            minutes_played
        FROM player_match_stats
        WHERE player_match_stat_id = ?
        """,
        (stat_id,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "Aktualisierte Statistik "
            "wurde nicht gefunden."
        )

    return row


def get_match_label(
    connection: sqlite3.Connection,
    match_id: int,
) -> str:
    row = connection.execute(
        """
        SELECT
            m.matchday,
            ht.name AS home_team,
            at.name AS away_team
        FROM matches AS m

        INNER JOIN teams AS ht
            ON ht.team_id =
                m.home_team_id

        INNER JOIN teams AS at
            ON at.team_id =
                m.away_team_id

        WHERE m.match_id = ?
        """,
        (match_id,),
    ).fetchone()

    if row is None:
        return f"Spiel {match_id}"

    return (
        f"Spiel {match_id} | "
        f"ST {row['matchday']} | "
        f"{row['home_team']} - "
        f"{row['away_team']}"
    )


def player_name(
    row: sqlite3.Row,
) -> str:
    name = (
        f"{row['first_name'] or ''} "
        f"{row['last_name'] or ''}"
    ).strip()

    if name:
        return name

    return (
        f"player_id={row['player_id']}"
    )


def main() -> None:
    print("=" * 100)
    print(
        "REPARATUR: RÜCK-/MEHRFACHWECHSEL "
        "PLAYER_MATCH_STATS"
    )
    print("=" * 100)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {DB_PATH}"
        )

    backup_path = create_backup()

    print(f"Haupt-DB: {DB_PATH}")
    print(f"Backup:   {backup_path}")
    print(
        "Es werden ausschließlich Zeit-/"
        "Wechselfelder betroffener "
        "player_match_stats aktualisiert."
    )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    mapper = EventMapper()

    try:
        connection.execute(
            "BEGIN"
        )

        candidates = get_candidate_rows(
            connection
        )

        print()
        print(
            f"Gefundene Kandidaten: "
            f"{len(candidates)}"
        )

        if not candidates:
            print(
                "Keine Reparatur notwendig."
            )
            connection.rollback()
            return

        changed = 0
        unchanged = 0
        validation_errors: list[str] = []

        current_match_id: int | None = None

        for row in candidates:
            match_id = int(
                row["match_id"]
            )
            player_id = int(
                row["player_id"]
            )

            if current_match_id != match_id:
                current_match_id = match_id

                print()
                print("=" * 100)
                print(
                    get_match_label(
                        connection,
                        match_id,
                    )
                )
                print("=" * 100)

            events = get_player_events(
                connection,
                match_id,
                player_id,
            )

            stat = (
                build_stat_for_recalculation(
                    row
                )
            )

            mapper.apply(
                stats=[stat],
                events=events,
            )

            errors = validate_calculated_stat(
                stat
            )

            name = player_name(
                row
            )

            before = stat_snapshot(
                row
            )

            after = calculated_snapshot(
                stat
            )

            if errors:
                validation_errors.append(
                    (
                        f"Spiel {match_id} | "
                        f"{name}: "
                        + " ".join(errors)
                    )
                )

                print(
                    f"[FEHLER] {name}"
                )
                print(
                    f"  VORHER: {before}"
                )
                print(
                    f"  BERECHNET: {after}"
                )

                for error in errors:
                    print(
                        f"  - {error}"
                    )

                continue

            if before == after:
                unchanged += 1

                print(
                    f"[OK/UNVERÄNDERT] {name} | "
                    f"{after}"
                )
                continue

            update_time_fields(
                connection,
                stat,
            )

            updated_row = get_updated_row(
                connection,
                int(
                    stat.player_match_stat_id
                ),
            )

            persisted = {
                "is_starting": int(
                    updated_row[
                        "is_starting"
                    ] or 0
                ),
                "was_substituted_in": int(
                    updated_row[
                        "was_substituted_in"
                    ] or 0
                ),
                "was_substituted_out": int(
                    updated_row[
                        "was_substituted_out"
                    ] or 0
                ),
                "minute_in": updated_row[
                    "minute_in"
                ],
                "minute_out": updated_row[
                    "minute_out"
                ],
                "minutes_played": int(
                    updated_row[
                        "minutes_played"
                    ] or 0
                ),
            }

            if persisted != after:
                validation_errors.append(
                    (
                        f"Spiel {match_id} | "
                        f"{name}: Persistenzprüfung "
                        "fehlgeschlagen."
                    )
                )

                print(
                    f"[FEHLER] {name} | "
                    "Persistenzprüfung"
                )
                print(
                    f"  SOLL: {after}"
                )
                print(
                    f"  DB:   {persisted}"
                )
                continue

            changed += 1

            print(
                f"[GEÄNDERT] {name}"
            )
            print(
                f"  VORHER: {before}"
            )
            print(
                f"  NACHHER: {after}"
            )

        print()
        print("=" * 100)
        print("ABSCHLUSSPRÜFUNG")
        print("=" * 100)
        print(
            f"Kandidaten:  {len(candidates)}"
        )
        print(
            f"Geändert:    {changed}"
        )
        print(
            f"Unverändert: {unchanged}"
        )
        print(
            f"Fehler:      "
            f"{len(validation_errors)}"
        )

        if validation_errors:
            print()
            print(
                "ERGEBNIS: REPARATUR "
                "ABGEBROCHEN."
            )
            print(
                "Alle Änderungen werden "
                "zurückgerollt."
            )

            for error in validation_errors:
                print(
                    f"- {error}"
                )

            connection.rollback()

            raise RuntimeError(
                "Qualitätsprüfung der "
                "Rückwechsel-Reparatur "
                "nicht bestanden."
            )

        connection.commit()

        print()
        print(
            "ERGEBNIS: REPARATUR "
            "ERFOLGREICH."
        )
        print(
            "Änderungen wurden in die "
            "Haupt-DB übernommen."
        )
        print(
            "Das Backup bleibt unverändert "
            "erhalten."
        )
        print("=" * 100)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
