import sqlite3


DATABASE_PATH = "data/database/kreisligamanager.db"


def main():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        cursor = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        )

        tables = [
            row[0]
            for row in cursor.fetchall()
        ]

        print("=" * 70)
        print("TABELLEN IN DER DATENBANK")
        print("=" * 70)

        for table in tables:
            print(table)

        print("-" * 70)
        print(
            f"Anzahl Tabellen: {len(tables)}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()