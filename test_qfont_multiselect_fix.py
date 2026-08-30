from __future__ import annotations

import sys

from PySide6.QtCore import (
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
)

from src.ui.theme.typography import Typography


warnings: list[str] = []


def qt_message_handler(
    mode: QtMsgType,
    context,
    message: str,
) -> None:
    if (
        "QFont::setPointSize" in message
        or "Point size <= 0" in message
    ):
        warnings.append(
            message
        )
        print(
            f"[QT-WARNUNG] {message}"
        )


def run_case(
    title: str,
    set_font_before_editable: bool,
) -> int:
    warnings.clear()

    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    combo = QComboBox()

    print(
        "Font vor setEditable():",
        {
            "family": combo.font().family(),
            "pointSize": combo.font().pointSize(),
            "pointSizeF": combo.font().pointSizeF(),
            "pixelSize": combo.font().pixelSize(),
        },
    )

    if set_font_before_editable:
        combo.setFont(
            Typography.body()
        )

        print(
            "Expliziter Font gesetzt:",
            {
                "family": combo.font().family(),
                "pointSize": combo.font().pointSize(),
                "pointSizeF": combo.font().pointSizeF(),
                "pixelSize": combo.font().pixelSize(),
            },
        )

    combo.setEditable(
        True
    )

    line_edit = combo.lineEdit()

    if line_edit is not None:
        print(
            "LineEdit-Font danach:",
            {
                "family": line_edit.font().family(),
                "pointSize": line_edit.font().pointSize(),
                "pointSizeF": line_edit.font().pointSizeF(),
                "pixelSize": line_edit.font().pixelSize(),
            },
        )

    print(
        f"QFont-Warnungen: {len(warnings)}"
    )

    return len(
        warnings
    )


def main() -> None:
    qInstallMessageHandler(
        qt_message_handler
    )

    app = QApplication(
        sys.argv
    )

    with open(
        "src/ui/styles/dark.qss",
        "r",
        encoding="utf-8",
    ) as style_file:
        app.setStyleSheet(
            style_file.read()
        )

    baseline = run_case(
        "TEST A - AKTUELLER WEG",
        set_font_before_editable=False,
    )

    fixed = run_case(
        "TEST B - Typography.body() VOR setEditable()",
        set_font_before_editable=True,
    )

    print()
    print("=" * 100)
    print("ERGEBNIS")
    print("=" * 100)
    print(
        f"Aktueller Weg: {baseline} Warnung(en)"
    )
    print(
        f"Mit Font-Fix:   {fixed} Warnung(en)"
    )

    if (
        baseline > 0
        and fixed == 0
    ):
        print()
        print(
            "FIX BESTÄTIGT: "
            "MultiSelectTeamCombo muss vor "
            "setEditable(True) einen gültigen "
            "Point-Size-Font erhalten."
        )
    elif fixed == 0:
        print()
        print(
            "Der Fix-Weg ist warnungsfrei."
        )
    else:
        print()
        print(
            "Der Font-Fix reicht noch nicht aus."
        )

    print("=" * 100)


if __name__ == "__main__":
    main()
