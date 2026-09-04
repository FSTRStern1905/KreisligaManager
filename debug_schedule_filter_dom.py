from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.browser import FussballDeBrowser


URL = (
    "https://www.fussball.de/spielplan/"
    "regionalliga-suedwest-deutschland-"
    "regionalliga-suedwest-herren-saison2627-"
    "deutschland/-/staffel/"
    "031D0NRQ3O000004VS5489BUVUR5FS5A-G"
    "#!/section/matchplan"
)


def short_html(
    value: str,
    limit: int = 1400,
) -> str:
    value = " ".join(
        value.split()
    )

    if len(value) <= limit:
        return value

    return (
        value[:limit]
        + " ..."
    )


def main() -> None:
    browser = FussballDeBrowser()

    try:
        print(
            "Browser wird gestartet ..."
        )

        browser.start(
            headless=False,
        )

        browser.open(
            URL
        )

        if browser.page is None:
            raise RuntimeError(
                "FUSSBALL.DE wurde nicht geladen."
            )

        page = browser.page

        page.wait_for_timeout(
            1500
        )

        print()
        print(
            "=" * 100
        )
        print(
            "FILTER-DOM DEBUG"
        )
        print(
            "=" * 100
        )

        inputs = page.locator(
            "input"
        )

        print(
            f"INPUTS: {inputs.count()}"
        )

        for index in range(
            inputs.count()
        ):
            locator = inputs.nth(
                index
            )

            try:
                attrs = locator.evaluate(
                    """el => ({
                        type: el.type,
                        name: el.name,
                        id: el.id,
                        className: el.className,
                        value: el.value,
                        placeholder: el.placeholder,
                        outerHTML: el.outerHTML
                    })"""
                )
            except Exception as error:
                print(
                    f"[INPUT {index}] FEHLER: {error}"
                )
                continue

            print(
                f"[INPUT {index}] "
                f"type={attrs.get('type')!r} "
                f"name={attrs.get('name')!r} "
                f"id={attrs.get('id')!r} "
                f"class={attrs.get('className')!r} "
                f"value={attrs.get('value')!r} "
                f"placeholder={attrs.get('placeholder')!r}"
            )
            print(
                short_html(
                    str(
                        attrs.get(
                            "outerHTML",
                            "",
                        )
                    )
                )
            )
            print()

        print(
            "=" * 100
        )
        print(
            "BUTTONS / LINKS MIT LOS"
        )
        print(
            "=" * 100
        )

        candidates = page.locator(
            "button, a, input[type='submit'], "
            "input[type='button']"
        )

        found = 0

        for index in range(
            candidates.count()
        ):
            locator = candidates.nth(
                index
            )

            try:
                data = locator.evaluate(
                    """el => ({
                        tag: el.tagName,
                        text: (el.innerText || el.value || '').trim(),
                        id: el.id,
                        className: el.className,
                        href: el.href || '',
                        type: el.type || '',
                        outerHTML: el.outerHTML
                    })"""
                )
            except Exception:
                continue

            text = str(
                data.get(
                    "text",
                    "",
                )
            )

            outer_html = str(
                data.get(
                    "outerHTML",
                    "",
                )
            )

            if (
                "LOS" not in text.upper()
                and "LOS" not in outer_html.upper()
            ):
                continue

            found += 1

            print(
                f"[KANDIDAT {found}] "
                f"tag={data.get('tag')} "
                f"text={text!r} "
                f"id={data.get('id')!r} "
                f"class={data.get('className')!r} "
                f"type={data.get('type')!r} "
                f"href={data.get('href')!r}"
            )
            print(
                short_html(
                    outer_html,
                    2200,
                )
            )
            print()

        if found == 0:
            print(
                "Kein LOS-Kandidat gefunden."
            )

        print(
            "=" * 100
        )
        print(
            "FORMULARE MIT DATUMSFELDERN"
        )
        print(
            "=" * 100
        )

        html = page.content()

        soup = BeautifulSoup(
            html,
            "lxml",
        )

        forms = soup.find_all(
            "form"
        )

        for index, form in enumerate(
            forms,
            start=1,
        ):
            if not isinstance(
                form,
                Tag,
            ):
                continue

            form_text = " ".join(
                form.get_text(
                    " ",
                    strip=True,
                ).split()
            )

            form_html = str(
                form
            )

            if (
                "2026" not in form_html
                and "2027" not in form_html
                and "Von:" not in form_text
                and "Bis:" not in form_text
            ):
                continue

            print(
                f"[FORM {index}]"
            )
            print(
                short_html(
                    form_html,
                    5000,
                )
            )
            print()

        print(
            "=" * 100
        )
        print(
            "DEBUG FERTIG"
        )
        print(
            "=" * 100
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()
