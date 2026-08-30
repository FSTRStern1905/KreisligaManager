from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import (
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtWidgets import QApplication

from src.database.database import Database
from src.database.repository import Repository
from src.database.schema import DatabaseSchema
from src.ui.windows.main_window import MainWindow


def qt_message_handler(
    mode: QtMsgType,
    context,
    message: str,
) -> None:
    print()
    print("=" * 110)
    print("QT-MELDUNG")
    print("=" * 110)
    print(f"Typ:     {mode}")
    print(f"Meldung: {message}")

    if context is not None:
        print(
            f"Datei:   {getattr(context, 'file', None)}"
        )
        print(
            f"Zeile:   {getattr(context, 'line', None)}"
        )
        print(
            f"Funktion:{getattr(context, 'function', None)}"
        )

    if (
        "QFont::setPointSize" in message
        or "Point size <= 0" in message
    ):
        print()
        print("PYTHON-CALLSTACK BEIM AUSLÖSEN")
        print("-" * 110)

        stack = traceback.format_stack()

        for entry in stack[:-1]:
            print(
                entry.rstrip()
            )

    print("=" * 110)


def main() -> None:
    qInstallMessageHandler(
        qt_message_handler
    )

    print("=" * 110)
    print(
        "QFONT RUNTIME TRACE"
    )
    print("=" * 110)

    database = Database()
    connection = database.connect()

    schema = DatabaseSchema(
        connection
    )
    schema.create_all_tables()

    repository = Repository(
        connection
    )

    print(
        "[1] QApplication wird erzeugt ..."
    )

    app = QApplication(
        sys.argv
    )

    print(
        "[2] Stylesheet wird geladen ..."
    )

    with open(
        "src/ui/styles/dark.qss",
        "r",
        encoding="utf-8",
    ) as style_file:
        app.setStyleSheet(
            style_file.read()
        )

    print(
        "[3] MainWindow wird erzeugt ..."
    )

    window = MainWindow(
        repository
    )

    print(
        "[4] MainWindow erzeugt."
    )

    print(
        "[5] MainWindow wird angezeigt ..."
    )

    window.show()

    print(
        "[6] MainWindow angezeigt."
    )
    print()
    print(
        "Wenn die QFont-Warnung oben mit "
        "Python-Callstack erschien, bitte die "
        "komplette Ausgabe schicken."
    )
    print()
    print(
        "Fenster kann jetzt geschlossen werden."
    )

    exit_code = app.exec()

    database.close()

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()
