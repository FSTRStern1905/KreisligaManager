from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.importer.fussballde.font_decoder import FontDecoder
from src.importer.fussballde.parsers.lineup_parser import LineupParser

MATCH_ID = "02TKDR1UT8000000VS5489BUVUD1610F"
TICKER_ID = "02UR2JDJ7K000001VS5489C0VU0KF5US"
TARGET_ID = "01MH0AKR74000001VV0AG13EVSFDFGE6"

URL = (
    "https://www.fussball.de/ajax.match.lineup/"
    f"-/mode/PAGE/spiel/{MATCH_ID}/ticker-id/{TICKER_ID}"
)


def private_unicode(text):
    return any("\ue000" <= c <= "\uf8ff" for c in text)


def main():
    print("=" * 90)
    print("LINEUP-NAMENSDEKODIERUNG: SPIEL 251 / KEVIN STÖGER")
    print("=" * 90)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        response = page.request.get(URL, timeout=60000)

        print("HTTP:", response.status)
        html = response.text()
        print("HTML-Länge:", len(html))

        soup = BeautifulSoup(html, "html.parser")
        decoder = FontDecoder(page.request)

        target = None
        for node in soup.select(".player-wrapper"):
            if TARGET_ID in str(node):
                target = node
                break

        if target is None:
            print("External-ID nicht im player-wrapper gefunden.")
            print("Kevin-Kandidaten:")
            for node in soup.select(".player-wrapper"):
                if "kevin" in node.get_text(" ", strip=True).casefold():
                    print(node.prettify()[:4000])
            browser.close()
            return

        print("\n" + "=" * 90)
        print("1) ROHES PLAYER-ELEMENT")
        print("=" * 90)
        print(target.prettify()[:6000])

        print("\n" + "=" * 90)
        print("2) NAME-DEKODIERUNG")
        print("=" * 90)

        for selector in (".firstname", ".lastname"):
            node = target.select_one(selector)
            print("\n", selector)

            if node is None:
                print("NICHT VORHANDEN")
                continue

            raw = node.get_text("", strip=False)
            classes = " ".join(node.get("class", []))
            font_id = decoder.extract_font_id(classes)

            if font_id:
                decoded = decoder.decode(raw, font_id)
            else:
                decoded = raw

            print("raw repr:       ", repr(raw))
            print("raw codepoints: ", " ".join(f"U+{ord(c):04X}" for c in raw))
            print("class:          ", repr(classes))
            print("font_id:        ", repr(font_id))
            print("decoded repr:   ", repr(decoded))
            print("private raw:    ", private_unicode(raw))
            print("private decoded:", private_unicode(decoded))

            if font_id:
                cmap = decoder.get_character_map(font_id)
                relevant = {
                    f"U+{ord(c):04X}": cmap.get(ord(c))
                    for c in raw
                    if "\ue000" <= c <= "\uf8ff"
                }
                print("relevante cmap: ", relevant)

        print("\n" + "=" * 90)
        print("3) LINEUPPARSER-ERGEBNIS")
        print("=" * 90)

        lineup = LineupParser(request_context=page.request).parse(html)

        for label, team in (("HEIM", lineup.home), ("AUSWÄRTS", lineup.away)):
            for player in team.players:
                name = f"{player.first_name} {player.last_name}".strip()
                if player.external_id == TARGET_ID or "kevin" in name.casefold():
                    print(
                        label,
                        "|", team.team_name,
                        "|", repr(player.first_name),
                        "|", repr(player.last_name),
                        "|", player.external_id,
                        "| Starter:", player.is_starting,
                    )

        print("\n" + "=" * 90)
        print("DIAGNOSE ENDE")
        print("=" * 90)
        browser.close()


if __name__ == "__main__":
    main()
