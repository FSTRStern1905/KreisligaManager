from __future__ import annotations

from datetime import datetime
import re
from html import escape
from pathlib import Path
from typing import Any

from PySide6.QtCore import QMarginsF, QPointF, QRectF, QUrl
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
    QPen,
    QTextDocument,
)
from PySide6.QtPrintSupport import QPrinter


class TeamStatisticsPdfExporter:
    SECTION_TITLES = {
        "overview": "Übersicht",
        "table_form": "Tabelle & Form",
        "results": "Ergebnisse",
        "goals": "Tore & Torphasen",
        "match_flow": "Spielverlauf",
        "patterns": "Spielmuster & Effizienz",
        "control": "Punkteverluste & Spielkontrolle",
        "halftime_phases": "Halbzeiten & Spielphasen",
        "consistency": "Konstanz & Volatilität",
        "attack_defense": "Offensiv- & Defensivprofil",
        "strengths_weaknesses": "Stärken & Schwächen",
        "season_progress": "Saisonverlauf",
        "players": "Spieler",
        "discipline": "Karten & Fairplay",
        "streaks": "Serien",
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

        self._image_resources: dict[str, QImage] = {}

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

        for resource_name, image in (
            self._image_resources.items()
        ):
            document.addResource(
                QTextDocument.ResourceType.ImageResource,
                QUrl(resource_name),
                image,
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

        report_type = str(
            report_data.get(
                "report_type",
                "short",
            )
        )

        if report_type == "full":
            body_parts = self._build_full_report_body(
                team_name=team_name,
                competition_name=competition_name,
                season_name=season_name,
                generated_text=generated_text,
                sections=sections,
                selected=selected,
            )
        else:
            body_parts = None

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

        if body_parts is None:
            body_parts = [
                self._render_report_header(
                    team_name=team_name,
                    competition_name=competition_name,
                    season_name=season_name,
                    generated_text=generated_text,
                )
            ]

        if report_type != "full" and page_1:
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

        if report_type != "full" and page_2:
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

    .full-report-label {{
        color: #68717b;
        font-size: 7pt;
        font-weight: bold;
        letter-spacing: 0.8px;
        margin: -5px 0 10px 0;
    }}

    .full-report-page {{
        width: 100%;
    }}

    .full-report-page-break {{
        page-break-before: always;
    }}

    .full-page-kicker {{
        color: #7a8189;
        font-size: 6pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }}

    .full-page-title {{
        color: #17191b;
        font-size: 16pt;
        font-weight: bold;
        margin-bottom: 7px;
    }}

    .full-section {{
        margin-bottom: 8px;
    }}

    .section-season_progress,
    .section-goals,
    .section-match_flow,
    .section-players {{
        page-break-inside: avoid;
    }}

    .editorial-flow,
    .editorial-flow tr,
    .editorial-flow td,
    .editorial-flow-cell {{
        page-break-inside: avoid;
    }}

    .full-chart-title {{
        color: #40464d;
        font-size: 8pt;
        font-weight: bold;
        margin: 0;
    }}

    .full-chart-card {{
        width: 100%;
        border: 1px solid #dfe3e7;
        padding: 5px 9px 4px 9px;
        margin: 3px 0 5px 0;
        page-break-inside: avoid;
        background: #ffffff;
    }}

    .full-chart-heading-row {{
        width: 100%;
        margin-bottom: 4px;
    }}

    .full-chart-trend {{
        font-size: 6pt;
        margin-top: 2px;
        margin-bottom: 5px;
    }}

    .full-chart-image {{
        width: 100%;
        text-align: center;
    }}

    .full-chart-image img {{
        max-width: 100%;
    }}

    .chart-trend-positive {{
        color: #2f9e44;
    }}

    .chart-trend-neutral {{
        color: #b47b00;
    }}

    .chart-trend-negative {{
        color: #d94848;
    }}

    .full-progress-table,
    .full-position-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 6.7pt;
        margin-bottom: 12px;
    }}

    .full-progress-table th,
    .full-position-table th {{
        text-align: left;
        color: #68717b;
        border-bottom: 1px solid #d9dde2;
        padding: 5px 6px;
    }}

    .full-progress-table td,
    .full-position-table td {{
        color: #202326;
        border-bottom: 1px solid #edf0f2;
        padding: 5px 6px;
    }}

    .full-progress-table td:nth-child(1),
    .full-progress-table td:nth-child(2),
    .full-progress-table td:nth-child(4) {{
        width: 9%;
    }}

    .full-progress-track {{
        width: 100%;
        height: 7px;
        background: #edf0f2;
    }}

    .full-progress-fill {{
        height: 7px;
        background: #2f6fa3;
    }}

    .full-position-table th,
    .full-position-table td {{
        width: 50%;
    }}

    .appendix-label {{
        color: #2f6fa3;
        font-size: 6pt;
        font-weight: bold;
        letter-spacing: 0.7px;
        text-transform: uppercase;
        margin: 0 0 3px 0;
    }}

    .appendix-title {{
        margin-bottom: 5px;
    }}

    .appendix-note {{
        background: #f7f8f9;
        border-left: 3px solid #cfd4d9;
        color: #737b84;
        padding: 6px 9px;
        margin: 0 0 8px 0;
        font-size: 5.7pt;
        line-height: 1.25;
    }}

    .appendix-table {{
        margin-top: 3px;
    }}

    .appendix-table table.data {{
        width: 100%;
        border-collapse: collapse;
        font-size: 6.15pt;
        margin: 0;
    }}

    .appendix-table table.data th {{
        background: #eef1f4;
        color: #3f464d;
        border: none;
        border-bottom: 1px solid #cfd4d9;
        padding: 4px 5px;
        font-size: 5.8pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.15px;
    }}

    .appendix-table table.data td {{
        background: #ffffff;
        color: #202326;
        border: none;
        border-bottom: 1px solid #eceff1;
        padding: 3.2px 5px;
        line-height: 1.08;
        vertical-align: middle;
    }}

    .appendix-table table.data tr:nth-child(even) td {{
        background: #fafbfc;
    }}

    .appendix-table .keyfacts {{
        background: #f7f8f9;
        border-left: 3px solid #cfd4d9;
        color: #59616a;
        padding: 5px 8px;
        margin: 0 0 7px 0;
        font-size: 5.8pt;
    }}

    .appendix-results table.data th:nth-child(1),
    .appendix-results table.data td:nth-child(1) {{
        width: 5%;
        text-align: center;
    }}

    .appendix-results table.data th:nth-child(2),
    .appendix-results table.data td:nth-child(2) {{
        width: 11%;
        white-space: nowrap;
    }}

    .appendix-results table.data th:nth-child(3),
    .appendix-results table.data td:nth-child(3) {{
        width: 60%;
    }}

    .appendix-results table.data th:nth-child(4),
    .appendix-results table.data td:nth-child(4) {{
        width: 12%;
        text-align: center;
        font-weight: bold;
        white-space: nowrap;
    }}

    .appendix-results table.data th:nth-child(5),
    .appendix-results table.data td:nth-child(5) {{
        width: 12%;
        text-align: center;
        white-space: nowrap;
    }}

    .appendix-results .result-dot {{
        font-size: 9pt;
        vertical-align: middle;
    }}

    .appendix-results .result-letter {{
        color: #4f565e;
        font-size: 5.8pt;
        font-weight: bold;
        margin-left: 2px;
    }}

    .appendix-cards table.data th:first-child,
    .appendix-cards table.data td:first-child {{
        width: 70%;
    }}

    .appendix-cards table.data th:not(:first-child),
    .appendix-cards table.data td:not(:first-child) {{
        width: 10%;
        text-align: center;
    }}

    .appendix-players table.data {{
        font-size: 5.75pt;
    }}

    .appendix-players table.data th,
    .appendix-players table.data td {{
        padding: 2.8px 4px;
    }}

    .appendix-players table.data th:first-child,
    .appendix-players table.data td:first-child {{
        width: 31%;
    }}

    .appendix-players table.data th:nth-child(2),
    .appendix-players table.data td:nth-child(2) {{
        width: 9%;
    }}

    .appendix-players table.data th:nth-child(n+3),
    .appendix-players table.data td:nth-child(n+3) {{
        text-align: center;
    }}

    .executive-intro {{
        border-left: 4px solid #2f6fa3;
        background: #f7f8f9;
        padding: 8px 12px;
        margin: 0 0 10px 0;
    }}

    .executive-intro-title {{
        color: #17191b;
        font-size: 9pt;
        font-weight: bold;
    }}

    .executive-intro-text {{
        color: #777f88;
        font-size: 5.8pt;
        margin-top: 2px;
    }}

    .executive-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin-bottom: 7px;
    }}

    .executive-kpis td {{
        width: 20%;
        border-top: 2px solid #202326;
        padding: 7px 3px 5px 3px;
        vertical-align: top;
    }}

    .executive-kpi-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .executive-kpi-value {{
        color: #17191b;
        font-size: 16pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .executive-positive {{ color: #2f9e44; }}
    .executive-negative {{ color: #d94848; }}
    .executive-neutral {{ color: #17191b; }}

    .executive-form {{
        margin: 1px 0 9px 0;
    }}

    .executive-form-label {{
        color: #777f88;
        font-size: 5.6pt;
        font-weight: bold;
        margin-right: 8px;
    }}

    .executive-venue {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
        margin: 0 0 10px 0;
    }}

    .executive-venue td {{
        border: 1px solid #dfe3e7;
        padding: 9px 12px;
        vertical-align: top;
    }}

    .executive-venue-title {{
        color: #777f88;
        font-size: 5.8pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .executive-venue-balance {{
        color: #17191b;
        font-size: 13pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .executive-venue-goals,
    .executive-venue-meta {{
        color: #69717a;
        font-size: 5.8pt;
        margin-top: 2px;
    }}

    .executive-bar-track {{
        width: 100%;
        height: 7px;
        background: #eef0f2;
        margin: 7px 0 4px 0;
    }}

    .executive-bar-fill {{
        height: 7px;
    }}

    .executive-home {{
        background: #2f6fa3;
    }}

    .executive-away {{
        background: #6f42c1;
    }}

    .executive-insights-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        margin: 5px 0 5px 0;
    }}

    .executive-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .executive-insights td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 9px 10px;
        vertical-align: top;
    }}

    .executive-insight-title {{
        color: #17191b;
        font-size: 8pt;
        font-weight: bold;
        margin-bottom: 3px;
    }}

    .executive-insight-text {{
        color: #69717a;
        font-size: 5.8pt;
        line-height: 1.3;
    }}

    .section-overview,
    .section-table_form {{
        page-break-inside: avoid;
    }}

    .fairplay-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 14px 0;
    }}

    .fairplay-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .fairplay-label,
    .fairplay-insight-label,
    .record-summary-label,
    .streak-current-label,
    .streak-card-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .fairplay-value {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .fairplay-yellow {{ color: #c99a00; }}
    .fairplay-orange {{ color: #e67e22; }}
    .fairplay-red {{ color: #d94848; }}

    .fairplay-chart-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 10px 12px 8px 12px;
        margin: 6px 0 13px 0;
        page-break-inside: avoid;
        text-align: center;
    }}

    .fairplay-chart-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .fairplay-chart-note,
    .fairplay-footer,
    .fairplay-insight-text {{
        color: #858c94;
        font-size: 5.8pt;
        line-height: 1.3;
    }}

    .fairplay-chart-note {{
        margin: 2px 0 5px 0;
        text-align: left;
    }}

    .fairplay-insight-row {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
    }}

    .fairplay-insight-row td {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 10px 12px;
        vertical-align: top;
    }}

    .fairplay-insight-value {{
        color: #17191b;
        font-size: 11pt;
        font-weight: bold;
        margin-top: 4px;
    }}

    .fairplay-footer {{
        margin-top: 7px;
    }}

    .streak-current {{
        border-left: 4px solid #2f6fa3;
        background: #f7f8f9;
        padding: 10px 13px;
        margin: 2px 0 14px 0;
    }}

    .streak-current-value {{
        color: #17191b;
        font-size: 16pt;
        font-weight: bold;
        margin-top: 4px;
    }}

    .streak-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 9px 0;
        margin-bottom: 18px;
    }}

    .streak-cards td {{
        width: 20%;
        border: 1px solid #dfe3e7;
        padding: 10px 10px 9px 10px;
        vertical-align: top;
    }}

    .streak-card-value {{
        font-size: 17pt;
        font-weight: bold;
        margin: 5px 0 6px 0;
    }}

    .streak-track {{
        width: 100%;
        background: #eef0f2;
        height: 7px;
    }}

    .streak-fill {{
        height: 7px;
    }}

    .streak-card-sub,
    .record-summary-sub,
    .full-record-match {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 4px;
        line-height: 1.25;
    }}

    .record-summary {{
        width: 48%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 0 0 15px 0;
    }}

    .record-summary td {{
        width: 50%;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .record-summary-value {{
        color: #17191b;
        font-size: 16pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .full-record-cards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
    }}

    .full-record-cards td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 13px 14px;
        vertical-align: top;
    }}

    .full-record-label {{
        color: #737b84;
        font-size: 6pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .full-record-result {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 6px;
    }}

    .full-record-value {{
        color: #5e656d;
        font-size: 7pt;
        font-weight: bold;
        margin: 2px 0 7px 0;
    }}

    .section-discipline,
    .section-streaks,
    .section-records {{
        page-break-inside: avoid;
    }}

    .sw-intro {{
        color: #69717a;
        font-size: 6pt;
        line-height: 1.3;
        margin: 2px 0 10px 0;
    }}

    .sw-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .sw-column {{
        width: 33%;
        vertical-align: top;
    }}

    .sw-section-title {{
        font-size: 9pt;
        font-weight: bold;
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 2px solid #dfe3e7;
    }}

    .sw-positive-title {{
        color: #2f9e44;
    }}

    .sw-negative-title {{
        color: #d94848;
    }}

    .sw-neutral-title {{
        color: #2f6fa3;
    }}

    .sw-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 8px 9px;
        margin-bottom: 8px;
        page-break-inside: avoid;
    }}

    .sw-positive {{
        border-top: 3px solid #2f9e44;
    }}

    .sw-negative {{
        border-top: 3px solid #d94848;
    }}

    .sw-neutral {{
        border-top: 3px solid #2f6fa3;
    }}

    .sw-card-top {{
        margin-bottom: 4px;
    }}

    .sw-rank {{
        display: inline-block;
        min-width: 14px;
        font-size: 6pt;
        font-weight: bold;
        color: #ffffff;
        background: #25282c;
        padding: 1px 4px;
        margin-right: 5px;
    }}

    .sw-title {{
        color: #17191b;
        font-size: 7.4pt;
        font-weight: bold;
    }}

    .sw-metric {{
        float: right;
        color: #25282c;
        font-size: 7.2pt;
        font-weight: bold;
    }}

    .sw-text {{
        color: #69717a;
        font-size: 5.6pt;
        line-height: 1.28;
        margin-top: 4px;
    }}

    .sw-source {{
        color: #9aa1a8;
        font-size: 5pt;
        margin-top: 5px;
        text-transform: uppercase;
    }}

    .sw-footer-note {{
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid #e5e8eb;
        color: #858c94;
        font-size: 5.4pt;
        line-height: 1.25;
    }}

    .section-strengths_weaknesses {{
        page-break-inside: avoid;
    }}

    .attack-defense-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 12px 0;
    }}

    .attack-defense-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .attack-defense-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .attack-defense-value {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .attack-defense-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .attack-defense-chart-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 8px 10px 6px 10px;
        margin: 5px 0 8px 0;
        text-align: center;
        page-break-inside: avoid;
    }}

    .attack-defense-chart-title,
    .attack-defense-insights-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .attack-defense-chart-note {{
        color: #858c94;
        font-size: 5.7pt;
        margin: 2px 0 4px 0;
        text-align: left;
    }}

    .attack-defense-insights-title {{
        margin: 5px 0 4px 0;
    }}

    .attack-defense-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .attack-defense-insights td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 7px 9px;
        vertical-align: top;
    }}

    .attack-defense-insight-title {{
        color: #17191b;
        font-size: 7.4pt;
        font-weight: bold;
        margin-bottom: 3px;
    }}

    .attack-defense-insight-text {{
        color: #69717a;
        font-size: 5.5pt;
        line-height: 1.25;
    }}

    .section-attack_defense {{
        page-break-inside: avoid;
    }}

    .consistency-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 12px 0;
    }}

    .consistency-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .consistency-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .consistency-value {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .consistency-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .consistency-chart-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 8px 10px 6px 10px;
        margin: 5px 0 8px 0;
        text-align: center;
        page-break-inside: avoid;
    }}

    .consistency-chart-title,
    .consistency-insights-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .consistency-chart-note {{
        color: #858c94;
        font-size: 5.7pt;
        margin: 2px 0 4px 0;
        text-align: left;
    }}

    .consistency-insights-title {{
        margin: 5px 0 4px 0;
    }}

    .consistency-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .consistency-insights td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 7px 9px;
        vertical-align: top;
    }}

    .consistency-insight-title {{
        color: #17191b;
        font-size: 7.4pt;
        font-weight: bold;
        margin-bottom: 3px;
    }}

    .consistency-insight-text {{
        color: #69717a;
        font-size: 5.5pt;
        line-height: 1.25;
    }}

    .section-consistency {{
        page-break-inside: avoid;
    }}

    .halftime-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 12px 0;
    }}

    .halftime-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .halftime-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .halftime-value {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .halftime-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .halftime-chart-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 8px 10px 6px 10px;
        margin: 5px 0 8px 0;
        text-align: center;
        page-break-inside: avoid;
    }}

    .halftime-chart-title,
    .halftime-insights-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .halftime-chart-note {{
        color: #858c94;
        font-size: 5.7pt;
        margin: 2px 0 4px 0;
        text-align: left;
    }}

    .halftime-insights-title {{
        margin: 5px 0 4px 0;
    }}

    .halftime-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .halftime-insights td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 7px 9px;
        vertical-align: top;
    }}

    .halftime-insight-title {{
        color: #17191b;
        font-size: 7.4pt;
        font-weight: bold;
        margin-bottom: 3px;
    }}

    .halftime-insight-text {{
        color: #69717a;
        font-size: 5.5pt;
        line-height: 1.25;
    }}

    .halftime-footnote {{
        color: #858c94;
        font-size: 5.4pt;
        margin-top: 5px;
        text-align: right;
    }}

    .section-halftime_phases {{
        page-break-inside: avoid;
    }}

    .control-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 12px 0;
    }}

    .control-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .control-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .control-value {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .control-positive {{ color: #2f9e44; }}
    .control-negative {{ color: #d94848; }}

    .control-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .control-chart-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 8px 10px 6px 10px;
        margin: 5px 0 9px 0;
        text-align: center;
        page-break-inside: avoid;
    }}

    .control-chart-title,
    .control-insights-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .control-chart-note {{
        color: #858c94;
        font-size: 5.7pt;
        margin: 2px 0 4px 0;
        text-align: left;
    }}

    .control-insights-title {{
        margin: 6px 0 5px 0;
    }}

    .control-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .control-insights td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 8px 10px;
        vertical-align: top;
    }}

    .control-insight-title {{
        color: #17191b;
        font-size: 7.6pt;
        font-weight: bold;
        margin-bottom: 3px;
    }}

    .control-insight-text {{
        color: #69717a;
        font-size: 5.7pt;
        line-height: 1.28;
    }}

    .section-control {{
        page-break-inside: avoid;
    }}

    .patterns-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 12px 0;
    }}

    .patterns-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .patterns-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .patterns-value {{
        color: #17191b;
        font-size: 15pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .patterns-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .patterns-chart-card {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 8px 10px 6px 10px;
        margin: 5px 0 9px 0;
        text-align: center;
        page-break-inside: avoid;
    }}

    .patterns-chart-title,
    .patterns-score-title,
    .patterns-insights-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .patterns-chart-note {{
        color: #858c94;
        font-size: 5.7pt;
        margin: 2px 0 4px 0;
        text-align: left;
    }}

    .patterns-score-title,
    .patterns-insights-title {{
        margin: 6px 0 5px 0;
    }}

    .patterns-scorecards {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 9px 0;
        margin-bottom: 8px;
    }}

    .patterns-scorecards td {{
        width: 20%;
        border: 1px solid #dfe3e7;
        padding: 7px 8px;
        text-align: center;
        vertical-align: top;
    }}

    .patterns-scoreline {{
        color: #17191b;
        font-size: 13pt;
        font-weight: bold;
    }}

    .patterns-scoreline-count {{
        color: #2f6fa3;
        font-size: 7pt;
        font-weight: bold;
        margin-top: 2px;
    }}

    .patterns-scoreline-share {{
        color: #858c94;
        font-size: 5.5pt;
        margin-top: 1px;
    }}

    .patterns-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .patterns-insights td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 8px 10px;
        vertical-align: top;
    }}

    .patterns-insight-title {{
        color: #17191b;
        font-size: 7.6pt;
        font-weight: bold;
        margin-bottom: 3px;
    }}

    .patterns-insight-text {{
        color: #69717a;
        font-size: 5.7pt;
        line-height: 1.28;
    }}

    .section-patterns {{
        page-break-inside: avoid;
    }}

    .results-story-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 14px 0;
    }}

    .results-story-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 8px 3px 6px 3px;
    }}

    .results-story-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .results-story-value {{
        color: #17191b;
        font-size: 13pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .results-story-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .results-dashboard-chart {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 9px 11px 7px 11px;
        margin: 6px 0 13px 0;
        page-break-inside: avoid;
        text-align: center;
    }}

    .results-dashboard-title,
    .results-bottom-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .results-dashboard-note,
    .results-appendix-hint {{
        color: #858c94;
        font-size: 5.7pt;
        line-height: 1.25;
    }}

    .results-dashboard-note {{
        margin: 2px 0 5px 0;
        text-align: left;
    }}

    .results-story-bottom {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
        page-break-inside: avoid;
    }}

    .results-story-bottom > tbody > tr > td {{
        vertical-align: top;
        border: 1px solid #dfe3e7;
        padding: 9px 11px;
    }}

    .recent-results-table {{
        border-collapse: collapse;
        margin-top: 5px;
        font-size: 6pt;
    }}

    .recent-results-table td {{
        border-bottom: 1px solid #eceff1;
        padding: 4px 5px;
    }}

    .recent-result-status {{
        width: 42px;
        font-weight: bold;
    }}

    .recent-result-score {{
        width: 48px;
        text-align: right;
        font-weight: bold;
    }}

    .results-form-string {{
        font-size: 16pt;
        font-weight: bold;
        letter-spacing: 4px;
        margin: 14px 0 7px 0;
    }}

    .results-form-note {{
        color: #69717a;
        font-size: 6pt;
        line-height: 1.3;
    }}

    .results-appendix-hint {{
        margin-top: 7px;
    }}

    .section-results {{
        page-break-inside: avoid;
    }}

    .player-story-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 2px 0 12px 0;
    }}

    .player-story-kpis td {{
        width: 25%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 7px 3px 5px 3px;
    }}

    .player-story-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .player-story-value {{
        color: #17191b;
        font-size: 10.5pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .player-story-sub {{
        color: #858c94;
        font-size: 5.7pt;
        margin-top: 2px;
    }}

    .section-players {{
        page-break-inside: avoid;
    }}

    .player-dashboard-chart {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 9px 11px 7px 11px;
        margin: 5px 0 8px 0;
        page-break-inside: avoid;
        text-align: center;
    }}

    .player-dashboard-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .player-dashboard-note,
    .player-dashboard-footer,
    .appendix-note {{
        color: #858c94;
        font-size: 5.7pt;
        line-height: 1.25;
    }}

    .player-dashboard-note {{
        margin: 2px 0 5px 0;
        text-align: left;
    }}

    .player-dashboard-footer {{
        margin-top: 5px;
    }}

    .appendix-note {{
        border-left: 2px solid #cfd4d9;
        padding: 4px 7px;
        margin: -4px 0 10px 0;
    }}

    .goal-story-kpis {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 9px 0;
        margin: 2px 0 12px 0;
    }}

    .goal-story-kpis td {{
        width: 20%;
        vertical-align: top;
        border-top: 2px solid #202326;
        padding: 7px 3px 5px 3px;
    }}

    .goal-story-label {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .goal-story-value {{
        color: #17191b;
        font-size: 14pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .goal-story-sub {{
        color: #858c94;
        font-size: 5.6pt;
        margin-top: 2px;
    }}

    .goal-story-chart {{
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 6px 9px 5px 9px;
        margin: 3px 0 6px 0;
        page-break-inside: avoid;
        text-align: center;
    }}

    .goal-story-chart-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        text-align: left;
    }}

    .goal-story-chart-note {{
        color: #858c94;
        font-size: 5.6pt;
        margin: 2px 0 5px 0;
        text-align: left;
    }}

    .goal-story-insights {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin-top: 4px;
    }}

    .goal-story-insights td {{
        vertical-align: top;
        border: 1px solid #dfe3e7;
        background: #ffffff;
        padding: 9px 10px;
    }}

    .goal-insight-kicker {{
        color: #818890;
        font-size: 5.5pt;
        text-transform: uppercase;
    }}

    .goal-insight-title {{
        color: #17191b;
        font-size: 10pt;
        font-weight: bold;
        margin: 3px 0;
    }}

    .goal-insight-text {{
        color: #69717a;
        font-size: 6pt;
        line-height: 1.25;
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
       PDF V12 - STRICT 2-PAGE FIT
       Same design, better pagination
       ============================================================ */

    @page {{
        size: A4 landscape;
        margin: 8mm 9mm 8mm 9mm;
    }}

    .report-page {{
        page-break-after: always;
        page-break-inside: avoid;
        break-inside: avoid;
        width: 100%;
    }}

    .report-page:last-child {{
        page-break-after: auto;
    }}

    /* ---------------- PAGE 1 ---------------- */

    .page-one .report-header {{
        margin-bottom: 7px;
        padding-bottom: 6px;
    }}

    .page-one .compact-section {{
        margin-bottom: 8px;
    }}

    .page-one .compact-title {{
        margin-bottom: 4px;
        padding-bottom: 3px;
    }}

    .page-one .compact-title h2 {{
        font-size: 10.8pt;
    }}

    .page-one .editorial-kpi {{
        padding-top: 5px;
        padding-bottom: 4px;
    }}

    .page-one .editorial-kpi-value {{
        font-size: 16pt;
    }}

    .page-one .editorial-form-line {{
        padding-top: 4px;
        padding-bottom: 5px;
        margin-bottom: 7px;
    }}

    .page-one .form-dot {{
        font-size: 14pt;
    }}

    .page-one .v11-analysis-row {{
        border-spacing: 16px 0;
        margin-bottom: 7px;
    }}

    .page-one .editorial-compare {{
        font-size: 6.9pt;
    }}

    .page-one .editorial-compare th,
    .page-one .editorial-compare td {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .page-one .editorial-goal-bars {{
        font-size: 6.8pt;
    }}

    .page-one .editorial-goal-bars th,
    .page-one .editorial-goal-bars td {{
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    .page-one .v11-flow-block {{
        margin-top: 0;
    }}

    .page-one .v11-flow-block .editorial-flow {{
        border-spacing: 18px 0;
    }}

    .page-one .v11-flow-block .editorial-flow-cell {{
        padding-top: 4px;
        padding-bottom: 2px;
    }}

    .page-one .v11-flow-block .editorial-flow-heading {{
        font-size: 7pt;
    }}

    .page-one .v11-flow-block .editorial-flow-value {{
        font-size: 20pt;
        margin-top: 3px;
    }}

    .page-one .v11-flow-block .editorial-flow-label {{
        font-size: 5.8pt;
        margin-bottom: 3px;
    }}

    .page-one .v11-flow-block .editorial-flow-record {{
        font-size: 6.2pt;
        margin-top: 3px;
    }}

    .page-one .v11-flow-block .progress-track,
    .page-one .v11-flow-block .progress-empty,
    .page-one .v11-flow-block .progress-good {{
        height: 7px;
    }}

    /* Keep the complete match-flow section together */
    .v11-flow-block,
    .v11-flow-block table,
    .v11-flow-block tr,
    .v11-flow-block td {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}

    /* ---------------- PAGE 2 ---------------- */

    .page-two .page-header {{
        margin-bottom: 6px;
        padding-bottom: 4px;
    }}

    .page-two .page-header-team {{
        font-size: 12pt;
    }}

    .page-two .page-header-meta {{
        font-size: 6pt;
    }}

    .page-two .compact-section {{
        margin-bottom: 7px;
    }}

    .page-two .compact-title {{
        margin-bottom: 3px;
        padding-bottom: 3px;
    }}

    .page-two .compact-title h2 {{
        font-size: 10.6pt;
    }}

    .page-two .v11-results {{
        margin-bottom: 7px;
    }}

    .page-two .v11-results .dashboard-kpis {{
        margin-bottom: 4px;
        border-spacing: 5px 0;
    }}

    .page-two .v11-results .dashboard-kpis td {{
        padding: 4px 5px 3px 5px;
    }}

    .page-two .v11-results .dashboard-kpis .kpi-label {{
        font-size: 5.2pt;
    }}

    .page-two .v11-results .dashboard-kpis .kpi-value {{
        font-size: 12pt;
    }}

    .page-two .v11-results table.data {{
        font-size: 6.2pt;
    }}

    .page-two .v11-results table.data th,
    .page-two .v11-results table.data td {{
        padding-top: 2.7px;
        padding-bottom: 2.7px;
        padding-left: 5px;
        padding-right: 5px;
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
        padding-top: 2.4px;
        padding-bottom: 2.4px;
        padding-left: 4px;
        padding-right: 4px;
    }}

    .page-two .small-note {{
        font-size: 5.2pt;
        margin-top: 2px;
    }}

    .page-two .v11-records {{
        margin-bottom: 0;
    }}

    .page-two .v11-records .record-cards {{
        border-spacing: 8px 0;
    }}

    .page-two .v11-records .record-cards td {{
        padding-top: 5px;
        padding-bottom: 4px;
    }}

    .page-two .v11-records .record-card-label {{
        font-size: 5.2pt;
    }}

    .page-two .v11-records .record-card-value {{
        font-size: 12pt;
        margin-top: 2px;
        margin-bottom: 2px;
    }}

    .page-two .v11-records .record-card-match {{
        font-size: 5pt;
        line-height: 1.15;
    }}

    /* Keep each logical section on page 2 together as far as possible */
    .v11-results,
    .v11-players,
    .v11-records {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}

</style>
</head>
<body>
{''.join(body_parts)}
</body>
</html>
"""

    def _build_full_report_body(
        self,
        team_name: str,
        competition_name: str,
        season_name: str,
        generated_text: str,
        sections: dict[str, Any],
        selected: set[str],
    ) -> list[str]:
        parts: list[str] = [
            self._render_report_header(
                team_name=team_name,
                competition_name=competition_name,
                season_name=season_name,
                generated_text=generated_text,
            ),
            (
                '<div class="full-report-label">'
                'VOLLSTÄNDIGER TEAMREPORT'
                '</div>'
            ),
        ]

        page_groups = [
            (
                "Leistung & Tabelle",
                [
                    "overview",
                    "table_form",
                ],
            ),
            (
                "Saisonverlauf",
                [
                    "season_progress",
                ],
            ),
            (
                "Tore & Spielverlauf",
                [
                    "goals",
                    "match_flow",
                ],
            ),
            (
                "Ergebnisse",
                [
                    "results",
                ],
            ),
            (
                "Spielmuster & Effizienz",
                [
                    "patterns",
                ],
            ),
            (
                "Punkteverluste & Spielkontrolle",
                [
                    "control",
                ],
            ),
            (
                "Halbzeiten & Spielphasen",
                [
                    "halftime_phases",
                ],
            ),
            (
                "Konstanz & Volatilität",
                [
                    "consistency",
                ],
            ),
            (
                "Offensiv- & Defensivprofil",
                [
                    "attack_defense",
                ],
            ),
            (
                "Stärken & Schwächen",
                [
                    "strengths_weaknesses",
                ],
            ),
            (
                "Spieler",
                [
                    "players",
                ],
            ),
            (
                "Fairplay",
                [
                    "discipline",
                ],
            ),
            (
                "Serien & Rekorde",
                [
                    "streaks",
                    "records",
                ],
            ),
        ]

        first_page = True

        for page_title, section_keys in page_groups:
            active_keys = [
                key
                for key in section_keys
                if key in selected
                and sections.get(key) is not None
            ]

            if not active_keys:
                continue

            page_class = (
                "report-page full-report-page"
                if first_page
                else (
                    "report-page full-report-page "
                    "full-report-page-break"
                )
            )

            parts.append(
                f'<div class="{page_class}">'
            )

            if not first_page:
                parts.append(
                    self._render_page_header(
                        team_name=team_name,
                        competition_name=competition_name,
                        season_name=season_name,
                    )
                )

            parts.append(
                '<div class="full-page-kicker">'
                'Vollständiger Teamreport'
                '</div>'
                '<div class="full-page-title">'
                f'{escape(page_title)}'
                '</div>'
            )

            for section_key in active_keys:
                parts.append(
                    self._render_full_section(
                        section_key=section_key,
                        section_data=sections[
                            section_key
                        ],
                    )
                )

            parts.append(
                "</div>"
            )

            first_page = False

        if (
            "discipline" in selected
            and isinstance(
                sections.get(
                    "discipline"
                ),
                dict,
            )
        ):
            discipline_tables = sections[
                "discipline"
            ].get(
                "tables",
                [],
            )

            if (
                isinstance(
                    discipline_tables,
                    list,
                )
                and discipline_tables
                and isinstance(
                    discipline_tables[0],
                    dict,
                )
            ):
                parts.append(
                    '<div class="report-page full-report-page '
                    'full-report-page-break">'
                )
                parts.append(
                    self._render_page_header(
                        team_name=team_name,
                        competition_name=competition_name,
                        season_name=season_name,
                    )
                )
                parts.append(
                    '<div class="appendix-label">ANHANG A · FAIRPLAY</div>'
                    '<div class="full-page-title appendix-title">'
                    'Vollständige Kartenstatistik'
                    '</div>'
                    '<div class="appendix-note">'
                    'Alle Spieler mit Kartenereignissen. '
                    'Im Hauptbericht werden die auffälligsten '
                    'Spieler grafisch dargestellt.'
                    '</div>'
                )
                parts.append(
                    '<div class="appendix-table appendix-cards">'
                    + self._render_table(
                        discipline_tables[
                            0
                        ]
                    )
                    + '</div>'
                )
                parts.append(
                    "</div>"
                )

        if (
            "results" in selected
            and isinstance(
                sections.get(
                    "results"
                ),
                dict,
            )
        ):
            parts.append(
                '<div class="report-page full-report-page '
                'full-report-page-break">'
            )
            parts.append(
                self._render_page_header(
                    team_name=team_name,
                    competition_name=competition_name,
                    season_name=season_name,
                )
            )
            parts.append(
                '<div class="appendix-label">ANHANG B · ERGEBNISSE</div>'
                '<div class="full-page-title appendix-title">'
                'Vollständige Ergebnisliste'
                '</div>'
                '<div class="appendix-note">'
                'Alle Saisonspiele chronologisch zur Nachschlagefunktion. '
                'Die Ergebnisentwicklung ist im Hauptbericht '
                'grafisch zusammengefasst.'
                '</div>'
            )

            result_tables = sections[
                "results"
            ].get(
                "tables",
                [],
            )

            if (
                isinstance(
                    result_tables,
                    list,
                )
                and result_tables
            ):
                parts.append(
                    '<div class="appendix-table appendix-results">'
                    + self._render_result_table(
                        result_tables[0]
                    )
                    + '</div>'
                )

            parts.append(
                "</div>"
            )

        if (
            "players" in selected
            and isinstance(
                sections.get(
                    "players"
                ),
                dict,
            )
        ):
            parts.append(
                '<div class="report-page full-report-page '
                'full-report-page-break">'
            )
            parts.append(
                self._render_page_header(
                    team_name=team_name,
                    competition_name=competition_name,
                    season_name=season_name,
                )
            )
            parts.append(
                '<div class="appendix-label">ANHANG C · SPIELER</div>'
                '<div class="full-page-title appendix-title">'
                'Vollständige Spielerliste'
                '</div>'
                '<div class="appendix-note">'
                'Detaildaten zur Nachschlagefunktion. '
                'Die wichtigsten Spielerwerte sind im Hauptbericht '
                'grafisch zusammengefasst.'
                '</div>'
            )
            parts.append(
                '<div class="appendix-table appendix-players">'
                + self._render_section_dict(
                    sections[
                        "players"
                    ],
                    section_key="players",
                )
                + '</div>'
            )
            parts.append(
                "</div>"
            )

        return parts

    def _render_full_section(
        self,
        section_key: str,
        section_data: Any,
    ) -> str:
        title = escape(
            self.SECTION_TITLES.get(
                section_key,
                section_key,
            )
        )

        parts = [
            (
                '<div class="compact-section '
                f'full-section section-{escape(section_key)}">'
            ),
            (
                '<div class="compact-title">'
                f'<h2>{title}</h2>'
                '</div>'
            ),
        ]

        if isinstance(
            section_data,
            dict,
        ):
            if section_key == "season_progress":
                parts.append(
                    self._render_full_season_progress(
                        section_data
                    )
                )
            elif section_key == "players":
                parts.append(
                    self._render_full_players_visual(
                        section_data
                    )
                )
            else:
                custom_renderer = {
                    "overview": self._render_full_overview_summary,
                    "table_form": self._render_full_table_form_summary,
                    "goals": self._render_full_goals_visual,
                    "match_flow": self._render_match_flow_dashboard,
                    "results": self._render_full_results_visual,
                    "patterns": self._render_full_patterns_visual,
                    "control": self._render_full_control_visual,
                    "halftime_phases": self._render_full_halftime_phases_visual,
                    "consistency": self._render_full_consistency_visual,
                    "attack_defense": self._render_full_attack_defense_visual,
                    "strengths_weaknesses": self._render_full_strengths_weaknesses_visual,
                    "discipline": self._render_full_discipline_visual,
                    "streaks": self._render_full_streaks_visual,
                    "records": self._render_full_records_visual,
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

    def _render_full_season_progress(
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

        charts = section_data.get(
            "charts",
            {},
        )

        points_progress = (
            charts.get(
                "points_progress",
                [],
            )
            if isinstance(charts, dict)
            else []
        )

        position_progress = (
            charts.get(
                "position_progress",
                [],
            )
            if isinstance(charts, dict)
            else []
        )

        if points_progress:
            parts.append(
                self._render_svg_line_chart(
                    title=(
                        "Punkteentwicklung nach absolvierten Spielen"
                    ),
                    rows=points_progress,
                    value_key="points",
                    value_label="Punkte",
                    invert_y=False,
                )
            )

        if position_progress:
            parts.append(
                self._render_svg_line_chart(
                    title=(
                        "Tabellenplatz nach absolvierten Spielen"
                    ),
                    rows=position_progress,
                    value_key="position",
                    value_label="Platz",
                    invert_y=True,
                )
            )

        if not parts:
            return self._render_section_dict(
                section_data,
                section_key="season_progress",
            )

        return "".join(
            parts
        )

    def _render_svg_line_chart(
        self,
        title: str,
        rows: list[dict[str, Any]],
        value_key: str,
        value_label: str,
        invert_y: bool = False,
    ) -> str:
        if not rows:
            return ""

        clean_rows: list[tuple[int, float]] = []

        for row in rows:
            try:
                played = int(
                    row.get(
                        "played",
                        0,
                    )
                )
                value = float(
                    row.get(
                        value_key,
                        0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if played <= 0:
                continue

            clean_rows.append(
                (
                    played,
                    value,
                )
            )

        if not clean_rows:
            return ""

        clean_rows.sort(
            key=lambda item: item[0]
        )

        resource_name = (
            "chart://"
            + value_key
            + "_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        image = self._create_line_chart_image(
            rows=clean_rows,
            value_key=value_key,
            value_label=value_label,
            invert_y=invert_y,
        )

        self._image_resources[
            resource_name
        ] = image

        first_value = clean_rows[
            0
        ][1]

        last_value = clean_rows[
            -1
        ][1]

        if value_key == "position":
            trend_value = (
                first_value
                - last_value
            )
        else:
            trend_value = (
                last_value
                - first_value
            )

        if trend_value > 0:
            trend_text = "positive Entwicklung"
            trend_class = "chart-trend-positive"
        elif trend_value < 0:
            trend_text = "negative Entwicklung"
            trend_class = "chart-trend-negative"
        else:
            trend_text = "unverändert"
            trend_class = "chart-trend-neutral"

        return (
            '<div class="full-chart-card">'
            f'<div class="full-chart-title">{escape(title)}</div>'
            f'<div class="full-chart-trend {trend_class}">'
            f'{escape(trend_text)}'
            '</div>'
            '<div class="full-chart-image">'
            f'<img src="{escape(resource_name)}" '
            'width="980" />'
            '</div>'
            '</div>'
        )

    def _create_line_chart_image(
        self,
        rows: list[tuple[int, float]],
        value_key: str,
        value_label: str,
        invert_y: bool,
    ) -> QImage:
        width = 1800
        height = 285

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )

        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        margin_left = 105
        margin_right = 45
        margin_top = 25
        margin_bottom = 65

        plot_left = float(
            margin_left
        )
        plot_top = float(
            margin_top
        )
        plot_width = float(
            width
            - margin_left
            - margin_right
        )
        plot_height = float(
            height
            - margin_top
            - margin_bottom
        )

        x_values = [
            row[0]
            for row in rows
        ]

        y_values = [
            row[1]
            for row in rows
        ]

        x_min = min(
            x_values
        )
        x_max = max(
            x_values
        )

        raw_y_min = min(
            y_values
        )
        raw_y_max = max(
            y_values
        )

        if value_key == "position":
            y_min = max(
                1,
                int(
                    raw_y_min
                ),
            )
            y_max = max(
                y_min + 1,
                int(
                    raw_y_max
                ),
            )
        else:
            y_min = 0
            y_max = max(
                1,
                int(
                    raw_y_max
                ),
            )

        def scale_x(
            value: int,
        ) -> float:
            if x_max == x_min:
                return plot_left

            return (
                plot_left
                + (
                    (
                        value
                        - x_min
                    )
                    / (
                        x_max
                        - x_min
                    )
                )
                * plot_width
            )

        def scale_y(
            value: float,
        ) -> float:
            if y_max == y_min:
                return plot_top

            ratio = (
                (
                    value
                    - y_min
                )
                / (
                    y_max
                    - y_min
                )
            )

            if invert_y:
                return (
                    plot_top
                    + ratio
                    * plot_height
                )

            return (
                plot_top
                + (
                    1.0
                    - ratio
                )
                * plot_height
            )

        grid_pen = QPen(
            QColor(
                "#e4e7ea"
            )
        )
        grid_pen.setWidth(
            2
        )

        axis_pen = QPen(
            QColor(
                "#aeb4ba"
            )
        )
        axis_pen.setWidth(
            2
        )

        line_pen = QPen(
            QColor(
                "#2f6fa3"
            )
        )
        line_pen.setWidth(
            7
        )

        text_color = QColor(
            "#69717a"
        )

        axis_font = QFont(
            "Arial",
            15,
        )

        label_font = QFont(
            "Arial",
            16,
        )

        painter.setFont(
            axis_font
        )

        painter.setPen(
            grid_pen
        )

        y_ticks = 5

        for index in range(
            y_ticks + 1
        ):
            ratio = (
                index
                / y_ticks
            )

            tick_value = (
                y_min
                + (
                    y_max
                    - y_min
                )
                * ratio
            )

            y_position = scale_y(
                tick_value
            )

            painter.drawLine(
                QPointF(
                    plot_left,
                    y_position,
                ),
                QPointF(
                    plot_left
                    + plot_width,
                    y_position,
                ),
            )

            painter.setPen(
                text_color
            )

            painter.drawText(
                QRectF(
                    0,
                    y_position - 20,
                    margin_left - 15,
                    40,
                ),
                int(
                    0x0002
                    | 0x0080
                ),
                str(
                    int(
                        round(
                            tick_value
                        )
                    )
                ),
            )

            painter.setPen(
                grid_pen
            )

        painter.setPen(
            axis_pen
        )

        painter.drawLine(
            QPointF(
                plot_left,
                plot_top
                + plot_height,
            ),
            QPointF(
                plot_left
                + plot_width,
                plot_top
                + plot_height,
            ),
        )

        total_games = len(
            rows
        )

        desired_ticks = min(
            8,
            total_games,
        )

        if desired_ticks <= 1:
            tick_indices = [
                0
            ]
        else:
            tick_indices = sorted(
                {
                    round(
                        i
                        * (
                            total_games
                            - 1
                        )
                        / (
                            desired_ticks
                            - 1
                        )
                    )
                    for i in range(
                        desired_ticks
                    )
                }
            )

        painter.setFont(
            axis_font
        )

        for index in tick_indices:
            x_value = rows[
                index
            ][0]

            x_position = scale_x(
                x_value
            )

            painter.setPen(
                axis_pen
            )

            painter.drawLine(
                QPointF(
                    x_position,
                    plot_top
                    + plot_height,
                ),
                QPointF(
                    x_position,
                    plot_top
                    + plot_height
                    + 10,
                ),
            )

            painter.setPen(
                text_color
            )

            painter.drawText(
                QRectF(
                    x_position - 38,
                    plot_top
                    + plot_height
                    + 14,
                    76,
                    38,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                str(
                    x_value
                ),
            )

        painter.setPen(
            line_pen
        )

        points = [
            QPointF(
                scale_x(
                    x_value
                ),
                scale_y(
                    y_value
                ),
            )
            for x_value, y_value
            in rows
        ]

        for first, second in zip(
            points,
            points[1:],
        ):
            painter.drawLine(
                first,
                second,
            )

        painter.setPen(
            QPen(
                QColor(
                    "#ffffff"
                ),
                3,
            )
        )

        painter.setBrush(
            QColor(
                "#2f6fa3"
            )
        )

        for point in points:
            painter.drawEllipse(
                point,
                8,
                8,
            )

        painter.setPen(
            text_color
        )

        painter.setFont(
            label_font
        )

        painter.drawText(
            QRectF(
                plot_left,
                height - 42,
                plot_width,
                32,
            ),
            int(
                0x0004
                | 0x0080
            ),
            "Absolvierte Spiele",
        )

        painter.save()

        painter.translate(
            28,
            plot_top
            + plot_height
            / 2,
        )

        painter.rotate(
            -90
        )

        painter.drawText(
            QRectF(
                -plot_height / 2,
                -25,
                plot_height,
                32,
            ),
            int(
                0x0004
                | 0x0080
            ),
            value_label,
        )

        painter.restore()

        painter.end()

        return image

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



    def _render_full_overview_summary(
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
            return self._render_overview_dashboard(
                section_data
            )

        preferred = (
            "Tabellenplatz",
            "Punkte",
            "Tordifferenz",
            "Tore / Spiel",
            "Gegentore / Spiel",
        )

        items = []

        for label in preferred:
            value = facts.get(
                label,
                "–",
            )

            status = self._fact_status_class(
                label,
                value,
            )

            cls = {
                "status-positive": "executive-positive",
                "status-neutral": "executive-neutral",
                "status-negative": "executive-negative",
            }.get(
                status,
                "",
            )

            items.append(
                '<td>'
                f'<div class="executive-kpi-label">{escape(label)}</div>'
                f'<div class="executive-kpi-value {cls}">'
                f'{escape(self._format_value(value))}'
                '</div>'
                '</td>'
            )

        form_value = None

        for label, value in facts.items():
            if "form" in str(
                label
            ).casefold():
                form_value = value
                break

        form_html = self._render_form_from_value(
            form_value
        )

        return (
            '<div class="executive-intro">'
            '<div class="executive-intro-title">Saison auf einen Blick</div>'
            '<div class="executive-intro-text">'
            'Die wichtigsten Leistungswerte kompakt zusammengefasst.'
            '</div>'
            '</div>'
            '<table width="100%" class="executive-kpis"><tr>'
            + "".join(
                items
            )
            + '</tr></table>'
            '<div class="executive-form">'
            '<span class="executive-form-label">LETZTE FORM</span>'
            f'{form_html}'
            '</div>'
        )

    def _render_full_table_form_summary(
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
            return self._render_table_form_dashboard(
                section_data
            )

        named_blocks: dict[str, dict[str, Any]] = {}

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
            return self._render_table_form_dashboard(
                section_data
            )

        def facts_of(
            block: Any,
        ) -> dict[str, Any]:
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

        home_facts = facts_of(
            home
        )
        away_facts = facts_of(
            away
        )
        form_facts = facts_of(
            form
        )

        home_points = self._to_number(
            home_facts.get(
                "Punkte",
                0,
            )
        )
        away_points = self._to_number(
            away_facts.get(
                "Punkte",
                0,
            )
        )
        home_ppg = self._to_number(
            home_facts.get(
                "Punkte / Spiel",
                0,
            )
        )
        away_ppg = self._to_number(
            away_facts.get(
                "Punkte / Spiel",
                0,
            )
        )
        home_diff = self._to_number(
            home_facts.get(
                "Tordifferenz",
                0,
            )
        )
        away_diff = self._to_number(
            away_facts.get(
                "Tordifferenz",
                0,
            )
        )

        max_points = max(
            1.0,
            home_points,
            away_points,
        )

        home_width = int(
            round(
                home_points
                / max_points
                * 100
            )
        )
        away_width = int(
            round(
                away_points
                / max_points
                * 100
            )
        )

        if home_ppg > away_ppg + 0.05:
            venue_title = "Zuhause stärker"
            venue_text = (
                f"{self._format_value(home_ppg)} Punkte pro Spiel zuhause "
                f"gegenüber {self._format_value(away_ppg)} auswärts."
            )
        elif away_ppg > home_ppg + 0.05:
            venue_title = "Auswärts stärker"
            venue_text = (
                f"{self._format_value(away_ppg)} Punkte pro Spiel auswärts "
                f"gegenüber {self._format_value(home_ppg)} zuhause."
            )
        else:
            venue_title = "Ausgeglichen"
            venue_text = (
                "Die Punkteausbeute zuhause und auswärts liegt "
                "nahezu auf demselben Niveau."
            )

        if home_diff > away_diff:
            balance_title = "Heimbilanz"
            balance_text = (
                f"Die Tordifferenz zuhause liegt bei "
                f"{self._format_value(home_facts.get('Tordifferenz', 0))}, "
                f"auswärts bei "
                f"{self._format_value(away_facts.get('Tordifferenz', 0))}."
            )
        elif away_diff > home_diff:
            balance_title = "Auswärtsbilanz"
            balance_text = (
                f"Die Tordifferenz auswärts liegt bei "
                f"{self._format_value(away_facts.get('Tordifferenz', 0))}, "
                f"zuhause bei "
                f"{self._format_value(home_facts.get('Tordifferenz', 0))}."
            )
        else:
            balance_title = "Tordifferenz"
            balance_text = (
                "Die Tordifferenz ist zuhause und auswärts identisch."
            )

        recent_ppg = self._to_number(
            form_facts.get(
                "Punkte / Spiel",
                0,
            )
        )

        if recent_ppg >= 2.0:
            form_title = "Starke Schlussform"
            form_text = (
                f"Die letzten fünf Spiele bringen "
                f"{self._format_value(recent_ppg)} Punkte pro Spiel."
            )
        elif recent_ppg >= 1.4:
            form_title = "Solide Form"
            form_text = (
                f"Die letzten fünf Spiele liegen bei "
                f"{self._format_value(recent_ppg)} Punkten pro Spiel."
            )
        else:
            form_title = "Form mit Luft nach oben"
            form_text = (
                f"Aus den letzten fünf Spielen entstehen "
                f"{self._format_value(recent_ppg)} Punkte pro Spiel."
            )

        return (
            '<table width="100%" class="executive-venue"><tr>'
            '<td width="50%">'
            '<div class="executive-venue-title">Heim</div>'
            f'<div class="executive-venue-balance">{escape(self._bilanz_text(home_facts))}</div>'
            f'<div class="executive-venue-goals">{escape(self._goal_pair_text(home_facts))} Tore</div>'
            '<div class="executive-bar-track">'
            f'<div class="executive-bar-fill executive-home" style="width:{home_width}%;">&nbsp;</div>'
            '</div>'
            f'<div class="executive-venue-meta">{escape(self._format_value(home_points))} Punkte · '
            f'{escape(self._format_value(home_ppg))} Pkt./Spiel · '
            f'TD {escape(self._format_value(home_facts.get("Tordifferenz", "–")))}</div>'
            '</td>'
            '<td width="50%">'
            '<div class="executive-venue-title">Auswärts</div>'
            f'<div class="executive-venue-balance">{escape(self._bilanz_text(away_facts))}</div>'
            f'<div class="executive-venue-goals">{escape(self._goal_pair_text(away_facts))} Tore</div>'
            '<div class="executive-bar-track">'
            f'<div class="executive-bar-fill executive-away" style="width:{away_width}%;">&nbsp;</div>'
            '</div>'
            f'<div class="executive-venue-meta">{escape(self._format_value(away_points))} Punkte · '
            f'{escape(self._format_value(away_ppg))} Pkt./Spiel · '
            f'TD {escape(self._format_value(away_facts.get("Tordifferenz", "–")))}</div>'
            '</td>'
            '</tr></table>'
            '<div class="executive-insights-title">Kernaussagen</div>'
            '<table width="100%" class="executive-insights"><tr>'
            '<td>'
            f'<div class="executive-insight-title">{escape(venue_title)}</div>'
            f'<div class="executive-insight-text">{escape(venue_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="executive-insight-title">{escape(balance_title)}</div>'
            f'<div class="executive-insight-text">{escape(balance_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="executive-insight-title">{escape(form_title)}</div>'
            f'<div class="executive-insight-text">{escape(form_text)}</div>'
            '</td>'
            '</tr></table>'
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


    def _render_full_goals_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        phase_table = self._find_goal_phase_table(
            section_data
        )

        if phase_table is None:
            return self._render_goals_dashboard(
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

        parsed: list[tuple[str, int, int]] = []

        for row in rows:
            values = self._table_values(
                headers,
                row,
            )

            if len(values) < 3:
                continue

            phase = str(
                values[0]
            )
            goals = int(
                round(
                    self._to_number(
                        values[1]
                    )
                )
            )
            against = int(
                round(
                    self._to_number(
                        values[2]
                    )
                )
            )

            parsed.append(
                (
                    phase,
                    goals,
                    against,
                )
            )

        if not parsed:
            return self._render_goals_dashboard(
                section_data
            )

        total_goals = sum(
            goals
            for _phase, goals, _against
            in parsed
        )
        total_against = sum(
            against
            for _phase, _goals, against
            in parsed
        )

        best_phase = max(
            parsed,
            key=lambda item: (
                item[1],
                item[1] - item[2],
            ),
        )

        danger_phase = max(
            parsed,
            key=lambda item: (
                item[2],
                item[2] - item[1],
            ),
        )

        strongest_balance = max(
            parsed,
            key=lambda item: (
                item[1] - item[2],
                item[1],
            ),
        )

        weakest_balance = min(
            parsed,
            key=lambda item: (
                item[1] - item[2],
                -item[2],
            ),
        )

        first_half_goals = sum(
            goals
            for phase, goals, _against
            in parsed
            if self._phase_is_first_half(
                phase
            )
        )
        second_half_goals = (
            total_goals
            - first_half_goals
        )

        first_half_against = sum(
            against
            for phase, _goals, against
            in parsed
            if self._phase_is_first_half(
                phase
            )
        )
        second_half_against = (
            total_against
            - first_half_against
        )

        resource_name = (
            "chart://goal_phases_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_goal_phase_chart_image(
            parsed
        )

        goal_difference = (
            total_goals
            - total_against
        )

        diff_class = (
            "editorial-positive"
            if goal_difference > 0
            else (
                "editorial-negative"
                if goal_difference < 0
                else "editorial-neutral"
            )
        )

        balance_best = (
            strongest_balance[1]
            - strongest_balance[2]
        )
        balance_weakest = (
            weakest_balance[1]
            - weakest_balance[2]
        )

        if second_half_goals > first_half_goals:
            half_attack_text = (
                "Offensiv fällt nach der Pause mehr."
            )
        elif first_half_goals > second_half_goals:
            half_attack_text = (
                "Offensiv fällt vor der Pause mehr."
            )
        else:
            half_attack_text = (
                "Die eigenen Tore verteilen sich gleichmäßig auf beide Halbzeiten."
            )

        if second_half_against > first_half_against:
            half_defence_text = (
                "Defensiv fallen nach der Pause mehr Gegentore."
            )
        elif first_half_against > second_half_against:
            half_defence_text = (
                "Defensiv fallen vor der Pause mehr Gegentore."
            )
        else:
            half_defence_text = (
                "Die Gegentore verteilen sich gleichmäßig auf beide Halbzeiten."
            )

        return (
            '<table width="100%" class="goal-story-kpis"><tr>'
            '<td>'
            '<div class="goal-story-label">Tore</div>'
            f'<div class="goal-story-value editorial-positive">{total_goals}</div>'
            '</td>'
            '<td>'
            '<div class="goal-story-label">Gegentore</div>'
            f'<div class="goal-story-value editorial-negative">{total_against}</div>'
            '</td>'
            '<td>'
            '<div class="goal-story-label">Tordifferenz</div>'
            f'<div class="goal-story-value {diff_class}">'
            f'{goal_difference:+d}'
            '</div>'
            '</td>'
            '<td>'
            '<div class="goal-story-label">Torreichste Phase</div>'
            f'<div class="goal-story-value">{escape(best_phase[0])}</div>'
            f'<div class="goal-story-sub">{best_phase[1]} eigene Tore</div>'
            '</td>'
            '<td>'
            '<div class="goal-story-label">Gefährlichste Phase</div>'
            f'<div class="goal-story-value">{escape(danger_phase[0])}</div>'
            f'<div class="goal-story-sub">{danger_phase[2]} Gegentore</div>'
            '</td>'
            '</tr></table>'
            '<div class="goal-story-chart">'
            '<div class="goal-story-chart-title">'
            'Torverteilung über 90 Minuten'
            '</div>'
            '<div class="goal-story-chart-note">'
            'Grün = Tore &nbsp;&nbsp; Rot = Gegentore'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<table width="100%" class="goal-story-insights"><tr>'
            '<td width="33%">'
            '<div class="goal-insight-kicker">Stärkste Bilanz</div>'
            f'<div class="goal-insight-title">{escape(strongest_balance[0])}</div>'
            f'<div class="goal-insight-text">{strongest_balance[1]}:{strongest_balance[2]} Tore '
            f'({balance_best:+d})</div>'
            '</td>'
            '<td width="33%">'
            '<div class="goal-insight-kicker">Schwächste Bilanz</div>'
            f'<div class="goal-insight-title">{escape(weakest_balance[0])}</div>'
            f'<div class="goal-insight-text">{weakest_balance[1]}:{weakest_balance[2]} Tore '
            f'({balance_weakest:+d})</div>'
            '</td>'
            '<td width="34%">'
            '<div class="goal-insight-kicker">Halbzeiten</div>'
            f'<div class="goal-insight-title">{first_half_goals}:{second_half_goals} eigene Tore</div>'
            f'<div class="goal-insight-text">{escape(half_attack_text)} '
            f'{escape(half_defence_text)}</div>'
            '</td>'
            '</tr></table>'
        )

    @staticmethod
    def _phase_is_first_half(
        phase: str,
    ) -> bool:
        match = re.search(
            r"(\d+)",
            str(
                phase
            ),
        )

        if match is None:
            return False

        return int(
            match.group(
                1
            )
        ) <= 45

    def _create_goal_phase_chart_image(
        self,
        rows: list[tuple[str, int, int]],
    ) -> QImage:
        width = 1800
        height = 340

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        left = 105
        right = 45
        top = 45
        bottom = 100

        plot_width = (
            width
            - left
            - right
        )
        plot_height = (
            height
            - top
            - bottom
        )

        max_value = max(
            [
                max(
                    goals,
                    against,
                )
                for _phase, goals, against
                in rows
            ]
            or [1]
        )
        max_value = max(
            1,
            max_value,
        )

        grid_pen = QPen(
            QColor(
                "#e5e8eb"
            )
        )
        grid_pen.setWidth(
            2
        )

        axis_pen = QPen(
            QColor(
                "#aeb4ba"
            )
        )
        axis_pen.setWidth(
            2
        )

        text_pen = QPen(
            QColor(
                "#68717b"
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                15,
            )
        )

        tick_count = min(
            5,
            max_value,
        )

        for index in range(
            tick_count + 1
        ):
            value = (
                max_value
                * index
                / tick_count
            )
            y = (
                top
                + plot_height
                - (
                    value
                    / max_value
                    * plot_height
                )
            )

            painter.setPen(
                grid_pen
            )
            painter.drawLine(
                QPointF(
                    left,
                    y,
                ),
                QPointF(
                    left
                    + plot_width,
                    y,
                ),
            )

            painter.setPen(
                text_pen
            )
            painter.drawText(
                QRectF(
                    0,
                    y - 18,
                    left - 15,
                    36,
                ),
                int(
                    0x0002
                    | 0x0080
                ),
                str(
                    int(
                        round(
                            value
                        )
                    )
                ),
            )

        painter.setPen(
            axis_pen
        )
        painter.drawLine(
            QPointF(
                left,
                top + plot_height,
            ),
            QPointF(
                left + plot_width,
                top + plot_height,
            ),
        )

        group_width = (
            plot_width
            / max(
                1,
                len(
                    rows
                ),
            )
        )
        bar_width = min(
            90.0,
            group_width
            * 0.28,
        )
        gap = min(
            20.0,
            group_width
            * 0.06,
        )

        green = QColor(
            "#2f9e44"
        )
        red = QColor(
            "#d94848"
        )
        label_color = QColor(
            "#4f565e"
        )

        painter.setFont(
            QFont(
                "Arial",
                15,
            )
        )

        for index, (
            phase,
            goals,
            against,
        ) in enumerate(
            rows
        ):
            center_x = (
                left
                + group_width
                * (
                    index
                    + 0.5
                )
            )

            values = [
                (
                    goals,
                    green,
                    -bar_width - gap / 2,
                ),
                (
                    against,
                    red,
                    gap / 2,
                ),
            ]

            for value, color, offset in values:
                bar_height = (
                    value
                    / max_value
                    * plot_height
                )

                x = (
                    center_x
                    + offset
                )
                y = (
                    top
                    + plot_height
                    - bar_height
                )

                painter.fillRect(
                    QRectF(
                        x,
                        y,
                        bar_width,
                        bar_height,
                    ),
                    color,
                )

                painter.setPen(
                    QPen(
                        color
                    )
                )
                painter.drawText(
                    QRectF(
                        x - 8,
                        max(
                            0.0,
                            y - 35,
                        ),
                        bar_width + 16,
                        30,
                    ),
                    int(
                        0x0004
                        | 0x0080
                    ),
                    str(
                        value
                    ),
                )

            painter.setPen(
                QPen(
                    label_color
                )
            )
            painter.drawText(
                QRectF(
                    center_x
                    - group_width / 2,
                    top
                    + plot_height
                    + 18,
                    group_width,
                    42,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                phase,
            )

        painter.end()

        return image

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

    def _render_full_strengths_weaknesses_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        strengths = section_data.get("strengths", [])
        weaknesses = section_data.get("weaknesses", [])
        patterns = section_data.get("patterns", [])

        def render_column(
            title: str,
            items: list[dict[str, Any]],
            accent: str,
        ) -> str:
            cards: list[str] = []

            for index, item in enumerate(items[:3], start=1):
                item_title = escape(str(item.get("title", "-")))
                metric = escape(str(item.get("metric", "-")))
                description = escape(str(item.get("text", "")))
                source = escape(str(item.get("source", "")))

                cards.append(
                    '<table width="100%" cellspacing="0" cellpadding="0" '
                    'style="border-collapse:collapse; margin:0 0 13px 0;">'
                    '<tr>'
                    f'<td width="7" bgcolor="{accent}">&nbsp;</td>'
                    '<td height="105" valign="top" style="border:1px solid #dfe3e7; padding:12px 13px;">'
                    '<table width="100%" cellspacing="0" cellpadding="0">'
                    '<tr>'
                    f'<td width="30" valign="top" style="font-size:8pt;"><b>{index:02d}</b></td>'
                    f'<td valign="top" style="font-size:8.3pt;"><b>{item_title}</b></td>'
                    f'<td width="125" align="right" valign="top">'
                    f'<span style="font-size:11.5pt;"><b>{metric}</b></span>'
                    '</td>'
                    '</tr>'
                    '</table>'
                    f'<div style="font-size:6.8pt; color:#626a72; '
                    f'line-height:1.45; margin-top:9px;">{description}</div>'
                    f'<div style="font-size:5.5pt; color:#9aa1a8; '
                    f'margin-top:9px;">QUELLE · {source}</div>'
                    '</td>'
                    '</tr>'
                    '</table>'
                )

            return (
                '<td width="33%" valign="top" style="padding:0 7px;">'
                '<table width="100%" cellspacing="0" cellpadding="0">'
                '<tr>'
                f'<td style="border-bottom:3px solid {accent}; '
                'padding:0 0 8px 0; font-size:10.5pt;">'
                f'<b>{escape(title)}</b>'
                '</td>'
                '</tr>'
                '<tr><td height="11"></td></tr>'
                f'<tr><td>{"".join(cards)}</td></tr>'
                '</table>'
                '</td>'
            )

        return (
            '<table width="100%" cellspacing="0" cellpadding="0">'
            '<tr>'
            '<td style="padding:0 0 13px 0; color:#69717a; '
            'font-size:6.6pt; line-height:1.4;">'
            'Kompakte Teamcharakteristik aus den auffälligsten '
            'bereits berechneten Saisonkennzahlen.'
            '</td>'
            '</tr>'
            '</table>'
            '<table width="100%" cellspacing="0" cellpadding="0" '
            'style="table-layout:fixed;">'
            '<tr>'
            f'{render_column("Stärken", strengths, "#2f9e44")}'
            f'{render_column("Schwächen", weaknesses, "#d94848")}'
            f'{render_column("Typische Spielmuster", patterns, "#2f6fa3")}'
            '</tr>'
            '</table>'
        )

    def _render_full_attack_defense_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )
        charts = section_data.get(
            "charts",
            {},
        )

        if not (
            isinstance(facts, dict)
            and isinstance(charts, dict)
        ):
            return self._render_section_dict(
                section_data,
                section_key="attack_defense",
            )

        played = int(
            self._to_number(
                facts.get("Spiele", 0)
            )
        )
        scored = int(
            self._to_number(
                facts.get("Mit eigenem Tor", 0)
            )
        )
        scored_pct = self._to_number(
            facts.get("Mit eigenem Tor %", 0)
        )
        multi = int(
            self._to_number(
                facts.get("Mind. 2 eigene Tore", 0)
            )
        )
        multi_pct = self._to_number(
            facts.get("Mind. 2 eigene Tore %", 0)
        )
        clean = int(
            self._to_number(
                facts.get("Zu Null", 0)
            )
        )
        clean_pct = self._to_number(
            facts.get("Zu Null %", 0)
        )
        max_one = int(
            self._to_number(
                facts.get("Max. 1 Gegentor", 0)
            )
        )
        max_one_pct = self._to_number(
            facts.get("Max. 1 Gegentor %", 0)
        )
        three_against = int(
            self._to_number(
                facts.get("Mind. 3 Gegentore", 0)
            )
        )

        resource_name = (
            "chart://attack_defense_"
            + str(len(self._image_resources))
        )

        self._image_resources[
            resource_name
        ] = self._create_attack_defense_chart_image(
            attack_rows=charts.get(
                "attack_output",
                [],
            ),
            defense_rows=charts.get(
                "defense_output",
                [],
            ),
        )

        ppg_1 = self._to_number(
            facts.get("PPG bei 1 Tor", 0)
        )
        ppg_2 = self._to_number(
            facts.get("PPG bei 2 Toren", 0)
        )
        ppg_3 = self._to_number(
            facts.get("PPG bei 3+ Toren", 0)
        )

        win_1 = self._to_number(
            facts.get("Siegquote bei 1 Tor %", 0)
        )
        win_2 = self._to_number(
            facts.get("Siegquote bei 2 Toren %", 0)
        )
        win_3 = self._to_number(
            facts.get("Siegquote bei 3+ Toren %", 0)
        )

        if scored_pct >= 85:
            attack_title = "Offensiv fast immer präsent"
        elif scored_pct >= 70:
            attack_title = "Offensiv häufig erfolgreich"
        else:
            attack_title = "Offensiv mit Aussetzern"

        attack_text = (
            f"In {scored} von {played} Spielen wurde getroffen "
            f"({self._format_value(scored_pct)} %). "
            f"{multi}× gelangen mindestens zwei Tore."
        )

        if clean_pct >= 30:
            defense_title = "Defensiv häufig stabil"
        elif max_one_pct >= 60:
            defense_title = "Defensiv oft im Rahmen"
        else:
            defense_title = "Defensiv oft unter Druck"

        defense_text = (
            f"{clean} Zu-Null-Spiele und {max_one} Partien "
            f"mit höchstens einem Gegentor. "
            f"{three_against}× wurden mindestens drei Gegentore kassiert."
        )

        if ppg_3 > ppg_2 > ppg_1:
            efficiency_title = "Mehr Tore zahlen sich klar aus"
        else:
            efficiency_title = "Torausbeute entscheidet nicht allein"

        efficiency_text = (
            f"Bei 1 Tor: {self._format_value(ppg_1)} Pkt./Spiel "
            f"({self._format_value(win_1)} % Siege) · "
            f"bei 2 Toren: {self._format_value(ppg_2)} "
            f"({self._format_value(win_2)} %) · "
            f"bei 3+ Toren: {self._format_value(ppg_3)} "
            f"({self._format_value(win_3)} %)."
        )

        return (
            '<table width="100%" class="attack-defense-kpis"><tr>'
            '<td>'
            '<div class="attack-defense-label">Mit eigenem Tor</div>'
            f'<div class="attack-defense-value">{scored}</div>'
            f'<div class="attack-defense-sub">{escape(self._format_value(scored_pct))} % der Spiele</div>'
            '</td>'
            '<td>'
            '<div class="attack-defense-label">Mind. 2 Tore</div>'
            f'<div class="attack-defense-value">{multi}</div>'
            f'<div class="attack-defense-sub">{escape(self._format_value(multi_pct))} % der Spiele</div>'
            '</td>'
            '<td>'
            '<div class="attack-defense-label">Zu Null</div>'
            f'<div class="attack-defense-value">{clean}</div>'
            f'<div class="attack-defense-sub">{escape(self._format_value(clean_pct))} % der Spiele</div>'
            '</td>'
            '<td>'
            '<div class="attack-defense-label">Max. 1 Gegentor</div>'
            f'<div class="attack-defense-value">{max_one}</div>'
            f'<div class="attack-defense-sub">{escape(self._format_value(max_one_pct))} % der Spiele</div>'
            '</td>'
            '<td>'
            '<div class="attack-defense-label">3+ Gegentore</div>'
            f'<div class="attack-defense-value">{three_against}</div>'
            '<div class="attack-defense-sub">defensive Ausreißer</div>'
            '</td>'
            '</tr></table>'
            '<div class="attack-defense-chart-card">'
            '<div class="attack-defense-chart-title">'
            'Torproduktion & Gegentorprofil'
            '</div>'
            '<div class="attack-defense-chart-note">'
            'Links: eigene Tore pro Spiel inkl. Punkteausbeute · '
            'Rechts: Gegentore pro Spiel'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<div class="attack-defense-insights-title">Kernaussagen</div>'
            '<table width="100%" class="attack-defense-insights"><tr>'
            '<td>'
            f'<div class="attack-defense-insight-title">{escape(attack_title)}</div>'
            f'<div class="attack-defense-insight-text">{escape(attack_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="attack-defense-insight-title">{escape(defense_title)}</div>'
            f'<div class="attack-defense-insight-text">{escape(defense_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="attack-defense-insight-title">{escape(efficiency_title)}</div>'
            f'<div class="attack-defense-insight-text">{escape(efficiency_text)}</div>'
            '</td>'
            '</tr></table>'
        )

    def _create_attack_defense_chart_image(
        self,
        attack_rows: list[dict[str, Any]],
        defense_rows: list[dict[str, Any]],
    ) -> QImage:
        width = 1800
        height = 520

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(QColor("#ffffff"))

        painter = QPainter(image)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        text = QColor("#25282c")
        muted = QColor("#737b84")
        border = QColor("#dfe3e7")
        green = QColor("#2f9e44")
        amber = QColor("#d99a00")
        red = QColor("#d94848")
        blue = QColor("#2f6fa3")
        track = QColor("#eef0f2")

        def panel(x, y, w, h, title):
            painter.setPen(QPen(border, 2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(
                QRectF(x, y, w, h),
                8,
                8,
            )
            painter.setPen(QPen(text))
            painter.setFont(
                QFont(
                    "Arial",
                    15,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x + 20,
                    y + 15,
                    w - 40,
                    32,
                ),
                int(0x0001 | 0x0080),
                title,
            )

        panel(
            25,
            30,
            860,
            450,
            "Eigene Tore & Punkteausbeute",
        )
        panel(
            915,
            30,
            860,
            450,
            "Gegentore pro Spiel",
        )

        # Left panel: attack output.
        attack_max_games = max(
            [1]
            + [
                int(r.get("games", 0) or 0)
                for r in attack_rows[:4]
            ]
        )

        for index, row in enumerate(
            attack_rows[:4]
        ):
            label = str(row.get("label", ""))
            games = int(row.get("games", 0) or 0)
            ppg = float(row.get("ppg", 0) or 0)
            win_pct = float(
                row.get(
                    "win_percentage",
                    0,
                )
                or 0
            )
            y = 95 + index * 82

            painter.setPen(QPen(text))
            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    55,
                    y,
                    110,
                    24,
                ),
                int(0x0001 | 0x0080),
                f"{label} Tore",
            )

            painter.fillRect(
                QRectF(
                    165,
                    y + 2,
                    330,
                    20,
                ),
                track,
            )
            painter.fillRect(
                QRectF(
                    165,
                    y + 2,
                    330 * games / attack_max_games,
                    20,
                ),
                green if label != "0" else red,
            )

            painter.setPen(QPen(muted))
            painter.setFont(
                QFont(
                    "Arial",
                    9,
                )
            )
            painter.drawText(
                QRectF(
                    515,
                    y - 2,
                    300,
                    26,
                ),
                int(0x0001 | 0x0080),
                f"{games} Spiele · {ppg:.2f} Pkt./Sp. · {win_pct:.1f} % Siege",
            )

        # Right panel: defense distribution.
        defense_max = max(
            [1]
            + [
                int(r.get("games", 0) or 0)
                for r in defense_rows[:4]
            ]
        )
        colors = [
            green,
            blue,
            amber,
            red,
        ]

        for index, row in enumerate(
            defense_rows[:4]
        ):
            label = str(row.get("label", ""))
            games = int(row.get("games", 0) or 0)
            pct = float(
                row.get(
                    "percentage",
                    0,
                )
                or 0
            )
            y = 95 + index * 82

            painter.setPen(QPen(text))
            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    945,
                    y,
                    125,
                    24,
                ),
                int(0x0001 | 0x0080),
                f"{label} Gegentore",
            )

            painter.fillRect(
                QRectF(
                    1080,
                    y + 2,
                    390,
                    20,
                ),
                track,
            )
            painter.fillRect(
                QRectF(
                    1080,
                    y + 2,
                    390 * games / defense_max,
                    20,
                ),
                colors[index],
            )

            painter.setPen(QPen(colors[index]))
            painter.setFont(
                QFont(
                    "Arial",
                    10,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    1490,
                    y - 2,
                    210,
                    26,
                ),
                int(0x0001 | 0x0080),
                f"{games} Spiele · {pct:.1f} %",
            )

        painter.end()
        return image

    def _render_full_consistency_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )
        charts = section_data.get(
            "charts",
            {},
        )

        if not (
            isinstance(facts, dict)
            and isinstance(charts, dict)
        ):
            return self._render_section_dict(
                section_data,
                section_key="consistency",
            )

        played = int(
            self._to_number(
                facts.get("Spiele", 0)
            )
        )
        close_matches = int(
            self._to_number(
                facts.get("Knappe Spiele", 0)
            )
        )
        close_pct = self._to_number(
            facts.get("Knappe Spiele %", 0)
        )
        clear_wins = int(
            self._to_number(
                facts.get("Klare Siege", 0)
            )
        )
        clear_losses = int(
            self._to_number(
                facts.get("Klare Niederlagen", 0)
            )
        )
        gd_stddev = self._to_number(
            facts.get("Streuung Tordifferenz", 0)
        )
        volatility = str(
            facts.get("Volatilität", "-")
        )
        ppg_spread = self._to_number(
            facts.get("PPG-Spannweite", 0)
        )

        best_block = section_data.get(
            "best_block"
        )
        worst_block = section_data.get(
            "worst_block"
        )

        resource_name = (
            "chart://consistency_"
            + str(len(self._image_resources))
        )
        self._image_resources[
            resource_name
        ] = self._create_consistency_chart_image(
            margin_rows=charts.get(
                "result_margins",
                [],
            ),
            form_blocks=charts.get(
                "form_blocks",
                [],
            ),
        )

        if close_pct >= 70:
            close_title = "Viele Spiele auf Messers Schneide"
            close_text = (
                f"{close_matches} von {played} Spielen "
                f"({self._format_value(close_pct)} %) endeten "
                "mit höchstens einem Tor Unterschied."
            )
        elif close_pct >= 50:
            close_title = "Viele enge Entscheidungen"
            close_text = (
                f"{close_matches} von {played} Spielen "
                f"({self._format_value(close_pct)} %) waren "
                "Remis oder Ein-Tor-Spiele."
            )
        else:
            close_title = "Ergebnisse häufig deutlicher"
            close_text = (
                f"Nur {close_matches} von {played} Spielen "
                f"({self._format_value(close_pct)} %) waren "
                "Remis oder Ein-Tor-Spiele."
            )

        if volatility.lower() == "hoch":
            vol_title = "Hohe Ergebnisschwankung"
        elif volatility.lower() == "niedrig":
            vol_title = "Relativ konstante Ergebnisabstände"
        else:
            vol_title = "Mittlere Ergebnisschwankung"

        vol_text = (
            f"Die Standardabweichung der Tordifferenz liegt bei "
            f"{self._format_value(gd_stddev)}. "
            f"Die Volatilität wird als {volatility} eingeordnet."
        )

        if ppg_spread >= 1.5:
            phase_title = "Starke Formschwankungen"
        elif ppg_spread >= 0.8:
            phase_title = "Spürbare Formschwankungen"
        else:
            phase_title = "Relativ stabile Saisonabschnitte"

        if (
            isinstance(best_block, dict)
            and isinstance(worst_block, dict)
        ):
            phase_text = (
                f"Bester Abschnitt: {best_block.get('label', '-')} "
                f"mit {self._format_value(best_block.get('ppg', 0))} "
                f"Pkt./Spiel. Schwächster: "
                f"{worst_block.get('label', '-')} mit "
                f"{self._format_value(worst_block.get('ppg', 0))} "
                f"Pkt./Spiel."
            )
        else:
            phase_text = (
                f"Die Spannweite der Punkteausbeute zwischen "
                f"Saisonabschnitten beträgt "
                f"{self._format_value(ppg_spread)} Pkt./Spiel."
            )

        return (
            '<table width="100%" class="consistency-kpis"><tr>'
            '<td>'
            '<div class="consistency-label">Knappe Spiele</div>'
            f'<div class="consistency-value">{close_matches}</div>'
            f'<div class="consistency-sub">{escape(self._format_value(close_pct))} % aller Spiele</div>'
            '</td>'
            '<td>'
            '<div class="consistency-label">Klare Siege</div>'
            f'<div class="consistency-value">{clear_wins}</div>'
            '<div class="consistency-sub">mit mindestens +2 Toren</div>'
            '</td>'
            '<td>'
            '<div class="consistency-label">Klare Niederlagen</div>'
            f'<div class="consistency-value">{clear_losses}</div>'
            '<div class="consistency-sub">mit mindestens -2 Toren</div>'
            '</td>'
            '<td>'
            '<div class="consistency-label">Ergebnisstreuung</div>'
            f'<div class="consistency-value">{escape(self._format_value(gd_stddev))}</div>'
            f'<div class="consistency-sub">Volatilität: {escape(volatility)}</div>'
            '</td>'
            '<td>'
            '<div class="consistency-label">PPG-Spannweite</div>'
            f'<div class="consistency-value">{escape(self._format_value(ppg_spread))}</div>'
            '<div class="consistency-sub">zwischen Saisonblöcken</div>'
            '</td>'
            '</tr></table>'
            '<div class="consistency-chart-card">'
            '<div class="consistency-chart-title">'
            'Ergebnismargen & Leistung über Saisonabschnitte'
            '</div>'
            '<div class="consistency-chart-note">'
            'Links: Verteilung der Ergebnisabstände · '
            'Rechts: Punkte pro Spiel in 5-Spiele-Blöcken'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<div class="consistency-insights-title">Kernaussagen</div>'
            '<table width="100%" class="consistency-insights"><tr>'
            '<td>'
            f'<div class="consistency-insight-title">{escape(close_title)}</div>'
            f'<div class="consistency-insight-text">{escape(close_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="consistency-insight-title">{escape(vol_title)}</div>'
            f'<div class="consistency-insight-text">{escape(vol_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="consistency-insight-title">{escape(phase_title)}</div>'
            f'<div class="consistency-insight-text">{escape(phase_text)}</div>'
            '</td>'
            '</tr></table>'
        )

    def _create_consistency_chart_image(
        self,
        margin_rows: list[dict[str, Any]],
        form_blocks: list[dict[str, Any]],
    ) -> QImage:
        width = 1800
        height = 520

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(QColor("#ffffff"))

        painter = QPainter(image)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        text = QColor("#25282c")
        muted = QColor("#737b84")
        border = QColor("#dfe3e7")
        green = QColor("#2f9e44")
        amber = QColor("#d99a00")
        red = QColor("#d94848")
        blue = QColor("#2f6fa3")
        track = QColor("#eef0f2")

        def panel(x, y, w, h, title):
            painter.setPen(QPen(border, 2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(
                QRectF(x, y, w, h),
                8,
                8,
            )
            painter.setPen(QPen(text))
            painter.setFont(
                QFont(
                    "Arial",
                    15,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x + 20,
                    y + 15,
                    w - 40,
                    32,
                ),
                int(0x0001 | 0x0080),
                title,
            )

        panel(
            25,
            30,
            720,
            450,
            "Ergebnisabstände",
        )
        panel(
            780,
            30,
            995,
            450,
            "Punkteausbeute nach Saisonabschnitten",
        )

        margin_colors = [
            green,
            green,
            amber,
            red,
            red,
        ]
        margin_values = [
            int(row.get("count", 0) or 0)
            for row in margin_rows[:5]
        ]
        max_margin = max([1] + margin_values)

        for index, row in enumerate(
            margin_rows[:5]
        ):
            label = str(
                row.get("label", "")
            )
            value = int(
                row.get("count", 0)
                or 0
            )
            y = 95 + index * 68

            painter.setPen(QPen(text))
            painter.setFont(
                QFont(
                    "Arial",
                    10,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    55,
                    y,
                    190,
                    24,
                ),
                int(0x0001 | 0x0080),
                label,
            )

            painter.fillRect(
                QRectF(
                    250,
                    y + 2,
                    365,
                    18,
                ),
                track,
            )
            painter.fillRect(
                QRectF(
                    250,
                    y + 2,
                    365 * value / max_margin,
                    18,
                ),
                margin_colors[index],
            )

            painter.setPen(
                QPen(margin_colors[index])
            )
            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    630,
                    y - 2,
                    55,
                    26,
                ),
                int(0x0002 | 0x0080),
                str(value),
            )

        blocks = form_blocks[:8]
        if blocks:
            graph_x = 835.0
            graph_y = 100.0
            graph_w = 875.0
            graph_h = 270.0
            max_ppg = 3.0

            # Horizontal reference lines.
            for value in (0, 1, 2, 3):
                y = (
                    graph_y
                    + graph_h
                    - graph_h
                    * value
                    / max_ppg
                )
                painter.setPen(
                    QPen(
                        border,
                        1,
                    )
                )
                painter.drawLine(
                    int(graph_x),
                    int(y),
                    int(graph_x + graph_w),
                    int(y),
                )
                painter.setPen(QPen(muted))
                painter.setFont(
                    QFont(
                        "Arial",
                        9,
                    )
                )
                painter.drawText(
                    QRectF(
                        graph_x - 35,
                        y - 10,
                        28,
                        20,
                    ),
                    int(0x0002 | 0x0080),
                    str(value),
                )

            gap = (
                graph_w
                / max(
                    len(blocks),
                    1,
                )
            )
            points = []

            for index, row in enumerate(blocks):
                ppg = float(
                    row.get("ppg", 0)
                    or 0
                )
                x = (
                    graph_x
                    + gap * index
                    + gap / 2
                )
                y = (
                    graph_y
                    + graph_h
                    - graph_h
                    * ppg
                    / max_ppg
                )
                points.append((x, y))

            painter.setPen(
                QPen(
                    blue,
                    5,
                )
            )
            for index in range(
                len(points) - 1
            ):
                painter.drawLine(
                    int(points[index][0]),
                    int(points[index][1]),
                    int(points[index + 1][0]),
                    int(points[index + 1][1]),
                )

            for index, row in enumerate(blocks):
                x, y = points[index]
                ppg = float(
                    row.get("ppg", 0)
                    or 0
                )

                painter.setBrush(blue)
                painter.setPen(QPen(blue))
                painter.drawEllipse(
                    QRectF(
                        x - 7,
                        y - 7,
                        14,
                        14,
                    )
                )

                painter.setFont(
                    QFont(
                        "Arial",
                        10,
                        QFont.Weight.Bold,
                    )
                )
                painter.drawText(
                    QRectF(
                        x - 38,
                        y - 34,
                        76,
                        24,
                    ),
                    int(0x0004 | 0x0080),
                    f"{ppg:.2f}",
                )

                painter.setPen(QPen(muted))
                painter.setFont(
                    QFont(
                        "Arial",
                        8,
                    )
                )
                painter.drawText(
                    QRectF(
                        x - gap / 2,
                        graph_y + graph_h + 14,
                        gap,
                        38,
                    ),
                    int(0x0004 | 0x0080),
                    str(
                        row.get(
                            "label",
                            "",
                        )
                    ),
                )

        painter.end()
        return image

    def _render_full_halftime_phases_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )
        charts = section_data.get(
            "charts",
            {},
        )

        if not (
            isinstance(
                facts,
                dict,
            )
            and isinstance(
                charts,
                dict,
            )
        ):
            return self._render_section_dict(
                section_data,
                section_key="halftime_phases",
            )

        matches_with_halftime = int(
            self._to_number(
                facts.get(
                    "Spiele mit Halbzeitstand",
                    0,
                )
            )
        )

        first_for = int(
            self._to_number(
                facts.get(
                    "Tore 1. HZ",
                    0,
                )
            )
        )
        first_against = int(
            self._to_number(
                facts.get(
                    "Gegentore 1. HZ",
                    0,
                )
            )
        )
        second_for = int(
            self._to_number(
                facts.get(
                    "Tore 2. HZ",
                    0,
                )
            )
        )
        second_against = int(
            self._to_number(
                facts.get(
                    "Gegentore 2. HZ",
                    0,
                )
            )
        )

        leading = int(
            self._to_number(
                facts.get(
                    "Halbzeitführung",
                    0,
                )
            )
        )
        drawing = int(
            self._to_number(
                facts.get(
                    "Halbzeitremis",
                    0,
                )
            )
        )
        trailing = int(
            self._to_number(
                facts.get(
                    "Halbzeitrückstand",
                    0,
                )
            )
        )

        lead_conversion = self._to_number(
            facts.get(
                "Führung gehalten %",
                0,
            )
        )
        dropped_after_lead = int(
            self._to_number(
                facts.get(
                    "Verlorene Punkte nach HZ-Führung",
                    0,
                )
            )
        )
        comeback_pct = self._to_number(
            facts.get(
                "Comeback-Quote nach HZ %",
                0,
            )
        )
        points_after_trail = int(
            self._to_number(
                facts.get(
                    "Punkte nach HZ-Rückstand",
                    0,
                )
            )
        )
        win_after_draw_pct = self._to_number(
            facts.get(
                "Siegquote nach HZ-Remis %",
                0,
            )
        )

        resource_name = (
            "chart://halftime_phases_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_halftime_phases_chart_image(
            half_goals=charts.get(
                "half_goals",
                [],
            ),
            halftime_states=charts.get(
                "halftime_states",
                [],
            ),
            after_lead=charts.get(
                "after_halftime_lead",
                [],
            ),
            after_draw=charts.get(
                "after_halftime_draw",
                [],
            ),
            after_trail=charts.get(
                "after_halftime_trail",
                [],
            ),
        )

        first_balance = (
            first_for
            - first_against
        )
        second_balance = (
            second_for
            - second_against
        )

        if second_balance > first_balance:
            half_title = "Nach der Pause verbessert"
            half_text = (
                f"Die Torbilanz verbessert sich von "
                f"{first_balance:+d} in der "
                f"1. Halbzeit auf "
                f"{second_balance:+d} nach der Pause."
            )
        elif second_balance < first_balance:
            half_title = "Nach der Pause schwächer"
            half_text = (
                f"Die Torbilanz fällt von "
                f"{first_balance:+d} in der "
                f"1. Halbzeit auf "
                f"{second_balance:+d} nach der Pause."
            )
        else:
            half_title = "Über beide Halbzeiten stabil"
            half_text = (
                f"Die Torbilanz ist in beiden Halbzeiten identisch "
                f"({first_balance:+d})."
            )

        if lead_conversion >= 80:
            lead_title = "Halbzeitführungen sehr stabil"
        elif lead_conversion >= 60:
            lead_title = "Halbzeitführungen meist genutzt"
        else:
            lead_title = "Halbzeitführungen bleiben riskant"

        lead_text = (
            f"{leading} Halbzeitführungen · "
            f"{self._format_value(lead_conversion)} % davon endeten mit Sieg. "
            f"Dabei gingen {dropped_after_lead} mögliche Punkte verloren."
        )

        if trailing <= 0:
            comeback_title = "Keine Halbzeitrückstände"
            comeback_text = (
                "Für diese Saison liegen keine auswertbaren "
                "Halbzeitrückstände vor."
            )
        elif comeback_pct >= 35:
            comeback_title = "Gute Reaktion auf Rückstände"
            comeback_text = (
                f"Aus {trailing} Halbzeitrückständen wurden noch "
                f"{points_after_trail} Punkte geholt "
                f"({self._format_value(comeback_pct)} % Comeback-Quote)."
            )
        elif comeback_pct >= 15:
            comeback_title = "Rückstände teilweise repariert"
            comeback_text = (
                f"Aus {trailing} Halbzeitrückständen wurden noch "
                f"{points_after_trail} Punkte geholt "
                f"({self._format_value(comeback_pct)} % Comeback-Quote)."
            )
        else:
            comeback_title = "Halbzeitrückstände selten gedreht"
            comeback_text = (
                f"Aus {trailing} Halbzeitrückständen wurden nur "
                f"{points_after_trail} Punkte geholt "
                f"({self._format_value(comeback_pct)} % Comeback-Quote)."
            )

        return (
            '<table width="100%" class="halftime-kpis"><tr>'
            '<td>'
            '<div class="halftime-label">1. Halbzeit</div>'
            f'<div class="halftime-value">{first_for}:{first_against}</div>'
            f'<div class="halftime-sub">Torbilanz {first_balance:+d}</div>'
            '</td>'
            '<td>'
            '<div class="halftime-label">2. Halbzeit</div>'
            f'<div class="halftime-value">{second_for}:{second_against}</div>'
            f'<div class="halftime-sub">Torbilanz {second_balance:+d}</div>'
            '</td>'
            '<td>'
            '<div class="halftime-label">HZ-Führungen</div>'
            f'<div class="halftime-value">{leading}</div>'
            f'<div class="halftime-sub">{escape(self._format_value(lead_conversion))} % gewonnen</div>'
            '</td>'
            '<td>'
            '<div class="halftime-label">HZ-Rückstände</div>'
            f'<div class="halftime-value">{trailing}</div>'
            f'<div class="halftime-sub">{points_after_trail} Punkte danach</div>'
            '</td>'
            '<td>'
            '<div class="halftime-label">HZ-Datenbasis</div>'
            f'<div class="halftime-value">{matches_with_halftime}</div>'
            '<div class="halftime-sub">Spiele mit Halbzeitstand</div>'
            '</td>'
            '</tr></table>'
            '<div class="halftime-chart-card">'
            '<div class="halftime-chart-title">'
            'Halbzeitenvergleich & Halbzeitstand → Endergebnis'
            '</div>'
            '<div class="halftime-chart-note">'
            'Torbilanz je Halbzeit · Verteilung der Halbzeitstände · '
            'Ausgang nach Führung, Remis oder Rückstand zur Pause'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<div class="halftime-insights-title">Kernaussagen</div>'
            '<table width="100%" class="halftime-insights"><tr>'
            '<td>'
            f'<div class="halftime-insight-title">{escape(half_title)}</div>'
            f'<div class="halftime-insight-text">{escape(half_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="halftime-insight-title">{escape(lead_title)}</div>'
            f'<div class="halftime-insight-text">{escape(lead_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="halftime-insight-title">{escape(comeback_title)}</div>'
            f'<div class="halftime-insight-text">{escape(comeback_text)}</div>'
            '</td>'
            '</tr></table>'
            '<div class="halftime-footnote">'
            f'Nach Halbzeitremis: Siegquote {escape(self._format_value(win_after_draw_pct))} %'
            '</div>'
        )

    def _create_halftime_phases_chart_image(
        self,
        half_goals: list[dict[str, Any]],
        halftime_states: list[dict[str, Any]],
        after_lead: list[dict[str, Any]],
        after_draw: list[dict[str, Any]],
        after_trail: list[dict[str, Any]],
    ) -> QImage:
        width = 1800
        height = 560

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        text = QColor("#25282c")
        muted = QColor("#737b84")
        border = QColor("#dfe3e7")
        green = QColor("#2f9e44")
        amber = QColor("#d99a00")
        red = QColor("#d94848")
        blue = QColor("#2f6fa3")
        grey = QColor("#eef0f2")

        def panel(
            x: float,
            y: float,
            w: float,
            h: float,
            title: str,
        ) -> None:
            painter.setPen(
                QPen(
                    border,
                    2,
                )
            )
            painter.setBrush(
                QColor("#ffffff")
            )
            painter.drawRoundedRect(
                QRectF(
                    x,
                    y,
                    w,
                    h,
                ),
                8,
                8,
            )
            painter.setPen(
                QPen(
                    text
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    15,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x + 18,
                    y + 14,
                    w - 36,
                    32,
                ),
                int(0x0001 | 0x0080),
                title,
            )

        # Top-left: first vs second half goals.
        panel(
            25,
            30,
            550,
            235,
            "Torbilanz je Halbzeit",
        )

        half_max = max(
            [1]
            + [
                int(row.get("goals_for", 0) or 0)
                for row in half_goals[:2]
            ]
            + [
                int(row.get("goals_against", 0) or 0)
                for row in half_goals[:2]
            ]
        )

        for index, row in enumerate(
            half_goals[:2]
        ):
            base_x = (
                105
                + index
                * 235
            )
            gf = int(
                row.get(
                    "goals_for",
                    0,
                )
                or 0
            )
            ga = int(
                row.get(
                    "goals_against",
                    0,
                )
                or 0
            )
            label = str(
                row.get(
                    "label",
                    "",
                )
            )

            graph_base = 210
            graph_height = 105

            gf_h = (
                graph_height
                * gf
                / half_max
            )
            ga_h = (
                graph_height
                * ga
                / half_max
            )

            painter.fillRect(
                QRectF(
                    base_x,
                    graph_base - gf_h,
                    55,
                    gf_h,
                ),
                green,
            )
            painter.fillRect(
                QRectF(
                    base_x + 68,
                    graph_base - ga_h,
                    55,
                    ga_h,
                ),
                red,
            )

            painter.setFont(
                QFont(
                    "Arial",
                    12,
                    QFont.Weight.Bold,
                )
            )
            painter.setPen(
                QPen(
                    green
                )
            )
            painter.drawText(
                QRectF(
                    base_x,
                    graph_base - gf_h - 27,
                    55,
                    24,
                ),
                int(0x0004 | 0x0080),
                str(gf),
            )
            painter.setPen(
                QPen(
                    red
                )
            )
            painter.drawText(
                QRectF(
                    base_x + 68,
                    graph_base - ga_h - 27,
                    55,
                    24,
                ),
                int(0x0004 | 0x0080),
                str(ga),
            )

            painter.setPen(
                QPen(
                    muted
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    10,
                )
            )
            painter.drawText(
                QRectF(
                    base_x - 30,
                    219,
                    180,
                    24,
                ),
                int(0x0004 | 0x0080),
                label,
            )

        painter.setFont(
            QFont(
                "Arial",
                9,
            )
        )
        painter.setPen(
            QPen(
                green
            )
        )
        painter.drawText(
            QRectF(
                35,
                185,
                70,
                20,
            ),
            int(0x0001 | 0x0080),
            "Tore",
        )
        painter.setPen(
            QPen(
                red
            )
        )
        painter.drawText(
            QRectF(
                35,
                205,
                90,
                20,
            ),
            int(0x0001 | 0x0080),
            "Gegentore",
        )

        # Top-right: halftime state distribution.
        panel(
            610,
            30,
            1165,
            235,
            "Spielstand zur Halbzeit",
        )

        state_colors = {
            "Führung": green,
            "Remis": amber,
            "Rückstand": red,
        }

        state_values = [
            int(
                row.get(
                    "count",
                    0,
                )
                or 0
            )
            for row in halftime_states[:3]
        ]
        state_total = sum(
            state_values
        )
        bar_x = 655.0
        bar_y = 105.0
        bar_w = 1070.0
        bar_h = 52.0
        current_x = bar_x

        for row in halftime_states[:3]:
            label = str(
                row.get(
                    "label",
                    "",
                )
            )
            value = int(
                row.get(
                    "count",
                    0,
                )
                or 0
            )
            part_w = (
                bar_w
                * value
                / state_total
                if state_total
                else 0
            )

            if part_w > 0:
                painter.fillRect(
                    QRectF(
                        current_x,
                        bar_y,
                        part_w,
                        bar_h,
                    ),
                    state_colors.get(
                        label,
                        blue,
                    ),
                )
                current_x += part_w

        legend_x = 680.0
        for index, row in enumerate(
            halftime_states[:3]
        ):
            label = str(
                row.get(
                    "label",
                    "",
                )
            )
            value = int(
                row.get(
                    "count",
                    0,
                )
                or 0
            )
            pct = (
                value
                / state_total
                * 100
                if state_total
                else 0
            )
            x = (
                legend_x
                + index
                * 330
            )

            painter.fillRect(
                QRectF(
                    x,
                    182,
                    18,
                    18,
                ),
                state_colors.get(
                    label,
                    blue,
                ),
            )
            painter.setPen(
                QPen(
                    text
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x + 28,
                    176,
                    280,
                    28,
                ),
                int(0x0001 | 0x0080),
                f"{label}: {value} ({pct:.1f} %)",
            )

        # Bottom: outcomes after HT state.
        bottom_y = 300.0
        panel(
            25,
            bottom_y,
            1750,
            225,
            "Vom Halbzeitstand zum Endergebnis",
        )

        groups = [
            (
                "Nach HZ-Führung",
                after_lead,
            ),
            (
                "Nach HZ-Remis",
                after_draw,
            ),
            (
                "Nach HZ-Rückstand",
                after_trail,
            ),
        ]
        outcome_colors = {
            "Sieg": green,
            "Remis": amber,
            "Niederlage": red,
        }

        for group_index, (
            title,
            rows,
        ) in enumerate(
            groups
        ):
            x = (
                70.0
                + group_index
                * 570.0
            )

            painter.setPen(
                QPen(
                    text
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x,
                    bottom_y + 58,
                    500,
                    28,
                ),
                int(0x0001 | 0x0080),
                title,
            )

            values = [
                int(
                    row.get(
                        "count",
                        0,
                    )
                    or 0
                )
                for row in rows[:3]
            ]
            max_value = max(
                [1]
                + values
            )

            for row_index, row in enumerate(
                rows[:3]
            ):
                label = str(
                    row.get(
                        "label",
                        "",
                    )
                )
                value = int(
                    row.get(
                        "count",
                        0,
                    )
                    or 0
                )
                yy = (
                    bottom_y
                    + 96
                    + row_index
                    * 37
                )

                painter.setPen(
                    QPen(
                        muted
                    )
                )
                painter.setFont(
                    QFont(
                        "Arial",
                        9,
                    )
                )
                painter.drawText(
                    QRectF(
                        x,
                        yy,
                        105,
                        22,
                    ),
                    int(0x0001 | 0x0080),
                    label,
                )

                painter.fillRect(
                    QRectF(
                        x + 105,
                        yy + 2,
                        285,
                        16,
                    ),
                    grey,
                )

                painter.fillRect(
                    QRectF(
                        x + 105,
                        yy + 2,
                        285
                        * value
                        / max_value,
                        16,
                    ),
                    outcome_colors.get(
                        label,
                        blue,
                    ),
                )

                painter.setPen(
                    QPen(
                        outcome_colors.get(
                            label,
                            blue,
                        )
                    )
                )
                painter.setFont(
                    QFont(
                        "Arial",
                        10,
                        QFont.Weight.Bold,
                    )
                )
                painter.drawText(
                    QRectF(
                        x + 405,
                        yy - 2,
                        55,
                        24,
                    ),
                    int(0x0002 | 0x0080),
                    str(value),
                )

        painter.end()

        return image

    def _render_full_control_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )
        charts = section_data.get(
            "charts",
            {},
        )

        if not (
            isinstance(
                facts,
                dict,
            )
            and isinstance(
                charts,
                dict,
            )
        ):
            return self._render_section_dict(
                section_data,
                section_key="control",
            )

        matches_leading = int(
            self._to_number(
                facts.get(
                    "Führungen",
                    0,
                )
            )
        )
        wins_after_leading = int(
            self._to_number(
                facts.get(
                    "Siege nach Führung",
                    0,
                )
            )
        )
        draws_after_leading = int(
            self._to_number(
                facts.get(
                    "Remis nach Führung",
                    0,
                )
            )
        )
        losses_after_leading = int(
            self._to_number(
                facts.get(
                    "Niederlagen nach Führung",
                    0,
                )
            )
        )
        dropped_points = int(
            self._to_number(
                facts.get(
                    "Punkte nach Führung verloren",
                    0,
                )
            )
        )
        lead_yield = self._to_number(
            facts.get(
                "Punktausbeute aus Führungen %",
                0,
            )
        )

        matches_trailing = int(
            self._to_number(
                facts.get(
                    "Rückstände",
                    0,
                )
            )
        )
        wins_after_trailing = int(
            self._to_number(
                facts.get(
                    "Siege nach Rückstand",
                    0,
                )
            )
        )
        draws_after_trailing = int(
            self._to_number(
                facts.get(
                    "Remis nach Rückstand",
                    0,
                )
            )
        )
        points_after_trailing = int(
            self._to_number(
                facts.get(
                    "Punkte nach Rückstand",
                    0,
                )
            )
        )
        comeback_pct = self._to_number(
            facts.get(
                "Comeback-Quote %",
                0,
            )
        )

        resource_name = (
            "chart://control_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_control_chart_image(
            lead_rows=charts.get(
                "lead_outcomes",
                [],
            ),
            trailing_rows=charts.get(
                "trailing_outcomes",
                [],
            ),
            points_rows=charts.get(
                "points_balance",
                [],
            ),
        )

        not_won_after_leading = (
            draws_after_leading
            + losses_after_leading
        )
        recovered_matches = (
            wins_after_trailing
            + draws_after_trailing
        )

        if lead_yield >= 80:
            lead_title = "Führungen werden gut genutzt"
        elif lead_yield >= 60:
            lead_title = "Führungsausbeute solide"
        else:
            lead_title = "Führungen kosten viele Punkte"

        lead_text = (
            f"{wins_after_leading} von {matches_leading} Führungen "
            f"wurden gewonnen. {dropped_points} mögliche Punkte "
            "gingen nach Führung verloren."
        )

        if comeback_pct >= 40:
            comeback_title = "Starke Reaktion auf Rückstände"
        elif comeback_pct >= 20:
            comeback_title = "Teilweise Comeback-Fähigkeit"
        else:
            comeback_title = "Rückstände kaum repariert"

        comeback_text = (
            f"{recovered_matches} von {matches_trailing} Rückständen "
            f"brachten noch Punkte. Insgesamt wurden "
            f"{points_after_trailing} Punkte nach Rückstand geholt."
        )

        net_balance = (
            points_after_trailing
            - dropped_points
        )

        if net_balance > 0:
            balance_title = "Comebacks gleichen Verluste aus"
            balance_text = (
                f"Gerettete Punkte nach Rückstand übersteigen "
                f"die verlorenen Punkte nach Führung um "
                f"{net_balance}."
            )
        elif net_balance < 0:
            balance_title = "Netto Punkte liegen gelassen"
            balance_text = (
                f"Nach Führungen gingen netto "
                f"{abs(net_balance)} Punkte mehr verloren, "
                "als nach Rückständen gerettet wurden."
            )
        else:
            balance_title = "Ausgeglichene Kontrollbilanz"
            balance_text = (
                "Gerettete Punkte nach Rückstand und verlorene "
                "Punkte nach Führung halten sich die Waage."
            )

        return (
            '<table width="100%" class="control-kpis"><tr>'
            '<td>'
            '<div class="control-label">Führungen</div>'
            f'<div class="control-value">{matches_leading}</div>'
            f'<div class="control-sub">{wins_after_leading} gewonnen</div>'
            '</td>'
            '<td>'
            '<div class="control-label">Verlorene Punkte</div>'
            f'<div class="control-value control-negative">{dropped_points}</div>'
            '<div class="control-sub">nach Führung</div>'
            '</td>'
            '<td>'
            '<div class="control-label">Führungsausbeute</div>'
            f'<div class="control-value">{escape(self._format_value(lead_yield))} %</div>'
            f'<div class="control-sub">{not_won_after_leading}× Führung nicht gewonnen</div>'
            '</td>'
            '<td>'
            '<div class="control-label">Rückstände</div>'
            f'<div class="control-value">{matches_trailing}</div>'
            f'<div class="control-sub">{recovered_matches}× noch gepunktet</div>'
            '</td>'
            '<td>'
            '<div class="control-label">Gerettete Punkte</div>'
            f'<div class="control-value control-positive">{points_after_trailing}</div>'
            '<div class="control-sub">nach Rückstand</div>'
            '</td>'
            '</tr></table>'
            '<div class="control-chart-card">'
            '<div class="control-chart-title">'
            'Führung verwalten & Rückstände reparieren'
            '</div>'
            '<div class="control-chart-note">'
            'Links: Spielausgänge nach eigener Führung · '
            'Mitte: Spielausgänge nach Rückstand · '
            'Rechts: Punktebilanz'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<div class="control-insights-title">Kernaussagen</div>'
            '<table width="100%" class="control-insights"><tr>'
            '<td>'
            f'<div class="control-insight-title">{escape(lead_title)}</div>'
            f'<div class="control-insight-text">{escape(lead_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="control-insight-title">{escape(comeback_title)}</div>'
            f'<div class="control-insight-text">{escape(comeback_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="control-insight-title">{escape(balance_title)}</div>'
            f'<div class="control-insight-text">{escape(balance_text)}</div>'
            '</td>'
            '</tr></table>'
        )

    def _create_control_chart_image(
        self,
        lead_rows: list[dict[str, Any]],
        trailing_rows: list[dict[str, Any]],
        points_rows: list[dict[str, Any]],
    ) -> QImage:
        width = 1800
        height = 500

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        text_color = QColor(
            "#25282c"
        )
        muted = QColor(
            "#737b84"
        )
        border = QColor(
            "#dfe3e7"
        )
        green = QColor(
            "#2f9e44"
        )
        amber = QColor(
            "#d99a00"
        )
        red = QColor(
            "#d94848"
        )
        blue = QColor(
            "#2f6fa3"
        )
        track = QColor(
            "#eef0f2"
        )

        panels = [
            (
                35.0,
                42.0,
                540.0,
                410.0,
                "Nach eigener Führung",
            ),
            (
                630.0,
                42.0,
                540.0,
                410.0,
                "Nach Rückstand",
            ),
            (
                1225.0,
                42.0,
                540.0,
                410.0,
                "Punktebilanz",
            ),
        ]

        for x, y, w, h, title in panels:
            painter.setPen(
                QPen(
                    border,
                    2,
                )
            )
            painter.setBrush(
                QColor(
                    "#ffffff"
                )
            )
            painter.drawRoundedRect(
                QRectF(
                    x,
                    y,
                    w,
                    h,
                ),
                8,
                8,
            )
            painter.setPen(
                QPen(
                    text_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    16,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x + 22,
                    y + 18,
                    w - 44,
                    34,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                title,
            )

        def draw_outcomes(
            x: float,
            y: float,
            rows: list[dict[str, Any]],
        ) -> None:
            colors = {
                "Sieg": green,
                "Remis": amber,
                "Niederlage": red,
            }

            values = [
                int(
                    row.get(
                        "count",
                        0,
                    )
                    or 0
                )
                for row in rows[:3]
            ]
            max_value = max(
                [1]
                + values
            )

            row_y = (
                y
                + 82
            )

            for index, row in enumerate(
                rows[:3]
            ):
                label = str(
                    row.get(
                        "label",
                        "",
                    )
                )
                value = int(
                    row.get(
                        "count",
                        0,
                    )
                    or 0
                )
                yy = (
                    row_y
                    + index
                    * 88
                )

                painter.setPen(
                    QPen(
                        text_color
                    )
                )
                painter.setFont(
                    QFont(
                        "Arial",
                        13,
                        QFont.Weight.Bold,
                    )
                )
                painter.drawText(
                    QRectF(
                        x + 24,
                        yy,
                        130,
                        28,
                    ),
                    int(
                        0x0001
                        | 0x0080
                    ),
                    label,
                )

                painter.fillRect(
                    QRectF(
                        x + 155,
                        yy + 2,
                        280,
                        20,
                    ),
                    track,
                )

                painter.fillRect(
                    QRectF(
                        x + 155,
                        yy + 2,
                        280
                        * value
                        / max_value,
                        20,
                    ),
                    colors.get(
                        label,
                        blue,
                    ),
                )

                painter.setPen(
                    QPen(
                        colors.get(
                            label,
                            blue,
                        )
                    )
                )
                painter.setFont(
                    QFont(
                        "Arial",
                        14,
                        QFont.Weight.Bold,
                    )
                )
                painter.drawText(
                    QRectF(
                        x + 450,
                        yy - 3,
                        60,
                        32,
                    ),
                    int(
                        0x0002
                        | 0x0080
                    ),
                    str(
                        value
                    ),
                )

        draw_outcomes(
            panels[0][0],
            panels[0][1],
            lead_rows,
        )
        draw_outcomes(
            panels[1][0],
            panels[1][1],
            trailing_rows,
        )

        points_x = panels[
            2
        ][
            0
        ]
        points_y = panels[
            2
        ][
            1
        ]

        point_values = [
            int(
                row.get(
                    "value",
                    0,
                )
                or 0
            )
            for row in points_rows[:3]
        ]
        max_points = max(
            [1]
            + point_values
        )

        point_colors = [
            blue,
            red,
            green,
        ]

        base_y = (
            points_y
            + 340
        )
        chart_height = 210.0
        gap = 26.0
        bar_width = 125.0

        for index, row in enumerate(
            points_rows[:3]
        ):
            value = int(
                row.get(
                    "value",
                    0,
                )
                or 0
            )
            label = str(
                row.get(
                    "label",
                    "",
                )
            )
            x = (
                points_x
                + 55
                + index
                * (
                    bar_width
                    + gap
                )
            )
            h = (
                chart_height
                * value
                / max_points
            )
            y = (
                base_y
                - h
            )

            painter.fillRect(
                QRectF(
                    x,
                    y,
                    bar_width,
                    h,
                ),
                point_colors[
                    index
                ],
            )

            painter.setPen(
                QPen(
                    point_colors[
                        index
                    ]
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    15,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x,
                    y - 31,
                    bar_width,
                    28,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                str(
                    value
                ),
            )

            compact = (
                label
                .replace(
                    "Punkte aus ",
                    ""
                )
                .replace(
                    "Punkte nach ",
                    ""
                )
            )

            painter.setPen(
                QPen(
                    muted
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    10,
                )
            )
            painter.drawText(
                QRectF(
                    x - 8,
                    base_y + 8,
                    bar_width + 16,
                    46,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                compact,
            )

        painter.end()

        return image

    def _render_full_patterns_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        facts = section_data.get(
            "facts",
            {},
        )
        charts = section_data.get(
            "charts",
            {},
        )
        tables = section_data.get(
            "tables",
            [],
        )

        if not (
            isinstance(
                facts,
                dict,
            )
            and isinstance(
                charts,
                dict,
            )
        ):
            return self._render_section_dict(
                section_data,
                section_key="patterns",
            )

        played = int(
            self._to_number(
                facts.get(
                    "Spiele",
                    0,
                )
            )
        )
        clean_sheets = int(
            self._to_number(
                facts.get(
                    "Zu Null",
                    0,
                )
            )
        )
        scoreless = int(
            self._to_number(
                facts.get(
                    "Ohne eigenes Tor",
                    0,
                )
            )
        )
        btts = int(
            self._to_number(
                facts.get(
                    "Beide treffen",
                    0,
                )
            )
        )
        avg_total = self._to_number(
            facts.get(
                "Ø Gesamttore / Spiel",
                0,
            )
        )
        scored_first = int(
            self._to_number(
                facts.get(
                    "Erstes Tor erzielt",
                    0,
                )
            )
        )
        conceded_first = int(
            self._to_number(
                facts.get(
                    "Erstes Tor kassiert",
                    0,
                )
            )
        )

        threshold_rows = charts.get(
            "goal_thresholds",
            [],
        )
        margin_rows = charts.get(
            "result_margins",
            [],
        )

        if not isinstance(
            threshold_rows,
            list,
        ):
            threshold_rows = []

        if not isinstance(
            margin_rows,
            list,
        ):
            margin_rows = []

        resource_name = (
            "chart://patterns_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_patterns_chart_image(
            threshold_rows=threshold_rows,
            margin_rows=margin_rows,
        )

        if scored_first > conceded_first:
            opening_title = "Häufiger selbst eröffnet"
            opening_text = (
                f"{scored_first} Spiele mit eigenem ersten Tor "
                f"gegenüber {conceded_first} mit erstem Gegentor."
            )
        elif conceded_first > scored_first:
            opening_title = "Häufiger in Rückstand geraten"
            opening_text = (
                f"{conceded_first} Spiele mit erstem Gegentor "
                f"gegenüber {scored_first} mit eigener Toreröffnung."
            )
        else:
            opening_title = "Ausgeglichene Toreröffnung"
            opening_text = (
                f"Je {scored_first} Spiele wurden selbst bzw. "
                "vom Gegner eröffnet."
            )

        btts_pct = self._to_number(
            facts.get(
                "Beide treffen %",
                0,
            )
        )
        over25_pct = self._to_number(
            facts.get(
                "Over 2,5 %",
                0,
            )
        )

        if over25_pct >= 60:
            goals_title = "Torreiche Spielstruktur"
            goals_text = (
                f"In {self._format_value(over25_pct)} % der Spiele "
                "fielen mindestens drei Tore."
            )
        elif over25_pct <= 40:
            goals_title = "Eher torarme Spielstruktur"
            goals_text = (
                f"Nur {self._format_value(over25_pct)} % der Spiele "
                "erreichten mindestens drei Tore."
            )
        else:
            goals_title = "Gemischte Torstruktur"
            goals_text = (
                f"{self._format_value(over25_pct)} % der Spiele "
                "hatten mindestens drei Tore."
            )

        if btts_pct >= 60:
            btts_title = "Beide Teams häufig erfolgreich"
        elif btts_pct <= 40:
            btts_title = "Oft nur eine Seite erfolgreich"
        else:
            btts_title = "Ausgewogene Trefferverteilung"

        btts_text = (
            f"In {btts} von {played} Spielen trafen beide Teams "
            f"({self._format_value(btts_pct)} %)."
        )

        scoreline_cards: list[str] = []

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
            headers = tables[
                0
            ].get(
                "headers",
                [],
            )

            for row in tables[
                0
            ].get(
                "rows",
                [],
            )[:5]:
                values = self._table_values(
                    headers,
                    row,
                )

                if len(
                    values
                ) < 3:
                    continue

                scoreline_cards.append(
                    '<td>'
                    '<div class="patterns-scoreline">'
                    f'{escape(str(values[0]))}'
                    '</div>'
                    '<div class="patterns-scoreline-count">'
                    f'{escape(str(values[1]))}×'
                    '</div>'
                    '<div class="patterns-scoreline-share">'
                    f'{escape(self._format_value(values[2]))} %'
                    '</div>'
                    '</td>'
                )

        while len(
            scoreline_cards
        ) < 5:
            scoreline_cards.append(
                '<td></td>'
            )

        return (
            '<table width="100%" class="patterns-kpis"><tr>'
            '<td>'
            '<div class="patterns-label">Zu Null</div>'
            f'<div class="patterns-value">{clean_sheets}</div>'
            f'<div class="patterns-sub">{escape(self._format_value(facts.get("Zu Null %", 0)))} %</div>'
            '</td>'
            '<td>'
            '<div class="patterns-label">Ohne eigenes Tor</div>'
            f'<div class="patterns-value">{scoreless}</div>'
            f'<div class="patterns-sub">{escape(self._format_value(facts.get("Ohne eigenes Tor %", 0)))} %</div>'
            '</td>'
            '<td>'
            '<div class="patterns-label">Beide treffen</div>'
            f'<div class="patterns-value">{btts}</div>'
            f'<div class="patterns-sub">{escape(self._format_value(btts_pct))} %</div>'
            '</td>'
            '<td>'
            '<div class="patterns-label">Ø Gesamttore</div>'
            f'<div class="patterns-value">{escape(self._format_value(avg_total))}</div>'
            '<div class="patterns-sub">pro Spiel</div>'
            '</td>'
            '<td>'
            '<div class="patterns-label">Selbst eröffnet</div>'
            f'<div class="patterns-value">{scored_first}</div>'
            f'<div class="patterns-sub">von {played} Spielen</div>'
            '</td>'
            '</tr></table>'
            '<div class="patterns-chart-card">'
            '<div class="patterns-chart-title">'
            'Torwahrscheinlichkeit & Ergebnismargen'
            '</div>'
            '<div class="patterns-chart-note">'
            'Links: Anteil der Spiele über Tor-Schwellen · '
            'Rechts: Verteilung nach Ergebnisabstand'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<div class="patterns-score-title">Häufigste Ergebnisse</div>'
            '<table width="100%" class="patterns-scorecards"><tr>'
            + "".join(
                scoreline_cards
            )
            + '</tr></table>'
            '<div class="patterns-insights-title">Kernaussagen</div>'
            '<table width="100%" class="patterns-insights"><tr>'
            '<td>'
            f'<div class="patterns-insight-title">{escape(opening_title)}</div>'
            f'<div class="patterns-insight-text">{escape(opening_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="patterns-insight-title">{escape(goals_title)}</div>'
            f'<div class="patterns-insight-text">{escape(goals_text)}</div>'
            '</td>'
            '<td>'
            f'<div class="patterns-insight-title">{escape(btts_title)}</div>'
            f'<div class="patterns-insight-text">{escape(btts_text)}</div>'
            '</td>'
            '</tr></table>'
        )

    def _create_patterns_chart_image(
        self,
        threshold_rows: list[dict[str, Any]],
        margin_rows: list[dict[str, Any]],
    ) -> QImage:
        width = 1800
        height = 500

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        text_color = QColor(
            "#25282c"
        )
        muted_color = QColor(
            "#737b84"
        )
        grid_color = QColor(
            "#e7eaed"
        )
        blue = QColor(
            "#2f6fa3"
        )
        green = QColor(
            "#2f9e44"
        )
        amber = QColor(
            "#d99a00"
        )
        red = QColor(
            "#d94848"
        )

        # Left panel: percentage bars.
        left_x = 45.0
        left_y = 42.0
        panel_width = 805.0
        panel_height = 405.0

        painter.setPen(
            QPen(
                QColor(
                    "#dfe3e7"
                ),
                2,
            )
        )
        painter.drawRoundedRect(
            QRectF(
                left_x,
                left_y,
                panel_width,
                panel_height,
            ),
            8,
            8,
        )

        painter.setPen(
            QPen(
                text_color
            )
        )
        painter.setFont(
            QFont(
                "Arial",
                17,
                QFont.Weight.Bold,
            )
        )
        painter.drawText(
            QRectF(
                left_x + 25,
                left_y + 18,
                panel_width - 50,
                34,
            ),
            int(
                0x0001
                | 0x0080
            ),
            "Tor-Schwellen",
        )

        row_y = (
            left_y
            + 77
        )
        row_height = 74.0
        label_width = 165.0
        bar_x = (
            left_x
            + 210
        )
        bar_width = (
            panel_width
            - 300
        )

        for index, row in enumerate(
            threshold_rows[:4]
        ):
            y = (
                row_y
                + index
                * row_height
            )
            label = str(
                row.get(
                    "label",
                    "",
                )
            )
            pct = max(
                0.0,
                min(
                    100.0,
                    float(
                        row.get(
                            "percentage",
                            0.0,
                        )
                        or 0.0
                    ),
                ),
            )
            count = int(
                row.get(
                    "count",
                    0,
                )
                or 0
            )

            painter.setPen(
                QPen(
                    text_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    14,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    left_x + 25,
                    y,
                    label_width,
                    30,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                label,
            )

            painter.fillRect(
                QRectF(
                    bar_x,
                    y + 3,
                    bar_width,
                    20,
                ),
                grid_color,
            )

            color = (
                green
                if index == 3
                else blue
            )

            painter.fillRect(
                QRectF(
                    bar_x,
                    y + 3,
                    bar_width
                    * pct
                    / 100.0,
                    20,
                ),
                color,
            )

            painter.setPen(
                QPen(
                    muted_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    12,
                )
            )
            painter.drawText(
                QRectF(
                    bar_x,
                    y + 29,
                    bar_width,
                    27,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                f"{pct:.1f} % · {count} Spiele",
            )

        # Right panel: result margins.
        right_x = 900.0
        right_y = left_y
        right_width = 855.0
        right_height = panel_height

        painter.setPen(
            QPen(
                QColor(
                    "#dfe3e7"
                ),
                2,
            )
        )
        painter.drawRoundedRect(
            QRectF(
                right_x,
                right_y,
                right_width,
                right_height,
            ),
            8,
            8,
        )

        painter.setPen(
            QPen(
                text_color
            )
        )
        painter.setFont(
            QFont(
                "Arial",
                17,
                QFont.Weight.Bold,
            )
        )
        painter.drawText(
            QRectF(
                right_x + 25,
                right_y + 18,
                right_width - 50,
                34,
            ),
            int(
                0x0001
                | 0x0080
            ),
            "Ergebnismargen",
        )

        values = [
            int(
                row.get(
                    "count",
                    0,
                )
                or 0
            )
            for row in margin_rows[:5]
        ]
        max_value = max(
            [1]
            + values
        )

        base_y = (
            right_y
            + right_height
            - 65
        )
        chart_top = (
            right_y
            + 82
        )
        chart_height = (
            base_y
            - chart_top
        )
        gap = 22.0
        count_bars = max(
            1,
            min(
                5,
                len(
                    margin_rows
                ),
            )
        )
        bar_width_2 = (
            right_width
            - 80
            - gap
            * (
                count_bars
                - 1
            )
        ) / count_bars

        colors = [
            green,
            green,
            amber,
            red,
            red,
        ]

        for index, row in enumerate(
            margin_rows[:5]
        ):
            value = int(
                row.get(
                    "count",
                    0,
                )
                or 0
            )
            label = str(
                row.get(
                    "label",
                    "",
                )
            )

            x = (
                right_x
                + 40
                + index
                * (
                    bar_width_2
                    + gap
                )
            )
            bar_height = (
                chart_height
                * value
                / max_value
            )
            y = (
                base_y
                - bar_height
            )

            painter.fillRect(
                QRectF(
                    x,
                    y,
                    bar_width_2,
                    bar_height,
                ),
                colors[
                    index
                ],
            )

            painter.setPen(
                QPen(
                    colors[
                        index
                    ]
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    14,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x,
                    max(
                        chart_top - 5,
                        y - 31,
                    ),
                    bar_width_2,
                    28,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                str(
                    value
                ),
            )

            painter.setPen(
                QPen(
                    muted_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    10,
                )
            )

            compact_label = (
                label
                .replace(
                    " oder mehr",
                    "+"
                )
                .replace(
                    "Niederlage",
                    "Ndl."
                )
            )

            painter.drawText(
                QRectF(
                    x - 10,
                    base_y + 9,
                    bar_width_2 + 20,
                    44,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                compact_label,
            )

        painter.end()

        return image

    def _render_full_results_visual(
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

        if (
            not isinstance(
                tables,
                list,
            )
            or not tables
            or not isinstance(
                tables[0],
                dict,
            )
        ):
            return self._render_results_dashboard(
                section_data
            )

        table = tables[0]
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

        if not headers or not rows:
            return self._render_results_dashboard(
                section_data
            )

        normalized = [
            str(
                header
            ).strip().casefold()
            for header in headers
        ]

        def find_index(
            *names: str,
        ) -> int | None:
            for name in names:
                name_cf = name.casefold()

                if name_cf in normalized:
                    return normalized.index(
                        name_cf
                    )

            return None

        matchday_idx = find_index(
            "st",
            "spieltag",
        )
        date_idx = find_index(
            "datum",
        )
        match_idx = find_index(
            "spiel",
        )
        score_idx = find_index(
            "ergebnis",
        )
        status_idx = find_index(
            "w/u/n",
            "form",
            "status",
        )

        parsed: list[dict[str, str]] = []

        for row in rows:
            values = self._table_values(
                headers,
                row,
            )

            def get_value(
                index: int | None,
            ) -> str:
                if (
                    index is None
                    or index >= len(
                        values
                    )
                ):
                    return ""

                return str(
                    values[
                        index
                    ]
                ).strip()

            status = get_value(
                status_idx
            ).upper()

            if status not in {
                "S",
                "U",
                "N",
            }:
                continue

            parsed.append(
                {
                    "matchday": get_value(
                        matchday_idx
                    ),
                    "date": get_value(
                        date_idx
                    ),
                    "match": get_value(
                        match_idx
                    ),
                    "score": get_value(
                        score_idx
                    ),
                    "status": status,
                }
            )

        if not parsed:
            return self._render_results_dashboard(
                section_data
            )

        wins = sum(
            row[
                "status"
            ] == "S"
            for row in parsed
        )
        draws = sum(
            row[
                "status"
            ] == "U"
            for row in parsed
        )
        losses = sum(
            row[
                "status"
            ] == "N"
            for row in parsed
        )

        total = len(
            parsed
        )
        points = (
            wins * 3
            + draws
        )
        points_per_game = (
            points
            / total
            if total
            else 0.0
        )

        resource_name = (
            "chart://results_dashboard_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_results_dashboard_image(
            parsed
        )

        recent = parsed[
            -5:
        ]

        recent_html = []

        status_colors = {
            "S": "#2f9e44",
            "U": "#d99a00",
            "N": "#d94848",
        }

        for row in recent:
            color = status_colors[
                row[
                    "status"
                ]
            ]

            recent_html.append(
                '<tr>'
                f'<td class="recent-result-status" style="color:{color};">'
                f'● {escape(row["status"])}'
                '</td>'
                f'<td>{escape(row["matchday"])}</td>'
                f'<td>{escape(row["match"])}</td>'
                f'<td class="recent-result-score">{escape(row["score"])}</td>'
                '</tr>'
            )

        form_string = " ".join(
            row[
                "status"
            ]
            for row in recent
        )

        best_run = self._longest_result_run(
            parsed,
            "S",
        )
        unbeaten_run = self._longest_unbeaten_run(
            parsed
        )

        goal_difference = (
            facts.get(
                "Tordifferenz",
                "–",
            )
            if isinstance(
                facts,
                dict,
            )
            else "–"
        )

        return (
            '<table width="100%" class="results-story-kpis"><tr>'
            '<td>'
            '<div class="results-story-label">Saisonbilanz</div>'
            f'<div class="results-story-value">{wins}-{draws}-{losses}</div>'
            '<div class="results-story-sub">S · U · N</div>'
            '</td>'
            '<td>'
            '<div class="results-story-label">Punkte</div>'
            f'<div class="results-story-value">{points}</div>'
            f'<div class="results-story-sub">{points_per_game:.2f} pro Spiel</div>'
            '</td>'
            '<td>'
            '<div class="results-story-label">Tordifferenz</div>'
            f'<div class="results-story-value">{escape(self._format_value(goal_difference))}</div>'
            '</td>'
            '<td>'
            '<div class="results-story-label">Längste Siegesserie</div>'
            f'<div class="results-story-value">{best_run}</div>'
            '<div class="results-story-sub">Spiele</div>'
            '</td>'
            '<td>'
            '<div class="results-story-label">Ungeschlagen max.</div>'
            f'<div class="results-story-value">{unbeaten_run}</div>'
            '<div class="results-story-sub">Spiele</div>'
            '</td>'
            '</tr></table>'
            '<div class="results-dashboard-chart">'
            '<div class="results-dashboard-title">'
            'Ergebnisverlauf der Saison'
            '</div>'
            '<div class="results-dashboard-note">'
            'Jedes Feld entspricht einem absolvierten Spiel · '
            'grün = Sieg, gelb = Remis, rot = Niederlage'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<table width="100%" class="results-story-bottom"><tr>'
            '<td width="68%">'
            '<div class="results-bottom-title">Letzte 5 Spiele</div>'
            '<table width="100%" class="recent-results-table">'
            '<tbody>'
            + "".join(
                recent_html
            )
            + '</tbody></table>'
            '</td>'
            '<td width="32%">'
            '<div class="results-bottom-title">Aktuelle Form</div>'
            f'<div class="results-form-string">{escape(form_string)}</div>'
            f'<div class="results-form-note">{wins} Siege · {draws} Remis · {losses} Niederlagen über die Saison</div>'
            '</td>'
            '</tr></table>'
            '<div class="results-appendix-hint">'
            'Die vollständige Liste aller Saisonspiele befindet sich im Datenanhang.'
            '</div>'
        )

    @staticmethod
    def _longest_result_run(
        rows: list[dict[str, str]],
        target: str,
    ) -> int:
        best = 0
        current = 0

        for row in rows:
            if row.get(
                "status"
            ) == target:
                current += 1
                best = max(
                    best,
                    current,
                )
            else:
                current = 0

        return best

    @staticmethod
    def _longest_unbeaten_run(
        rows: list[dict[str, str]],
    ) -> int:
        best = 0
        current = 0

        for row in rows:
            if row.get(
                "status"
            ) in {
                "S",
                "U",
            }:
                current += 1
                best = max(
                    best,
                    current,
                )
            else:
                current = 0

        return best

    def _create_results_dashboard_image(
        self,
        rows: list[dict[str, str]],
    ) -> QImage:
        width = 1800
        height = 470

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        colors = {
            "S": QColor(
                "#2f9e44"
            ),
            "U": QColor(
                "#d99a00"
            ),
            "N": QColor(
                "#d94848"
            ),
        }

        wins = sum(
            row[
                "status"
            ] == "S"
            for row in rows
        )
        draws = sum(
            row[
                "status"
            ] == "U"
            for row in rows
        )
        losses = sum(
            row[
                "status"
            ] == "N"
            for row in rows
        )

        total = max(
            1,
            len(
                rows
            ),
        )

        left = 55.0
        right = 55.0
        usable_width = (
            width
            - left
            - right
        )

        # Distribution bar.
        bar_y = 45.0
        bar_h = 52.0
        cursor = left

        for status, count in (
            (
                "S",
                wins,
            ),
            (
                "U",
                draws,
            ),
            (
                "N",
                losses,
            ),
        ):
            segment_width = (
                usable_width
                * count
                / total
            )

            if segment_width > 0:
                painter.fillRect(
                    QRectF(
                        cursor,
                        bar_y,
                        segment_width,
                        bar_h,
                    ),
                    colors[
                        status
                    ],
                )

            cursor += segment_width

        painter.setFont(
            QFont(
                "Arial",
                15,
                QFont.Weight.Bold,
            )
        )

        legend_y = 116.0
        legend_x = left

        for status, label, count in (
            (
                "S",
                "Siege",
                wins,
            ),
            (
                "U",
                "Remis",
                draws,
            ),
            (
                "N",
                "Niederlagen",
                losses,
            ),
        ):
            painter.setBrush(
                colors[
                    status
                ]
            )
            painter.setPen(
                QPen(
                    colors[
                        status
                    ]
                )
            )
            painter.drawEllipse(
                QPointF(
                    legend_x + 8,
                    legend_y + 8,
                ),
                7,
                7,
            )

            painter.setPen(
                QPen(
                    QColor(
                        "#4f565e"
                    )
                )
            )
            painter.drawText(
                QRectF(
                    legend_x + 24,
                    legend_y - 5,
                    220,
                    30,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                f"{label}: {count}",
            )

            legend_x += 250

        # Match strip in two rows.
        cols = 17
        gap = 10.0
        box_width = (
            usable_width
            - gap
            * (
                cols
                - 1
            )
        ) / cols
        box_height = 88.0
        start_y = 190.0

        for index, row in enumerate(
            rows
        ):
            line = (
                index
                // cols
            )
            column = (
                index
                % cols
            )

            x = (
                left
                + column
                * (
                    box_width
                    + gap
                )
            )
            y = (
                start_y
                + line
                * 118.0
            )

            color = colors[
                row[
                    "status"
                ]
            ]

            painter.setPen(
                QPen(
                    color,
                    2,
                )
            )
            painter.setBrush(
                QColor(
                    "#ffffff"
                )
            )
            painter.drawRoundedRect(
                QRectF(
                    x,
                    y,
                    box_width,
                    box_height,
                ),
                7,
                7,
            )

            painter.fillRect(
                QRectF(
                    x,
                    y,
                    box_width,
                    13,
                ),
                color,
            )

            painter.setPen(
                QPen(
                    QColor(
                        "#777f88"
                    )
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    11,
                )
            )
            painter.drawText(
                QRectF(
                    x,
                    y + 19,
                    box_width,
                    24,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                row.get(
                    "matchday",
                    str(
                        index + 1
                    ),
                ),
            )

            painter.setPen(
                QPen(
                    color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    16,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    x,
                    y + 43,
                    box_width,
                    30,
                ),
                int(
                    0x0004
                    | 0x0080
                ),
                row[
                    "status"
                ],
            )

        painter.end()

        return image

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

    def _render_full_players_visual(
        self,
        section_data: dict[str, Any],
    ) -> str:
        tables = section_data.get(
            "tables",
            [],
        )

        if (
            not isinstance(
                tables,
                list,
            )
            or not tables
            or not isinstance(
                tables[0],
                dict,
            )
        ):
            return self._render_section_dict(
                section_data,
                section_key="players",
            )

        table = tables[0]
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

        if not headers or not rows:
            return self._render_section_dict(
                section_data,
                section_key="players",
            )

        normalized_headers = [
            str(
                header
            ).strip().lower()
            for header in headers
        ]

        def header_index(
            *names: str,
        ) -> int | None:
            for name in names:
                normalized_name = (
                    name.strip().lower()
                )

                if normalized_name in normalized_headers:
                    return normalized_headers.index(
                        normalized_name
                    )

            return None

        player_idx = header_index(
            "spieler",
            "name",
        )
        appearances_idx = header_index(
            "eins.",
            "einsätze",
            "eins",
        )
        starts_idx = header_index(
            "start",
            "startelf",
        )
        minutes_idx = header_index(
            "min.",
            "minuten",
            "min",
        )
        goals_idx = header_index(
            "tore",
        )
        yellow_idx = header_index(
            "gelb",
        )
        yellow_red_idx = header_index(
            "g-r",
            "gelb-rot",
            "gelb-rote",
        )
        red_idx = header_index(
            "rot",
        )

        if player_idx is None:
            return self._render_section_dict(
                section_data,
                section_key="players",
            )

        players: dict[str, dict[str, int]] = {}

        for row in rows:
            values = self._table_values(
                headers,
                row,
            )

            if player_idx >= len(
                values
            ):
                continue

            name = str(
                values[
                    player_idx
                ]
            ).strip()

            if not name:
                continue

            current = players.setdefault(
                name,
                {
                    "appearances": 0,
                    "starts": 0,
                    "minutes": 0,
                    "goals": 0,
                    "yellow": 0,
                    "yellow_red": 0,
                    "red": 0,
                },
            )

            index_map = {
                "appearances": appearances_idx,
                "starts": starts_idx,
                "minutes": minutes_idx,
                "goals": goals_idx,
                "yellow": yellow_idx,
                "yellow_red": yellow_red_idx,
                "red": red_idx,
            }

            for key, column_index in index_map.items():
                if (
                    column_index is None
                    or column_index >= len(
                        values
                    )
                ):
                    continue

                current[
                    key
                ] += int(
                    round(
                        self._to_number(
                            values[
                                column_index
                            ]
                        )
                    )
                )

        if not players:
            return self._render_section_dict(
                section_data,
                section_key="players",
            )

        player_rows = [
            {
                "name": name,
                **stats,
                "cards": (
                    stats[
                        "yellow"
                    ]
                    + stats[
                        "yellow_red"
                    ]
                    + stats[
                        "red"
                    ]
                ),
            }
            for name, stats
            in players.items()
        ]

        active_players = [
            player
            for player in player_rows
            if (
                player[
                    "appearances"
                ] > 0
                or player[
                    "minutes"
                ] > 0
                or player[
                    "goals"
                ] > 0
                or player[
                    "cards"
                ] > 0
            )
        ]

        if not active_players:
            active_players = player_rows

        def top_players(
            key: str,
        ) -> list[tuple[str, int]]:
            ranked = sorted(
                active_players,
                key=lambda player: (
                    player[
                        key
                    ],
                    player[
                        "minutes"
                    ],
                    player[
                        "appearances"
                    ],
                    player[
                        "name"
                    ],
                ),
                reverse=True,
            )

            return [
                (
                    str(
                        player[
                            "name"
                        ]
                    ),
                    int(
                        player[
                            key
                        ]
                    ),
                )
                for player in ranked[:5]
            ]

        top_goals = top_players(
            "goals"
        )
        top_appearances = top_players(
            "appearances"
        )
        top_minutes = top_players(
            "minutes"
        )
        top_cards = top_players(
            "cards"
        )

        top_scorer_name, top_scorer_goals = (
            top_goals[
                0
            ]
        )
        minutes_name, minutes_value = (
            top_minutes[
                0
            ]
        )
        appearances_name, appearances_value = (
            top_appearances[
                0
            ]
        )

        resource_name = (
            "chart://player_dashboard_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_player_dashboard_image(
            top_goals=top_goals,
            top_appearances=top_appearances,
            top_minutes=top_minutes,
            top_cards=top_cards,
        )

        return (
            '<table width="100%" class="player-story-kpis"><tr>'
            '<td>'
            '<div class="player-story-label">Top-Torschütze</div>'
            f'<div class="player-story-value">{escape(top_scorer_name)}</div>'
            f'<div class="player-story-sub">{top_scorer_goals} Tore</div>'
            '</td>'
            '<td>'
            '<div class="player-story-label">Meiste Einsätze</div>'
            f'<div class="player-story-value">{escape(appearances_name)}</div>'
            f'<div class="player-story-sub">{appearances_value} Einsätze</div>'
            '</td>'
            '<td>'
            '<div class="player-story-label">Meiste Minuten</div>'
            f'<div class="player-story-value">{escape(minutes_name)}</div>'
            f'<div class="player-story-sub">{minutes_value} Minuten</div>'
            '</td>'
            '<td>'
            '<div class="player-story-label">Spieler mit Daten</div>'
            f'<div class="player-story-value">{len(players)}</div>'
            '<div class="player-story-sub">inkl. Kader-/Importdaten</div>'
            '</td>'
            '</tr></table>'
            '<div class="player-dashboard-chart">'
            '<div class="player-dashboard-title">'
            'Leistungsträger im Überblick'
            '</div>'
            '<div class="player-dashboard-note">'
            'Top 5 je Kategorie · doppelte Spielerzeilen werden '
            'für die Darstellung zusammengeführt'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<div class="player-dashboard-footer">'
            'Die vollständige Spielerliste mit Einsätzen, Startelf, '
            'Minuten, Toren und Karten befindet sich im Datenanhang.'
            '</div>'
        )

    def _create_player_dashboard_image(
        self,
        top_goals: list[tuple[str, int]],
        top_appearances: list[tuple[str, int]],
        top_minutes: list[tuple[str, int]],
        top_cards: list[tuple[str, int]],
    ) -> QImage:
        width = 1800
        height = 540

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )

        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        panel_gap = 40
        outer_x = 35
        outer_y = 25
        panel_width = (
            width
            - outer_x * 2
            - panel_gap
        ) / 2
        panel_height = (
            height
            - outer_y * 2
            - panel_gap
        ) / 2

        panels = [
            (
                "Top-Torschützen",
                top_goals,
                QColor(
                    "#2f9e44"
                ),
                "",
            ),
            (
                "Meiste Einsätze",
                top_appearances,
                QColor(
                    "#2f6fa3"
                ),
                "",
            ),
            (
                "Meiste Minuten",
                top_minutes,
                QColor(
                    "#6f42c1"
                ),
                "",
            ),
            (
                "Karten",
                top_cards,
                QColor(
                    "#d49a2a"
                ),
                "",
            ),
        ]

        for index, (
            title,
            ranking,
            color,
            suffix,
        ) in enumerate(
            panels
        ):
            column = (
                index
                % 2
            )
            row = (
                index
                // 2
            )

            x = (
                outer_x
                + column
                * (
                    panel_width
                    + panel_gap
                )
            )
            y = (
                outer_y
                + row
                * (
                    panel_height
                    + panel_gap
                )
            )

            self._draw_player_ranking_panel(
                painter=painter,
                rect=QRectF(
                    x,
                    y,
                    panel_width,
                    panel_height,
                ),
                title=title,
                ranking=ranking,
                color=color,
                suffix=suffix,
            )

        painter.end()

        return image

    def _draw_player_ranking_panel(
        self,
        painter: QPainter,
        rect: QRectF,
        title: str,
        ranking: list[tuple[str, int]],
        color: QColor,
        suffix: str,
    ) -> None:
        border_color = QColor(
            "#dfe3e7"
        )
        title_color = QColor(
            "#25282c"
        )
        secondary_color = QColor(
            "#777f88"
        )
        track_color = QColor(
            "#eef0f2"
        )

        painter.setPen(
            QPen(
                border_color,
                2,
            )
        )
        painter.setBrush(
            QColor(
                "#ffffff"
            )
        )
        painter.drawRoundedRect(
            rect,
            8,
            8,
        )

        painter.setPen(
            QPen(
                title_color
            )
        )
        painter.setFont(
            QFont(
                "Arial",
                17,
                QFont.Weight.Bold,
            )
        )
        painter.drawText(
            QRectF(
                rect.left()
                + 22,
                rect.top()
                + 17,
                rect.width()
                - 44,
                36,
            ),
            int(
                0x0001
                | 0x0080
            ),
            title,
        )

        if not ranking:
            painter.setPen(
                QPen(
                    secondary_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    14,
                )
            )
            painter.drawText(
                QRectF(
                    rect.left()
                    + 22,
                    rect.top()
                    + 72,
                    rect.width()
                    - 44,
                    40,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                "Keine Daten",
            )
            return

        max_value = max(
            1,
            max(
                value
                for _name, value
                in ranking
            ),
        )

        content_top = (
            rect.top()
            + 58
        )
        row_height = 38
        label_width = min(
            260.0,
            rect.width()
            * 0.35,
        )
        value_width = 72.0
        bar_left = (
            rect.left()
            + 24
            + label_width
        )
        bar_right = (
            rect.right()
            - 24
            - value_width
        )
        bar_width = max(
            40.0,
            bar_right
            - bar_left
        )

        for index, (
            name,
            value,
        ) in enumerate(
            ranking[:5]
        ):
            row_y = (
                content_top
                + index
                * row_height
            )

            painter.setPen(
                QPen(
                    title_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    13,
                )
            )

            display_name = (
                name
                if len(
                    name
                ) <= 24
                else (
                    name[:22]
                    + "…"
                )
            )

            painter.drawText(
                QRectF(
                    rect.left()
                    + 24,
                    row_y,
                    label_width
                    - 12,
                    30,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                display_name,
            )

            track_y = (
                row_y
                + 24
            )

            painter.fillRect(
                QRectF(
                    bar_left,
                    track_y,
                    bar_width,
                    12,
                ),
                track_color,
            )

            fill_width = (
                value
                / max_value
                * bar_width
            )

            painter.fillRect(
                QRectF(
                    bar_left,
                    track_y,
                    fill_width,
                    12,
                ),
                color,
            )

            painter.setPen(
                QPen(
                    color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    14,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    bar_right
                    + 8,
                    row_y,
                    value_width
                    - 8,
                    34,
                ),
                int(
                    0x0002
                    | 0x0080
                ),
                f"{value}{suffix}",
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

    def _render_full_discipline_visual(
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

        if not (
            isinstance(
                facts,
                dict,
            )
            and isinstance(
                tables,
                list,
            )
            and tables
            and isinstance(
                tables[0],
                dict,
            )
        ):
            return self._render_section_dict(
                section_data,
                section_key="discipline",
            )

        table = tables[0]
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

        parsed: list[dict[str, Any]] = []

        for row in rows:
            values = self._table_values(
                headers,
                row,
            )

            if len(
                values
            ) < 4:
                continue

            parsed.append(
                {
                    "name": str(
                        values[
                            0
                        ]
                    ),
                    "yellow": int(
                        round(
                            self._to_number(
                                values[
                                    1
                                ]
                            )
                        )
                    ),
                    "yellow_red": int(
                        round(
                            self._to_number(
                                values[
                                    2
                                ]
                            )
                        )
                    ),
                    "red": int(
                        round(
                            self._to_number(
                                values[
                                    3
                                ]
                            )
                        )
                    ),
                }
            )

        parsed.sort(
            key=lambda item: (
                item[
                    "yellow"
                ]
                + item[
                    "yellow_red"
                ]
                + item[
                    "red"
                ],
                item[
                    "red"
                ],
                item[
                    "yellow_red"
                ],
                item[
                    "yellow"
                ],
            ),
            reverse=True,
        )

        top_rows = parsed[
            :10
        ]

        resource_name = (
            "chart://discipline_"
            + str(
                len(
                    self._image_resources
                )
            )
        )

        self._image_resources[
            resource_name
        ] = self._create_discipline_chart_image(
            top_rows
        )

        yellow = int(
            self._to_number(
                facts.get(
                    "Gelbe Karten",
                    0,
                )
            )
        )
        yellow_red = int(
            self._to_number(
                facts.get(
                    "Gelb-Rote Karten",
                    0,
                )
            )
        )
        red = int(
            self._to_number(
                facts.get(
                    "Rote Karten",
                    0,
                )
            )
        )
        players_with_cards = int(
            self._to_number(
                facts.get(
                    "Spieler mit Karten",
                    0,
                )
            )
        )

        sendoffs = (
            yellow_red
            + red
        )

        most_booked = (
            top_rows[
                0
            ][
                "name"
            ]
            if top_rows
            else "–"
        )

        return (
            '<table width="100%" class="fairplay-kpis"><tr>'
            '<td>'
            '<div class="fairplay-label">Gelbe Karten</div>'
            f'<div class="fairplay-value fairplay-yellow">{yellow}</div>'
            '</td>'
            '<td>'
            '<div class="fairplay-label">Gelb-Rot</div>'
            f'<div class="fairplay-value fairplay-orange">{yellow_red}</div>'
            '</td>'
            '<td>'
            '<div class="fairplay-label">Rote Karten</div>'
            f'<div class="fairplay-value fairplay-red">{red}</div>'
            '</td>'
            '<td>'
            '<div class="fairplay-label">Platzverweise gesamt</div>'
            f'<div class="fairplay-value">{sendoffs}</div>'
            '</td>'
            '<td>'
            '<div class="fairplay-label">Spieler mit Karten</div>'
            f'<div class="fairplay-value">{players_with_cards}</div>'
            '</td>'
            '</tr></table>'
            '<div class="fairplay-chart-card">'
            '<div class="fairplay-chart-title">'
            'Auffälligste Spieler'
            '</div>'
            '<div class="fairplay-chart-note">'
            'Top 10 nach Anzahl der Karten · '
            'Gelb, Gelb-Rot und Rot separat dargestellt'
            '</div>'
            f'<img src="{escape(resource_name)}" width="980" />'
            '</div>'
            '<table width="100%" class="fairplay-insight-row"><tr>'
            '<td>'
            '<div class="fairplay-insight-label">Meiste Karten</div>'
            f'<div class="fairplay-insight-value">{escape(most_booked)}</div>'
            '</td>'
            '<td>'
            '<div class="fairplay-insight-label">Einordnung</div>'
            f'<div class="fairplay-insight-text">'
            f'{yellow} Verwarnungen und {sendoffs} Platzverweise '
            f'verteilen sich auf {players_with_cards} Spieler.'
            '</div>'
            '</td>'
            '</tr></table>'
            '<div class="fairplay-footer">'
            'Die vollständige Kartenliste befindet sich im Datenanhang.'
            '</div>'
        )

    def _create_discipline_chart_image(
        self,
        rows: list[dict[str, Any]],
    ) -> QImage:
        width = 1800
        height = 620

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(
            QColor(
                "#ffffff"
            )
        )

        painter = QPainter(
            image
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        if not rows:
            painter.end()
            return image

        yellow_color = QColor(
            "#e3b321"
        )
        orange_color = QColor(
            "#e67e22"
        )
        red_color = QColor(
            "#d94848"
        )
        track_color = QColor(
            "#eef0f2"
        )
        text_color = QColor(
            "#25282c"
        )
        muted_color = QColor(
            "#737b84"
        )

        left = 390.0
        right = 135.0
        top = 45.0
        row_height = 53.0
        bar_height = 20.0
        usable_width = (
            width
            - left
            - right
        )

        max_total = max(
            1,
            max(
                row[
                    "yellow"
                ]
                + row[
                    "yellow_red"
                ]
                + row[
                    "red"
                ]
                for row in rows
            ),
        )

        painter.setFont(
            QFont(
                "Arial",
                14,
            )
        )

        for index, row in enumerate(
            rows
        ):
            y = (
                top
                + index
                * row_height
            )

            name = str(
                row[
                    "name"
                ]
            )

            if len(
                name
            ) > 32:
                name = (
                    name[
                        :30
                    ]
                    + "…"
                )

            painter.setPen(
                QPen(
                    text_color
                )
            )
            painter.drawText(
                QRectF(
                    25,
                    y - 4,
                    left - 50,
                    30,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                name,
            )

            painter.fillRect(
                QRectF(
                    left,
                    y,
                    usable_width,
                    bar_height,
                ),
                track_color,
            )

            cursor_x = left

            for key, color in (
                (
                    "yellow",
                    yellow_color,
                ),
                (
                    "yellow_red",
                    orange_color,
                ),
                (
                    "red",
                    red_color,
                ),
            ):
                value = int(
                    row[
                        key
                    ]
                )

                segment_width = (
                    usable_width
                    * value
                    / max_total
                )

                if segment_width > 0:
                    painter.fillRect(
                        QRectF(
                            cursor_x,
                            y,
                            segment_width,
                            bar_height,
                        ),
                        color,
                    )

                cursor_x += segment_width

            total = (
                int(
                    row[
                        "yellow"
                    ]
                )
                + int(
                    row[
                        "yellow_red"
                    ]
                )
                + int(
                    row[
                        "red"
                    ]
                )
            )

            painter.setPen(
                QPen(
                    muted_color
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    13,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    width - 120,
                    y - 6,
                    90,
                    32,
                ),
                int(
                    0x0002
                    | 0x0080
                ),
                str(
                    total
                ),
            )

            painter.setFont(
                QFont(
                    "Arial",
                    11,
                )
            )
            painter.drawText(
                QRectF(
                    left,
                    y + 23,
                    usable_width,
                    24,
                ),
                int(
                    0x0001
                    | 0x0080
                ),
                (
                    f"Gelb {row['yellow']}   ·   "
                    f"Gelb-Rot {row['yellow_red']}   ·   "
                    f"Rot {row['red']}"
                ),
            )

        painter.end()

        return image

    def _render_full_streaks_visual(
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
            return self._render_section_dict(
                section_data,
                section_key="streaks",
            )

        current = str(
            facts.get(
                "Aktuelle Serie",
                "–",
            )
        )

        items = [
            (
                "Siegesserie",
                int(
                    self._to_number(
                        facts.get(
                            "Siegesserie max.",
                            0,
                        )
                    )
                ),
                "#2f9e44",
            ),
            (
                "Remisserie",
                int(
                    self._to_number(
                        facts.get(
                            "Remisserie max.",
                            0,
                        )
                    )
                ),
                "#d99a00",
            ),
            (
                "Niederlagenserie",
                int(
                    self._to_number(
                        facts.get(
                            "Niederlagenserie max.",
                            0,
                        )
                    )
                ),
                "#d94848",
            ),
            (
                "Ungeschlagen",
                int(
                    self._to_number(
                        facts.get(
                            "Ungeschlagen max.",
                            0,
                        )
                    )
                ),
                "#2f6fa3",
            ),
            (
                "Sieglos",
                int(
                    self._to_number(
                        facts.get(
                            "Sieglos max.",
                            0,
                        )
                    )
                ),
                "#777f88",
            ),
        ]

        max_value = max(
            1,
            max(
                value
                for _label, value, _color
                in items
            ),
        )

        cards = []

        for label, value, color in items:
            width = int(
                round(
                    value
                    / max_value
                    * 100
                )
            )

            cards.append(
                '<td>'
                f'<div class="streak-card-label">{escape(label)}</div>'
                f'<div class="streak-card-value" style="color:{color};">'
                f'{value}'
                '</div>'
                '<div class="streak-track">'
                f'<div class="streak-fill" style="width:{width}%; background:{color};">'
                '&nbsp;'
                '</div>'
                '</div>'
                '<div class="streak-card-sub">Spiele</div>'
                '</td>'
            )

        return (
            '<div class="streak-current">'
            '<div class="streak-current-label">Aktuelle Serie</div>'
            f'<div class="streak-current-value">{escape(current)}</div>'
            '</div>'
            '<table width="100%" class="streak-cards"><tr>'
            + "".join(
                cards
            )
            + '</tr></table>'
        )

    def _render_full_records_visual(
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

        clean_sheets = (
            facts.get(
                "Zu-Null-Spiele",
                0,
            )
            if isinstance(
                facts,
                dict,
            )
            else 0
        )
        scoreless = (
            facts.get(
                "Spiele ohne eigenes Tor",
                0,
            )
            if isinstance(
                facts,
                dict,
            )
            else 0
        )

        record_cards: list[str] = []

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

            for row in list(
                table.get(
                    "rows",
                    [],
                )
            )[:3]:
                values = self._table_values(
                    headers,
                    row,
                )

                if not values:
                    continue

                name = str(
                    values[
                        0
                    ]
                )
                matchday = (
                    str(
                        values[
                            1
                        ]
                    )
                    if len(
                        values
                    ) > 1
                    else ""
                )
                date = (
                    self._format_value(
                        values[
                            2
                        ]
                    )
                    if len(
                        values
                    ) > 2
                    else ""
                )
                match = (
                    str(
                        values[
                            3
                        ]
                    )
                    if len(
                        values
                    ) > 3
                    else ""
                )
                result = (
                    str(
                        values[
                            4
                        ]
                    )
                    if len(
                        values
                    ) > 4
                    else ""
                )
                value = (
                    str(
                        values[
                            5
                        ]
                    )
                    if len(
                        values
                    ) > 5
                    else ""
                )

                record_cards.append(
                    '<td>'
                    f'<div class="full-record-label">{escape(name)}</div>'
                    f'<div class="full-record-result">{escape(result)}</div>'
                    f'<div class="full-record-value">{escape(value)}</div>'
                    f'<div class="full-record-match">ST {escape(matchday)} · '
                    f'{escape(date)}<br>{escape(match)}</div>'
                    '</td>'
                )

        while len(
            record_cards
        ) < 3:
            record_cards.append(
                '<td></td>'
            )

        return (
            '<table width="100%" class="record-summary"><tr>'
            '<td>'
            '<div class="record-summary-label">Zu Null</div>'
            f'<div class="record-summary-value">{escape(self._format_value(clean_sheets))}</div>'
            '<div class="record-summary-sub">Spiele ohne Gegentor</div>'
            '</td>'
            '<td>'
            '<div class="record-summary-label">Ohne eigenes Tor</div>'
            f'<div class="record-summary-value">{escape(self._format_value(scoreless))}</div>'
            '<div class="record-summary-sub">torlose eigene Spiele</div>'
            '</td>'
            '</tr></table>'
            '<table width="100%" class="full-record-cards"><tr>'
            + "".join(
                record_cards
            )
            + '</tr></table>'
        )

    def _render_records_dashboard(
        self,
        section_data: dict[str, Any],
    ) -> str:
        tables = section_data.get(
            "tables",
            [],
        )

        if not (
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
            return self._render_section_dict(
                section_data
            )

        table = tables[0]
        headers = table.get(
            "headers",
            [],
        )
        rows = table.get(
            "rows",
            [],
        )

        cards = []

        for row in list(rows)[:3]:
            values = self._table_values(
                headers,
                row,
            )

            if not values:
                continue

            record_name = (
                str(values[0])
                if len(values) > 0
                else ""
            )
            matchday = (
                str(values[1])
                if len(values) > 1
                else ""
            )
            date = (
                self._format_value(
                    values[2]
                )
                if len(values) > 2
                else ""
            )
            match = (
                str(values[3])
                if len(values) > 3
                else ""
            )
            result = (
                str(values[4])
                if len(values) > 4
                else ""
            )
            value = (
                str(values[5])
                if len(values) > 5
                else ""
            )

            card_cls = ""

            name_cf = record_name.casefold()

            if "sieg" in name_cf:
                card_cls = "status-positive"
            elif "niederlage" in name_cf:
                card_cls = "status-negative"
            else:
                card_cls = "status-neutral"

            cards.append(
                (
                    f'<td class="{card_cls}">'
                    '<div class="record-card-label">'
                    f"{escape(record_name)}"
                    "</div>"
                    '<div class="record-card-value">'
                    f"{escape(result)}"
                    + (
                        f" · {escape(value)}"
                        if value
                        else ""
                    )
                    + "</div>"
                    '<div class="record-card-match">'
                    f"ST {escape(matchday)} · {escape(date)}<br>"
                    f"{escape(match)}"
                    "</div>"
                    "</td>"
                )
            )

        while len(cards) < 3:
            cards.append(
                "<td></td>"
            )

        facts = section_data.get(
            "facts"
        )

        facts_html = ""

        if isinstance(
            facts,
            dict,
        ) and facts:
            facts_html = self._render_facts(
                facts
            )

        return (
            facts_html
            + '<table width="100%" class="record-cards"><tr>'
            + "".join(
                cards[:3]
            )
            + "</tr></table>"
        )

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
