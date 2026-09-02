from __future__ import annotations

from datetime import datetime
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
                12.0,
                12.0,
                12.0,
                14.0,
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

        body_parts = [
            self._render_cover(
                team_name=team_name,
                competition_name=competition_name,
                season_name=season_name,
                generated_text=generated_text,
            )
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

        for section_key in selected_sections:
            if section_key not in (
                self.SECTION_TITLES
            ):
                continue

            section_data = sections.get(
                section_key
            )

            if section_data is None:
                continue

            body_parts.append(
                self._render_section(
                    section_key=section_key,
                    section_data=section_data,
                )
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
        font-size: 9.5pt;
        line-height: 1.35;
    }}

    h1 {{
        font-size: 24pt;
        margin: 0 0 10px 0;
        color: #111827;
    }}

    h2 {{
        font-size: 16pt;
        margin: 0 0 12px 0;
        color: #111827;
    }}

    h3 {{
        font-size: 11pt;
        margin: 12px 0 6px 0;
        color: #1f2933;
    }}

    p {{
        margin: 4px 0;
    }}

    .cover {{
        page-break-after: always;
    }}

    .cover-box {{
        margin-top: 100px;
        border: 1px solid #d1d5db;
        padding: 26px;
    }}

    .cover-team {{
        font-size: 27pt;
        font-weight: bold;
        margin-bottom: 18px;
    }}

    .cover-meta {{
        font-size: 13pt;
        margin-top: 8px;
    }}

    .muted {{
        color: #6b7280;
    }}

    .section {{
        page-break-before: always;
    }}

    .section:first-of-type {{
        page-break-before: auto;
    }}

    .facts {{
        width: 100%;
        border-collapse: collapse;
        margin: 8px 0 14px 0;
    }}

    .facts td {{
        width: 25%;
        border: 1px solid #d1d5db;
        padding: 8px;
        vertical-align: top;
    }}

    .fact-label {{
        color: #6b7280;
        font-size: 8pt;
    }}

    .fact-value {{
        font-weight: bold;
        font-size: 12pt;
        margin-top: 3px;
    }}

    table.data {{
        width: 100%;
        border-collapse: collapse;
        margin: 7px 0 14px 0;
    }}

    table.data th {{
        background: #e5e7eb;
        border: 1px solid #c7cdd4;
        padding: 5px;
        text-align: left;
        font-weight: bold;
    }}

    table.data td {{
        border: 1px solid #d8dde3;
        padding: 5px;
        vertical-align: top;
    }}

    .keyfacts {{
        border-left: 4px solid #64748b;
        background: #f3f4f6;
        padding: 8px 10px;
        margin: 6px 0 12px 0;
    }}

    .note {{
        color: #6b7280;
        font-size: 8pt;
        margin-top: 8px;
    }}

    .page-title {{
        border-bottom: 2px solid #9ca3af;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }}
</style>
</head>
<body>
{''.join(body_parts)}
</body>
</html>
"""

    def _render_cover(
        self,
        team_name: str,
        competition_name: str,
        season_name: str,
        generated_text: str,
    ) -> str:
        return f"""
<div class="cover">
    <div class="cover-box">
        <div class="muted">
            KreisligaManager
        </div>

        <div class="cover-team">
            {team_name}
        </div>

        <div class="cover-meta">
            {competition_name}
        </div>

        <div class="cover-meta">
            Saison {season_name}
        </div>

        <div class="cover-meta muted">
            Team-Statistikreport
        </div>

        <p class="note">
            Erstellt am {escape(generated_text)}
        </p>
    </div>
</div>
"""

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

        parts = [
            '<div class="section">',
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
                    "<td></td>"
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

        return "".join(
            parts
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
            return (
                f"{value:.2f}"
            )

        return str(
            value
        )
