from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag


HTML_FILE = Path(
    "data/temp/fussballde_match_detail.html"
)

MAX_EVENTS = 20


def clean_text(value: str) -> str:
    return " ".join(value.split())


def print_event(
    event: Tag,
    index: int,
) -> None:
    classes = event.get(
        "class",
        [],
    )

    team_side = "unbekannt"

    if "event-left" in classes:
        team_side = "Heim"

    elif "event-right" in classes:
        team_side = "Auswärts"

    print("\n" + "=" * 100)
    print(
        f"EVENT {index} | "
        f"Seite: {team_side}"
    )
    print("=" * 100)

    print("\nTEXT:")
    print(
        clean_text(
            event.get_text(
                " ",
                strip=True,
            )
        )
    )

    print("\nATTRIBUTE:")
    print(
        dict(event.attrs)
    )

    print("\nHTML:")
    print(
        event.prettify()
    )


def print_half(
    half: Tag,
    half_name: str,
) -> None:
    print("\n" + "#" * 100)
    print(half_name)
    print("#" * 100)

    events = half.select(
        ":scope > .events > .row-event"
    )

    if not events:
        events = half.select(
            ".row-event"
        )

    print(
        f"Gefundene Ereignisse: "
        f"{len(events)}"
    )

    for index, event in enumerate(
        events[:MAX_EVENTS],
        start=1,
    ):
        if not isinstance(
            event,
            Tag,
        ):
            continue

        print_event(
            event=event,
            index=index,
        )


def main() -> None:
    if not HTML_FILE.exists():
        raise FileNotFoundError(
            "HTML-Datei nicht gefunden:\n"
            f"{HTML_FILE.resolve()}"
        )

    html = HTML_FILE.read_text(
        encoding="utf-8",
    )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    match_course = soup.select_one(
        "#match_course_body"
    )

    if not isinstance(
        match_course,
        Tag,
    ):
        raise RuntimeError(
            "#match_course_body "
            "wurde nicht gefunden."
        )

    first_half = match_course.select_one(
        ".first-half"
    )

    second_half = match_course.select_one(
        ".second-half"
    )

    if isinstance(
        first_half,
        Tag,
    ):
        print_half(
            half=first_half,
            half_name="ERSTE HALBZEIT",
        )
    else:
        print(
            "Erste Halbzeit "
            "nicht gefunden."
        )

    if isinstance(
        second_half,
        Tag,
    ):
        print_half(
            half=second_half,
            half_name="ZWEITE HALBZEIT",
        )
    else:
        print(
            "Zweite Halbzeit "
            "nicht gefunden."
        )


if __name__ == "__main__":
    main()