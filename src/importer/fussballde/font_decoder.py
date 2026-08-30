from __future__ import annotations

import io
import re
from typing import Any

from fontTools.agl import toUnicode
from fontTools.ttLib import TTFont


class FontDecoder:
    FONT_URL_TEMPLATE = (
        "https://www.fussball.de/export.fontface/"
        "-/format/woff/id/{font_id}/type/font"
    )

    GLYPH_CHARACTER_MAP = {
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "hyphen": "-",
        "minus": "-",
        "period": ".",
        "comma": ",",
        "colon": ":",
        "semicolon": ";",
        "space": " ",
    }

    FONT_CLASS_PATTERN = re.compile(
        r"(?:^|\s)results-c-([a-zA-Z0-9]+)(?:\s|$)"
    )

    def __init__(self, request_context: Any) -> None:
        self.request_context = request_context
        self._font_maps: dict[str, dict[int, str]] = {}

    def load_font(self, font_id: str) -> dict[int, str]:
        font_id = self._clean_font_id(font_id)

        if font_id in self._font_maps:
            return self._font_maps[font_id]

        font_url = self.FONT_URL_TEMPLATE.format(
            font_id=font_id
        )

        response = self.request_context.get(font_url)

        if not response.ok:
            raise RuntimeError(
                "Schriftart konnte nicht geladen werden: "
                f"{font_id} – HTTP {response.status}"
            )

        font_bytes = response.body()

        if not font_bytes:
            raise RuntimeError(
                f"Schriftart enthält keine Daten: {font_id}"
            )

        character_map = self._create_character_map(
            font_bytes=font_bytes,
            font_id=font_id,
        )

        self._font_maps[font_id] = character_map

        return character_map

    def decode(
        self,
        text: str | None,
        font_id: str,
    ) -> str:
        if not text:
            return ""

        character_map = self.load_font(font_id)

        decoded_characters: list[str] = []

        for character in text:
            code_point = ord(character)

            if code_point in character_map:
                decoded_characters.append(
                    character_map[code_point]
                )
            else:
                decoded_characters.append(character)

        return "".join(decoded_characters)

    def decode_from_class(
        self,
        text: str | None,
        class_name: str | None,
    ) -> str:
        if not text:
            return ""

        font_id = self.extract_font_id(class_name)

        if not font_id:
            return text

        return self.decode(
            text=text,
            font_id=font_id,
        )

    def extract_font_id(
        self,
        class_name: str | None,
    ) -> str | None:
        if not class_name:
            return None

        match = self.FONT_CLASS_PATTERN.search(class_name)

        if not match:
            return None

        return match.group(1)

    def is_font_loaded(self, font_id: str) -> bool:
        font_id = self._clean_font_id(font_id)
        return font_id in self._font_maps

    def clear_cache(self) -> None:
        self._font_maps.clear()

    def get_loaded_font_ids(self) -> list[str]:
        return sorted(self._font_maps.keys())

    def get_character_map(
        self,
        font_id: str,
    ) -> dict[int, str]:
        character_map = self.load_font(font_id)
        return dict(character_map)

    def _create_character_map(
        self,
        font_bytes: bytes,
        font_id: str,
    ) -> dict[int, str]:
        try:
            font = TTFont(io.BytesIO(font_bytes))
        except Exception as error:
            raise RuntimeError(
                f"Schriftart konnte nicht gelesen werden: "
                f"{font_id}"
            ) from error

        try:
            cmap = font.getBestCmap() or {}

            character_map: dict[int, str] = {}

            for code_point, glyph_name in cmap.items():
                decoded_character = (
                    self._glyph_name_to_character(
                        glyph_name
                    )
                )

                if decoded_character is None:
                    continue

                character_map[code_point] = (
                    decoded_character
                )

            if not character_map:
                raise RuntimeError(
                    "Keine entschlüsselbaren Zeichen in "
                    f"Schriftart gefunden: {font_id}"
                )

            return character_map

        finally:
            font.close()

    def _glyph_name_to_character(
        self,
        glyph_name: str,
    ) -> str | None:
        if glyph_name in self.GLYPH_CHARACTER_MAP:
            return self.GLYPH_CHARACTER_MAP[glyph_name]

        if len(glyph_name) == 1:
            return glyph_name

        agl_character = toUnicode(glyph_name)

        if agl_character:
            return agl_character

        if glyph_name.startswith("uni"):
            unicode_value = glyph_name[3:]

            if len(unicode_value) == 4:
                try:
                    return chr(int(unicode_value, 16))
                except ValueError:
                    return None

        if glyph_name.startswith("u"):
            unicode_value = glyph_name[1:]

            if 4 <= len(unicode_value) <= 6:
                try:
                    return chr(int(unicode_value, 16))
                except ValueError:
                    return None

        return None

    def _clean_font_id(self, font_id: str) -> str:
        cleaned_font_id = font_id.strip()

        if not cleaned_font_id:
            raise ValueError(
                "Die Font-ID darf nicht leer sein."
            )

        if not re.fullmatch(
            r"[a-zA-Z0-9]+",
            cleaned_font_id,
        ):
            raise ValueError(
                f"Ungültige Font-ID: {font_id}"
            )

        return cleaned_font_id