from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(".")
SOURCE_ROOT = PROJECT_ROOT / "src"

PYTHON_PATTERN = re.compile(
    r"setPointSize\s*\(",
    re.IGNORECASE,
)

POINTSIZE_PATTERN = re.compile(
    r"\.pointSize\s*\(\s*\)",
    re.IGNORECASE,
)

QFONT_PATTERN = re.compile(
    r"\bQFont\s*\(",
)

QSS_NEGATIVE_FONT_PATTERN = re.compile(
    r"font-size\s*:\s*-\d+",
    re.IGNORECASE,
)


def print_match(
    file_path: Path,
    line_number: int,
    line: str,
    marker: str,
) -> None:
    print(
        f"{marker} {file_path}:"
        f"{line_number}: "
        f"{line.rstrip()}"
    )


def main() -> None:
    print("=" * 110)
    print(
        "QFONT-WARNUNG DIAGNOSE / "
        "setPointSize <= 0"
    )
    print("=" * 110)

    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(
            f"src-Ordner nicht gefunden: {SOURCE_ROOT}"
        )

    python_files = sorted(
        SOURCE_ROOT.rglob("*.py")
    )

    style_files = sorted(
        list(
            SOURCE_ROOT.rglob("*.qss")
        )
        + list(
            PROJECT_ROOT.glob(
                "assets/**/*.qss"
            )
        )
    )

    set_point_size_hits = 0
    dynamic_point_size_hits = 0
    qfont_hits = 0
    negative_qss_hits = 0

    print()
    print("1) setPointSize()-AUFRUFE")
    print("-" * 110)

    for file_path in python_files:
        lines = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        for index, line in enumerate(
            lines,
            start=1,
        ):
            if PYTHON_PATTERN.search(line):
                set_point_size_hits += 1

                marker = "[SET]"

                if POINTSIZE_PATTERN.search(
                    line
                ):
                    marker = "[DYNAMISCH]"
                    dynamic_point_size_hits += 1

                print_match(
                    file_path,
                    index,
                    line,
                    marker,
                )

                start = max(
                    1,
                    index - 4,
                )
                end = min(
                    len(lines),
                    index + 5,
                )

                for context_index in range(
                    start,
                    end + 1,
                ):
                    if context_index == index:
                        continue

                    context_line = lines[
                        context_index - 1
                    ]

                    if (
                        "pointSize(" in context_line
                        or "setPointSize(" in context_line
                        or "QFont(" in context_line
                        or "font =" in context_line
                    ):
                        print(
                            f"      {file_path}:"
                            f"{context_index}: "
                            f"{context_line.rstrip()}"
                        )

    if set_point_size_hits == 0:
        print("(keine)")

    print()
    print("2) pointSize()-VERWENDUNGEN")
    print("-" * 110)

    point_size_usage_hits = 0

    for file_path in python_files:
        lines = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        for index, line in enumerate(
            lines,
            start=1,
        ):
            if POINTSIZE_PATTERN.search(
                line
            ):
                point_size_usage_hits += 1

                print_match(
                    file_path,
                    index,
                    line,
                    "[POINTSIZE]",
                )

    if point_size_usage_hits == 0:
        print("(keine)")

    print()
    print("3) QFont()-ERZEUGUNG")
    print("-" * 110)

    for file_path in python_files:
        lines = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        for index, line in enumerate(
            lines,
            start=1,
        ):
            if QFONT_PATTERN.search(
                line
            ):
                qfont_hits += 1

                print_match(
                    file_path,
                    index,
                    line,
                    "[QFONT]",
                )

    if qfont_hits == 0:
        print("(keine)")

    print()
    print("4) NEGATIVE font-size IN QSS")
    print("-" * 110)

    for file_path in style_files:
        lines = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        for index, line in enumerate(
            lines,
            start=1,
        ):
            if QSS_NEGATIVE_FONT_PATTERN.search(
                line
            ):
                negative_qss_hits += 1

                print_match(
                    file_path,
                    index,
                    line,
                    "[QSS]",
                )

    if negative_qss_hits == 0:
        print("(keine)")

    print()
    print("=" * 110)
    print("ZUSAMMENFASSUNG")
    print("=" * 110)
    print(
        f"Python-Dateien geprüft:        "
        f"{len(python_files)}"
    )
    print(
        f"setPointSize()-Treffer:        "
        f"{set_point_size_hits}"
    )
    print(
        f"pointSize()-Treffer:           "
        f"{point_size_usage_hits}"
    )
    print(
        f"Dynamische Treffer:            "
        f"{dynamic_point_size_hits}"
    )
    print(
        f"QFont()-Treffer:               "
        f"{qfont_hits}"
    )
    print(
        f"Negative QSS-font-size Treffer:"
        f" {negative_qss_hits}"
    )

    print()
    print(
        "WICHTIG: Besonders verdächtig sind Stellen, "
        "die eine vorhandene Schrift kopieren und danach "
        "font.pointSize() weiterverwenden. Qt kann dort -1 "
        "liefern, wenn die Schrift pixelbasiert definiert ist."
    )
    print("=" * 110)


if __name__ == "__main__":
    main()
