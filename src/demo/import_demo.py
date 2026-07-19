from src.database.database import Database
from src.database.repository import Repository
from src.database.schema import DatabaseSchema
from src.importer.club_importer import ClubImporter


def main():
    print("=" * 50)
    print(" Club-Import Demo")
    print("=" * 50)

    database = Database()
    connection = database.connect()

    schema = DatabaseSchema(connection)
    schema.create_all_tables()

    repository = Repository(connection)

    try:
        importer = ClubImporter(
            repository=repository,
            file_path="imports/demo/clubs.csv",
        )

        imported, skipped = importer.run()

        print()
        print(f"Importiert    : {imported}")
        print(f"Übersprungen : {skipped}")
        print()
        print("Import erfolgreich abgeschlossen.")

    finally:
        database.close()


if __name__ == "__main__":
    main()