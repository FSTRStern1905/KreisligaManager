from src.database.database import Database
from src.database.schema import DatabaseSchema


def main():
    print("=================================")
    print(" KreisligaManager gestartet")

    database = Database()
    connection = database.connect()

    print(" Datenbank erfolgreich geöffnet")

    schema = DatabaseSchema(connection)
    schema.create_all_tables()

    print(" Tabellen erfolgreich erstellt")
    print("=================================")

    database.close()


if __name__ == "__main__":
    main()