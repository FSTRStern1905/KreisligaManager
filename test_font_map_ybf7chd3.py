from __future__ import annotations

import io

from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright

from src.importer.fussballde.font_decoder import FontDecoder


FONT_ID = "ybf7chd3"

FIRSTNAME_RAW = "\ue8c6\uee7d\uf026\ue9bb\uecd7"
LASTNAME_RAW = "\ued0a\ueea9\uea4f\uec35\ue819\ueeee"


def dump_text(
    label: str,
    text: str,
    decoder: FontDecoder,
    cmap: dict[int, str],
) -> None:
    print()
    print("=" * 90)
    print(label)
    print("=" * 90)

    decoded = decoder.decode(
        text=text,
        font_id=FONT_ID,
    )

    print(f"RAW:     {text!r}")
    print(f"DECODED: {decoded!r}")
    print()

    for char in text:
        cp = ord(char)

        print(
            f"U+{cp:04X} | "
            f"FontDecoder-Map={cmap.get(cp)!r}"
        )


def main() -> None:
    print("=" * 90)
    print("FONT-MAP-DIAGNOSE ybf7chd3")
    print("=" * 90)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True
        )
        page = browser.new_page()

        decoder = FontDecoder(
            page.request
        )

        cmap = decoder.get_character_map(
            FONT_ID
        )

        print(
            f"FontDecoder-Zuordnungen: "
            f"{len(cmap)}"
        )

        dump_text(
            "VORNAME",
            FIRSTNAME_RAW,
            decoder,
            cmap,
        )

        dump_text(
            "NACHNAME",
            LASTNAME_RAW,
            decoder,
            cmap,
        )

        print()
        print("=" * 90)
        print("ROHE FONT-CMAP / GLYPH-NAMEN")
        print("=" * 90)

        font_url = (
            "https://www.fussball.de/export.fontface/"
            f"-/format/woff/id/{FONT_ID}/type/font"
        )

        response = page.request.get(
            font_url,
            timeout=60_000,
        )

        if not response.ok:
            raise RuntimeError(
                f"Font HTTP {response.status}"
            )

        font = TTFont(
            io.BytesIO(
                response.body()
            )
        )

        try:
            raw_cmap = (
                font.getBestCmap()
                or {}
            )

            codepoints = {
                ord(char)
                for char in (
                    FIRSTNAME_RAW
                    + LASTNAME_RAW
                )
            }

            for cp in sorted(codepoints):
                glyph_name = raw_cmap.get(cp)

                print(
                    f"U+{cp:04X} | "
                    f"glyph={glyph_name!r} | "
                    f"decoder={cmap.get(cp)!r}"
                )
        finally:
            font.close()

        print()
        print("=" * 90)
        print("DIAGNOSE ENDE")
        print("=" * 90)

        browser.close()


if __name__ == "__main__":
    main()
