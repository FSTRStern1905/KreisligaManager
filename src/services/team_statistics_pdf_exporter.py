from __future__ import annotations

from datetime import datetime
import re
from html import escape
from pathlib import Path
from typing import Any

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter


class TeamStatisticsPdfExporter:
    SECTION_TITLES = {
        "overview": "Übersicht",
        "table_form": "Tabelle & Form",
        "results": "Ergebnisse",
        "goals": "Tore & Torphasen",
        "match_flow": "Spielverlauf",
        "players": "Spieler",
        "records": "Rekorde",
    }

    def export(
        self,
        destination_path: str | Path,
        report_data: dict[str, Any],
    ) -> Path:
        output_path = Path(
            destination_path
        )

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(
                ".pdf"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._validate_report_data(
            report_data
        )

        html = self._build_html(
            report_data
        )

        printer = QPrinter(
            QPrinter.PrinterMode.HighResolution
        )

        printer.setOutputFormat(
            QPrinter.OutputFormat.PdfFormat
        )

        printer.setOutputFileName(
            str(
                output_path
            )
        )

        printer.setPageSize(
            QPageSize(
                QPageSize.PageSizeId.A4
            )
        )

        printer.setPageOrientation(
            QPageLayout.Orientation.Portrait
        )

        printer.setPageMargins(
            QMarginsF(
                6.5,
                6.5,
                6.5,
                7.0,
            ),
            QPageLayout.Unit.Millimeter,
        )

        document = QTextDocument()
        document.setDocumentMargin(
            0
        )
        document.setHtml(
            html
        )

        document.print_(
            printer
        )

        if not output_path.exists():
            raise RuntimeError(
                "Die PDF-Datei wurde nicht erzeugt."
            )

        if output_path.stat().st_size <= 0:
            raise RuntimeError(
                "Die erzeugte PDF-Datei ist leer."
            )

        return output_path

    def _validate_report_data(
        self,
        report_data: dict[str, Any],
    ) -> None:
        required_keys = [
            "team_name",
            "competition_name",
            "season_name",
            "sections",
        ]

        missing_keys = [
            key
            for key in required_keys
            if key not in report_data
        ]

        if missing_keys:
            raise ValueError(
                "Fehlende Report-Daten: "
                + ", ".join(
                    missing_keys
                )
            )

        if not str(
            report_data.get(
                "team_name",
                "",
            )
        ).strip():
            raise ValueError(
                "Mannschaftsname fehlt."
            )

        sections = report_data.get(
            "sections"
        )

        if not isinstance(
            sections,
            dict,
        ):
            raise ValueError(
                "sections muss ein Dictionary sein."
            )

    def _build_html(
        self,
        report_data: dict[str, Any],
    ) -> str:
        team_name = escape(
            str(
                report_data[
                    "team_name"
                ]
            )
        )

        competition_name = escape(
            str(
                report_data[
                    "competition_name"
                ]
            )
        )

        season_name = escape(
            str(
                report_data[
                    "season_name"
                ]
            )
        )

        generated_at = report_data.get(
            "generated_at"
        )

        if isinstance(
            generated_at,
            datetime,
        ):
            generated_text = (
                generated_at.strftime(
                    "%d.%m.%Y %H:%M"
                )
            )
        elif generated_at:
            generated_text = str(
                generated_at
            )
        else:
            generated_text = (
                datetime.now().strftime(
                    "%d.%m.%Y %H:%M"
                )
            )

        sections = report_data[
            "sections"
        ]

        selected_sections = (
            report_data.get(
                "selected_sections"
            )
        )

        if selected_sections is None:
            selected_sections = list(
                self.SECTION_TITLES.keys()
            )

        selected = {
            key
            for key in selected_sections
            if key in self.SECTION_TITLES
            and sections.get(key) is not None
        }

        page_1_keys = [
            "overview",
            "table_form",
            "goals",
            "match_flow",
        ]

        page_2_keys = [
            "results",
            "players",
            "records",
        ]

        page_1 = [
            key
            for key in page_1_keys
            if key in selected
        ]

        page_2 = [
            key
            for key in page_2_keys
            if key in selected
        ]

        # Custom selections still remain usable:
        # anything not assigned above is appended to page 2.
        known = set(
            page_1_keys
            + page_2_keys
        )

        for key in selected_sections:
            if (
                key in selected
                and key not in known
            ):
                page_2.append(
                    key
                )

        body_parts = [
            self._render_report_header(
                team_name=team_name,
                competition_name=competition_name,
                season_name=season_name,
                generated_text=generated_text,
            )
        ]

        if page_1:
            body_parts.append(
                '<div class="report-page page-one">'
            )

            for section_key in page_1:
                body_parts.append(
                    self._render_compact_section(
                        section_key=section_key,
                        section_data=sections[
                            section_key
                        ],
                    )
                )

            body_parts.append(
                "</div>"
            )

        if page_2:
            body_parts.append(
                '<div class="report-page page-two">'
            )

            body_parts.append(
                self._render_page_header(
                    team_name=team_name,
                    competition_name=competition_name,
                    season_name=season_name,
                )
            )

            for section_key in page_2:
                body_parts.append(
                    self._render_compact_section(
                        section_key=section_key,
                        section_data=sections[
                            section_key
                        ],
                    )
                )

            body_parts.append(
                "</div>"
            )

        return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4 portrait;
    }}

    body {{
        font-family: "Arial", "DejaVu Sans", sans-serif;
        color: #1f2933;
        font-size: 6.45pt;
        line-height: 1.03;
        margin: 0;
        padding: 0;
    }}

    h2 {{
        font-size: 10.5pt;
        color: #132238;
        margin: 0;
    }}

    h3 {{
        font-size: 7.7pt;
        color: #22344d;
        margin: 3px 0 2px 0;
    }}

    p {{
        margin: 1px 0;
    }}

    .report-header {{
        border-top: 5px solid #2b5f8f;
        background: #f3f6f9;
        padding: 5px 8px 4px 8px;
        margin-bottom: 5px;
    }}

    .report-brand {{
        color: #2b5f8f;
        font-size: 6.5pt;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}

    .report-team {{
        font-size: 15.5pt;
        font-weight: bold;
        color: #132238;
        margin-top: 2px;
    }}

    .report-meta {{
        color: #526173;
        font-size: 7.5pt;
        margin-top: 2px;
    }}

    .report-date {{
        color: #7b8491;
        font-size: 6pt;
        margin-top: 2px;
    }}

    .report-page {{
        width: 100%;
    }}

    .page-two {{
        page-break-before: always;
    }}

    .page-header {{
        border-bottom: 2px solid #2b5f8f;
        margin-bottom: 5px;
        padding-bottom: 3px;
    }}

    .page-header-team {{
        font-size: 10pt;
        font-weight: bold;
        color: #132238;
    }}

    .page-header-meta {{
        font-size: 6.5pt;
        color: #6b7280;
    }}

    .compact-section {{
        margin: 0 0 3px 0;
    }}

    .compact-title {{
        border-bottom: 1px solid #9eb4c8;
        padding: 1px 0 1px 0;
        margin-bottom: 3px;
    }}

    .keyfacts {{
        border-left: 3px solid #2b5f8f;
        background: #edf3f8;
        color: #23364d;
        padding: 2px 4px;
        margin: 2px 0 3px 0;
        font-weight: bold;
        font-size: 6.4pt;
    }}

    .facts {{
        width: 100%;
        border-collapse: collapse;
        margin: 2px 0 3px 0;
        page-break-inside: avoid;
    }}

    .facts td {{
        width: 25%;
        border: 1px solid #d9dee5;
        background: #fbfcfd;
        padding: 1.4px 2px;
        vertical-align: top;
    }}

    .facts td.fact-empty {{
        border: none;
        background: transparent;
        padding: 0;
    }}

    .fact-label {{
        color: #687386;
        font-size: 5.4pt;
        line-height: 1.0;
    }}

    .fact-value {{
        font-weight: bold;
        font-size: 7.8pt;
        color: #17263a;
        margin-top: 1px;
    }}

    .block {{
        page-break-inside: auto;
        margin-bottom: 2px;
    }}

    table.data {{
        width: 100%;
        border-collapse: collapse;
        margin: 2px 0 3px 0;
        font-size: 6.2pt;
    }}

    table.data th {{
        background: #dfe8f0;
        color: #20354d;
        border: 1px solid #c4d0dc;
        padding: 1.6px 2px;
        text-align: left;
        font-weight: bold;
        white-space: nowrap;
    }}

    table.data td {{
        border: 1px solid #d8dde3;
        padding: 1.4px 2px;
        vertical-align: top;
    }}

    table.data tr:nth-child(even) td {{
        background: #f8fafc;
    }}

    .section-table_form .block {{
        display: block;
    }}

    .section-table_form .facts {{
        margin-bottom: 2px;
    }}

    .section-goals table.data {{
        font-size: 6pt;
    }}

    .section-match_flow {{
        margin-bottom: 1px;
    }}

    .section-match_flow h3 {{
        margin: 2px 0 1px 0;
        font-size: 7.2pt;
    }}

    .section-match_flow .facts {{
        margin: 1px 0 1px 0;
    }}

    .section-match_flow .facts td {{
        padding: 1.4px 2px;
    }}

    .section-match_flow .fact-label {{
        font-size: 5.1pt;
    }}

    .section-match_flow .fact-value {{
        font-size: 7.4pt;
    }}

    .section-results table.data {{
        font-size: 5.9pt;
    }}

    .section-players .keyfacts {{
        font-size: 6pt;
    }}

    .section-players table.data {{
        font-size: 5.55pt;
    }}

    .section-players table.data th {{
        padding: 1.4px 1.7px;
    }}

    .section-players table.data td {{
        padding: 1.2px 1.7px;
        line-height: 1.0;
    }}

    .section-players table.data th:first-child,
    .section-players table.data td:first-child {{
        width: 30%;
    }}

    .section-records table.data {{
        font-size: 5.9pt;
    }}

    .muted {{
        color: #6b7280;
    }}

    .small-note {{
        color: #7a8493;
        font-size: 5.8pt;
        margin-top: 2px;
    }}

    ul {{
        margin: 2px 0 3px 12px;
        padding: 0;
    }}

    li {{
        margin: 0;
    }}
</style>
</head>
<body>
{''.join(body_parts)}
</body>
</html>
"""

    def _render_report_header(
        self,
        team_name: str,
        competition_name: str,
        season_name: str,
        generated_text: str,
    ) -> str:
        return f"""
<div class="report-header">
    <div class="report-brand">
        KREISLIGAMANAGER · TEAM-STATISTIKREPORT
    </div>
    <div class="report-team">
        {team_name}
    </div>
    <div class="report-meta">
        {competition_name} · Saison {season_name}
    </div>
    <div class="report-date">
        Erstellt am {escape(generated_text)}
    </div>
</div>
"""

    def _render_page_header(
        self,
        team_name: str,
        competition_name: str,
        season_name: str,
    ) -> str:
        return f"""
<div class="page-header">
    <div class="page-header-team">
        {team_name}
    </div>
    <div class="page-header-meta">
        {competition_name} · Saison {season_name} ·
        Team-Statistikreport
    </div>
</div>
"""

    def _render_compact_section(
        self,
        section_key: str,
        section_data: Any,
    ) -> str:
        title = escape(
            self.SECTION_TITLES[
                section_key
            ]
        )

        section_class = (
            "compact-section "
            f"section-{escape(section_key)}"
        )

        parts = [
            f'<div class="{section_class}">',
            '<div class="compact-title">',
            f"<h2>{title}</h2>",
            "</div>",
        ]

        if isinstance(
            section_data,
            dict,
        ):
            parts.append(
                self._render_section_dict(
                    section_data
                )
            )
        elif isinstance(
            section_data,
            list,
        ):
            parts.append(
                self._render_generic_list(
                    section_data
                )
            )
        else:
            parts.append(
                f"<p>{escape(str(section_data))}</p>"
            )

        parts.append(
            "</div>"
        )

        return "".join(
            parts
        )

    def _render_section(
        self,
        section_key: str,
        section_data: Any,
    ) -> str:
        title = escape(
            self.SECTION_TITLES[
                section_key
            ]
        )

        section_class = (
            "compact-section "
            f"section-{escape(section_key)}"
        )

        parts = [
            (
                f'<div class="{section_class}">'
            ),
            (
                '<div class="section-kicker">'
                'Team-Statistikreport'
                '</div>'
            ),
            (
                '<h2 class="page-title">'
                f"{title}"
                "</h2>"
            ),
        ]

        if isinstance(
            section_data,
            dict,
        ):
            parts.append(
                self._render_section_dict(
                    section_data
                )
            )
        elif isinstance(
            section_data,
            list,
        ):
            parts.append(
                self._render_generic_list(
                    section_data
                )
            )
        else:
            parts.append(
                f"<p>{escape(str(section_data))}</p>"
            )

        parts.append(
            "</div>"
        )

        return "".join(
            parts
        )

    def _render_section_dict(
        self,
        section_data: dict[str, Any],
    ) -> str:
        parts: list[str] = []

        keyfacts = section_data.get(
            "keyfacts"
        )

        if keyfacts:
            parts.append(
                self._render_keyfacts(
                    keyfacts
                )
            )

        facts = section_data.get(
            "facts"
        )

        if isinstance(
            facts,
            dict,
        ) and facts:
            parts.append(
                self._render_facts(
                    facts
                )
            )

        blocks = section_data.get(
            "blocks"
        )

        if isinstance(
            blocks,
            list,
        ):
            for block in blocks:
                parts.append(
                    self._render_block(
                        block
                    )
                )

        tables = section_data.get(
            "tables"
        )

        if isinstance(
            tables,
            list,
        ):
            for table in tables:
                parts.append(
                    self._render_table(
                        table
                    )
                )

        text = section_data.get(
            "text"
        )

        if text:
            parts.append(
                f"<p>{escape(str(text))}</p>"
            )

        if not parts:
            parts.append(
                "<p class=\"muted\">"
                "Keine Daten vorhanden."
                "</p>"
            )

        return "".join(
            parts
        )

    def _render_keyfacts(
        self,
        keyfacts: Any,
    ) -> str:
        if isinstance(
            keyfacts,
            str,
        ):
            text = escape(
                keyfacts
            )
        elif isinstance(
            keyfacts,
            list,
        ):
            text = " | ".join(
                escape(
                    str(
                        value
                    )
                )
                for value in keyfacts
            )
        else:
            text = escape(
                str(
                    keyfacts
                )
            )

        return (
            '<div class="keyfacts">'
            f"{text}"
            "</div>"
        )

    def _render_facts(
        self,
        facts: dict[str, Any],
    ) -> str:
        items = list(
            facts.items()
        )

        if not items:
            return ""

        cells: list[str] = []

        for label, value in items:
            cells.append(
                (
                    "<td>"
                    '<div class="fact-label">'
                    f"{escape(str(label))}"
                    "</div>"
                    '<div class="fact-value">'
                    f"{escape(self._format_value(value))}"
                    "</div>"
                    "</td>"
                )
            )

        rows: list[str] = []

        for index in range(
            0,
            len(cells),
            4,
        ):
            row_cells = cells[
                index:index + 4
            ]

            while len(
                row_cells
            ) < 4:
                row_cells.append(
                    '<td class="fact-empty"></td>'
                )

            rows.append(
                "<tr>"
                + "".join(
                    row_cells
                )
                + "</tr>"
            )

        return (
            '<table class="facts">'
            + "".join(
                rows
            )
            + "</table>"
        )

    def _render_block(
        self,
        block: Any,
    ) -> str:
        if not isinstance(
            block,
            dict,
        ):
            return (
                f"<p>{escape(str(block))}</p>"
            )

        title = block.get(
            "title"
        )

        parts: list[str] = []

        if title:
            parts.append(
                f"<h3>{escape(str(title))}</h3>"
            )

        facts = block.get(
            "facts"
        )

        if isinstance(
            facts,
            dict,
        ):
            parts.append(
                self._render_facts(
                    facts
                )
            )

        table = block.get(
            "table"
        )

        if isinstance(
            table,
            dict,
        ):
            parts.append(
                self._render_table(
                    table
                )
            )

        text = block.get(
            "text"
        )

        if text:
            parts.append(
                f"<p>{escape(str(text))}</p>"
            )

        return (
            '<div class="block">'
            + "".join(
                parts
            )
            + "</div>"
        )

    def _render_table(
        self,
        table: Any,
    ) -> str:
        if not isinstance(
            table,
            dict,
        ):
            return ""

        title = table.get(
            "title"
        )

        headers = table.get(
            "headers",
            [],
        )

        rows = table.get(
            "rows",
            [],
        )

        parts: list[str] = []

        if title:
            parts.append(
                f"<h3>{escape(str(title))}</h3>"
            )

        if not headers:
            return "".join(
                parts
            )

        header_html = "".join(
            f"<th>{escape(str(header))}</th>"
            for header in headers
        )

        row_html: list[str] = []

        for row in rows:
            if isinstance(
                row,
                dict,
            ):
                values = [
                    row.get(
                        header,
                        "",
                    )
                    for header in headers
                ]
            else:
                values = list(
                    row
                )

            cells = "".join(
                (
                    "<td>"
                    f"{escape(self._format_value(value))}"
                    "</td>"
                )
                for value in values
            )

            row_html.append(
                f"<tr>{cells}</tr>"
            )

        return (
            '<table class="data">'
            f"<thead><tr>{header_html}</tr></thead>"
            "<tbody>"
            + "".join(
                row_html
            )
            + "</tbody>"
            "</table>"
        )

    def _render_generic_list(
        self,
        values: list[Any],
    ) -> str:
        if not values:
            return (
                "<p class=\"muted\">"
                "Keine Daten vorhanden."
                "</p>"
            )

        items = "".join(
            (
                "<li>"
                f"{escape(self._format_value(value))}"
                "</li>"
            )
            for value in values
        )

        return (
            f"<ul>{items}</ul>"
        )

    @staticmethod
    def _format_value(
        value: Any,
    ) -> str:
        if value is None:
            return "-"

        if isinstance(
            value,
            float,
        ):
            formatted = (
                f"{value:.2f}"
                .rstrip("0")
                .rstrip(".")
            )

            return formatted.replace(
                ".",
                ",",
            )

        if isinstance(
            value,
            str,
        ):
            stripped = value.strip()

            if re.fullmatch(
                r"\d{4}-\d{2}-\d{2}",
                stripped,
            ):
                try:
                    return datetime.strptime(
                        stripped,
                        "%Y-%m-%d",
                    ).strftime(
                        "%d.%m.%Y"
                    )
                except ValueError:
                    pass

            return stripped

        return str(
            value
        )
