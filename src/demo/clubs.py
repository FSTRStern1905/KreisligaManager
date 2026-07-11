from dataclasses import dataclass


@dataclass(slots=True)
class DemoClub:
    name: str
    short_name: str
    city: str
    colors: tuple[str, str]
    founded: int
    strength: int


DEMO_CLUBS = [

    DemoClub(
        "FC Musterstadt",
        "FCM",
        "Musterstadt",
        ("Rot", "Weiß"),
        1921,
        90,
    ),

    DemoClub(
        "SV Grünwald",
        "SVG",
        "Grünwald",
        ("Grün", "Weiß"),
        1948,
        78,
    ),

    DemoClub(
        "TuS Eichenberg",
        "TUSE",
        "Eichenberg",
        ("Blau", "Weiß"),
        1932,
        72,
    ),

    DemoClub(
        "SG Sonnenhof",
        "SGS",
        "Sonnenhof",
        ("Gelb", "Schwarz"),
        1956,
        74,
    ),

    DemoClub(
        "VfL Waldheim",
        "VFL",
        "Waldheim",
        ("Blau", "Gelb"),
        1919,
        81,
    ),

    DemoClub(
        "TSV Oberdorf",
        "TSV",
        "Oberdorf",
        ("Rot", "Schwarz"),
        1946,
        69,
    ),

    DemoClub(
        "FC Rotbach",
        "FCR",
        "Rotbach",
        ("Rot", "Blau"),
        1938,
        76,
    ),

    DemoClub(
        "SV Blaufels",
        "SVB",
        "Blaufels",
        ("Blau", "Weiß"),
        1964,
        67,
    ),

    DemoClub(
        "DJK Linden",
        "DJK",
        "Linden",
        ("Grün", "Schwarz"),
        1952,
        73,
    ),

    DemoClub(
        "FC Adlerhöhe",
        "FCA",
        "Adlerhöhe",
        ("Schwarz", "Gold"),
        1928,
        88,
    ),

    DemoClub(
        "SG Moseltal",
        "SGM",
        "Moseltal",
        ("Weiß", "Blau"),
        1972,
        70,
    ),

    DemoClub(
        "TuS Rheinblick",
        "TUSR",
        "Rheinblick",
        ("Blau", "Rot"),
        1949,
        82,
    ),
]