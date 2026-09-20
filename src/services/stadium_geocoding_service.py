from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

import sqlite3


@dataclass
class GeocodingResult:
    stadium_id: int
    stadium_name: str
    latitude: float | None
    longitude: float | None
    display_name: str | None = None
    success: bool = False
    message: str = ""
    query_used: str | None = None


class StadiumGeocodingService:
    NOMINATIM_URL = (
        "https://nominatim.openstreetmap.org/search"
    )

    USER_AGENT = (
        "KreisligaManager/1.0 "
        "(stadium geocoding)"
    )

    REQUEST_DELAY_SECONDS = 1.1
    TIMEOUT_SECONDS = 15

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def geocode_stadium(
        self,
        stadium_id: int,
        force: bool = False,
    ) -> GeocodingResult:
        stadium = self._get_stadium(
            stadium_id
        )

        if stadium is None:
            return GeocodingResult(
                stadium_id=stadium_id,
                stadium_name="",
                latitude=None,
                longitude=None,
                success=False,
                message="Stadion nicht gefunden.",
            )

        (
            stadium_id,
            name,
            city,
            address,
            latitude,
            longitude,
        ) = stadium

        if (
            not force
            and latitude is not None
            and longitude is not None
        ):
            return GeocodingResult(
                stadium_id=stadium_id,
                stadium_name=name,
                latitude=float(latitude),
                longitude=float(longitude),
                success=True,
                message=(
                    "Koordinaten bereits vorhanden."
                ),
            )

        expected_postal_code = self._extract_postal_code(
            name=name,
            city=city,
            address=address,
        )

        queries = self._build_queries(
            name=name,
            city=city,
            address=address,
        )

        if not queries:
            return GeocodingResult(
                stadium_id=stadium_id,
                stadium_name=name,
                latitude=None,
                longitude=None,
                success=False,
                message=(
                    "Keine Standortdaten vorhanden."
                ),
            )

        errors: list[str] = []

        for index, query in enumerate(queries):
            if index > 0:
                time.sleep(
                    self.REQUEST_DELAY_SECONDS
                )

            try:
                result = self._request_nominatim(
                    query
                )
            except Exception as exc:
                errors.append(
                    f"{query}: {exc}"
                )
                continue

            if result is None:
                continue

            if not self._postal_code_matches(
                result=result,
                expected_postal_code=expected_postal_code,
            ):
                returned_postal_code = (
                    self._postal_code_from_result(
                        result
                    )
                )

                errors.append(
                    (
                        f"{query}: "
                        "PLZ stimmt nicht überein "
                        f"(erwartet "
                        f"{expected_postal_code}, "
                        f"Treffer "
                        f"{returned_postal_code or 'ohne PLZ'})"
                    )
                )
                continue

            try:
                latitude = float(
                    result["lat"]
                )
                longitude = float(
                    result["lon"]
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            display_name = result.get(
                "display_name"
            )

            postal_code = self._postal_code_from_result(
                result
            )
            federal_state = self._state_from_result(
                result
            )

            self._save_location(
                stadium_id=stadium_id,
                latitude=latitude,
                longitude=longitude,
                postal_code=postal_code,
                federal_state=federal_state,
            )

            return GeocodingResult(
                stadium_id=stadium_id,
                stadium_name=name,
                latitude=latitude,
                longitude=longitude,
                display_name=display_name,
                success=True,
                message=(
                    "Koordinaten gespeichert."
                ),
                query_used=query,
            )

        message = "Kein Standort gefunden."

        if errors:
            message += (
                " Fehler: "
                + " | ".join(errors)
            )

        return GeocodingResult(
            stadium_id=stadium_id,
            stadium_name=name,
            latitude=None,
            longitude=None,
            success=False,
            message=message,
        )

    def geocode_missing(
        self,
        limit: int | None = None,
    ) -> list[GeocodingResult]:
        stadium_ids = (
            self._get_missing_stadium_ids(
                limit=limit
            )
        )

        results: list[GeocodingResult] = []

        for index, stadium_id in enumerate(
            stadium_ids
        ):
            if index > 0:
                time.sleep(
                    self.REQUEST_DELAY_SECONDS
                )

            result = self.geocode_stadium(
                stadium_id
            )

            results.append(result)

        return results

    def _get_stadium(
        self,
        stadium_id: int,
    ):
        self.cursor.execute(
            """
            SELECT
                stadium_id,
                name,
                city,
                address,
                latitude,
                longitude
            FROM stadiums
            WHERE stadium_id = ?
            """,
            (stadium_id,),
        )

        return self.cursor.fetchone()

    def _get_missing_stadium_ids(
        self,
        limit: int | None = None,
    ) -> list[int]:
        sql = """
            SELECT stadium_id
            FROM stadiums
            WHERE
                latitude IS NULL
                OR longitude IS NULL
            ORDER BY stadium_id
        """

        parameters: tuple = ()

        if limit is not None:
            sql += " LIMIT ?"
            parameters = (limit,)

        self.cursor.execute(
            sql,
            parameters,
        )

        return [
            int(row[0])
            for row in self.cursor.fetchall()
        ]

    def _build_queries(
        self,
        name: str | None,
        city: str | None,
        address: str | None,
    ) -> list[str]:
        queries: list[str] = []

        clean_name = (
            name.strip()
            if name
            else ""
        )

        clean_city = (
            city.strip()
            if city
            else ""
        )

        clean_address = (
            address.strip()
            if address
            else ""
        )

        # --------------------------------------------------
        # 1. Saubere DB-Adresse vorhanden
        # --------------------------------------------------

        if clean_address:
            if clean_city:
                self._add_query(
                    queries,
                    (
                        f"{clean_address}, "
                        f"{clean_city}, Deutschland"
                    ),
                )

            self._add_query(
                queries,
                (
                    f"{clean_address}, "
                    f"Deutschland"
                ),
            )

        # --------------------------------------------------
        # 2. FUSSBALL.DE-Text aus "name" analysieren
        #
        # Beispiel:
        #
        # Kunstrasenplatz, Ehrang-Heide,
        # Kunstrasenplatz,
        # Im Karrenbachtal, 54293 Ehrang
        # --------------------------------------------------

        if clean_name:
            parts = [
                part.strip()
                for part in clean_name.split(",")
                if part.strip()
            ]

            postal_index = None

            for index, part in enumerate(parts):
                if self._contains_postal_code(
                    part
                ):
                    postal_index = index
                    break

            if postal_index is not None:
                postal_part = parts[
                    postal_index
                ]

                # Straße + PLZ/Ort
                if postal_index > 0:
                    street_part = parts[
                        postal_index - 1
                    ]

                    if (
                        not self._is_pitch_type(
                            street_part
                        )
                    ):
                        self._add_query(
                            queries,
                            (
                                f"{street_part}, "
                                f"{postal_part}, "
                                f"Deutschland"
                            ),
                        )

                # Nur PLZ + Ort
                self._add_query(
                    queries,
                    (
                        f"{postal_part}, "
                        f"Deutschland"
                    ),
                )

                # Falls hinter PLZ/Ort noch Text steht
                if (
                    postal_index + 1
                    < len(parts)
                ):
                    remaining = ", ".join(
                        parts[postal_index:]
                    )

                    self._add_query(
                        queries,
                        (
                            f"{remaining}, "
                            f"Deutschland"
                        ),
                    )

            # --------------------------------------------------
            # 3. Orts-/Stadionname als Fallback
            # --------------------------------------------------

            if len(parts) >= 2:
                location_name = parts[1]

                if not self._is_pitch_type(
                    location_name
                ):
                    self._add_query(
                        queries,
                        (
                            f"{location_name}, "
                            f"Deutschland"
                        ),
                    )

            # --------------------------------------------------
            # 4. Kompletter Originaltext als letzter Versuch
            # --------------------------------------------------

            self._add_query(
                queries,
                (
                    f"{clean_name}, "
                    f"Deutschland"
                ),
            )

        return queries

    def _add_query(
        self,
        queries: list[str],
        query: str,
    ) -> None:
        query = re.sub(
            r"\s+",
            " ",
            query,
        ).strip()

        if query not in queries:
            queries.append(query)

    def _contains_postal_code(
        self,
        text: str,
    ) -> bool:
        return bool(
            re.search(
                r"\b\d{5}\b",
                text,
            )
        )

    def _is_pitch_type(
        self,
        text: str,
    ) -> bool:
        normalized = text.lower()

        pitch_terms = (
            "rasenplatz",
            "kunstrasen",
            "kunstrasenplatz",
            "hartplatz",
            "hybridrasen",
            "hybridrasenplatz",
            "sportplatz",
            "spielfeld",
        )

        return normalized in pitch_terms

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
            r"(?<!\\d)(\\d{5})(?!\\d)",
            source,
        )

        if match is None:
            return None

        return match.group(1)

    def _postal_code_from_result(
        self,
        result: dict,
    ) -> str | None:
        address = result.get("address")

        if not isinstance(address, dict):
            return None

        postal_code = address.get(
            "postcode"
        )

        if not postal_code:
            return None

        match = re.search(
            r"(?<!\\d)(\\d{5})(?!\\d)",
            str(postal_code),
        )

        if match is None:
            return None

        return match.group(1)

    def _postal_code_matches(
        self,
        *,
        result: dict,
        expected_postal_code: str | None,
    ) -> bool:
        if expected_postal_code is None:
            return True

        returned_postal_code = (
            self._postal_code_from_result(
                result
            )
        )

        if returned_postal_code is None:
            return False

        return (
            returned_postal_code
            == expected_postal_code
        )

    def _state_from_result(
        self,
        result: dict,
    ) -> str | None:
        address = result.get("address")

        if not isinstance(address, dict):
            return None

        state = address.get("state")

        if not state:
            return None

        state = str(state).strip()

        aliases = {
            "Baden-Wurttemberg":
                "Baden-Württemberg",
            "North Rhine-Westphalia":
                "Nordrhein-Westfalen",
            "Rhineland-Palatinate":
                "Rheinland-Pfalz",
            "Lower Saxony":
                "Niedersachsen",
            "Saxony":
                "Sachsen",
            "Saxony-Anhalt":
                "Sachsen-Anhalt",
            "Thuringia":
                "Thüringen",
            "Bavaria":
                "Bayern",
            "Hesse":
                "Hessen",
        }

        return aliases.get(
            state,
            state,
        )

    def _request_nominatim(
        self,
        query: str,
    ) -> dict | None:
        parameters = urllib.parse.urlencode(
            {
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "de",
                "addressdetails": 1,
            }
        )

        url = (
            f"{self.NOMINATIM_URL}"
            f"?{parameters}"
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    self.USER_AGENT,
                "Accept":
                    "application/json",
                "Accept-Language":
                    "de",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.TIMEOUT_SECONDS,
            ) as response:
                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"HTTP {exc.code}"
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                (
                    "Netzwerkfehler: "
                    f"{exc.reason}"
                )
            ) from exc

        if not data:
            return None

        return data[0]

    def _save_location(
        self,
        *,
        stadium_id: int,
        latitude: float,
        longitude: float,
        postal_code: str | None,
        federal_state: str | None,
    ) -> None:
        self.cursor.execute(
            """
            UPDATE stadiums
            SET
                latitude = ?,
                longitude = ?,
                postal_code = COALESCE(
                    ?,
                    postal_code
                ),
                federal_state = COALESCE(
                    ?,
                    federal_state
                )
            WHERE stadium_id = ?
            """,
            (
                latitude,
                longitude,
                postal_code,
                federal_state,
                stadium_id,
            ),
        )

        self.connection.commit()
