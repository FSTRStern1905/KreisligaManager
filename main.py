from src.database.database import Database
from src.database.schema import DatabaseSchema
from src.database.repository import Repository


def main():
    print("=================================")
    print(" KreisligaManager gestartet")

    database = Database()
    connection = database.connect()

    print(" Datenbank erfolgreich geöffnet")

    schema = DatabaseSchema(connection)
    schema.create_all_tables()

    print(" Tabellen erfolgreich erstellt")

    repository = Repository(connection)

    event_types_count = repository.count("event_types")
    print(f" Eventtypen vorhanden: {event_types_count}")

    database.close()

    print(" Datenbank geschlossen")
    print("=================================")


if __name__ == "__main__":
    main()