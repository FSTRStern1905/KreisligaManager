import sys

from PySide6.QtWidgets import QApplication

from src.database.database import Database
from src.database.schema import DatabaseSchema
from src.database.repository import Repository
from src.ui.windows.main_window import MainWindow


def main():
    database = Database()
    connection = database.connect()

    schema = DatabaseSchema(connection)
    schema.create_all_tables()

    repository = Repository(connection)

    app = QApplication(sys.argv)

    with open("src/ui/styles/dark.qss", "r", encoding="utf-8") as style_file:
        app.setStyleSheet(style_file.read())

    window = MainWindow(repository)
    window.show()

    exit_code = app.exec()

    database.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()