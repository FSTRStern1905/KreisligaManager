from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionStadiumMapTab(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.competition_id: int | None = None

        self.setup_ui()

    def setup_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )
        layout.setSpacing(10)

        self.info_label = QLabel(
            "🗺️ Spielstättenkarte"
        )
        self.info_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
            """
        )

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(500)
        self.web_view.titleChanged.connect(
            self._map_title_changed
        )

        self.sidebar = self._create_sidebar()

        content_layout.addWidget(
            self.web_view,
            1,
        )
        content_layout.addWidget(
            self.sidebar,
            0,
        )

        layout.addWidget(self.info_label)
        layout.addLayout(
            content_layout,
            1,
        )

        self.show_empty_map()

    def _create_sidebar(
        self,
    ) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setStyleSheet(
            """
            QFrame {
                background: #1b1f25;
                border: 1px solid #39424d;
                border-radius: 7px;
            }

            QLabel {
                border: none;
                background: transparent;
            }

            QRadioButton,
            QCheckBox {
                border: none;
                background: transparent;
                spacing: 8px;
                padding: 3px 0;
            }

            QRadioButton::indicator,
            QCheckBox::indicator {
                width: 17px;
                height: 17px;
            }
            """
        )

        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(
            14,
            14,
            14,
            14,
        )
        outer.setSpacing(9)

        title = QLabel("Anzeige")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 700;"
        )
        outer.addWidget(title)

        self.radio_all = QRadioButton(
            "Alle Spielstätten"
        )
        self.radio_competition = QRadioButton(
            "Nur ausgewählter Wettbewerb"
        )
        self.radio_clubs = QRadioButton(
            "Vereine anzeigen"
        )

        self.radio_competition.setChecked(True)

        # V5: competition/all is functional.
        # Club-specific markers are prepared visually and
        # will be wired once club venue assignment is defined.
        self.radio_clubs.setEnabled(False)

        self.radio_all.toggled.connect(
            self._display_mode_changed
        )
        self.radio_competition.toggled.connect(
            self._display_mode_changed
        )

        outer.addWidget(self.radio_all)
        outer.addWidget(self.radio_competition)
        outer.addWidget(self.radio_clubs)

        outer.addSpacing(6)

        self.check_germany = QCheckBox(
            "Deutschland-Grenze"
        )
        self.check_states = QCheckBox(
            "Bundesländer"
        )
        self.check_active_states = QCheckBox(
            "Teilnehmende Bundesländer hervorheben"
        )
        self.check_active_states.setToolTip(
            "Teilnehmende Bundesländer auf der Karte hervorheben"
        )

        self.check_germany.setChecked(True)
        self.check_states.setChecked(True)
        self.check_active_states.setChecked(True)

        self.check_germany.toggled.connect(
            self.refresh
        )
        self.check_states.toggled.connect(
            self.refresh
        )
        self.check_active_states.toggled.connect(
            self.refresh
        )

        outer.addWidget(self.check_germany)
        outer.addWidget(self.check_states)
        outer.addWidget(self.check_active_states)

        outer.addWidget(
            self._separator()
        )

        legend_title = QLabel("Legende")
        legend_title.setStyleSheet(
            "font-size: 15px; font-weight: 700;"
        )
        outer.addWidget(legend_title)

        self.legend_label = QLabel(
            "🔵  Hauptspielstätte\n"
            "🟠  Ausweichspielstätte\n"
            "▣  Teilnehmendes Bundesland\n"
            "□  Übriges Bundesland\n"
            "▭  Deutschland-Grenze"
        )
        self.legend_label.setWordWrap(True)
        self.legend_label.setStyleSheet(
            "line-height: 1.5;"
        )
        outer.addWidget(self.legend_label)

        outer.addWidget(
            self._separator()
        )

        info_title = QLabel("ℹ  Info")
        info_title.setStyleSheet(
            "font-size: 15px; font-weight: 700;"
        )
        outer.addWidget(info_title)

        self.competition_name_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.competition_name_label.setStyleSheet(
            "font-weight: 600;"
        )
        self.competition_name_label.setWordWrap(True)
        outer.addWidget(
            self.competition_name_label
        )

        self.states_label = QLabel(
            "Teilnehmende Bundesländer:\n–"
        )
        self.states_label.setWordWrap(True)
        self.states_label.setStyleSheet(
            "color: #b8bec8; line-height: 1.35;"
        )
        outer.addWidget(self.states_label)

        self.counts_label = QLabel(
            "Anzahl Vereine: –\n"
            "Hauptspielstätten: –\n"
            "Ausweichspielstätten: –\n"
            "Spielstätten gesamt: –"
        )
        self.counts_label.setStyleSheet(
            "color: #b8bec8; line-height: 1.35;"
        )
        outer.addWidget(self.counts_label)

        outer.addStretch(1)

        return sidebar

    def _separator(
        self,
    ) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(
            "background: #39424d; border: none;"
        )
        return line

    def _map_title_changed(
        self,
        title: str,
    ) -> None:
        if not hasattr(
            self,
            "states_label",
        ):
            return

        names = [
            value.strip()
            for value in title.split("|")
            if value.strip()
        ]

        if not names:
            self.states_label.setText(
                "Teilnehmende Bundesländer:\n–"
            )
            return

        lines = "\n".join(
            f"• {name}"
            for name in names
        )

        self.states_label.setText(
            "Teilnehmende Bundesländer:\n"
            + lines
        )

    def _display_mode_changed(
        self,
        checked: bool,
    ) -> None:
        if checked:
            self.refresh()

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        self.competition_id = competition_id

        self.refresh()

    def refresh(
        self,
    ) -> None:
        stadiums = self.load_stadiums()
        competition_info = (
            self.load_competition_info()
        )

        self.info_label.setText(
            (
                "🗺️ Spielstättenkarte"
                f" · {len(stadiums)} Standorte"
            )
        )

        if hasattr(
            self,
            "competition_name_label",
        ):
            self.competition_name_label.setText(
                competition_info["name"]
            )

            main_count = sum(
                1
                for stadium in stadiums
                if stadium.get("is_main")
            )
            alternate_count = sum(
                1
                for stadium in stadiums
                if stadium.get("is_alternate")
            )

            self.counts_label.setText(
                (
                    f'Vereine: {competition_info["team_count"]}\n'
                    f'Hauptspielstätten: {main_count}\n'
                    f'Ausweichspielstätten: {alternate_count}\n'
                    f'Gesamt: {len(stadiums)}'
                )
            )

        self.render_map(
            stadiums
        )

    def load_stadiums(
        self,
    ) -> list[dict]:
        connection = sqlite3.connect(
            DATABASE_PATH
        )

        connection.row_factory = (
            sqlite3.Row
        )

        try:
            cursor = connection.cursor()

            show_all = (
                self.competition_id is None
                or (
                    hasattr(self, "radio_all")
                    and self.radio_all.isChecked()
                )
            )

            if show_all:
                cursor.execute(
                    """
                    SELECT
                        stadium_id,
                        name,
                        city,
                        address,
                        latitude,
                        longitude
                    FROM stadiums
                    WHERE
                        latitude IS NOT NULL
                        AND longitude IS NOT NULL
                    ORDER BY name
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT DISTINCT
                        s.stadium_id,
                        s.name,
                        s.city,
                        s.address,
                        s.latitude,
                        s.longitude
                    FROM stadiums AS s
                    INNER JOIN matches AS m
                        ON m.stadium_id = s.stadium_id
                    WHERE
                        m.competition_id = ?
                        AND s.latitude IS NOT NULL
                        AND s.longitude IS NOT NULL
                    ORDER BY s.name
                    """,
                    (self.competition_id,),
                )

            stadiums = []

            for row in cursor.fetchall():
                stadiums.append(
                    {
                        "id": row[
                            "stadium_id"
                        ],
                        "name": (
                            row["name"]
                            or "Unbekannte Spielstätte"
                        ),
                        "city": (
                            row["city"]
                            or ""
                        ),
                        "address": (
                            row["address"]
                            or ""
                        ),
                        "latitude": float(
                            row["latitude"]
                        ),
                        "longitude": float(
                            row["longitude"]
                        ),
                    }
                )

            if (
                not show_all
                and self.competition_id is not None
            ):
                usage_rows = cursor.execute(
                    """
                    SELECT
                        home_team_id,
                        stadium_id,
                        COUNT(*) AS home_matches
                    FROM matches
                    WHERE
                        competition_id = ?
                        AND stadium_id IS NOT NULL
                    GROUP BY
                        home_team_id,
                        stadium_id
                    ORDER BY
                        home_team_id,
                        home_matches DESC,
                        stadium_id
                    """,
                    (self.competition_id,),
                ).fetchall()

                usage_by_team = {}

                for usage_row in usage_rows:
                    team_id = usage_row["home_team_id"]

                    usage_by_team.setdefault(
                        team_id,
                        [],
                    ).append(
                        {
                            "stadium_id":
                                usage_row["stadium_id"],
                            "home_matches":
                                usage_row["home_matches"],
                        }
                    )

                main_stadium_by_team = {}

                for team_id, usages in (
                    usage_by_team.items()
                ):
                    if usages:
                        main_stadium_by_team[
                            team_id
                        ] = usages[0]["stadium_id"]

                team_names = {
                    row["team_id"]: row["name"]
                    for row in cursor.execute(
                        """
                        SELECT team_id, name
                        FROM teams
                        """
                    ).fetchall()
                }

                for stadium in stadiums:
                    stadium_id = stadium["id"]
                    main_for = []
                    alternate_for = []
                    usage_details = []

                    for team_id, usages in (
                        usage_by_team.items()
                    ):
                        for usage in usages:
                            if (
                                usage["stadium_id"]
                                != stadium_id
                            ):
                                continue

                            team_name = team_names.get(
                                team_id,
                                f"Mannschaft {team_id}",
                            )
                            home_matches = usage[
                                "home_matches"
                            ]

                            is_main = (
                                main_stadium_by_team.get(
                                    team_id
                                )
                                == stadium_id
                            )

                            usage_details.append(
                                {
                                    "team": team_name,
                                    "home_matches":
                                        home_matches,
                                    "role": (
                                        "main"
                                        if is_main
                                        else "alternate"
                                    ),
                                }
                            )

                            if is_main:
                                main_for.append(
                                    team_name
                                )
                            else:
                                alternate_for.append(
                                    team_name
                                )

                    stadium["is_main"] = bool(
                        main_for
                    )
                    stadium["is_alternate"] = bool(
                        alternate_for
                    )
                    stadium["main_for"] = main_for
                    stadium[
                        "alternate_for"
                    ] = alternate_for
                    stadium[
                        "usage_details"
                    ] = usage_details
            else:
                for stadium in stadiums:
                    stadium["is_main"] = False
                    stadium[
                        "is_alternate"
                    ] = False
                    stadium["main_for"] = []
                    stadium[
                        "alternate_for"
                    ] = []
                    stadium[
                        "usage_details"
                    ] = []

            return stadiums

        finally:
            connection.close()

    def load_competition_info(
        self,
    ) -> dict:
        result = {
            "name": "Kein Wettbewerb ausgewählt",
            "team_count": 0,
        }

        if self.competition_id is None:
            return result

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            cursor = connection.cursor()

            row = cursor.execute(
                """
                SELECT name
                FROM competitions
                WHERE competition_id = ?
                """,
                (self.competition_id,),
            ).fetchone()

            if row:
                result["name"] = (
                    row[0]
                    or "Unbekannter Wettbewerb"
                )

            team_row = cursor.execute(
                """
                SELECT COUNT(DISTINCT team_id)
                FROM (
                    SELECT home_team_id AS team_id
                    FROM matches
                    WHERE competition_id = ?

                    UNION

                    SELECT away_team_id AS team_id
                    FROM matches
                    WHERE competition_id = ?
                )
                """,
                (
                    self.competition_id,
                    self.competition_id,
                ),
            ).fetchone()

            if team_row:
                result["team_count"] = (
                    team_row[0]
                    or 0
                )

            return result

        finally:
            connection.close()

    def show_empty_map(
        self,
    ) -> None:
        self.render_map([])

    def render_map(
        self,
        stadiums: list[dict],
    ) -> None:
        marker_data = json.dumps(
            stadiums,
            ensure_ascii=False,
        )

        show_germany = (
            self.check_germany.isChecked()
            if hasattr(self, "check_germany")
            else True
        )
        show_states = (
            self.check_states.isChecked()
            if hasattr(self, "check_states")
            else True
        )
        highlight_active = (
            self.check_active_states.isChecked()
            if hasattr(
                self,
                "check_active_states",
            )
            else True
        )

        html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Spielstättenkarte</title>

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    >

    <script
        src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
    </script>

    <style>
        html,
        body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            background: #15181d;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }}

        #map {{
            width: 100%;
            height: 100%;
            background: #15181d;
        }}

        .leaflet-popup-content-wrapper,
        .leaflet-popup-tip {{
            background: #22262d;
            color: #f2f2f2;
        }}

        .leaflet-popup-content {{
            margin: 12px 14px;
            line-height: 1.4;
        }}

        .stadium-name {{
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .stadium-detail {{
            color: #b8bec8;
            font-size: 12px;
        }}

        .stadium-role {{
            margin-top: 7px;
            font-size: 12px;
            font-weight: 700;
        }}

        .stadium-role-main {{
            color: #58a6ff;
        }}

        .stadium-role-alternate {{
            color: #ff9f43;
        }}

        .stadium-usage {{
            margin-top: 3px;
            color: #d7dbe0;
            font-size: 11px;
        }}

        .venue-marker {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            border: 3px solid #ffffff;
            box-shadow:
                0 1px 5px rgba(0, 0, 0, 0.65);
        }}

        .venue-marker-main {{
            background: #3388ff;
        }}

        .venue-marker-alternate {{
            background: #ff9f43;
        }}

        .venue-marker-mixed {{
            background:
                linear-gradient(
                    90deg,
                    #3388ff 0%,
                    #3388ff 50%,
                    #ff9f43 50%,
                    #ff9f43 100%
                );
        }}

        .map-legend {{
            background: rgba(25, 29, 35, 0.94);
            color: #e8ebef;
            padding: 10px 12px;
            border: 1px solid #46505c;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
            line-height: 1.45;
            min-width: 185px;
        }}

        .map-legend-title {{
            font-weight: 700;
            margin-bottom: 7px;
        }}

        .legend-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 4px 0;
            font-size: 12px;
        }}

        .legend-box {{
            width: 18px;
            height: 11px;
            box-sizing: border-box;
        }}

        .legend-active {{
            background: rgba(48, 145, 255, 0.30);
            border: 2px solid #3b9cff;
        }}

        .legend-state {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid #8c96a3;
        }}

        .legend-germany {{
            background: transparent;
            border: 2px solid #f2c94c;
        }}

        .state-tooltip {{
            background: rgba(24, 28, 34, 0.95);
            color: #ffffff;
            border: 1px solid #4e5966;
            box-shadow: none;
            font-weight: 600;
        }}
    </style>
</head>

<body>

<div id="map"></div>

<script>
    const stadiums = {marker_data};
    const showGermany = {str(show_germany).lower()};
    const showStates = {str(show_states).lower()};
    const highlightActive =
        {str(highlight_active).lower()};

    /*
     * Zwei Qualitätsstufen:
     *
     * - LOW: schnelle Darstellung der Bundesländer
     * - HIGH: präzise Punkt-in-Polygon-Zuordnung für
     *   Grenzstädte wie Ulm / Neu-Ulm
     */
    const STATES_DISPLAY_URL =
        "https://raw.githubusercontent.com/"
        + "isellsoap/deutschlandGeoJSON/master/"
        + "2_bundeslaender/4_niedrig.geo.json";

    const STATES_DETECTION_URL =
        "https://raw.githubusercontent.com/"
        + "isellsoap/deutschlandGeoJSON/master/"
        + "2_bundeslaender/1_sehr_hoch.geo.json";



    const map = L.map(
        "map",
        {{
            zoomControl: true,
            attributionControl: true
        }}
    );

    L.tileLayer(
        "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
        {{
            maxZoom: 19,
            attribution:
                "&copy; OpenStreetMap-Mitwirkende"
        }}
    ).addTo(map);

    map.attributionControl.addAttribution(
        "Grenzen: deutschlandGeoJSON"
    );

    const bounds = [];

    function escapeHtml(value) {{
        if (!value) {{
            return "";
        }}

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }}

    function featureName(feature) {{
        const properties = feature.properties || {{}};

        return (
            properties.NAME_1
            || properties.name
            || properties.NAME
            || properties.GEN
            || properties.Name
            || properties.NAME_0
            || "Bundesland"
        );
    }}

    function pointInRing(point, ring) {{
        const x = point[0];
        const y = point[1];

        let inside = false;

        for (
            let i = 0, j = ring.length - 1;
            i < ring.length;
            j = i++
        ) {{
            const xi = ring[i][0];
            const yi = ring[i][1];
            const xj = ring[j][0];
            const yj = ring[j][1];

            const intersects =
                ((yi > y) !== (yj > y))
                && (
                    x
                    < (
                        (xj - xi)
                        * (y - yi)
                        / ((yj - yi) || 1e-12)
                        + xi
                    )
                );

            if (intersects) {{
                inside = !inside;
            }}
        }}

        return inside;
    }}

    function pointInPolygon(point, polygon) {{
        if (!polygon || polygon.length === 0) {{
            return false;
        }}

        if (!pointInRing(point, polygon[0])) {{
            return false;
        }}

        for (let i = 1; i < polygon.length; i++) {{
            if (pointInRing(point, polygon[i])) {{
                return false;
            }}
        }}

        return true;
    }}

    function pointInFeature(point, feature) {{
        if (!feature.geometry) {{
            return false;
        }}

        const geometry = feature.geometry;

        if (geometry.type === "Polygon") {{
            return pointInPolygon(
                point,
                geometry.coordinates
            );
        }}

        if (geometry.type === "MultiPolygon") {{
            return geometry.coordinates.some(
                polygon => pointInPolygon(
                    point,
                    polygon
                )
            );
        }}

        return false;
    }}

    function participatingStates(statesGeoJson) {{
        const active = new Set();

        statesGeoJson.features.forEach(
            feature => {{
                const hasStadium = stadiums.some(
                    stadium => pointInFeature(
                        [
                            stadium.longitude,
                            stadium.latitude
                        ],
                        feature
                    )
                );

                if (hasStadium) {{
                    active.add(
                        featureName(feature)
                    );
                }}
            }}
        );

        return active;
    }}

    stadiums.forEach(
        stadium => {{
            const latitude =
                stadium.latitude;

            const longitude =
                stadium.longitude;

            let markerClass =
                "venue-marker-main";

            if (
                stadium.is_alternate
                && stadium.is_main
            ) {{
                markerClass =
                    "venue-marker-mixed";
            }}
            else if (stadium.is_alternate) {{
                markerClass =
                    "venue-marker-alternate";
            }}

            const venueIcon = L.divIcon(
                {{
                    className: "",
                    html:
                        '<div class="venue-marker '
                        + markerClass
                        + '"></div>',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12],
                    popupAnchor: [0, -12]
                }}
            );

            const marker = L.marker(
                [
                    latitude,
                    longitude
                ],
                {{
                    icon: venueIcon,
                    zIndexOffset: 1000
                }}
            ).addTo(map);

            let popup = `
                <div class="stadium-name">
                    ${{escapeHtml(
                        stadium.name
                    )}}
                </div>
            `;

            if (stadium.address) {{
                popup += `
                    <div class="stadium-detail">
                        ${{escapeHtml(
                            stadium.address
                        )}}
                    </div>
                `;
            }}

            if (stadium.city) {{
                popup += `
                    <div class="stadium-detail">
                        ${{escapeHtml(
                            stadium.city
                        )}}
                    </div>
                `;
            }}

            if (
                stadium.is_main
                || stadium.is_alternate
            ) {{
                const roleClass =
                    stadium.is_alternate
                    && !stadium.is_main
                    ? "stadium-role-alternate"
                    : "stadium-role-main";

                const roleText =
                    stadium.is_alternate
                    && !stadium.is_main
                    ? "Ausweichspielstätte"
                    : (
                        stadium.is_alternate
                        && stadium.is_main
                        ? "Haupt- und Ausweichspielstätte"
                        : "Hauptspielstätte"
                    );

                popup += `
                    <div class="stadium-role ${{roleClass}}">
                        ${{roleText}}
                    </div>
                `;
            }}

            if (
                stadium.usage_details
                && stadium.usage_details.length
            ) {{
                stadium.usage_details.forEach(
                    usage => {{
                        const roleText =
                            usage.role === "main"
                            ? "Haupt"
                            : "Ausweich";

                        popup += `
                            <div class="stadium-usage">
                                ${{escapeHtml(usage.team)}}:
                                ${{usage.home_matches}}
                                Heimspiel(e)
                                · ${{roleText}}
                            </div>
                        `;
                    }}
                );
            }}

            marker.bindPopup(
                popup
            );

            bounds.push(
                [
                    latitude,
                    longitude
                ]
            );
        }}
    );

    Promise.all([
        fetch(
            STATES_DISPLAY_URL
        ).then(
            response => {{
                if (!response.ok) {{
                    throw new Error(
                        "Bundesländer-Darstellung konnte "
                        + "nicht geladen werden."
                    );
                }}

                return response.json();
            }}
        ),

        fetch(
            STATES_DETECTION_URL
        ).then(
            response => {{
                if (!response.ok) {{
                    throw new Error(
                        "Präzise Bundeslanddaten konnten "
                        + "nicht geladen werden."
                    );
                }}

                return response.json();
            }}
        )
    ])
    .then(
        async ([statesGeoJson, detectionGeoJson]) => {{
            /*
             * Bundesland-Zuordnung:
             * 1. PLZ/Adresse, wenn eindeutig vorhanden
             * 2. hochauflösendes GeoJSON als Fallback
             *
             * Das verhindert Grenzfehler wie beim
             * Donaustadion Ulm.
             */
            function postalCodeFromStadium(stadium) {{
                const source = [
                    stadium.name || "",
                    stadium.address || "",
                    stadium.city || ""
                ].join(" ");

                const match =
                    source.match(
                        /(?:^|[^0-9])([0-9]{{5}})(?:[^0-9]|$)/
                    );

                return match ? match[1] : null;
            }}

            function stateFromGeometry(stadium) {{
                for (const feature
                    of detectionGeoJson.features) {{
                    if (
                        pointInFeature(
                            [
                                stadium.longitude,
                                stadium.latitude
                            ],
                            feature
                        )
                    ) {{
                        return featureName(feature);
                    }}
                }}

                return null;
            }}

            /*
             * Exakte PLZ-/Ortszuordnung über OpenPLZ.
             * Das API-Ergebnis enthält direkt federalState.name.
             *
             * Bei Netzwerk-/API-Fehlern bleibt das
             * hochauflösende GeoJSON der Fallback.
             */
            const postalStateCache = new Map();

            async function stateFromPostalCode(stadium) {{
                const postalCode =
                    postalCodeFromStadium(stadium);

                if (!postalCode) {{
                    return null;
                }}

                if (postalStateCache.has(postalCode)) {{
                    return postalStateCache.get(postalCode);
                }}

                try {{
                    const url =
                        "https://openplzapi.org/de/Localities"
                        + "?postalCode="
                        + encodeURIComponent(postalCode)
                        + "&page=1&pageSize=50";

                    const response = await fetch(url);

                    if (!response.ok) {{
                        throw new Error(
                            "OpenPLZ HTTP "
                            + response.status
                        );
                    }}

                    const localities =
                        await response.json();

                    const stateNames =
                        Array.from(
                            new Set(
                                localities
                                    .map(
                                        locality =>
                                            locality.federalState
                                            && locality.federalState.name
                                    )
                                    .filter(Boolean)
                            )
                        );

                    /*
                     * Eine deutsche PLZ kann mehrere Orte
                     * enthalten. Solange alle Treffer im
                     * selben Bundesland liegen, ist die
                     * Zuordnung eindeutig.
                     */
                    const stateName =
                        stateNames.length === 1
                        ? stateNames[0]
                        : null;

                    postalStateCache.set(
                        postalCode,
                        stateName
                    );

                    return stateName;
                }}
                catch (error) {{
                    console.warn(
                        "OpenPLZ-Fallback für "
                        + postalCode + ":",
                        error
                    );

                    postalStateCache.set(
                        postalCode,
                        null
                    );

                    return null;
                }}
            }}

            const activeStates = new Set();

            await Promise.all(
                stadiums.map(
                    async stadium => {{
                        const stateName =
                            await stateFromPostalCode(
                                stadium
                            )
                            || stateFromGeometry(
                                stadium
                            );

                        if (stateName) {{
                            activeStates.add(
                                stateName
                            );
                        }}
                    }}
                )
            );


            /*
             * Deutschland-Außengrenze als echte Außenkante.
             *
             * Alle Polygonkanten der 16 Bundesländer werden
             * gesammelt. Kanten, die zweimal vorkommen, sind
             * gemeinsame innere Landesgrenzen und entfallen.
             * Übrig bleiben nur die äußeren Grenzsegmente.
             */
            function coordinateKey(point) {{
                return (
                    Number(point[0]).toFixed(5)
                    + ","
                    + Number(point[1]).toFixed(5)
                );
            }}

            function edgeKey(a, b) {{
                const first = coordinateKey(a);
                const second = coordinateKey(b);

                return (
                    first < second
                    ? first + "|" + second
                    : second + "|" + first
                );
            }}

            function polygonRings(geometry) {{
                if (!geometry) {{
                    return [];
                }}

                if (geometry.type === "Polygon") {{
                    return geometry.coordinates;
                }}

                if (geometry.type === "MultiPolygon") {{
                    return geometry.coordinates.flat();
                }}

                return [];
            }}

            const edgeMap = new Map();

            statesGeoJson.features.forEach(
                feature => {{
                    polygonRings(
                        feature.geometry
                    ).forEach(
                        ring => {{
                            for (
                                let i = 0;
                                i < ring.length - 1;
                                i++
                            ) {{
                                const a = ring[i];
                                const b = ring[i + 1];
                                const key = edgeKey(a, b);

                                if (!edgeMap.has(key)) {{
                                    edgeMap.set(
                                        key,
                                        {{
                                            count: 1,
                                            a: a,
                                            b: b
                                        }}
                                    );
                                }}
                                else {{
                                    edgeMap.get(
                                        key
                                    ).count += 1;
                                }}
                            }}
                        }}
                    );
                }}
            );

            const outerSegments = [];

            edgeMap.forEach(
                edge => {{
                    if (edge.count === 1) {{
                        outerSegments.push(
                            [
                                [
                                    edge.a[1],
                                    edge.a[0]
                                ],
                                [
                                    edge.b[1],
                                    edge.b[0]
                                ]
                            ]
                        );
                    }}
                }}
            );

            const germanyLayer =
                L.layerGroup();

            outerSegments.forEach(
                segment => {{
                    L.polyline(
                        segment,
                        {{
                            color: "#f2c94c",
                            weight: 3.0,
                            opacity: 0.95,
                            interactive: false
                        }}
                    ).addTo(
                        germanyLayer
                    );
                }}
            );

            if (showGermany) {{
                germanyLayer.addTo(map);
            }}

            const stateLayer =
                L.geoJSON(
                    statesGeoJson,
                    {{
                        style: feature => {{
                            const active =
                                highlightActive
                                && activeStates.has(
                                    featureName(feature)
                                );

                            return {{
                                color:
                                    active
                                    ? "#3b9cff"
                                    : "#8c96a3",
                                weight:
                                    active
                                    ? 2.5
                                    : 1.25,
                                opacity:
                                    active
                                    ? 0.95
                                    : 0.75,
                                fillColor:
                                    active
                                    ? "#3091ff"
                                    : "#ffffff",
                                fillOpacity:
                                    active
                                    ? 0.18
                                    : 0.015
                            }};
                        }},

                        onEachFeature:
                            (feature, layer) => {{
                                /*
                                 * Bundesländer sind reine
                                 * Darstellungsebenen.
                                 *
                                 * Keine Klick-/Hover-Interaktion:
                                 * dadurch zeichnet Leaflet beim
                                 * Anklicken keine Bounding-Box
                                 * des Bundeslands mehr.
                                 */
                                layer.options.interactive = false;
                            }}
                    }}
                );

            if (showStates) {{
                stateLayer.addTo(map);
            }}

            if (showStates) {{
                stateLayer.bringToFront();
            }}

            const stateNames =
                Array.from(
                    activeStates
                ).sort();

            document.title =
                stateNames.join(" | ");

        }}
    )
    .catch(
        error => {{
            console.error(
                "Grenzdaten:",
                error
            );
        }}
    );

    if (bounds.length > 1) {{
        map.fitBounds(
            bounds,
            {{
                padding: [30, 30],
                maxZoom: 9
            }}
        );
    }}
    else if (bounds.length === 1) {{
        map.setView(
            bounds[0],
            12
        );
    }}
    else {{
        map.setView(
            [
                51.1657,
                10.4515
            ],
            6
        );
    }}
</script>

</body>
</html>
"""

        self.web_view.setHtml(
            html,
            QUrl(
                "https://localhost/"
            ),
        )