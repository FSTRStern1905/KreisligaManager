from __future__ import annotations

import io
import sys
from collections import Counter

from fontTools.ttLib import TTFont

from src.importer.fussballde.browser import FussballDeBrowser


TABLE_SELECTOR = "#fixtures-matchplan-table-matches-table"

FONT_CLASS_PREFIX = "results-c-"


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.font_mapping_tester "
            "\"https://www.fussball.de/spielplan/...\""
        )
        sys.exit(1)

    url = sys.argv[1]
    browser = FussballDeBrowser()

    try:
        browser.start()
        browser.open(url)

        if browser.page is None:
            raise RuntimeError(
                "Die fussball.de-Seite wurde nicht geladen."
            )

        page = browser.page

        font_data = page.evaluate(
            f"""
            () => {{
                const table = document.querySelector(
                    "{TABLE_SELECTOR}"
                );

                if (!table) {{
                    return [];
                }}

                const elements = table.querySelectorAll(
                    '[class*="{FONT_CLASS_PREFIX}"]'
                );

                const results = [];
                const seen = new Set();

                for (const element of elements) {{
                    const classNames = Array.from(element.classList);

                    const resultClass = classNames.find(
                        className =>
                            className.startsWith(
                                "{FONT_CLASS_PREFIX}"
                            )
                    );

                    if (!resultClass) {{
                        continue;
                    }}

                    const fontId = resultClass.replace(
                        "{FONT_CLASS_PREFIX}",
                        ""
                    );

                    const key = [
                        fontId,
                        element.textContent || ""
                    ].join("|");

                    if (seen.has(key)) {{
                        continue;
                    }}

                    seen.add(key);

                    results.push({{
                        fontId: fontId,
                        className: resultClass,
                        text: element.textContent || "",
                        codePoints: Array.from(
                            element.textContent || ""
                        ).map(character =>
                            character.codePointAt(0)
                        )
                    }});
                }}

                return results;
            }}
            """
        )

        if not font_data:
            raise RuntimeError(
                "Keine verschleierten Font-Elemente gefunden."
            )

        font_ids = sorted(
            {
                entry["fontId"]
                for entry in font_data
                if entry.get("fontId")
            }
        )

        print()
        print("=" * 80)
        print("GEFUNDENE DYNAMISCHE FONTS")
        print("=" * 80)

        for font_id in font_ids:
            print(font_id)

        for font_id in font_ids:
            inspect_font(
                page=page,
                font_id=font_id,
                font_data=font_data,
            )

    finally:
        browser.close()


def inspect_font(
    page,
    font_id: str,
    font_data: list[dict],
) -> None:
    font_url = (
        "https://www.fussball.de/export.fontface/"
        f"-/format/woff/id/{font_id}/type/font"
    )

    print()
    print("=" * 80)
    print(f"FONT: {font_id}")
    print("=" * 80)
    print(f"URL: {font_url}")

    response = page.request.get(font_url)

    if not response.ok:
        raise RuntimeError(
            f"Font konnte nicht geladen werden: "
            f"HTTP {response.status}"
        )

    font_bytes = response.body()

    print(f"Dateigröße: {len(font_bytes)} Bytes")

    font = TTFont(io.BytesIO(font_bytes))

    print_font_information(font)
    print_used_characters(
        font=font,
        font_id=font_id,
        font_data=font_data,
    )


def print_font_information(font: TTFont) -> None:
    print()
    print("FONT-INFORMATIONEN")
    print("-" * 80)

    print(f"Tabellen: {', '.join(font.keys())}")

    glyph_order = font.getGlyphOrder()

    print(f"Glyphen insgesamt: {len(glyph_order)}")

    print()
    print("ERSTE GLYPH-NAMEN")
    print("-" * 80)

    for index, glyph_name in enumerate(
        glyph_order[:100],
        start=1,
    ):
        print(f"{index:>3}: {glyph_name}")


def print_used_characters(
    font: TTFont,
    font_id: str,
    font_data: list[dict],
) -> None:
    cmap = font.getBestCmap() or {}

    matching_entries = [
        entry
        for entry in font_data
        if entry.get("fontId") == font_id
    ]

    character_counter: Counter[int] = Counter()

    for entry in matching_entries:
        for code_point in entry.get("codePoints", []):
            character_counter[code_point] += 1

    print()
    print("VERWENDETE ZEICHEN UND GLYPHEN")
    print("-" * 80)

    for code_point, count in character_counter.most_common():
        character = chr(code_point)
        glyph_name = cmap.get(code_point, "<nicht im cmap>")

        print(
            f"Zeichen: {repr(character):>10} | "
            f"Unicode: U+{code_point:04X} | "
            f"Glyph: {glyph_name:<25} | "
            f"Verwendet: {count}"
        )

    print()
    print("TEXTBEISPIELE")
    print("-" * 80)

    for index, entry in enumerate(
        matching_entries[:20],
        start=1,
    ):
        text = entry.get("text", "")

        mapped_glyphs = []

        for character in text:
            code_point = ord(character)
            glyph_name = cmap.get(
                code_point,
                "<nicht im cmap>",
            )

            mapped_glyphs.append(
                f"{character}=U+{code_point:04X}/{glyph_name}"
            )

        print()
        print(f"[{index}] Text: {repr(text)}")
        print("    " + " | ".join(mapped_glyphs))


if __name__ == "__main__":
    main()