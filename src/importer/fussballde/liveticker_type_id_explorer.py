from __future__ import annotations

import csv
import json
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class TypeIdExample:
    match_id: str
    description: str
    minute: int | None
    score: str
    team_id: str
    member_id: str
    member2_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TypeIdSummary:
    type_id: int
    count: int = 0
    descriptions: set[str] = field(
        default_factory=set
    )
    examples: list[TypeIdExample] = field(
        default_factory=list
    )
    with_team_id: int = 0
    with_member_id: int = 0
    with_member2_id: int = 0

    @property
    def team_assignment_rate(self) -> float:
        if self.count == 0:
            return 0.0

        return (
            self.with_team_id
            / self.count
            * 100
        )

    @property
    def player_assignment_rate(self) -> float:
        if self.count == 0:
            return 0.0

        return (
            self.with_member_id
            / self.count
            * 100
        )

    @property
    def second_player_assignment_rate(
        self,
    ) -> float:
        if self.count == 0:
            return 0.0

        return (
            self.with_member2_id
            / self.count
            * 100
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type_id": self.type_id,
            "count": self.count,
            "descriptions": sorted(
                self.descriptions
            ),
            "with_team_id": self.with_team_id,
            "with_member_id": self.with_member_id,
            "with_member2_id": (
                self.with_member2_id
            ),
            "team_assignment_rate": round(
                self.team_assignment_rate,
                1,
            ),
            "player_assignment_rate": round(
                self.player_assignment_rate,
                1,
            ),
            "second_player_assignment_rate": round(
                self.second_player_assignment_rate,
                1,
            ),
            "examples": [
                example.to_dict()
                for example in self.examples
            ],
        }


@dataclass(slots=True)
class TypeIdExplorerResult:
    files_scanned: int
    liveticker_files_found: int
    events_found: int
    match_ids: tuple[str, ...]
    summaries: tuple[TypeIdSummary, ...]
    json_report_path: str
    csv_report_path: str
    text_report_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_scanned": self.files_scanned,
            "liveticker_files_found": (
                self.liveticker_files_found
            ),
            "events_found": self.events_found,
            "match_ids": list(
                self.match_ids
            ),
            "summaries": [
                summary.to_dict()
                for summary in self.summaries
            ],
            "json_report_path": (
                self.json_report_path
            ),
            "csv_report_path": (
                self.csv_report_path
            ),
            "text_report_path": (
                self.text_report_path
            ),
        }


class LivetickerTypeIdExplorer:
    REPORT_DIRECTORY = Path(
        "debug/liveticker_type_ids"
    )

    LIVETICKER_FILENAME_MARKERS = (
        "ajax.liveticker",
        "liveticker",
        "liveTicker",
    )

    def explore(
        self,
        sources: Iterable[str | Path],
        max_examples_per_type: int = 5,
    ) -> TypeIdExplorerResult:
        if max_examples_per_type < 1:
            raise ValueError(
                "max_examples_per_type muss "
                "mindestens 1 sein."
            )

        normalized_sources = [
            Path(source)
            for source in sources
        ]

        if not normalized_sources:
            raise ValueError(
                "Mindestens eine Quelle wird benötigt."
            )

        summaries: dict[
            int,
            TypeIdSummary,
        ] = {}

        files_scanned = 0
        liveticker_files_found = 0
        events_found = 0
        match_ids: set[str] = set()

        for source in normalized_sources:
            for (
                display_name,
                payload,
            ) in self._iter_json_payloads(
                source
            ):
                files_scanned += 1

                if not self._looks_like_liveticker(
                    display_name=display_name,
                    payload=payload,
                ):
                    continue

                events = payload.get(
                    "events"
                )

                if not isinstance(
                    events,
                    list,
                ):
                    continue

                liveticker_files_found += 1

                match_id = str(
                    payload.get(
                        "matchId",
                        "",
                    )
                    or payload.get(
                        "id",
                        "",
                    )
                    or ""
                ).strip()

                if match_id:
                    match_ids.add(
                        match_id
                    )

                for raw_event in events:
                    if not isinstance(
                        raw_event,
                        dict,
                    ):
                        continue

                    type_id = self._to_integer(
                        raw_event.get(
                            "type_id"
                        )
                    )

                    if type_id is None:
                        continue

                    events_found += 1

                    summary = summaries.setdefault(
                        type_id,
                        TypeIdSummary(
                            type_id=type_id
                        ),
                    )

                    summary.count += 1

                    description = str(
                        raw_event.get(
                            "description",
                            "",
                        )
                        or ""
                    ).strip()

                    if description:
                        summary.descriptions.add(
                            description
                        )

                    team_id = str(
                        raw_event.get(
                            "team_id",
                            "",
                        )
                        or ""
                    ).strip()

                    member_id = str(
                        raw_event.get(
                            "member_id",
                            "",
                        )
                        or ""
                    ).strip()

                    member2_id = str(
                        raw_event.get(
                            "member2_id",
                            "",
                        )
                        or ""
                    ).strip()

                    if team_id:
                        summary.with_team_id += 1

                    if member_id:
                        summary.with_member_id += 1

                    if member2_id:
                        summary.with_member2_id += 1

                    if (
                        len(summary.examples)
                        < max_examples_per_type
                    ):
                        summary.examples.append(
                            TypeIdExample(
                                match_id=match_id,
                                description=(
                                    description
                                ),
                                minute=self._to_integer(
                                    raw_event.get(
                                        "minute"
                                    )
                                ),
                                score=str(
                                    raw_event.get(
                                        "score",
                                        "",
                                    )
                                    or ""
                                ).strip(),
                                team_id=team_id,
                                member_id=member_id,
                                member2_id=member2_id,
                            )
                        )

        ordered_summaries = tuple(
            sorted(
                summaries.values(),
                key=lambda item: item.type_id,
            )
        )

        self.REPORT_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_path = (
            self.REPORT_DIRECTORY
            / "type_id_report.json"
        )

        csv_path = (
            self.REPORT_DIRECTORY
            / "type_id_report.csv"
        )

        text_path = (
            self.REPORT_DIRECTORY
            / "type_id_report.txt"
        )

        result = TypeIdExplorerResult(
            files_scanned=files_scanned,
            liveticker_files_found=(
                liveticker_files_found
            ),
            events_found=events_found,
            match_ids=tuple(
                sorted(
                    match_ids
                )
            ),
            summaries=ordered_summaries,
            json_report_path=str(
                json_path
            ),
            csv_report_path=str(
                csv_path
            ),
            text_report_path=str(
                text_path
            ),
        )

        json_path.write_text(
            json.dumps(
                result.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self._write_csv(
            path=csv_path,
            summaries=ordered_summaries,
        )

        text_path.write_text(
            self._build_text_report(
                result
            ),
            encoding="utf-8",
        )

        self._print_result(
            result
        )

        return result

    def _iter_json_payloads(
        self,
        source: Path,
    ):
        if not source.exists():
            raise FileNotFoundError(
                f"Quelle nicht gefunden: {source}"
            )

        if source.is_dir():
            for path in source.rglob(
                "*.json"
            ):
                payload = self._load_json_bytes(
                    path.read_bytes()
                )

                if payload is not None:
                    yield str(path), payload

            return

        if source.suffix.casefold() == ".zip":
            with zipfile.ZipFile(
                source
            ) as archive:
                for name in archive.namelist():
                    if not name.casefold().endswith(
                        ".json"
                    ):
                        continue

                    payload = self._load_json_bytes(
                        archive.read(
                            name
                        )
                    )

                    if payload is not None:
                        yield (
                            f"{source.name}:{name}",
                            payload,
                        )

            return

        if source.suffix.casefold() == ".json":
            payload = self._load_json_bytes(
                source.read_bytes()
            )

            if payload is not None:
                yield str(source), payload

            return

        raise ValueError(
            "Unterstützt werden Ordner, "
            "ZIP-Dateien und JSON-Dateien."
        )

    @staticmethod
    def _load_json_bytes(
        raw_data: bytes,
    ) -> dict[str, Any] | None:
        try:
            decoded = raw_data.decode(
                "utf-8",
                errors="replace",
            )

            payload = json.loads(
                decoded
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return None

        if not isinstance(
            payload,
            dict,
        ):
            return None

        return payload

    def _looks_like_liveticker(
        self,
        display_name: str,
        payload: dict[str, Any],
    ) -> bool:
        normalized_name = (
            display_name.casefold()
        )

        filename_match = any(
            marker.casefold()
            in normalized_name
            for marker
            in self.LIVETICKER_FILENAME_MARKERS
        )

        structure_match = (
            isinstance(
                payload.get(
                    "events"
                ),
                list,
            )
            and (
                "liveticker_enabled"
                in payload
                or "matchId"
                in payload
                or "tickers"
                in payload
            )
        )

        return (
            filename_match
            or structure_match
        )

    @staticmethod
    def _to_integer(
        value: Any,
    ) -> int | None:
        if isinstance(
            value,
            bool,
        ):
            return None

        if isinstance(
            value,
            int,
        ):
            return value

        if isinstance(
            value,
            float,
        ):
            return int(
                value
            )

        if isinstance(
            value,
            str,
        ):
            normalized = value.strip()

            if normalized.lstrip(
                "-"
            ).isdigit():
                return int(
                    normalized
                )

        return None

    @staticmethod
    def _write_csv(
        path: Path,
        summaries: tuple[
            TypeIdSummary,
            ...,
        ],
    ) -> None:
        with path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            writer = csv.writer(
                file,
                delimiter=";",
            )

            writer.writerow(
                [
                    "type_id",
                    "count",
                    "team_assignment_rate",
                    "player_assignment_rate",
                    "second_player_assignment_rate",
                    "description_examples",
                ]
            )

            for summary in summaries:
                writer.writerow(
                    [
                        summary.type_id,
                        summary.count,
                        (
                            f"{summary.team_assignment_rate:.1f}"
                        ),
                        (
                            f"{summary.player_assignment_rate:.1f}"
                        ),
                        (
                            f"{summary.second_player_assignment_rate:.1f}"
                        ),
                        " | ".join(
                            sorted(
                                summary.descriptions
                            )[:5]
                        ),
                    ]
                )

    def _build_text_report(
        self,
        result: TypeIdExplorerResult,
    ) -> str:
        lines = [
            "=" * 90,
            "FUSSBALL.DE LIVETICKER TYPE-ID REPORT",
            "=" * 90,
            "",
            (
                "JSON-Dateien geprüft:       "
                f"{result.files_scanned}"
            ),
            (
                "Liveticker-Dateien:         "
                f"{result.liveticker_files_found}"
            ),
            (
                "Events gefunden:            "
                f"{result.events_found}"
            ),
            (
                "Spiele gefunden:            "
                f"{len(result.match_ids)}"
            ),
            "",
            "-" * 90,
            (
                "TYPE-ID | ANZAHL | TEAM % | "
                "SPIELER % | SPIELER 2 % | "
                "BEISPIEL"
            ),
            "-" * 90,
        ]

        for summary in result.summaries:
            example = ""

            if summary.examples:
                example = (
                    summary.examples[0]
                    .description
                )

            lines.append(
                f"{summary.type_id:7} | "
                f"{summary.count:6} | "
                f"{summary.team_assignment_rate:6.1f} | "
                f"{summary.player_assignment_rate:9.1f} | "
                f"{summary.second_player_assignment_rate:11.1f} | "
                f"{example}"
            )

        lines.extend(
            [
                "",
                "=" * 90,
            ]
        )

        return "\n".join(
            lines
        )

    @staticmethod
    def _print_result(
        result: TypeIdExplorerResult,
    ) -> None:
        print(
            Path(
                result.text_report_path
            ).read_text(
                encoding="utf-8"
            )
        )

        print()
        print(
            f"JSON-Bericht: "
            f"{result.json_report_path}"
        )
        print(
            f"CSV-Bericht:  "
            f"{result.csv_report_path}"
        )
        print(
            f"TXT-Bericht:  "
            f"{result.text_report_path}"
        )


def main() -> None:
    print(
        "Dieses Modul wird über "
        "test_liveticker_type_id_explorer.py "
        "gestartet."
    )


if __name__ == "__main__":
    main()