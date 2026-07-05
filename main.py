from src.database.database import Database


def main():
    db = Database()
    db.connect()

    print("=================================")
    print(" KreisligaManager gestartet")
    print(" Datenbank erfolgreich geöffnet")
    print("=================================")

    db.close()


if __name__ == "__main__":
    main()