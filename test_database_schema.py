import sqlite3
from pathlib import Path


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


def main():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        rows = connection.execute(
            """
            SELECT
                name,
                sql
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        print("=" * 80)
        print("DATENBANKSCHEMA")
        print("=" * 80)

        for name, sql in rows:
            print()
            print(name)
            print("-" * 80)
            print(sql)

    finally:
        connection.close()


if __name__ == "__main__":
    main()