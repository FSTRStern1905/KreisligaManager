from __future__ import annotations

import json
import re
import sqlite3
import urllib.request
from pathlib import Path


class StadiumLocationSyncService:
    GEOJSON_URL = (
        "https://raw.githubusercontent.com/"
        "isellsoap/deutschlandGeoJSON/master/"
        "2_bundeslaender/1_sehr_hoch.geo.json"
    )

    GEOJSON_PATH = Path(
        "data/cache/bundeslaender_sehr_hoch.geojson"
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def sync_all(self) -> dict:
        geojson = self._load_geojson()

        rows = self.cursor.execute(
            """
            SELECT
                stadium_id,
                name,
                city,
                address,
                latitude,
                longitude,
                postal_code,
                federal_state
            FROM stadiums
            ORDER BY stadium_id;
            """
        ).fetchall()

        postal_codes_updated = 0
        states_updated = 0
        states_existing = 0
        states_failed = 0

        for row in rows:
            (
                stadium_id,
                name,
                city,
                address,
                latitude,
                longitude,
                postal_code,
                federal_state,
            ) = row

            if not postal_code:
                postal_code = self._extract_postal_code(
                    name=name,
                    city=city,
                    address=address,
                )

                if postal_code:
                    self.cursor.execute(
                        """
                        UPDATE stadiums
                        SET postal_code = ?
                        WHERE stadium_id = ?;
                        """,
                        (
                            postal_code,
                            stadium_id,
                        ),
                    )
                    postal_codes_updated += 1

            if federal_state:
                states_existing += 1
                continue

            if latitude is None or longitude is None:
                states_failed += 1
                continue

            federal_state = self._state_from_point(
                latitude=float(latitude),
                longitude=float(longitude),
                geojson=geojson,
            )

            if not federal_state:
                states_failed += 1
                continue

            self.cursor.execute(
                """
                UPDATE stadiums
                SET federal_state = ?
                WHERE stadium_id = ?;
                """,
                (
                    federal_state,
                    stadium_id,
                ),
            )
            states_updated += 1

        self.connection.commit()

        return {
            "stadiums": len(rows),
            "postal_codes_updated":
                postal_codes_updated,
            "states_updated":
                states_updated,
            "states_existing":
                states_existing,
            "states_failed":
                states_failed,
        }

    def _load_geojson(self) -> dict:
        path = self.GEOJSON_PATH

        if not path.exists():
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            print(
                "Bundesland-Grenzen werden einmalig "
                "heruntergeladen ..."
            )

            request = urllib.request.Request(
                self.GEOJSON_URL,
                headers={
                    "User-Agent":
                        "KreisligaManager/1.0",
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=60,
            ) as response:
                path.write_bytes(
                    response.read()
                )

            print(
                f"Gespeichert: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _extract_postal_code(
        self,
        *,
        name: str | None,
        city: str | None,
        address: str | None,
    ) -> str | None:
        source = " ".join(
            str(value or "")
            for value in (
                name,
                address,
                city,
            )
        )

        match = re.search(
            r"(?<!\d)(\d{5})(?!\d)",
            source,
        )

        if match is None:
            return None

        return match.group(1)

    def _state_from_point(
        self,
        *,
        latitude: float,
        longitude: float,
        geojson: dict,
    ) -> str | None:
        point = (
            longitude,
            latitude,
        )

        for feature in geojson.get(
            "features",
            [],
        ):
            geometry = feature.get(
                "geometry"
            ) or {}

            if self._geometry_contains_point(
                geometry,
                point,
            ):
                return self._feature_name(
                    feature
                )

        return None

    def _geometry_contains_point(
        self,
        geometry: dict,
        point: tuple[float, float],
    ) -> bool:
        geometry_type = geometry.get(
            "type"
        )
        coordinates = geometry.get(
            "coordinates"
        )

        if not coordinates:
            return False

        if geometry_type == "Polygon":
            return self._polygon_contains_point(
                coordinates,
                point,
            )

        if geometry_type == "MultiPolygon":
            return any(
                self._polygon_contains_point(
                    polygon,
                    point,
                )
                for polygon in coordinates
            )

        return False

    def _polygon_contains_point(
        self,
        polygon: list,
        point: tuple[float, float],
    ) -> bool:
        if not polygon:
            return False

        outer_ring = polygon[0]

        if not self._ring_contains_point(
            outer_ring,
            point,
        ):
            return False

        for hole in polygon[1:]:
            if self._ring_contains_point(
                hole,
                point,
            ):
                return False

        return True

    def _ring_contains_point(
        self,
        ring: list,
        point: tuple[float, float],
    ) -> bool:
        x, y = point
        inside = False

        if len(ring) < 3:
            return False

        previous_x, previous_y = ring[-1]

        for current_x, current_y in ring:
            intersects = (
                (current_y > y)
                != (previous_y > y)
            )

            if intersects:
                denominator = (
                    previous_y - current_y
                )

                if denominator != 0:
                    crossing_x = (
                        (previous_x - current_x)
                        * (y - current_y)
                        / denominator
                        + current_x
                    )

                    if x < crossing_x:
                        inside = not inside

            previous_x = current_x
            previous_y = current_y

        return inside

    def _feature_name(
        self,
        feature: dict,
    ) -> str | None:
        properties = feature.get(
            "properties"
        ) or {}

        for key in (
            "name",
            "NAME_1",
            "GEN",
            "NAME",
        ):
            value = properties.get(key)

            if value:
                return str(value).strip()

        return None
