from __future__ import annotations

from src.importer.fussballde.parsers.match_detail_data import (
    MatchDetailData,
)


class MatchNotesBuilder:
    """
    Baut und bereinigt die gespeicherten Zusatzinformationen
    eines importierten Spiels.
    """

    MANAGED_PREFIXES = (
        "Halbzeit:",
        "Spielstätte:",
        "Schiedsrichter:",
        "fussball.de:",
    )

    REFEREE_SUFFIXES = (
        " Assistenten:",
        " Assistent:",
        " Schiedsrichterassistenten:",
        " Schiedsrichter-Assistenten:",
    )

    @classmethod
    def build(
        cls,
        existing_notes: str,
        detail_data: MatchDetailData,
        source_url: str,
    ) -> str:
        notes: list[str] = []

        existing_lines = (
            existing_notes.splitlines()
            if existing_notes
            else []
        )

        for line in existing_lines:
            normalized_line = line.strip()

            if not normalized_line:
                continue

            if normalized_line.startswith(
                cls.MANAGED_PREFIXES
            ):
                continue

            if cls.contains_private_unicode(
                normalized_line
            ):
                continue

            notes.append(
                normalized_line
            )

        if (
            detail_data.halftime_home is not None
            and detail_data.halftime_away is not None
        ):
            notes.append(
                "Halbzeit: "
                f"{detail_data.halftime_home}:"
                f"{detail_data.halftime_away}"
            )

        stadium = cls.clean_import_text(
            detail_data.stadium
        )

        if stadium:
            notes.append(
                f"Spielstätte: {stadium}"
            )

        referee = cls.clean_import_text(
            detail_data.referee
        )

        referee = cls.remove_referee_suffixes(
            referee
        )

        if referee:
            notes.append(
                f"Schiedsrichter: {referee}"
            )

        normalized_url = source_url.strip()

        if normalized_url:
            notes.append(
                f"fussball.de: {normalized_url}"
            )

        return "\n".join(
            dict.fromkeys(notes)
        )

    @classmethod
    def clean_import_text(
        cls,
        value: str,
        allow_private_unicode: bool = False,
    ) -> str:
        normalized = " ".join(
            (value or "").split()
        )

        if not normalized:
            return ""

        if (
            not allow_private_unicode
            and cls.contains_private_unicode(
                normalized
            )
        ):
            return ""

        return normalized.strip(
            " -|,;"
        )

    @staticmethod
    def contains_private_unicode(
        value: str,
    ) -> bool:
        return any(
            0xE000 <= ord(character) <= 0xF8FF
            for character in value
        )

    @classmethod
    def remove_referee_suffixes(
        cls,
        referee_name: str,
    ) -> str:
        normalized_name = referee_name.strip()

        for suffix in cls.REFEREE_SUFFIXES:
            position = normalized_name.casefold().find(
                suffix.casefold()
            )

            if position >= 0:
                normalized_name = (
                    normalized_name[:position]
                ).strip()

        return normalized_name