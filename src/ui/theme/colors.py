from __future__ import annotations


class Colors:
    """
    Zentrale Farbpalette des KreisligaManagers.

    In GUI-Dateien sollen keine Hex-Farben direkt
    verwendet werden. Farben werden ausschließlich
    über diese Klasse bezogen.
    """

    # Hauptflächen
    BACKGROUND = "#1B1D21"
    BACKGROUND_ELEVATED = "#202329"
    SIDEBAR_BACKGROUND = "#181A1F"
    SIDEBAR_BACKGROUND_HOVER = "#252932"
    SIDEBAR_BACKGROUND_ACTIVE = "#313743"

    # Karten und Oberflächen
    CARD_BACKGROUND = "#2B2F36"
    CARD_BACKGROUND_HOVER = "#343943"
    CARD_BACKGROUND_ACTIVE = "#3A404A"

    # Akzentfarben
    PRIMARY = "#4A90E2"
    PRIMARY_HOVER = "#5A9BE8"
    PRIMARY_ACTIVE = "#397DCA"
    PRIMARY_SOFT = "#243A55"

    # Statusfarben
    SUCCESS = "#4CAF50"
    SUCCESS_SOFT = "#203D28"

    WARNING = "#F9A825"
    WARNING_SOFT = "#463710"

    ERROR = "#E53935"
    ERROR_SOFT = "#48201F"

    INFO = "#29B6F6"
    INFO_SOFT = "#173A4D"

    # Text
    TEXT_PRIMARY = "#F5F6F7"
    TEXT_SECONDARY = "#A8AFBA"
    TEXT_MUTED = "#747C88"
    TEXT_DISABLED = "#565D67"
    TEXT_ON_PRIMARY = "#FFFFFF"

    # Linien und Rahmen
    BORDER = "#3A404C"
    BORDER_LIGHT = "#484F5B"
    BORDER_FOCUS = PRIMARY
    DIVIDER = "#2D323A"

    # Interaktion
    HOVER_OVERLAY = "#FFFFFF0A"
    PRESSED_OVERLAY = "#FFFFFF12"
    SELECTED_OVERLAY = "#4A90E226"

    # Tabellen
    TABLE_HEADER = "#252932"
    TABLE_ROW = "#202329"
    TABLE_ROW_ALTERNATE = "#24282F"
    TABLE_ROW_HOVER = "#2D323B"
    TABLE_ROW_SELECTED = "#263B55"

    # Eingabefelder
    INPUT_BACKGROUND = "#202329"
    INPUT_BACKGROUND_HOVER = "#252932"
    INPUT_BORDER = "#3A404C"
    INPUT_BORDER_FOCUS = PRIMARY
    INPUT_PLACEHOLDER = "#747C88"

    # Scrollbars
    SCROLLBAR_TRACK = "transparent"
    SCROLLBAR_HANDLE = "#3A404C"
    SCROLLBAR_HANDLE_HOVER = "#4A5261"

    # Transparenz
    TRANSPARENT = "transparent"

    @classmethod
    def as_dict(
        cls,
    ) -> dict[str, str]:
        return {
            name: value
            for name, value in vars(cls).items()
            if (
                name.isupper()
                and isinstance(value, str)
            )
        }