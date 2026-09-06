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
            QPageLayout.Orientation.Landscape
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
                '<div class="report-page page-one v11-page">'
            )

            if "overview" in page_1:
                body_parts.append(
                    self._render_compact_section(
                        section_key="overview",
                        section_data=sections[
                            "overview"
                        ],
                    )
                )

            comparison_html = ""
            goals_html = ""

            if "table_form" in page_1:
                comparison_html = (
                    self._render_compact_section(
                        section_key="table_form",
                        section_data=sections[
                            "table_form"
                        ],
                    )
                )

            if "goals" in page_1:
                goals_html = (
                    self._render_compact_section(
                        section_key="goals",
                        section_data=sections[
                            "goals"
                        ],
                    )
                )

            if comparison_html or goals_html:
                body_parts.append(
                    '<table width="100%" class="v11-analysis-row">'
                    '<tr>'
                    '<td width="38%" class="v11-analysis-left">'
                    f"{comparison_html}"
                    '</td>'
                    '<td width="62%" class="v11-analysis-right">'
                    f"{goals_html}"
                    '</td>'
                    '</tr>'
                    '</table>'
                )

            if "match_flow" in page_1:
                body_parts.append(
                    '<div class="v11-flow-block">'
                    + self._render_compact_section(
                        section_key="match_flow",
                        section_data=sections[
                            "match_flow"
                        ],
                    )
                    + "</div>"
                )

            body_parts.append(
                "</div>"
            )

        if page_2:
            body_parts.append(
                '<div class="report-page page-two v11-page">'
            )

            body_parts.append(
                self._render_page_header(
                    team_name=team_name,
                    competition_name=competition_name,
                    season_name=season_name,
                )
            )

            if "results" in page_2:
                body_parts.append(
                    '<div class="v11-full-section v11-results">'
                    + self._render_compact_section(
                        section_key="results",
                        section_data=sections[
                            "results"
                        ],
                    )
                    + "</div>"
                )

            if "players" in page_2:
                body_parts.append(
                    '<div class="v11-full-section v11-players">'
                    + self._render_compact_section(
                        section_key="players",
                        section_data=sections[
                            "players"
                        ],
                    )
                    + "</div>"
                )

            if "records" in page_2:
                body_parts.append(
                    '<div class="v11-full-section v11-records">'
                    + self._render_compact_section(
                        section_key="records",
                        section_data=sections[
                            "records"
                        ],
                    )
                    + "</div>"
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
        size: A4 landscape;
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
        color: #e7edf4;
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
        
    }}

    .facts td {{
        width: 25%;
        border: 1px solid #d9dee5;
        background: #24282e;
        padding: 1.4px 2px;
        vertical-align: top;
    }}

    .facts td.fact-empty {{
        border: none;
        background: transparent;
        padding: 0;
    }}

    .fact-label {{
        color: #9ea8b4;
        font-size: 5.4pt;
        line-height: 1.0;
    }}

    .fact-value {{
        font-weight: bold;
        font-size: 7.8pt;
        color: #f4f6f8;
        margin-top: 1px;
    }}

    .block {{
        
        margin-bottom: 2px;
    }}

    table.data {{
        width: 100%;
        border-collapse: collapse;
        margin: 2px 0 3px 0;
        font-size: 6.2pt;
    }}

    table.data th {{
        background: #2c333d;
        color: #dce6f0;
        border: 1px solid #46515e;
        padding: 1.6px 2px;
        text-align: left;
        font-weight: bold;
        white-space: nowrap;
    }}

    table.data td {{
        border: 1px solid #3b424c;
        padding: 1.4px 2px;
        vertical-align: top;
    }}

    table.data tr:nth-child(even) td {{
        background: #22262b;
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

    /* PDF Design v2: visual status language */
    .status-positive {{
        background: #e8f5ec !important;
        border-color: #9fd2ad !important;
    }}

    .status-positive .fact-value {{ color: #42b85a; }}

    .status-neutral {{
        background: #fff7dc !important;
        border-color: #e4ca72 !important;
    }}

    .status-neutral .fact-value {{ color: #d49a2a; }}

    .status-negative {{
        background: #fdebec !important;
        border-color: #e2a3a7 !important;
    }}

    .status-negative .fact-value {{ color: #e04b4b; }}

    .form-strip {{
        margin: 2px 0 3px 0;
        white-space: nowrap;
    }}

    .form-chip {{
        display: inline-block;
        min-width: 17px;
        padding: 3px 5px;
        margin-right: 3px;
        text-align: center;
        font-weight: bold;
        font-size: 8pt;
        border: 1px solid #48515c;
    }}

    .form-win {{ background: #25823b; color: #ffffff; border-color: #8fc79e; }}
    .form-draw {{ background: #b47b16; color: #ffffff; border-color: #d9bd5c; }}
    .form-loss {{ background: #bd3b3b; color: #ffffff; border-color: #d99399; }}

    .visual-summary {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 3px 0;
        margin: 2px 0 4px 0;
    }}

    .visual-summary td {{
        width: 33%;
        padding: 4px 5px;
        border: 1px solid #3b424c;
        vertical-align: top;
    }}

    .visual-summary .summary-label {{
        font-size: 5.4pt;
        color: #6a7584;
    }}

    .visual-summary .summary-value {{
        margin-top: 1px;
        font-size: 9pt;
        font-weight: bold;
    }}

    .data tr.row-positive td {{ background: #24282e; }}
    .data tr.row-neutral td {{ background: #fff9e8; }}
    .data tr.row-negative td {{ background: #24282e; }}

    /* PDF Design v3: dashboard-style report */
    .dashboard-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 3px 0;
        margin: 2px 0 4px 0;
    }}

    .dashboard-kpis td {{
        width: 20%;
        border: 1px solid #3b424c;
        background: #24282e;
        padding: 4px 5px;
        vertical-align: top;
    }}

    .dashboard-kpis .kpi-label {{
        font-size: 5.2pt;
        color: #9ea8b4;
    }}

    .dashboard-kpis .kpi-value {{
        font-size: 10pt;
        font-weight: bold;
        color: #f4f6f8;
        margin-top: 1px;
    }}

    .dashboard-kpis td.kpi-positive {{
        background: #24282e;
        border-color: #9fd2ad;
    }}

    .dashboard-kpis td.kpi-positive .kpi-value {{
        color: #42b85a;
    }}

    .dashboard-kpis td.kpi-neutral {{
        background: #24282e;
        border-color: #e4ca72;
    }}

    .dashboard-kpis td.kpi-neutral .kpi-value {{
        color: #d49a2a;
    }}

    .dashboard-kpis td.kpi-negative {{
        background: #24282e;
        border-color: #e2a3a7;
    }}

    .dashboard-kpis td.kpi-negative .kpi-value {{
        color: #e04b4b;
    }}

    .form-panel {{
        border: 1px solid #3b424c;
        background: #22262b;
        padding: 4px 6px;
        margin: 2px 0 4px 0;
    }}

    .form-panel-title {{
        color: #9ea8b4;
        font-size: 5.4pt;
        margin-bottom: 2px;
    }}

    .form-panel .form-chip {{
        min-width: 22px;
        padding: 4px 7px;
        margin-right: 4px;
        font-size: 9pt;
    }}

    .compare-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 2px 0 4px 0;
        font-size: 6pt;
    }}

    .compare-table th {{
        border: 1px solid #46515e;
        background: #2c333d;
        color: #dce6f0;
        padding: 2px 3px;
        text-align: center;
    }}

    .compare-table th:first-child {{
        text-align: left;
    }}

    .compare-table td {{
        border: 1px solid #3b424c;
        padding: 2px 3px;
        text-align: center;
    }}

    .compare-table td:first-child {{
        text-align: left;
        color: #9ea8b4;
        font-weight: bold;
    }}

    .compare-positive {{
        color: #42b85a;
        font-weight: bold;
    }}

    .compare-neutral {{
        color: #d49a2a;
        font-weight: bold;
    }}

    .compare-negative {{
        color: #e04b4b;
        font-weight: bold;
    }}

    .phase-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 2px 0 3px 0;
        font-size: 5.8pt;
    }}

    .phase-table td {{
        border-bottom: 1px solid #343a42;
        padding: 2px 3px;
        vertical-align: middle;
    }}

    .phase-label {{
        width: 14%;
        font-weight: bold;
        color: #d3dbe4;
    }}

    .phase-number {{
        width: 7%;
        text-align: right;
        font-weight: bold;
    }}

    .bar-track {{
        width: 100%;
        border-collapse: collapse;
        background: #30353c;
    }}

    .bar-fill-positive {{
        background: #329447;
        height: 7px;
    }}

    .bar-fill-negative {{
        background: #c63d3d;
        height: 7px;
    }}

    .bar-empty {{
        background: #30353c;
        height: 7px;
    }}

    .flow-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 4px 0;
        margin: 2px 0 3px 0;
    }}

    .flow-card {{
        width: 50%;
        border: 1px solid #3b424c;
        padding: 4px 6px;
        vertical-align: top;
    }}

    .flow-positive {{
        background: #24282e;
        border-color: #9fd2ad;
    }}

    .flow-negative {{
        background: #24282e;
        border-color: #e2a3a7;
    }}

    .flow-card-title {{
        font-size: 7.2pt;
        font-weight: bold;
        color: #e7edf4;
        margin-bottom: 2px;
    }}

    .flow-main {{
        font-size: 13pt;
        font-weight: bold;
        margin-bottom: 2px;
    }}

    .flow-positive .flow-main {{
        color: #42b85a;
    }}

    .flow-negative .flow-main {{
        color: #e04b4b;
    }}

    .flow-detail {{
        font-size: 5.8pt;
        color: #b8c0ca;
    }}

    .progress-track {{
        width: 100%;
        border-collapse: collapse;
        background: #30353c;
        margin: 2px 0;
    }}

    .progress-good {{
        height: 6px;
        background: #329447;
    }}

    .progress-bad {{
        height: 6px;
        background: #c63d3d;
    }}

    .progress-empty {{
        height: 6px;
        background: #30353c;
    }}

    .result-chip {{
        display: inline-block;
        min-width: 14px;
        text-align: center;
        padding: 1px 3px;
        font-weight: bold;
        border: 1px solid #48515c;
    }}

    .result-win {{
        background: #25823b;
        color: #ffffff;
        border-color: #8fc79e;
    }}

    .result-draw {{
        background: #b47b16;
        color: #ffffff;
        border-color: #d9bd5c;
    }}

    .result-loss {{
        background: #bd3b3b;
        color: #ffffff;
        border-color: #d99399;
    }}

    .ranking-table td.rank-value {{
        font-weight: bold;
        color: #42b85a;
        text-align: right;
    }}

    .record-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 3px 0;
        margin-top: 2px;
    }}

    .record-cards td {{
        width: 33%;
        border: 1px solid #3b424c;
        background: #22262b;
        padding: 4px 5px;
        vertical-align: top;
    }}

    .record-card-label {{
        font-size: 5.4pt;
        color: #9ea8b4;
    }}

    .record-card-value {{
        font-size: 9pt;
        font-weight: bold;
        color: #f4f6f8;
        margin: 1px 0;
    }}

    .record-card-match {{
        font-size: 5.2pt;
        color: #9ea8b4;
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

    /* KreisligaManager Dark Theme - PDF v4 */
    body {{
        background: #1b1b1b;
        color: #eef1f4;
    }}

    .page {{
        background: #1b1b1b;
        color: #eef1f4;
    }}

    h1, h2, h3, p, td, th, div, span {{
        color: #eef1f4;
    }}

    .report-header {{
        border-bottom: 1px solid #3b424c;
    }}

    .section {{
        background: #1b1b1b;
    }}

    .section-title {{
        background: #2b3038;
        color: #f2f5f8;
        border: 1px solid #3d4652;
    }}

    .data,
    .compare-table,
    .phase-table {{
        background: #202327;
    }}

    .data th,
    .compare-table th {{
        background: #2b3038;
        color: #dbe3ec;
        border-color: #424a55;
    }}

    .data td,
    .compare-table td,
    .phase-table td {{
        background: #202327;
        color: #e8ebef;
        border-color: #343a42;
    }}

    .dashboard-kpis td,
    .record-cards td,
    .flow-card,
    .form-panel {{
        background: #24282e;
        border-color: #3b424c;
    }}

    .dashboard-kpis td.kpi-positive,
    .dashboard-kpis td.kpi-neutral,
    .dashboard-kpis td.kpi-negative,
    .flow-positive,
    .flow-negative {{
        background: #24282e;
    }}

    .kpi-label,
    .form-panel-title,
    .record-card-label,
    .record-card-match,
    .flow-detail,
    .small-note,
    .muted {{
        color: #9ea8b4;
    }}

    .kpi-value,
    .record-card-value,
    .flow-card-title,
    .phase-label {{
        color: #f3f5f7;
    }}

    /* Semantic accents: only the important values get color */
    .kpi-positive .kpi-value,
    .compare-positive,
    .status-positive,
    .ranking-table td.rank-value,
    .flow-positive .flow-main {{
        color: #42b85a;
    }}

    .kpi-neutral .kpi-value,
    .compare-neutral,
    .status-neutral {{
        color: #d49a2a;
    }}

    .kpi-negative .kpi-value,
    .compare-negative,
    .status-negative,
    .flow-negative .flow-main {{
        color: #e04b4b;
    }}

    .bar-track,
    .progress-track,
    .bar-empty,
    .progress-empty {{
        background: #343a42;
    }}

    .bar-fill-positive,
    .progress-good {{
        background: #329447;
    }}

    .bar-fill-negative,
    .progress-bad {{
        background: #c63d3d;
    }}

    .result-win {{
        background: #25823b;
        color: #ffffff;
        border-color: #329447;
    }}

    .result-draw {{
        background: #b47b16;
        color: #ffffff;
        border-color: #c58a1c;
    }}

    .result-loss {{
        background: #bd3b3b;
        color: #ffffff;
        border-color: #d14a4a;
    }}

    .form-win {{
        background: #25823b;
        color: #ffffff;
        border-color: #329447;
    }}

    .form-draw {{
        background: #b47b16;
        color: #ffffff;
        border-color: #c58a1c;
    }}

    .form-loss {{
        background: #bd3b3b;
        color: #ffffff;
        border-color: #d14a4a;
    }}


    /* PDF v5 - Landscape full-width dashboard */
    .report-page {{
        width: 100%;
    }}

    .compact-section {{
        width: 100%;
    }}

    .dashboard-row {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 6px 0;
        margin: 0 0 6px 0;
    }}

    .dashboard-col {{
        vertical-align: top;
        padding: 0;
    }}

    .dashboard-col-left {{
        width: 40%;
    }}

    .dashboard-col-right {{
        width: 60%;
    }}

    .page-two-results {{
        width: 58%;
    }}

    .page-two-players {{
        width: 42%;
    }}

    .dashboard-kpis,
    .compare-table,
    .phase-table,
    .flow-cards,
    .record-cards,
    table.data {{
        width: 100%;
    }}

    .dashboard-kpis td {{
        padding: 7px 8px;
    }}

    .dashboard-kpis .kpi-label {{
        font-size: 6.2pt;
    }}

    .dashboard-kpis .kpi-value {{
        font-size: 13pt;
    }}

    .form-panel {{
        padding: 6px 8px;
    }}

    .form-panel .form-chip {{
        min-width: 28px;
        padding: 5px 9px;
        font-size: 10pt;
    }}

    .compare-table {{
        font-size: 7pt;
    }}

    .compare-table th,
    .compare-table td {{
        padding: 4px 5px;
    }}

    .phase-table {{
        font-size: 6.8pt;
    }}

    .phase-table td {{
        padding: 3px 4px;
    }}

    .bar-fill-positive,
    .bar-fill-negative,
    .bar-empty {{
        height: 10px;
    }}

    .flow-card {{
        padding: 9px 12px;
    }}

    .flow-card-title {{
        font-size: 8.3pt;
    }}

    .flow-main {{
        font-size: 18pt;
    }}

    .flow-detail {{
        font-size: 6.7pt;
    }}

    .progress-good,
    .progress-bad,
    .progress-empty {{
        height: 9px;
    }}

    .section-results table.data,
    .section-players table.data {{
        font-size: 6.4pt;
    }}

    .section-results table.data th,
    .section-results table.data td,
    .section-players table.data th,
    .section-players table.data td {{
        padding: 2.2px 3px;
    }}

    .record-cards td {{
        padding: 8px 9px;
    }}

    .record-card-label {{
        font-size: 6.2pt;
    }}

    .record-card-value {{
        font-size: 13pt;
    }}

    .record-card-match {{
        font-size: 6pt;
    }}


    /* PDF v6 - genuine full-width landscape components */
    .wide-form-row {{
        width: 100%;
        border-collapse: collapse;
        margin: 3px 0 7px 0;
        background: #24282e;
        border: 1px solid #3b424c;
    }}

    .wide-form-row td {{
        padding: 6px 8px;
        vertical-align: middle;
    }}

    .wide-form-label {{
        color: #9ea8b4;
        font-weight: bold;
        font-size: 7pt;
    }}

    .wide-form-value {{
        text-align: left;
    }}

    .comparison-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 5px 0;
    }}

    .comparison-card {{
        vertical-align: top;
        background: #24282e;
        border: 1px solid #3b424c;
        padding: 0;
    }}

    .comparison-card-title {{
        background: #2b3038;
        color: #dfe7ef;
        font-size: 8pt;
        font-weight: bold;
        text-align: center;
        padding: 5px 4px;
        border-bottom: 1px solid #424a55;
    }}

    .comparison-card-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 6.7pt;
    }}

    .comparison-card-table td {{
        border-bottom: 1px solid #343a42;
        padding: 4px 6px;
    }}

    .comparison-card-table td:first-child {{
        color: #9ea8b4;
        width: 48%;
    }}

    .comparison-card-table td:last-child {{
        text-align: right;
    }}

    .comparison-card-form {{
        padding: 6px;
        text-align: center;
    }}

    .phase-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 4px 0;
        margin-top: 5px;
    }}

    .phase-card {{
        vertical-align: top;
        background: #24282e;
        border: 1px solid #3b424c;
        padding: 5px 5px 6px 5px;
    }}

    .phase-card-title {{
        text-align: center;
        font-weight: bold;
        font-size: 7pt;
        color: #dfe7ef;
        margin-bottom: 3px;
    }}

    .phase-card-score {{
        text-align: center;
        font-size: 10pt;
        font-weight: bold;
        margin-bottom: 4px;
    }}

    .phase-card-label {{
        font-size: 5.4pt;
        color: #9ea8b4;
        margin-top: 2px;
    }}

    .section-table_form,
    .section-goals,
    .section-match_flow,
    .section-results,
    .section-players,
    .section-records {{
        width: 100%;
    }}

    .dashboard-row td.dashboard-col {{
        box-sizing: border-box;
    }}

    .section-match_flow .flow-cards td {{
        min-height: 90px;
    }}


    /* PDF v7 - Light / airy / print-first */
    body {{
        background: #ffffff;
        color: #151515;
        font-family: "Arial", "DejaVu Sans", sans-serif;
        font-size: 7.2pt;
        line-height: 1.22;
    }}

    .report-page,
    .section {{
        background: #ffffff;
        color: #151515;
    }}

    h1, h2, h3,
    p, div, span,
    td, th {{
        color: #151515;
    }}

    .report-header {{
        background: #ffffff;
        border: none;
        border-bottom: 1px solid #d9dde2;
        padding: 6px 0 8px 0;
        margin-bottom: 12px;
    }}

    .report-brand {{
        color: #68717b;
        font-size: 6.2pt;
        letter-spacing: 0.7px;
    }}

    .report-team {{
        color: #101214;
        font-size: 18pt;
        margin-top: 3px;
    }}

    .report-meta,
    .report-date,
    .page-header-meta {{
        color: #727982;
    }}

    .page-header {{
        border-bottom: 1px solid #d9dde2;
        margin-bottom: 12px;
        padding-bottom: 6px;
    }}

    .compact-section {{
        margin: 0 0 14px 0;
    }}

    .compact-title {{
        border: none;
        border-bottom: 1px solid #e1e4e8;
        margin-bottom: 8px;
        padding: 0 0 4px 0;
    }}

    .compact-title h2 {{
        color: #17191b;
        font-size: 11pt;
        font-weight: bold;
    }}

    .dashboard-row {{
        border-spacing: 16px 0;
        margin-bottom: 14px;
    }}

    .dashboard-kpis {{
        border-spacing: 8px 0;
        margin: 0 0 10px 0;
    }}

    .dashboard-kpis td {{
        background: #ffffff;
        border: 1px solid #dfe3e7;
        padding: 10px 11px;
    }}

    .dashboard-kpis td.kpi-positive,
    .dashboard-kpis td.kpi-neutral,
    .dashboard-kpis td.kpi-negative {{
        background: #ffffff;
    }}

    .dashboard-kpis .kpi-label {{
        color: #727982;
        font-size: 5.9pt;
    }}

    .dashboard-kpis .kpi-value {{
        color: #17191b;
        font-size: 14pt;
        margin-top: 3px;
    }}

    /* Only genuinely important semantic values are colored */
    .dashboard-kpis td.kpi-positive .kpi-value,
    .compare-positive,
    .status-positive,
    .ranking-table td.rank-value {{
        color: #2f9e44;
    }}

    .dashboard-kpis td.kpi-neutral .kpi-value,
    .compare-neutral,
    .status-neutral {{
        color: #b47b00;
    }}

    .dashboard-kpis td.kpi-negative .kpi-value,
    .compare-negative,
    .status-negative {{
        color: #d94848;
    }}

    .wide-form-row {{
        background: #ffffff;
        border: 1px solid #dfe3e7;
        margin: 0 0 12px 0;
    }}

    .wide-form-row td {{
        padding: 8px 10px;
    }}

    .wide-form-label {{
        color: #727982;
        font-size: 6.4pt;
        letter-spacing: 0.3px;
    }}

    .form-dots {{
        white-space: nowrap;
    }}

    .form-dot-item {{
        display: inline-block;
        margin-right: 11px;
    }}

    .form-dot {{
        font-size: 14pt;
        vertical-align: middle;
    }}

    .form-dot-letter {{
        color: #4f565e;
        font-size: 7pt;
        font-weight: bold;
        margin-left: 2px;
        vertical-align: middle;
    }}

    .comparison-cards {{
        border-spacing: 10px 0;
    }}

    .comparison-card {{
        background: #ffffff;
        border: 1px solid #dfe3e7;
    }}

    .comparison-card-title {{
        background: #f7f8f9;
        color: #25282c;
        border-bottom: 1px solid #e1e4e8;
        font-size: 7.4pt;
        padding: 7px 6px;
    }}

    .comparison-card-table {{
        font-size: 6.6pt;
    }}

    .comparison-card-table td {{
        border-bottom: 1px solid #edf0f2;
        padding: 6px 8px;
    }}

    .comparison-card-table td:first-child {{
        color: #777f88;
    }}

    .phase-cards {{
        border-spacing: 7px 0;
        margin-top: 8px;
    }}

    .phase-card {{
        background: #ffffff;
        border: 1px solid #dfe3e7;
        padding: 8px 7px 9px 7px;
    }}

    .phase-card-title {{
        color: #545b63;
        font-size: 6.5pt;
        margin-bottom: 5px;
    }}

    .phase-card-score {{
        font-size: 11pt;
        margin-bottom: 7px;
    }}

    .phase-card-label {{
        color: #8a9199;
        font-size: 5pt;
    }}

    .bar-track,
    .progress-track,
    .bar-empty,
    .progress-empty {{
        background: #eef0f2;
    }}

    .bar-fill-positive,
    .progress-good {{
        background: #2f9e44;
    }}

    .bar-fill-negative,
    .progress-bad {{
        background: #d94848;
    }}

    .flow-cards {{
        border-spacing: 12px 0;
    }}

    .flow-card,
    .flow-positive,
    .flow-negative {{
        background: #ffffff;
        border: 1px solid #dfe3e7;
        padding: 12px 14px;
    }}

    .flow-card-title {{
        color: #4f565e;
        font-size: 7.5pt;
    }}

    .flow-main {{
        color: #17191b;
        font-size: 20pt;
        margin: 5px 0 4px 0;
    }}

    .flow-positive .flow-main,
    .flow-negative .flow-main {{
        color: #17191b;
    }}

    .flow-detail {{
        color: #7a8189;
        font-size: 6.2pt;
    }}

    table.data {{
        background: #ffffff;
        border-collapse: collapse;
        font-size: 6.6pt;
    }}

    table.data th {{
        background: #f5f6f7;
        color: #42474d;
        border: none;
        border-bottom: 1px solid #d9dde2;
        padding: 6px 7px;
    }}

    table.data td {{
        background: #ffffff;
        color: #202326;
        border: none;
        border-bottom: 1px solid #eceff1;
        padding: 5px 7px;
    }}

    table.data tr:nth-child(even) td {{
        background: #fbfbfc;
    }}

    .airy-table td {{
        padding-top: 6px;
        padding-bottom: 6px;
    }}

    .result-status-cell {{
        white-space: nowrap;
        text-align: center;
    }}

    .result-dot {{
        font-size: 11pt;
        vertical-align: middle;
    }}

    .result-letter {{
        color: #5f666e;
        font-weight: bold;
        margin-left: 2px;
        vertical-align: middle;
    }}

    .keyfacts {{
        background: transparent;
        color: #5e656d;
        border-left: 2px solid #cfd4d9;
        padding: 4px 7px;
        margin-bottom: 8px;
    }}

    .record-cards {{
        border-spacing: 10px 0;
    }}

    .record-cards td {{
        background: #ffffff;
        border: 1px solid #dfe3e7;
        padding: 11px 12px;
    }}

    .record-card-label {{
        color: #737b84;
        font-size: 5.8pt;
    }}

    .record-card-value {{
        color: #17191b;
        font-size: 14pt;
        margin: 4px 0;
    }}

    .record-card-match {{
        color: #777f88;
        font-size: 5.7pt;
        line-height: 1.25;
    }}

    .small-note,
    .muted {{
        color: #8a9199;
    }}

    /* Remove the heavy "app panel" impression in the PDF */
    .section-title,
    .form-panel {{
        background: transparent;
        border-color: #dfe3e7;
    }}


    /* PDF v8 - Editorial, calm, spacious */
    body {{
        background: #ffffff;
        color: #17191b;
        font-family: "Arial", "DejaVu Sans", sans-serif;
        font-size: 7.5pt;
        line-height: 1.28;
    }}

    .report-header {{
        background: #ffffff;
        border: none;
        border-bottom: 1px solid #d9dde2;
        padding: 6px 0 10px 0;
        margin-bottom: 14px;
    }}

    .report-team {{
        color: #101214;
        font-size: 19pt;
    }}

    .report-meta,
    .report-date,
    .report-brand,
    .page-header-meta {{
        color: #707780;
    }}

    .page-header {{
        border-bottom: 1px solid #d9dde2;
        padding-bottom: 8px;
        margin-bottom: 14px;
    }}

    .compact-section {{
        margin-bottom: 18px;
    }}

    .compact-title {{
        border: none;
        margin: 0 0 8px 0;
        padding: 0;
    }}

    .compact-title h2 {{
        font-size: 11.5pt;
        color: #17191b;
    }}

    .editorial-two-col {{
        border-collapse: separate;
        border-spacing: 20px 0;
        margin-bottom: 8px;
    }}

    .editorial-col {{
        vertical-align: top;
        padding: 0;
    }}

    .editorial-kpi-strip {{
        border-collapse: separate;
        border-spacing: 10px 0;
        margin-bottom: 12px;
    }}

    .editorial-kpi {{
        border: none;
        border-top: 2px solid #202326;
        padding: 7px 2px 4px 2px;
    }}

    .editorial-kpi-label {{
        font-size: 5.8pt;
        color: #767d85;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}

    .editorial-kpi-value {{
        font-size: 15pt;
        font-weight: bold;
        color: #17191b;
        margin-top: 3px;
    }}

    .editorial-positive {{
        color: #2f9e44;
    }}

    .editorial-neutral {{
        color: #b47b00;
    }}

    .editorial-negative {{
        color: #d94848;
    }}

    .editorial-form-line {{
        border-bottom: 1px solid #e4e7ea;
        padding: 7px 0 10px 0;
        margin-bottom: 4px;
    }}

    .editorial-inline-label {{
        display: inline-block;
        width: 55px;
        color: #767d85;
        font-size: 5.9pt;
        font-weight: bold;
        vertical-align: middle;
    }}

    .form-dots {{
        display: inline-block;
        vertical-align: middle;
    }}

    .form-dot-item {{
        margin-right: 13px;
    }}

    .form-dot {{
        font-size: 14pt;
    }}

    .form-dot-letter {{
        color: #555c64;
        font-size: 6.8pt;
    }}

    .editorial-compare {{
        border-collapse: collapse;
        font-size: 7pt;
    }}

    .editorial-compare th {{
        background: transparent;
        color: #6f767f;
        border: none;
        border-bottom: 1px solid #dfe3e7;
        padding: 6px 4px;
        text-align: right;
        font-weight: bold;
    }}

    .editorial-compare th:first-child {{
        text-align: left;
    }}

    .editorial-compare td {{
        background: #ffffff;
        color: #202326;
        border: none;
        border-bottom: 1px solid #edf0f2;
        padding: 7px 4px;
        text-align: right;
    }}

    .editorial-compare td:first-child {{
        text-align: left;
        color: #737b84;
    }}

    .editorial-goal-bars {{
        border-collapse: collapse;
        font-size: 6.7pt;
    }}

    .editorial-goal-bars th {{
        color: #737b84;
        background: transparent;
        border: none;
        border-bottom: 1px solid #dfe3e7;
        padding: 5px 3px;
        text-align: left;
    }}

    .editorial-goal-bars td {{
        background: #ffffff;
        border: none;
        border-bottom: 1px solid #eef0f2;
        padding: 6px 3px;
    }}

    .editorial-phase {{
        width: 12%;
        color: #4c535b;
        font-weight: bold;
    }}

    .editorial-number {{
        width: 7%;
        text-align: right;
        font-weight: bold;
    }}

    .editorial-bar-cell {{
        width: 37%;
    }}

    .bar-track,
    .progress-track,
    .bar-empty,
    .progress-empty {{
        background: #eff1f3;
    }}

    .bar-fill-positive,
    .progress-good {{
        background: #2f9e44;
    }}

    .bar-fill-negative,
    .progress-bad {{
        background: #d94848;
    }}

    .editorial-flow {{
        border-collapse: separate;
        border-spacing: 18px 0;
    }}

    .editorial-flow-cell {{
        vertical-align: top;
        padding: 2px 0 0 0;
        border-top: 2px solid #202326;
    }}

    .editorial-flow-heading {{
        color: #565d65;
        font-size: 7.2pt;
        font-weight: bold;
        margin-top: 6px;
    }}

    .editorial-flow-value {{
        color: #17191b;
        font-size: 21pt;
        font-weight: bold;
        margin: 5px 0 1px 0;
    }}

    .editorial-flow-label {{
        color: #7a8189;
        font-size: 6pt;
        margin-bottom: 5px;
    }}

    .editorial-flow-record {{
        color: #555c64;
        font-size: 6.5pt;
        margin-top: 5px;
    }}

    table.data {{
        width: 100%;
        border-collapse: collapse;
        font-size: 6.8pt;
    }}

    table.data th {{
        background: transparent;
        color: #666e77;
        border: none;
        border-bottom: 1px solid #d9dde2;
        padding: 6px 7px;
    }}

    table.data td {{
        background: #ffffff;
        color: #202326;
        border: none;
        border-bottom: 1px solid #edf0f2;
        padding: 6px 7px;
    }}

    table.data tr:nth-child(even) td {{
        background: #fbfbfc;
    }}

    .keyfacts {{
        border: none;
        background: transparent;
        color: #626a73;
        padding: 0;
        margin: 0 0 8px 0;
        font-size: 6.4pt;
    }}

    .record-cards {{
        border-collapse: collapse;
    }}

    .record-cards td {{
        background: #ffffff;
        border: none;
        border-bottom: 1px solid #e1e4e8;
        padding: 8px 0;
    }}

    .record-card-label {{
        color: #7a8189;
        font-size: 5.8pt;
    }}

    .record-card-value {{
        color: #17191b;
        font-size: 13pt;
        margin: 3px 0;
    }}

    .record-card-match {{
        color: #7a8189;
        font-size: 5.6pt;
    }}

    .small-note,
    .muted {{
        color: #8a9199;
    }}

    /* Suppress old card/panel feel */
    .dashboard-kpis,
    .comparison-cards,
    .phase-cards,
    .flow-cards,
    .wide-form-row {{
        background: transparent;
        border: none;
    }}


    /* PDF v9 - Medium spacing / balanced density */
    .report-header {{
        padding-bottom: 7px;
        margin-bottom: 9px;
    }}

    .page-header {{
        padding-bottom: 5px;
        margin-bottom: 9px;
    }}

    .compact-section {{
        margin-bottom: 11px;
    }}

    .compact-title {{
        margin-bottom: 5px;
    }}

    .editorial-two-col {{
        border-spacing: 14px 0;
        margin-bottom: 4px;
    }}

    .editorial-kpi-strip {{
        border-spacing: 7px 0;
        margin-bottom: 7px;
    }}

    .editorial-kpi {{
        padding-top: 5px;
        padding-bottom: 3px;
    }}

    .editorial-kpi-value {{
        margin-top: 2px;
    }}

    .editorial-form-line {{
        padding-top: 5px;
        padding-bottom: 6px;
        margin-bottom: 2px;
    }}

    .form-dot-item {{
        margin-right: 10px;
    }}

    .editorial-compare th {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .editorial-compare td {{
        padding-top: 5px;
        padding-bottom: 5px;
    }}

    .editorial-goal-bars th {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .editorial-goal-bars td {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .editorial-flow {{
        border-spacing: 14px 0;
    }}

    .editorial-flow-heading {{
        margin-top: 4px;
    }}

    .editorial-flow-value {{
        margin-top: 3px;
        margin-bottom: 0;
    }}

    .editorial-flow-label {{
        margin-bottom: 3px;
    }}

    .editorial-flow-record {{
        margin-top: 3px;
    }}

    table.data th {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    table.data td {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .keyfacts {{
        margin-bottom: 5px;
    }}

    .record-cards td {{
        padding-top: 6px;
        padding-bottom: 6px;
    }}

    .record-card-value {{
        margin-top: 2px;
        margin-bottom: 2px;
    }}

    .editorial-bottom {{
        margin-top: 3px;
    }}


    /* PDF v10 - balanced fill: larger content, still calm */
    body {{
        font-size: 8.2pt;
        line-height: 1.30;
    }}

    .report-team {{
        font-size: 21pt;
    }}

    .compact-title h2 {{
        font-size: 12.5pt;
    }}

    .report-header {{
        margin-bottom: 11px;
        padding-bottom: 9px;
    }}

    .page-header {{
        margin-bottom: 11px;
        padding-bottom: 7px;
    }}

    .compact-section {{
        margin-bottom: 14px;
    }}

    .editorial-kpi-strip {{
        margin-bottom: 10px;
    }}

    .editorial-kpi {{
        padding-top: 7px;
        padding-bottom: 6px;
    }}

    .editorial-kpi-label {{
        font-size: 6.4pt;
    }}

    .editorial-kpi-value {{
        font-size: 17pt;
        margin-top: 3px;
    }}

    .editorial-form-line {{
        padding-top: 7px;
        padding-bottom: 8px;
    }}

    .editorial-inline-label {{
        font-size: 6.4pt;
    }}

    .form-dot {{
        font-size: 16pt;
    }}

    .form-dot-letter {{
        font-size: 7.2pt;
    }}

    .editorial-two-col {{
        border-spacing: 16px 0;
        margin-bottom: 8px;
    }}

    .editorial-compare {{
        font-size: 7.6pt;
    }}

    .editorial-compare th,
    .editorial-compare td {{
        padding-top: 6px;
        padding-bottom: 6px;
    }}

    .editorial-goal-bars {{
        font-size: 7.4pt;
    }}

    .editorial-goal-bars th,
    .editorial-goal-bars td {{
        padding-top: 5px;
        padding-bottom: 5px;
    }}

    .bar-fill-positive,
    .bar-fill-negative,
    .bar-empty {{
        height: 8px;
    }}

    .editorial-flow {{
        border-spacing: 16px 0;
    }}

    .editorial-flow-cell {{
        padding-top: 3px;
        padding-bottom: 4px;
    }}

    .editorial-flow-heading {{
        font-size: 7.8pt;
        margin-top: 6px;
    }}

    .editorial-flow-value {{
        font-size: 23pt;
        margin-top: 5px;
        margin-bottom: 2px;
    }}

    .editorial-flow-label {{
        font-size: 6.5pt;
        margin-bottom: 5px;
    }}

    .editorial-flow-record {{
        font-size: 7pt;
        margin-top: 5px;
    }}

    .progress-good,
    .progress-bad,
    .progress-empty {{
        height: 8px;
    }}

    table.data {{
        font-size: 7.3pt;
    }}

    table.data th {{
        padding-top: 5px;
        padding-bottom: 5px;
    }}

    table.data td {{
        padding-top: 5px;
        padding-bottom: 5px;
    }}

    .keyfacts {{
        font-size: 6.8pt;
        margin-bottom: 7px;
    }}

    .record-card-label {{
        font-size: 6.1pt;
    }}

    .record-card-value {{
        font-size: 15pt;
        margin-top: 3px;
        margin-bottom: 3px;
    }}

    .record-card-match {{
        font-size: 6pt;
    }}

    .record-cards td {{
        padding-top: 8px;
        padding-bottom: 8px;
    }}

    .small-note {{
        font-size: 6pt;
    }}


    /* ============================================================
       PDF V11 - STRUCTURAL REPORT LAYOUT
       ============================================================ */

    .v11-page {{
        width: 100%;
    }}

    /* More deliberate section rhythm */
    .v11-page .compact-section {{
        margin: 0 0 12px 0;
    }}

    .v11-page .compact-title {{
        margin: 0 0 6px 0;
        padding: 0 0 4px 0;
        border-bottom: 1px solid #d9dde2;
    }}

    .v11-page .compact-title h2 {{
        font-size: 12pt;
        margin: 0;
    }}

    /* ------------------------------------------------------------
       PAGE 1 - KPI / FORM
       ------------------------------------------------------------ */

    .v11-page .editorial-kpi-strip {{
        width: 100%;
        border-collapse: collapse;
        margin: 0 0 8px 0;
    }}

    .v11-page .editorial-kpi {{
        border: none;
        border-top: 2px solid #1f2328;
        padding: 7px 8px 6px 8px;
    }}

    .v11-page .editorial-kpi:first-child {{
        padding-left: 0;
    }}

    .v11-page .editorial-kpi:last-child {{
        padding-right: 0;
    }}

    .v11-page .editorial-kpi-label {{
        font-size: 6.1pt;
        color: #727982;
    }}

    .v11-page .editorial-kpi-value {{
        font-size: 18pt;
        margin-top: 3px;
    }}

    .v11-page .editorial-form-line {{
        width: 100%;
        border: none;
        border-bottom: 1px solid #e2e5e8;
        padding: 5px 0 8px 0;
        margin: 0 0 12px 0;
    }}

    .v11-page .editorial-inline-label {{
        width: 60px;
        font-size: 6.4pt;
    }}

    .v11-page .form-dot {{
        font-size: 16pt;
    }}

    .v11-page .form-dot-item {{
        margin-right: 12px;
    }}

    /* ------------------------------------------------------------
       PAGE 1 - real two-column analysis row
       ------------------------------------------------------------ */

    .v11-analysis-row {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 22px 0;
        margin: 0 0 12px 0;
    }}

    .v11-analysis-left,
    .v11-analysis-right {{
        vertical-align: top;
        padding: 0;
    }}

    .v11-analysis-left {{
        padding-right: 4px;
    }}

    .v11-analysis-right {{
        padding-left: 4px;
    }}

    .v11-analysis-row .compact-section {{
        margin-bottom: 0;
    }}

    /* Season comparison: one readable table */
    .v11-analysis-left .editorial-compare {{
        width: 100%;
        font-size: 7.5pt;
    }}

    .v11-analysis-left .editorial-compare th {{
        padding: 6px 5px;
    }}

    .v11-analysis-left .editorial-compare td {{
        padding: 7px 5px;
    }}

    /* Goal phases: make the chart area dominant */
    .v11-analysis-right .editorial-goal-bars {{
        width: 100%;
        font-size: 7.3pt;
    }}

    .v11-analysis-right .editorial-goal-bars th {{
        padding: 6px 4px;
    }}

    .v11-analysis-right .editorial-goal-bars td {{
        padding: 6px 4px;
    }}

    .v11-analysis-right .editorial-phase {{
        width: 11%;
    }}

    .v11-analysis-right .editorial-number {{
        width: 7%;
    }}

    .v11-analysis-right .editorial-bar-cell {{
        width: 37%;
    }}

    .v11-analysis-right .bar-track,
    .v11-analysis-right .bar-empty {{
        height: 9px;
        background: #eceff1;
    }}

    .v11-analysis-right .bar-fill-positive {{
        height: 9px;
        background: #2f9e44;
    }}

    .v11-analysis-right .bar-fill-negative {{
        height: 9px;
        background: #d94848;
    }}

    /* ------------------------------------------------------------
       PAGE 1 - match flow becomes a full-width closing section
       ------------------------------------------------------------ */

    .v11-flow-block {{
        width: 100%;
        margin-top: 2px;
    }}

    .v11-flow-block .compact-section {{
        margin-bottom: 0;
    }}

    .v11-flow-block .editorial-flow {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 26px 0;
    }}

    .v11-flow-block .editorial-flow-cell {{
        border-top: 2px solid #1f2328;
        padding: 7px 0 4px 0;
    }}

    .v11-flow-block .editorial-flow-heading {{
        font-size: 7.6pt;
        margin-top: 0;
    }}

    .v11-flow-block .editorial-flow-value {{
        font-size: 24pt;
        margin: 5px 0 1px 0;
    }}

    .v11-flow-block .editorial-flow-label {{
        font-size: 6.2pt;
        margin-bottom: 5px;
    }}

    .v11-flow-block .progress-track,
    .v11-flow-block .progress-empty {{
        height: 9px;
        background: #eceff1;
    }}

    .v11-flow-block .progress-good {{
        height: 9px;
        background: #2f9e44;
    }}

    .v11-flow-block .editorial-flow-record {{
        font-size: 6.8pt;
        margin-top: 5px;
    }}

    /* ------------------------------------------------------------
       PAGE 2 - true vertical report hierarchy
       ------------------------------------------------------------ */

    .v11-full-section {{
        width: 100%;
        margin: 0 0 13px 0;
    }}

    .v11-full-section .compact-section {{
        width: 100%;
        margin: 0;
    }}

    .v11-results {{
        margin-bottom: 14px;
    }}

    .v11-results table.data {{
        width: 100%;
        font-size: 7.1pt;
    }}

    .v11-results table.data th {{
        padding: 5px 7px;
    }}

    .v11-results table.data td {{
        padding: 5px 7px;
    }}

    /* Result KPI row: spread across the complete page */
    .v11-results .dashboard-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 8px 0;
        margin: 0 0 8px 0;
    }}

    .v11-results .dashboard-kpis td {{
        background: #ffffff;
        border: none;
        border-top: 2px solid #d8dde2;
        padding: 6px 7px 5px 7px;
    }}

    .v11-results .dashboard-kpis .kpi-label {{
        font-size: 5.8pt;
    }}

    .v11-results .dashboard-kpis .kpi-value {{
        font-size: 15pt;
    }}

    /* Players now use full width instead of the old left half */
    .v11-players {{
        margin-bottom: 13px;
    }}

    .v11-players table.data {{
        width: 100%;
        font-size: 7pt;
    }}

    .v11-players table.data th {{
        padding: 5px 7px;
    }}

    .v11-players table.data td {{
        padding: 5px 7px;
    }}

    .v11-players .keyfacts {{
        font-size: 6.7pt;
        margin-bottom: 6px;
    }}

    /* Records: one horizontal closing band */
    .v11-records {{
        margin-bottom: 0;
    }}

    .v11-records .record-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
    }}

    .v11-records .record-cards td {{
        background: #ffffff;
        border: none;
        border-top: 2px solid #d8dde2;
        padding: 8px 5px 6px 5px;
        vertical-align: top;
    }}

    .v11-records .record-card-label {{
        font-size: 5.9pt;
        color: #737b84;
    }}

    .v11-records .record-card-value {{
        font-size: 15pt;
        color: #17191b;
        margin: 3px 0;
    }}

    .v11-records .record-card-match {{
        font-size: 5.8pt;
        color: #777f88;
        line-height: 1.25;
    }}

    /* Keep semantic color restrained */
    .editorial-positive,
    .compare-positive,
    .status-positive {{
        color: #2f9e44;
    }}

    .editorial-neutral,
    .compare-neutral,
    .status-neutral {{
        color: #b47b00;
    }}

    .editorial-negative,
    .compare-negative,
    .status-negative {{
        color: #d94848;
    }}


    /* ============================================================
       PDF V13 - CLEAN TWO PAGE PAGINATION
       Keep V11 design. One explicit break only.
       ============================================================ */

    @page {{
        size: A4 landscape;
        margin: 9mm 10mm 9mm 10mm;
    }}

    /* No global "avoid" rules on large sections. */
    .report-page,
    .v11-full-section,
    .v11-results,
    .v11-players,
    .v11-records,
    .v11-flow-block {{
        
        
    }}

    /* Page 1 stays in normal document flow. */
    .page-one {{
        
        
    }}

    /* Page 2 must NOT create another forced page. */
    .page-two {{
        
        
        
        
    }}

    /* Tables may split only if absolutely necessary.
       Rows themselves stay intact. */
    table {{
        
        
    }}

    tr {{
        
        
    }}

    /* ---------------- PAGE 1 ---------------- */

    .page-one .report-header {{
        margin-bottom: 8px;
        padding-bottom: 7px;
    }}

    .page-one .compact-section {{
        margin-bottom: 9px;
    }}

    .page-one .editorial-kpi-strip {{
        margin-bottom: 6px;
    }}

    .page-one .editorial-kpi {{
        padding-top: 5px;
        padding-bottom: 4px;
    }}

    .page-one .editorial-kpi-value {{
        font-size: 16.5pt;
    }}

    .page-one .editorial-form-line {{
        padding-top: 4px;
        padding-bottom: 6px;
        margin-bottom: 8px;
    }}

    .page-one .v11-analysis-row {{
        border-spacing: 18px 0;
        margin-bottom: 8px;
    }}

    .page-one .editorial-compare th,
    .page-one .editorial-compare td,
    .page-one .editorial-goal-bars th,
    .page-one .editorial-goal-bars td {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .page-one .v11-flow-block .editorial-flow-cell {{
        padding-top: 5px;
        padding-bottom: 2px;
    }}

    .page-one .v11-flow-block .editorial-flow-value {{
        font-size: 21pt;
        margin-top: 3px;
    }}

    /* ---------------- PAGE 2 ---------------- */

    .page-two .page-header {{
        margin-bottom: 5px;
        padding-bottom: 4px;
    }}

    .page-two .compact-section {{
        margin-bottom: 6px;
    }}

    .page-two .compact-title {{
        margin-bottom: 3px;
        padding-bottom: 2px;
    }}

    .page-two .compact-title h2 {{
        font-size: 10.5pt;
    }}

    .page-two .v11-results {{
        margin-bottom: 7px;
    }}

    .page-two .v11-results .dashboard-kpis {{
        margin-bottom: 4px;
    }}

    .page-two .v11-results .dashboard-kpis td {{
        padding-top: 4px;
        padding-bottom: 3px;
    }}

    .page-two .v11-results .dashboard-kpis .kpi-value {{
        font-size: 12.5pt;
    }}

    .page-two .v11-results table.data {{
        font-size: 6.25pt;
    }}

    .page-two .v11-results table.data th,
    .page-two .v11-results table.data td {{
        padding-top: 2.6px;
        padding-bottom: 2.6px;
    }}

    .page-two .v11-players {{
        margin-bottom: 6px;
    }}

    .page-two .v11-players .keyfacts {{
        font-size: 5.8pt;
        margin-bottom: 3px;
    }}

    .page-two .v11-players table.data {{
        font-size: 5.9pt;
    }}

    .page-two .v11-players table.data th,
    .page-two .v11-players table.data td {{
        padding-top: 2.25px;
        padding-bottom: 2.25px;
    }}

    .page-two .small-note {{
        font-size: 5.1pt;
        margin-top: 2px;
    }}

    /* Records remain a horizontal closing strip,
       but are allowed to use the remaining page space. */
    .page-two .v11-records {{
        margin: 0;
    }}

    .page-two .v11-records .record-cards {{
        width: 100%;
        border-spacing: 8px 0;
    }}

    .page-two .v11-records .record-cards td {{
        padding-top: 5px;
        padding-bottom: 3px;
    }}

    .page-two .v11-records .record-card-label {{
        font-size: 5.2pt;
    }}

    .page-two .v11-records .record-card-value {{
        font-size: 12pt;
        margin-top: 1px;
        margin-bottom: 1px;
    }}

    .page-two .v11-records .record-card-match {{
        font-size: 4.9pt;
        line-height: 1.12;
    }}


    /* ============================================================
       PDF V14 - HARD TWO PAGE PAGINATION
       One page break only: after page one.
       No inner element is allowed to force a page break.
       ============================================================ */

    @page {{
        size: A4 landscape;
        margin: 9mm 10mm 9mm 10mm;
    }}

    html,
    body {{
        margin: 0;
        padding: 0;
    }}

    .report-page,
    .compact-section,
    .v11-analysis-row,
    .v11-flow-block,
    .v11-full-section,
    .v11-results,
    .v11-players,
    .v11-records,
    table,
    thead,
    tbody,
    tr,
    td,
    th,
    div {{
        page-break-inside: auto !important;
        break-inside: auto !important;
        page-break-before: auto !important;
        break-before: auto !important;
        page-break-after: auto !important;
        break-after: auto !important;
    }}

    /* Exactly one forced break between the two logical report pages. */
    .page-one {{
        page-break-after: always !important;
        break-after: page !important;
    }}

    .page-two {{
        page-break-before: auto !important;
        break-before: auto !important;
        page-break-after: auto !important;
        break-after: auto !important;
    }}

    /* Keep rows readable, but do not force the whole table away. */
    .page-one tr,
    .page-two tr {{
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }}

    /* Compact just enough to ensure page 1 fits as one page. */
    .page-one .report-header {{
        margin-bottom: 6px;
        padding-bottom: 5px;
    }}

    .page-one .compact-section {{
        margin-bottom: 7px;
    }}

    .page-one .compact-title {{
        margin-bottom: 3px;
        padding-bottom: 2px;
    }}

    .page-one .editorial-kpi-strip {{
        margin-bottom: 5px;
    }}

    .page-one .editorial-kpi {{
        padding-top: 4px;
        padding-bottom: 3px;
    }}

    .page-one .editorial-kpi-value {{
        font-size: 16pt;
    }}

    .page-one .editorial-form-line {{
        padding-top: 3px;
        padding-bottom: 4px;
        margin-bottom: 6px;
    }}

    .page-one .v11-analysis-row {{
        border-spacing: 16px 0;
        margin-bottom: 6px;
    }}

    .page-one .editorial-compare th,
    .page-one .editorial-compare td,
    .page-one .editorial-goal-bars th,
    .page-one .editorial-goal-bars td {{
        padding-top: 3px;
        padding-bottom: 3px;
    }}

    .page-one .v11-flow-block .editorial-flow-value {{
        font-size: 20pt;
        margin-top: 2px;
    }}

    .page-one .v11-flow-block .editorial-flow-label {{
        margin-bottom: 2px;
    }}

    .page-one .v11-flow-block .editorial-flow-record {{
        margin-top: 2px;
    }}

    /* Page 2 compact enough to keep results, players and records together. */
    .page-two .page-header {{
        margin-bottom: 4px;
        padding-bottom: 3px;
    }}

    .page-two .compact-section {{
        margin-bottom: 5px;
    }}

    .page-two .compact-title {{
        margin-bottom: 2px;
        padding-bottom: 2px;
    }}

    .page-two .v11-results {{
        margin-bottom: 5px;
    }}

    .page-two .v11-results .dashboard-kpis {{
        margin-bottom: 3px;
    }}

    .page-two .v11-results table.data {{
        font-size: 6.1pt;
    }}

    .page-two .v11-results table.data th,
    .page-two .v11-results table.data td {{
        padding-top: 2.2px;
        padding-bottom: 2.2px;
    }}

    .page-two .v11-players {{
        margin-bottom: 4px;
    }}

    .page-two .v11-players .keyfacts {{
        font-size: 5.7pt;
        margin-bottom: 2px;
    }}

    .page-two .v11-players table.data {{
        font-size: 5.7pt;
    }}

    .page-two .v11-players table.data th,
    .page-two .v11-players table.data td {{
        padding-top: 1.9px;
        padding-bottom: 1.9px;
    }}

    .page-two .small-note {{
        font-size: 5pt;
        margin-top: 1px;
    }}

    .page-two .v11-records .record-cards {{
        border-spacing: 6px 0;
    }}

    .page-two .v11-records .record-cards td {{
        padding-top: 4px;
        padding-bottom: 3px;
    }}

    .page-two .v11-records .record-card-value {{
        font-size: 11.5pt;
    }}

    .page-two .v11-records .record-card-match {{
        font-size: 4.8pt;
        line-height: 1.08;
    }}


    /* PDF V15 - clean records redesign */
    .record-facts-clean {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 0 0 7px 0;
    }}

    .record-fact {{
        background: #ffffff;
        border: none;
        border-top: 1px solid #d9dde2;
        padding: 5px 2px 4px 2px;
        vertical-align: top;
    }}

    .record-fact-label {{
        color: #737b84;
        font-size: 5.3pt;
        text-transform: uppercase;
        letter-spacing: 0.2px;
    }}

    .record-fact-value {{
        color: #17191b;
        font-size: 12.5pt;
        font-weight: bold;
        margin-top: 2px;
    }}

    .record-fact-positive .record-fact-value {{
        color: #2f9e44;
    }}

    .record-fact-negative .record-fact-value {{
        color: #d94848;
    }}

    .record-main-row {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
    }}

    .record-main {{
        background: #ffffff;
        border: none;
        border-top: 1px solid #d9dde2;
        padding: 6px 3px 4px 3px;
        vertical-align: top;
    }}

    .record-main-label {{
        color: #737b84;
        font-size: 5.5pt;
        text-transform: uppercase;
        letter-spacing: 0.2px;
    }}

    .record-main-value {{
        color: #17191b;
        font-size: 13pt;
        font-weight: bold;
        margin: 2px 0 2px 0;
    }}

    .record-main-positive .record-main-value {{
        color: #2f9e44;
    }}

    .record-main-negative .record-main-value {{
        color: #d94848;
    }}

    .record-main-meta {{
        color: #777f88;
        font-size: 4.9pt;
        margin-bottom: 1px;
    }}

    .record-main-match {{
        color: #5f666e;
        font-size: 5.1pt;
        line-height: 1.12;
    }}

    /* Old records styles no longer contribute visually. */
    .v11-records .record-cards,
    .v11-records .facts-grid,
    .v11-records .fact-grid {{
        display: none;
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
            custom_renderer = {
                "overview": self._render_overview_dashboard,
                "table_form": self._render_table_form_dashboard,
                "goals": self._render_goals_dashboard,
                "match_flow": self._render_match_flow_dashboard,
                "results": self._render_results_dashboard,
                "players": self._render_players_dashboard,
                "records": self._render_records_dashboard,
            }.get(
                section_key
            )

            if custom_renderer is not None:
                parts.append(
                    custom_renderer(
                        section_data
                    )
                )
            else:
                parts.append(
                    self._render_section_dict(
                        section_data,
                        section_key=section_key,
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
            custom_renderer = {
                "overview": self._render_overview_dashboard,
                "table_form": self._render_table_form_dashboard,
                "goals": self._render_goals_dashboard,
                "match_flow": self._render_match_flow_dashboard,
                "results": self._render_results_dashboard,
                "players": self._render_players_dashboard,
                "records": self._render_records_dashboard,
            }.get(
                section_key
            )

            if custom_renderer is not None:
                parts.append(
                    custom_renderer(
                        section_data
                    )
                )
            else:
                parts.append(
                    self._render_section_dict(
                        section_data,
                        section_key=section_key,
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



    def _render_overview_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )

        if not isinstance(
            facts,
            dict,
        ):
            facts = {}

        preferred = (
            "Tabellenplatz",
            "Punkte",
            "Tordifferenz",
            "Tore / Spiel",
            "Gegentore / Spiel",
        )

        items = []

        for label in preferred:
            if label not in facts:
                continue

            value = facts[label]
            status = self._fact_status_class(
                label,
                value,
            )

            cls = {
                "status-positive": "editorial-positive",
                "status-neutral": "editorial-neutral",
                "status-negative": "editorial-negative",
            }.get(
                status,
                "",
            )

            items.append(
                (
                    '<td width="20%" class="editorial-kpi">'
                    f'<div class="editorial-kpi-label">{escape(label)}</div>'
                    f'<div class="editorial-kpi-value {cls}">'
                    f"{escape(self._format_value(value))}"
                    "</div>"
                    "</td>"
                )
            )

        while len(items) < 5:
            items.append(
                '<td width="20%" class="editorial-kpi"></td>'
            )

        form_value = None

        for label, value in facts.items():
            if "form" in str(label).casefold():
                form_value = value
                break

        if form_value is None:
            form_value = section_data.get(
                "keyfacts"
            )

        form_html = self._render_form_from_value(
            form_value
        )

        return (
            '<table width="100%" class="editorial-kpi-strip">'
            "<tr>"
            + "".join(
                items[:5]
            )
            + "</tr></table>"
            '<div class="editorial-form-line">'
            '<span class="editorial-inline-label">FORM</span>'
            f"{form_html}"
            "</div>"
        )


    def _render_table_form_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        blocks = section_data.get(
            "blocks",
            [],
        )

        if not isinstance(
            blocks,
            list,
        ):
            return self._render_section_dict(
                section_data
            )

        named_blocks = {}

        for block in blocks:
            if not isinstance(
                block,
                dict,
            ):
                continue

            title = str(
                block.get(
                    "title",
                    "",
                )
            ).strip()

            if title:
                named_blocks[
                    title.casefold()
                ] = block

        home = self._find_block_by_title(
            named_blocks,
            "heim",
        )
        away = self._find_block_by_title(
            named_blocks,
            "auswärts",
            "auswaerts",
        )
        form = self._find_block_by_title(
            named_blocks,
            "form",
        )

        if home is None or away is None:
            return self._render_section_dict(
                section_data
            )

        def facts_of(block: Any) -> dict[str, Any]:
            if not isinstance(
                block,
                dict,
            ):
                return {}
            facts = block.get(
                "facts",
                {},
            )
            return (
                facts
                if isinstance(
                    facts,
                    dict,
                )
                else {}
            )

        home_facts = facts_of(home)
        away_facts = facts_of(away)
        form_facts = facts_of(form)

        rows = (
            (
                "Bilanz",
                self._bilanz_text(home_facts),
                self._bilanz_text(away_facts),
                self._bilanz_text(form_facts),
            ),
            (
                "Tore",
                self._goal_pair_text(home_facts),
                self._goal_pair_text(away_facts),
                self._goal_pair_text(form_facts),
            ),
            (
                "Punkte",
                self._dict_value(home_facts, "Punkte"),
                self._dict_value(away_facts, "Punkte"),
                self._dict_value(form_facts, "Punkte"),
            ),
            (
                "Pkt./Spiel",
                self._dict_value(home_facts, "Punkte / Spiel"),
                self._dict_value(away_facts, "Punkte / Spiel"),
                self._dict_value(form_facts, "Punkte / Spiel"),
            ),
            (
                "Tordiff.",
                self._dict_value(home_facts, "Tordifferenz"),
                self._dict_value(away_facts, "Tordifferenz"),
                self._dict_value(form_facts, "Tordifferenz"),
            ),
        )

        row_html = []

        for label, h, a, f in rows:
            row_html.append(
                (
                    "<tr>"
                    f"<td>{escape(label)}</td>"
                    f"<td>{escape(h)}</td>"
                    f"<td>{escape(a)}</td>"
                    f"<td>{escape(f)}</td>"
                    "</tr>"
                )
            )

        return (
            '<table width="100%" class="editorial-compare">'
            "<thead>"
            "<tr>"
            "<th></th>"
            "<th>Heim</th>"
            "<th>Auswärts</th>"
            "<th>Letzte 5</th>"
            "</tr>"
            "</thead>"
            "<tbody>"
            + "".join(row_html)
            + "</tbody>"
            "</table>"
        )


    def _render_goals_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        phase_table = self._find_goal_phase_table(
            section_data
        )

        if phase_table is None:
            return self._render_section_dict(
                section_data
            )

        headers = phase_table.get(
            "headers",
            [],
        )
        rows = phase_table.get(
            "rows",
            [],
        )

        parsed = []

        for row in rows:
            values = self._table_values(
                headers,
                row,
            )

            if len(values) < 3:
                continue

            parsed.append(
                (
                    str(values[0]),
                    self._to_number(values[1]),
                    self._to_number(values[2]),
                )
            )

        max_value = max(
            [
                max(goals, against)
                for _phase, goals, against in parsed
            ]
            or [1]
        )

        lines = []

        for phase, goals, against in parsed[:6]:
            goal_width = self._percent_width(
                goals,
                max_value,
            )
            against_width = self._percent_width(
                against,
                max_value,
            )

            lines.append(
                (
                    "<tr>"
                    f'<td class="editorial-phase">{escape(phase)}</td>'
                    f'<td class="editorial-number editorial-positive">{self._format_value(goals)}</td>'
                    '<td class="editorial-bar-cell">'
                    f"{self._bar_html(goal_width, 'positive')}"
                    "</td>"
                    f'<td class="editorial-number editorial-negative">{self._format_value(against)}</td>'
                    '<td class="editorial-bar-cell">'
                    f"{self._bar_html(against_width, 'negative')}"
                    "</td>"
                    "</tr>"
                )
            )

        return (
            '<table width="100%" class="editorial-goal-bars">'
            "<thead>"
            "<tr>"
            "<th>Minute</th>"
            "<th>Tore</th>"
            "<th></th>"
            "<th>GT</th>"
            "<th></th>"
            "</tr>"
            "</thead>"
            "<tbody>"
            + "".join(lines)
            + "</tbody>"
            "</table>"
        )


    def _render_match_flow_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        blocks = section_data.get(
            "blocks",
            [],
        )

        if not isinstance(
            blocks,
            list,
        ):
            return self._render_section_dict(
                section_data
            )

        lead = None
        deficit = None

        for block in blocks:
            if not isinstance(
                block,
                dict,
            ):
                continue

            title = str(
                block.get(
                    "title",
                    "",
                )
            ).casefold()

            if "führung" in title or "fuehrung" in title:
                lead = block
            elif (
                "gegentor" in title
                or "rückstand" in title
                or "rueckstand" in title
            ):
                deficit = block

        def flow_cell(
            block: dict[str, Any] | None,
            heading: str,
        ) -> str:
            if not isinstance(
                block,
                dict,
            ):
                return '<td width="50%"></td>'

            facts = block.get(
                "facts",
                {},
            )

            if not isinstance(
                facts,
                dict,
            ):
                facts = {}

            percentage = 0.0
            label = "Quote"

            for fact_label, value in facts.items():
                if "%" in str(fact_label):
                    percentage = self._to_number(
                        value
                    )
                    label = str(
                        fact_label
                    )
                    break

            wins = self._dict_value(
                facts,
                "Siege",
            )
            draws = self._dict_value(
                facts,
                "Remis",
            )
            losses = self._dict_value(
                facts,
                "Niederlagen",
            )

            return (
                '<td width="50%" class="editorial-flow-cell">'
                f'<div class="editorial-flow-heading">{escape(heading)}</div>'
                f'<div class="editorial-flow-value">{self._format_value(percentage)} %</div>'
                f'<div class="editorial-flow-label">{escape(label)}</div>'
                f"{self._progress_html(self._percent_width(percentage, 100.0), 'good')}"
                '<div class="editorial-flow-record">'
                f"{escape(wins)} S &nbsp;&nbsp; "
                f"{escape(draws)} U &nbsp;&nbsp; "
                f"{escape(losses)} N"
                "</div>"
                "</td>"
            )

        return (
            '<table width="100%" class="editorial-flow">'
            "<tr>"
            + flow_cell(
                lead,
                "Nach eigener Führung",
            )
            + flow_cell(
                deficit,
                "Nach erstem Gegentor",
            )
            + "</tr>"
            "</table>"
        )

    def _render_results_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        parts: list[str] = []

        facts = section_data.get(
            "facts",
            {},
        )

        if isinstance(
            facts,
            dict,
        ):
            labels = (
                "Siege",
                "Remis",
                "Niederlagen",
                "Siegquote %",
                "Tordifferenz",
            )

            cells = []

            for label in labels:
                if label not in facts:
                    continue

                value = facts[label]

                if "sieg" in label.casefold():
                    cls = "kpi-positive"
                elif (
                    "nieder" in label.casefold()
                ):
                    cls = "kpi-negative"
                elif "remis" in label.casefold():
                    cls = "kpi-neutral"
                elif "tordifferenz" in label.casefold():
                    number = self._to_number(
                        value
                    )
                    cls = (
                        "kpi-positive"
                        if number > 0
                        else (
                            "kpi-negative"
                            if number < 0
                            else "kpi-neutral"
                        )
                    )
                else:
                    cls = ""

                cells.append(
                    (
                        f'<td class="{cls}">'
                        '<div class="kpi-label">'
                        f"{escape(label)}"
                        "</div>"
                        '<div class="kpi-value">'
                        f"{escape(self._format_value(value))}"
                        "</div>"
                        "</td>"
                    )
                )

            if cells:
                while len(cells) < 5:
                    cells.append(
                        "<td></td>"
                    )

                parts.append(
                    '<table class="dashboard-kpis"><tr>'
                    + "".join(
                        cells[:5]
                    )
                    + "</tr></table>"
                )

        tables = section_data.get(
            "tables",
            [],
        )

        if isinstance(
            tables,
            list,
        ) and tables:
            parts.append(
                self._render_result_table(
                    tables[0]
                )
            )

        if not parts:
            return self._render_section_dict(
                section_data
            )

        return "".join(
            parts
        )

    def _render_players_dashboard(
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

        tables = section_data.get(
            "tables",
            [],
        )

        if (
            isinstance(
                tables,
                list,
            )
            and tables
        ):
            table = tables[0]

            if isinstance(
                table,
                dict,
            ):
                headers = list(
                    table.get(
                        "headers",
                        [],
                    )
                )

                rows = list(
                    table.get(
                        "rows",
                        [],
                    )
                )[:10]

                compact_table = dict(
                    table
                )
                compact_table[
                    "rows"
                ] = rows

                parts.append(
                    self._render_table(
                        compact_table
                    )
                )

                if len(
                    table.get(
                        "rows",
                        [],
                    )
                ) > 10:
                    parts.append(
                        '<div class="small-note">'
                        "Top 10 im Kurzreport · vollständige "
                        "Spielerliste bleibt in der Datenbank verfügbar."
                        "</div>"
                    )

        if not parts:
            return self._render_section_dict(
                section_data
            )

        return "".join(
            parts
        )


    def _render_records_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )

        tables = section_data.get(
            "tables",
            [],
        )

        fact_items: list[tuple[str, str]] = []

        if isinstance(
            facts,
            dict,
        ):
            for label, value in facts.items():
                fact_items.append(
                    (
                        str(label),
                        self._format_value(value),
                    )
                )

        record_items: list[dict[str, str]] = []

        if (
            isinstance(
                tables,
                list,
            )
            and tables
            and isinstance(
                tables[0],
                dict,
            )
        ):
            table = tables[0]
            headers = table.get(
                "headers",
                [],
            )
            rows = table.get(
                "rows",
                [],
            )

            for row in list(rows)[:3]:
                values = self._table_values(
                    headers,
                    row,
                )

                if not values:
                    continue

                record_items.append(
                    {
                        "label": (
                            str(values[0])
                            if len(values) > 0
                            else ""
                        ),
                        "matchday": (
                            str(values[1])
                            if len(values) > 1
                            else ""
                        ),
                        "date": (
                            self._format_value(values[2])
                            if len(values) > 2
                            else ""
                        ),
                        "match": (
                            str(values[3])
                            if len(values) > 3
                            else ""
                        ),
                        "result": (
                            str(values[4])
                            if len(values) > 4
                            else ""
                        ),
                        "value": (
                            str(values[5])
                            if len(values) > 5
                            else ""
                        ),
                    }
                )

        parts: list[str] = []

        if fact_items:
            fact_cells = []

            width = max(
                1,
                int(
                    100 / len(fact_items)
                ),
            )

            for label, value in fact_items:
                tone = "record-fact-neutral"
                label_cf = label.casefold()

                if (
                    "zu-null" in label_cf
                    or "zu null" in label_cf
                ):
                    tone = "record-fact-positive"
                elif (
                    "ohne eigenes tor" in label_cf
                    or "ohne tor" in label_cf
                ):
                    tone = "record-fact-negative"

                fact_cells.append(
                    (
                        f'<td width="{width}%" class="record-fact {tone}">'
                        f'<div class="record-fact-label">{escape(label)}</div>'
                        f'<div class="record-fact-value">{escape(value)}</div>'
                        "</td>"
                    )
                )

            parts.append(
                '<table width="100%" class="record-facts-clean">'
                "<tr>"
                + "".join(fact_cells)
                + "</tr></table>"
            )

        if record_items:
            record_cells = []

            for item in record_items:
                label_cf = item["label"].casefold()

                tone = "record-main-neutral"

                if "sieg" in label_cf:
                    tone = "record-main-positive"
                elif "niederlage" in label_cf:
                    tone = "record-main-negative"

                value_text = item["result"]

                if item["value"]:
                    value_text += (
                        " · "
                        + item["value"]
                    )

                detail_parts = []

                if item["matchday"]:
                    detail_parts.append(
                        f"ST {escape(item['matchday'])}"
                    )

                if item["date"]:
                    detail_parts.append(
                        escape(item["date"])
                    )

                detail_line = (
                    " · ".join(detail_parts)
                )

                record_cells.append(
                    (
                        '<td width="33%" '
                        f'class="record-main {tone}">'
                        '<div class="record-main-label">'
                        f"{escape(item['label'])}"
                        "</div>"
                        '<div class="record-main-value">'
                        f"{escape(value_text)}"
                        "</div>"
                        '<div class="record-main-meta">'
                        f"{detail_line}"
                        "</div>"
                        '<div class="record-main-match">'
                        f"{escape(item['match'])}"
                        "</div>"
                        "</td>"
                    )
                )

            while len(record_cells) < 3:
                record_cells.append(
                    '<td width="33%" class="record-main"></td>'
                )

            parts.append(
                '<table width="100%" class="record-main-row">'
                "<tr>"
                + "".join(record_cells[:3])
                + "</tr></table>"
            )

        if not parts:
            return (
                '<p class="muted">'
                "Keine Rekorddaten vorhanden."
                "</p>"
            )

        return "".join(parts)

    @staticmethod
    def _find_block_by_title(
        named_blocks: dict[str, dict[str, Any]],
        *needles: str,
    ) -> dict[str, Any] | None:
        for title, block in named_blocks.items():
            if any(
                needle.casefold() in title
                for needle in needles
            ):
                return block

        return None

    def _bilanz_text(
        self,
        facts: Any,
    ) -> str:
        if not isinstance(
            facts,
            dict,
        ):
            return "-"

        return (
            f"{self._dict_value(facts, 'Siege')}-"
            f"{self._dict_value(facts, 'Remis')}-"
            f"{self._dict_value(facts, 'Niederlagen')}"
        )

    def _goal_pair_text(
        self,
        facts: Any,
    ) -> str:
        if not isinstance(
            facts,
            dict,
        ):
            return "-"

        return (
            f"{self._dict_value(facts, 'Tore')}:"
            f"{self._dict_value(facts, 'Gegentore')}"
        )

    def _dict_value(
        self,
        data: Any,
        key: str,
    ) -> str:
        if not isinstance(
            data,
            dict,
        ):
            return "-"

        if key not in data:
            return "-"

        return self._format_value(
            data[key]
        )

    def _find_goal_phase_table(
        self,
        section_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        candidates = []

        tables = section_data.get(
            "tables",
            [],
        )

        if isinstance(
            tables,
            list,
        ):
            candidates.extend(
                table
                for table in tables
                if isinstance(
                    table,
                    dict,
                )
            )

        blocks = section_data.get(
            "blocks",
            [],
        )

        if isinstance(
            blocks,
            list,
        ):
            for block in blocks:
                if not isinstance(
                    block,
                    dict,
                ):
                    continue

                table = block.get(
                    "table"
                )

                if isinstance(
                    table,
                    dict,
                ):
                    candidates.append(
                        table
                    )

        for table in candidates:
            headers_cf = [
                str(header).casefold()
                for header in table.get(
                    "headers",
                    [],
                )
            ]

            if (
                any(
                    "minute" in header
                    for header in headers_cf
                )
                and any(
                    header == "tore"
                    for header in headers_cf
                )
                and any(
                    "gegentor" in header
                    for header in headers_cf
                )
            ):
                return table

        return None

    @staticmethod
    def _table_values(
        headers: list[Any],
        row: Any,
    ) -> list[Any]:
        if isinstance(
            row,
            dict,
        ):
            return [
                row.get(
                    header,
                    "",
                )
                for header in headers
            ]

        try:
            return list(
                row
            )
        except TypeError:
            return []

    @staticmethod
    def _to_number(
        value: Any,
    ) -> float:
        if isinstance(
            value,
            bool,
        ):
            return float(
                int(
                    value
                )
            )

        if isinstance(
            value,
            (int, float),
        ):
            return float(
                value
            )

        text = str(
            value
            or ""
        ).strip()

        text = text.replace(
            "%",
            "",
        ).replace(
            ",",
            ".",
        )

        match = re.search(
            r"[-+]?\d+(?:\.\d+)?",
            text,
        )

        if not match:
            return 0.0

        try:
            return float(
                match.group(0)
            )
        except ValueError:
            return 0.0

    @staticmethod
    def _percent_width(
        value: float,
        maximum: float,
    ) -> int:
        if maximum <= 0:
            return 0

        return max(
            0,
            min(
                100,
                int(
                    round(
                        value
                        / maximum
                        * 100
                    )
                ),
            ),
        )

    @staticmethod
    def _bar_html(
        width: int,
        kind: str,
    ) -> str:
        filled = max(
            0,
            min(
                100,
                int(
                    width
                ),
            ),
        )
        empty = 100 - filled

        fill_class = (
            "bar-fill-positive"
            if kind == "positive"
            else "bar-fill-negative"
        )

        return (
            '<table class="bar-track"><tr>'
            f'<td class="{fill_class}" width="{filled}%"></td>'
            f'<td class="bar-empty" width="{empty}%"></td>'
            "</tr></table>"
        )

    def _render_flow_card(
        self,
        block: dict[str, Any],
        positive: bool,
    ) -> str:
        title = str(
            block.get(
                "title",
                "",
            )
        )

        facts = block.get(
            "facts",
            {},
        )

        if not isinstance(
            facts,
            dict,
        ):
            facts = {}

        percentage_label = None
        percentage_value = 0.0

        for label, value in facts.items():
            if "%" in str(label):
                percentage_label = str(
                    label
                )
                percentage_value = self._to_number(
                    value
                )
                break

        wins = self._dict_value(
            facts,
            "Siege",
        )
        draws = self._dict_value(
            facts,
            "Remis",
        )
        losses = self._dict_value(
            facts,
            "Niederlagen",
        )

        if percentage_label is None:
            percentage_label = (
                "Erfolgsquote"
            )

        width = self._percent_width(
            percentage_value,
            100.0,
        )

        progress_kind = (
            "good"
            if positive
            else "good"
        )

        return (
            '<td width="50%" class="flow-card '
            + (
                "flow-positive"
                if positive
                else "flow-negative"
            )
            + '">'
            '<div class="flow-card-title">'
            f"{escape(title)}"
            "</div>"
            '<div class="flow-main">'
            f"{escape(self._format_value(percentage_value))} %"
            "</div>"
            '<div class="flow-detail">'
            f"{escape(percentage_label)}"
            "</div>"
            f"{self._progress_html(width, progress_kind)}"
            '<div class="flow-detail">'
            '<span class="compare-positive">'
            f"{escape(wins)} S"
            "</span>"
            " · "
            '<span class="compare-neutral">'
            f"{escape(draws)} U"
            "</span>"
            " · "
            '<span class="compare-negative">'
            f"{escape(losses)} N"
            "</span>"
            "</div>"
            "</td>"
        )

    @staticmethod
    def _progress_html(
        width: int,
        kind: str,
    ) -> str:
        filled = max(
            0,
            min(
                100,
                int(
                    width
                ),
            ),
        )
        empty = 100 - filled

        fill_class = (
            "progress-good"
            if kind == "good"
            else "progress-bad"
        )

        return (
            '<table class="progress-track"><tr>'
            f'<td class="{fill_class}" width="{filled}%"></td>'
            f'<td class="progress-empty" width="{empty}%"></td>'
            "</tr></table>"
        )


    def _render_result_table(
        self,
        table: Any,
    ) -> str:
        if not isinstance(
            table,
            dict,
        ):
            return ""

        headers = list(
            table.get(
                "headers",
                [],
            )
        )
        rows = list(
            table.get(
                "rows",
                [],
            )
        )

        if not headers:
            return ""

        header_html = "".join(
            f"<th>{escape(str(header))}</th>"
            for header in headers
        )

        result_index = None

        for index, header in enumerate(
            headers
        ):
            header_cf = str(
                header
            ).casefold()

            if (
                "w/u/n" in header_cf
                or header_cf in {
                    "form",
                    "status",
                }
            ):
                result_index = index

        color_map = {
            "S": "#2f9e44",
            "U": "#d99a00",
            "N": "#d94848",
        }

        row_html = []

        for row in rows:
            values = self._table_values(
                headers,
                row,
            )

            cells = []

            for index, value in enumerate(
                values
            ):
                if (
                    result_index is not None
                    and index == result_index
                ):
                    token = str(
                        value
                    ).strip().upper()

                    color = color_map.get(
                        token,
                        "#6b7280",
                    )

                    cells.append(
                        (
                            '<td class="result-status-cell">'
                            '<span class="result-dot" '
                            f'style="color:{color};">●</span>'
                            f'<span class="result-letter">{escape(token)}</span>'
                            "</td>"
                        )
                    )
                else:
                    cells.append(
                        "<td>"
                        f"{escape(self._format_value(value))}"
                        "</td>"
                    )

            row_html.append(
                "<tr>"
                + "".join(
                    cells
                )
                + "</tr>"
            )

        return (
            '<table width="100%" class="data airy-table">'
            f"<thead><tr>{header_html}</tr></thead>"
            "<tbody>"
            + "".join(
                row_html
            )
            + "</tbody></table>"
        )

    def _render_section_dict(
        self,
        section_data: dict[str, Any],
        section_key: str | None = None,
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

            if section_key == "table_form":
                form_html = self._render_form_from_value(
                    keyfacts
                )
                if form_html:
                    parts.append(form_html)

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
            status_class = self._fact_status_class(
                label,
                value,
            )
            value_html = self._render_value_html(
                label,
                value,
            )
            cells.append(
                (
                    f'<td class="{status_class}">'
                    '<div class="fact-label">'
                    f"{escape(str(label))}"
                    "</div>"
                    '<div class="fact-value">'
                    f"{value_html}"
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

            row_class = self._table_row_status_class(
                headers,
                values,
            )
            row_html.append(
                f'<tr class="{row_class}">{cells}</tr>'
            )

        return (
            '<table width="100%" class="data">'
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

    def _render_value_html(
        self,
        label: Any,
        value: Any,
    ) -> str:
        label_text = str(label).casefold()

        if "form" in label_text:
            form_html = self._render_form_from_value(value)
            if form_html:
                return form_html

        return escape(
            self._format_value(value)
        )


    def _render_form_from_value(
        self,
        value: Any,
    ) -> str:
        raw = ""

        if isinstance(
            value,
            str,
        ):
            raw = value
        elif isinstance(
            value,
            list,
        ):
            raw = " ".join(
                str(item)
                for item in value
            )
        elif value is not None:
            raw = str(
                value
            )

        tokens = re.findall(
            r"[SUN]",
            raw.upper(),
        )

        if len(tokens) < 2:
            return ""

        tokens = tokens[-5:]

        color_map = {
            "S": "#2f9e44",
            "U": "#d99a00",
            "N": "#d94848",
        }

        items = []

        for token in tokens:
            color = color_map[
                token
            ]

            items.append(
                (
                    '<span class="form-dot-item">'
                    '<span class="form-dot" '
                    f'style="color:{color};">●</span>'
                    '<span class="form-dot-letter">'
                    f"{token}"
                    "</span>"
                    "</span>"
                )
            )

        return (
            '<div class="form-dots">'
            + "".join(
                items
            )
            + "</div>"
        )

    @staticmethod
    def _fact_status_class(
        label: Any,
        value: Any,
    ) -> str:
        text = str(label).casefold()

        positive_terms = (
            "sieg", "punkte", "tore erzielt", "tordifferenz",
            "clean sheet", "zu null", "gehalten", "gerettet",
            "comeback", "best", "höchster sieg",
        )
        neutral_terms = (
            "remis", "unentschieden", "durchschnitt", "spiele",
            "einsätze", "minuten", "platz",
        )
        negative_terms = (
            "niederlage", "gegentor", "kassiert", "verloren",
            "rückstand", "schlech", "höchste niederlage",
        )

        if "tordifferenz" in text:
            number = TeamStatisticsPdfExporter._to_number(
                value
            )
            if number > 0:
                return "status-positive"
            if number < 0:
                return "status-negative"
            return "status-neutral"

        if any(term in text for term in negative_terms):
            return "status-negative"
        if any(term in text for term in positive_terms):
            return "status-positive"
        if any(term in text for term in neutral_terms):
            return "status-neutral"

        return ""

    @staticmethod
    def _table_row_status_class(
        headers: list[Any],
        values: list[Any],
    ) -> str:
        combined = " | ".join(
            str(value) for value in values
        ).casefold()

        # Explicit result/status values first.
        if re.search(r"(^|[ |])s(ieg)?($|[ |])", combined):
            return "row-positive"
        if re.search(r"(^|[ |])u(nentschieden)?($|[ |])", combined):
            return "row-neutral"
        if re.search(r"(^|[ |])n(iederlage)?($|[ |])", combined):
            return "row-negative"

        return ""

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
