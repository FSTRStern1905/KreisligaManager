from __future__ import annotations

from src.ui.theme.typography import Typography


METHOD_NAMES = (
    "hero",
    "title",
    "heading",
    "subtitle",
    "body",
    "small",
    "caption",
)


def main() -> None:
    print("=" * 100)
    print("TYPOGRAPHY FONT-SIZE DIAGNOSE")
    print("=" * 100)

    print()
    print("KLASSENATTRIBUTE")
    print("-" * 100)

    for name in sorted(
        key
        for key in dir(Typography)
        if key.isupper()
    ):
        try:
            value = getattr(
                Typography,
                name,
            )
        except Exception as exc:
            value = f"<FEHLER: {exc}>"

        print(
            f"{name} = {value!r}"
        )

    print()
    print("METHODEN")
    print("-" * 100)

    found_method = False

    for method_name in METHOD_NAMES:
        method = getattr(
            Typography,
            method_name,
            None,
        )

        if method is None:
            continue

        found_method = True

        try:
            font = method()
        except Exception as exc:
            print(
                f"{method_name}(): FEHLER -> "
                f"{type(exc).__name__}: {exc}"
            )
            continue

        point_size = font.pointSize()
        point_size_f = font.pointSizeF()
        pixel_size = font.pixelSize()

        marker = (
            "OK"
            if point_size > 0
            else "AUFFÄLLIG"
        )

        print(
            f"[{marker}] "
            f"{method_name}() | "
            f"family={font.family()!r} | "
            f"pointSize={point_size} | "
            f"pointSizeF={point_size_f} | "
            f"pixelSize={pixel_size} | "
            f"bold={font.bold()} | "
            f"weight={font.weight()}"
        )

    if not found_method:
        print(
            "Keine bekannten Typography-Methoden gefunden."
        )

    print()
    print("=" * 100)
    print("ERGEBNIS")
    print("=" * 100)
    print(
        "Wenn bereits beim Aufruf einer Typography-Methode "
        "die Qt-Warnung erscheint, liegt der Fehler direkt "
        "in src/ui/theme/typography.py."
    )
    print(
        "Wenn alle Methoden positive pointSize-Werte liefern "
        "und keine Warnung erscheint, liegt die Warnung "
        "wahrscheinlich außerhalb von Typography."
    )
    print("=" * 100)


if __name__ == "__main__":
    main()
