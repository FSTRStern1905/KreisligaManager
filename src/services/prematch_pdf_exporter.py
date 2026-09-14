from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import (
    QPageLayout,
    QPageSize,
    QTextDocument,
)
from PySide6.QtPrintSupport import QPrinter


class PrematchPdfExporter:
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
        required = [
            "competition_name",
            "season_name",
            "team_a",
            "team_b",
            "headline_comparison",
            "venue_comparison",
        ]

        missing = [
            key
            for key in required
            if key not in report_data
        ]

        if missing:
            raise ValueError(
                "Fehlende Prematch-Daten: "
                + ", ".join(
                    missing
                )
            )

        for key in (
            "team_a",
            "team_b",
        ):
            team = report_data.get(
                key
            )

            if not isinstance(
                team,
                dict,
            ):
                raise ValueError(
                    f"{key} muss ein Dictionary sein."
                )

            if not str(
                team.get(
                    "team_name",
                    "",
                )
            ).strip():
                raise ValueError(
                    f"Mannschaftsname für {key} fehlt."
                )

    def _build_html(
        self,
        report_data: dict[str, Any],
    ) -> str:
        team_a = report_data[
            "team_a"
        ]
        team_b = report_data[
            "team_b"
        ]

        team_a_name = escape(
            str(
                team_a.get(
                    "team_name",
                    "",
                )
            )
        )
        team_b_name = escape(
            str(
                team_b.get(
                    "team_name",
                    "",
                )
            )
        )

        competition_name = escape(
            str(
                report_data.get(
                    "competition_name",
                    "",
                )
            )
        )
        season_name = escape(
            str(
                report_data.get(
                    "season_name",
                    "",
                )
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

        headline_comparison = self._correct_headline_comparison(
            report_data.get(
                "headline_comparison",
                [],
            ),
            team_a,
            team_b,
        )

        page_one = (
            self._render_executive_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                generated_text=generated_text,
                comparison=headline_comparison,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_two = (
            self._render_venue_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                venue=report_data.get(
                    "venue_comparison",
                    {},
                ),
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_three = (
            self._render_attack_defense_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_four = (
            self._render_patterns_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_five = (
            self._render_halftime_phases_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_six = (
            self._render_control_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_seven = (
            self._render_consistency_progress_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_eight = (
            self._render_strengths_weaknesses_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_nine = (
            self._render_players_fairplay_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_ten = (
            self._render_h2h_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
        )

        page_eleven = (
            self._render_scouting_summary_page(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                competition_name=competition_name,
                season_name=season_name,
                team_a=team_a,
                team_b=team_b,
            )
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
        color: #17191b;
        font-size: 7pt;
        margin: 0;
        padding: 0;
    }}

    .page {{
        width: 100%;
    }}

    .page-break {{
        page-break-before: always;
    }}

    .brand {{
        color: #2f6fa3;
        font-size: 6pt;
        font-weight: bold;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    .matchup {{
        width: 100%;
        border-collapse: collapse;
        margin: 2px 0 4px 0;
    }}

    .matchup td {{
        vertical-align: middle;
    }}

    .team-name {{
        width: 43%;
        font-size: 22pt;
        font-weight: bold;
        color: #17191b;
    }}

    .team-left {{
        text-align: left;
    }}

    .team-right {{
        text-align: right;
    }}

    .versus {{
        width: 14%;
        text-align: center;
        color: #777f88;
        font-size: 11pt;
        font-weight: bold;
    }}

    .meta {{
        color: #777f88;
        font-size: 6pt;
        margin-bottom: 12px;
    }}

    .page-kicker {{
        color: #7a8189;
        font-size: 6pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }}

    .page-title {{
        color: #17191b;
        font-size: 16pt;
        font-weight: bold;
        margin-bottom: 8px;
    }}

    .comparison-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 4px 0 12px 0;
    }}

    .comparison-table th {{
        color: #68717b;
        font-size: 5.8pt;
        font-weight: bold;
        text-transform: uppercase;
        padding: 5px 8px;
        border-bottom: 1px solid #cfd4d9;
    }}

    .comparison-table td {{
        padding: 5px 8px;
        border-bottom: 1px solid #eceff1;
        vertical-align: middle;
    }}

    .comparison-label {{
        width: 36%;
        color: #69717a;
        font-size: 6.3pt;
        text-align: center;
    }}

    .comparison-value {{
        width: 32%;
        color: #17191b;
        font-size: 10pt;
        font-weight: bold;
    }}

    .value-left {{
        text-align: right;
    }}

    .value-right {{
        text-align: left;
    }}

    .summary-row {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
        margin-top: 7px;
    }}

    .summary-card {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 10px 12px;
        vertical-align: top;
    }}

    .summary-team {{
        color: #777f88;
        font-size: 5.8pt;
        text-transform: uppercase;
        letter-spacing: 0.25px;
    }}

    .summary-form {{
        color: #17191b;
        font-size: 14pt;
        font-weight: bold;
        letter-spacing: 2px;
        margin: 4px 0 5px 0;
    }}

    .summary-note {{
        color: #69717a;
        font-size: 5.8pt;
        line-height: 1.3;
    }}

    .venue-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 14px 0;
        margin: 5px 0 12px 0;
    }}

    .venue-card {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 13px 15px;
        vertical-align: top;
    }}

    .venue-card-home {{
        border-top: 4px solid #2f6fa3;
    }}

    .venue-card-away {{
        border-top: 4px solid #6f42c1;
    }}

    .venue-role {{
        color: #777f88;
        font-size: 5.8pt;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}

    .venue-team {{
        color: #17191b;
        font-size: 14pt;
        font-weight: bold;
        margin: 3px 0 8px 0;
    }}

    .venue-facts {{
        width: 100%;
        border-collapse: collapse;
    }}

    .venue-facts td {{
        border-bottom: 1px solid #eceff1;
        padding: 5px 2px;
    }}

    .venue-fact-label {{
        width: 55%;
        color: #69717a;
        font-size: 6pt;
    }}

    .venue-fact-value {{
        width: 45%;
        color: #17191b;
        font-size: 8.5pt;
        font-weight: bold;
        text-align: right;
    }}

    .venue-bottom {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
        margin-top: 8px;
    }}

    .venue-bottom td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 9px 11px;
        vertical-align: top;
    }}

    .bottom-label {{
        color: #777f88;
        font-size: 5.6pt;
        text-transform: uppercase;
    }}

    .bottom-value {{
        color: #17191b;
        font-size: 11pt;
        font-weight: bold;
        margin-top: 3px;
    }}

    .bottom-note {{
        color: #858c94;
        font-size: 5.5pt;
        line-height: 1.25;
        margin-top: 3px;
    }}

    .footer-note {{
        color: #858c94;
        font-size: 5.4pt;
        margin-top: 8px;
    }}

    .attack-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 14px 0;
        margin: 5px 0 10px 0;
    }}

    .attack-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 12px 14px;
        vertical-align: top;
    }}

    .attack-panel-a {{
        border-top: 4px solid #2f6fa3;
    }}

    .attack-panel-b {{
        border-top: 4px solid #6f42c1;
    }}

    .attack-kicker {{
        color: #777f88;
        font-size: 5.7pt;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}

    .attack-team {{
        color: #17191b;
        font-size: 13pt;
        font-weight: bold;
        margin: 3px 0 8px 0;
    }}

    .attack-metric-grid {{
        width: 100%;
        border-collapse: collapse;
    }}

    .attack-metric-grid td {{
        border-bottom: 1px solid #eceff1;
        padding: 5px 2px;
    }}

    .attack-metric-label {{
        width: 58%;
        color: #69717a;
        font-size: 6pt;
    }}

    .attack-metric-value {{
        width: 42%;
        color: #17191b;
        font-size: 9pt;
        font-weight: bold;
        text-align: right;
    }}

    .attack-matchup-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        margin: 8px 0 5px 0;
    }}

    .attack-matchups {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin-top: 4px;
    }}

    .attack-matchups td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 9px 10px;
        vertical-align: top;
    }}

    .attack-matchup-label {{
        color: #777f88;
        font-size: 5.5pt;
        text-transform: uppercase;
    }}

    .attack-matchup-value {{
        color: #17191b;
        font-size: 11pt;
        font-weight: bold;
        margin: 3px 0;
    }}

    .attack-matchup-note {{
        color: #858c94;
        font-size: 5.5pt;
        line-height: 1.25;
    }}


    .patterns-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 14px 0;
        margin: 5px 0 10px 0;
    }}

    .patterns-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 12px 14px;
        vertical-align: top;
    }}

    .patterns-panel-a {{
        border-top: 4px solid #2f6fa3;
    }}

    .patterns-panel-b {{
        border-top: 4px solid #6f42c1;
    }}

    .patterns-team {{
        color: #17191b;
        font-size: 13pt;
        font-weight: bold;
        margin: 3px 0 8px 0;
    }}

    .patterns-grid {{
        width: 100%;
        border-collapse: collapse;
    }}

    .patterns-grid td {{
        border-bottom: 1px solid #eceff1;
        padding: 5px 2px;
    }}

    .patterns-grid-label {{
        width: 58%;
        color: #69717a;
        font-size: 6pt;
    }}

    .patterns-grid-value {{
        width: 42%;
        color: #17191b;
        font-size: 9pt;
        font-weight: bold;
        text-align: right;
    }}

    .patterns-summary-title {{
        color: #25282c;
        font-size: 8pt;
        font-weight: bold;
        margin: 8px 0 5px 0;
    }}

    .patterns-summary {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
    }}

    .patterns-summary td {{
        width: 33%;
        border: 1px solid #dfe3e7;
        padding: 9px 10px;
        vertical-align: top;
    }}

    .patterns-summary-label {{
        color: #777f88;
        font-size: 5.5pt;
        text-transform: uppercase;
    }}

    .patterns-summary-value {{
        color: #17191b;
        font-size: 11pt;
        font-weight: bold;
        margin: 3px 0;
    }}

    .patterns-summary-note {{
        color: #858c94;
        font-size: 5.5pt;
        line-height: 1.25;
    }}

    .margin-row {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin-top: 8px;
    }}

    .margin-row td {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 9px 10px;
        vertical-align: top;
    }}

    .margin-title {{
        color: #25282c;
        font-size: 7.5pt;
        font-weight: bold;
        margin-bottom: 5px;
    }}

    .margin-text {{
        color: #69717a;
        font-size: 5.8pt;
        line-height: 1.35;
    }}


    .phase-halves {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 12px 0;
        margin: 5px 0 10px 0;
    }}

    .phase-team {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 11px 13px;
        vertical-align: top;
    }}

    .phase-team-a {{ border-top: 4px solid #2f6fa3; }}
    .phase-team-b {{ border-top: 4px solid #6f42c1; }}

    .phase-team-name {{
        font-size: 12pt;
        font-weight: bold;
        color: #17191b;
        margin-bottom: 7px;
    }}

    .half-grid {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 7px 0;
    }}

    .half-card {{
        width: 50%;
        border: 1px solid #e1e5e8;
        padding: 8px;
        vertical-align: top;
    }}

    .half-title {{
        font-size: 6pt;
        color: #777f88;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    .half-score {{
        font-size: 14pt;
        font-weight: bold;
        color: #17191b;
    }}

    .half-note {{
        font-size: 5.4pt;
        color: #858c94;
        margin-top: 3px;
    }}

    .phase-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 5px;
    }}

    .phase-table th {{
        background: #f1f3f5;
        color: #5f666d;
        font-size: 5.5pt;
        padding: 5px;
        border: 1px solid #dfe3e7;
    }}

    .phase-table td {{
        font-size: 6.4pt;
        padding: 5px;
        border: 1px solid #e3e6e9;
        text-align: center;
    }}

    .phase-bar {{
        font-family: monospace;
        font-size: 7pt;
        letter-spacing: 0;
    }}

    .phase-summary {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 9px 0;
        margin-top: 8px;
    }}

    .phase-summary td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 8px;
        vertical-align: top;
    }}

    .phase-summary-label {{
        font-size: 5.2pt;
        color: #777f88;
        text-transform: uppercase;
    }}

    .phase-summary-value {{
        font-size: 10pt;
        font-weight: bold;
        color: #17191b;
        margin-top: 3px;
    }}


    .control-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 3px 0 5px 0;
    }}

    .control-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 7px 10px;
        vertical-align: top;
    }}

    .control-panel-a {{ border-top: 4px solid #2f6fa3; }}
    .control-panel-b {{ border-top: 4px solid #6f42c1; }}

    .control-team {{
        font-size: 11.5pt;
        font-weight: bold;
        color: #17191b;
        margin: 2px 0 4px 0;
    }}

    .control-section-title {{
        font-size: 5.4pt;
        color: #777f88;
        text-transform: uppercase;
        margin: 4px 0 2px 0;
    }}

    .control-grid {{
        width: 100%;
        border-collapse: collapse;
    }}

    .control-grid td {{
        border-bottom: 1px solid #eceff1;
        padding: 2.7px 2px;
    }}

    .control-label {{
        width: 62%;
        color: #69717a;
        font-size: 5.5pt;
    }}

    .control-value {{
        width: 38%;
        color: #17191b;
        font-size: 7.6pt;
        font-weight: bold;
        text-align: right;
    }}

    .control-matchups {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 7px 0;
        margin-top: 3px;
    }}

    .control-matchups td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 5px 7px;
        vertical-align: top;
    }}

    .control-matchup-label {{
        font-size: 4.8pt;
        color: #777f88;
        text-transform: uppercase;
    }}

    .control-matchup-value {{
        font-size: 9pt;
        font-weight: bold;
        color: #17191b;
        margin-top: 2px;
    }}

    .control-note {{
        font-size: 4.7pt;
        color: #858c94;
        margin-top: 2px;
        line-height: 1.15;
    }}


    .consistency-top {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 8px 0;
        margin: 2px 0 4px 0;
    }}

    .consistency-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 5px 8px;
        vertical-align: top;
    }}

    .consistency-a {{ border-top: 4px solid #2f6fa3; }}
    .consistency-b {{ border-top: 4px solid #6f42c1; }}

    .consistency-team {{
        font-size: 10.5pt;
        font-weight: bold;
        color: #17191b;
        margin: 1px 0 3px 0;
    }}

    .consistency-grid {{
        width: 100%;
        border-collapse: collapse;
    }}

    .consistency-grid td {{
        border-bottom: 1px solid #eceff1;
        padding: 2px 2px;
    }}

    .consistency-label {{
        color: #69717a;
        font-size: 5pt;
    }}

    .consistency-value {{
        color: #17191b;
        font-size: 7pt;
        font-weight: bold;
        text-align: right;
    }}

    .form-block-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 2px;
    }}

    .form-block-table th {{
        background: #f1f3f5;
        border: 1px solid #dfe3e7;
        color: #656d75;
        font-size: 4.6pt;
        padding: 2px;
    }}

    .form-block-table td {{
        border: 1px solid #e3e6e9;
        font-size: 5pt;
        padding: 2px;
        text-align: center;
    }}

    .progress-wrap {{
        width: 100%;
        border: 1px solid #dfe3e7;
        padding: 4px 6px;
        margin-top: 3px;
    }}

    .progress-table {{
        width: 100%;
        border-collapse: collapse;
    }}

    .progress-table th {{
        background: #f1f3f5;
        color: #656d75;
        border: 1px solid #dfe3e7;
        padding: 2px;
        font-size: 4.4pt;
    }}

    .progress-table td {{
        border: 1px solid #e3e6e9;
        padding: 2px;
        font-size: 4.8pt;
        text-align: center;
    }}

    .progress-a {{
        font-weight: bold;
        color: #2f6fa3;
    }}

    .progress-b {{
        font-weight: bold;
        color: #6f42c1;
    }}

    .consistency-compare {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 6px 0;
        margin-top: 3px;
    }}

    .consistency-compare td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 4px 5px;
        vertical-align: top;
    }}

    .consistency-compare-label {{
        color: #777f88;
        font-size: 4.3pt;
        text-transform: uppercase;
    }}

    .consistency-compare-value {{
        color: #17191b;
        font-size: 7.5pt;
        font-weight: bold;
        margin-top: 1px;
    }}


    .sw-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 3px 0 6px 0;
    }}

    .sw-team-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 7px 9px;
        vertical-align: top;
    }}

    .sw-team-a {{ border-top: 4px solid #2f6fa3; }}
    .sw-team-b {{ border-top: 4px solid #6f42c1; }}

    .sw-team-name {{
        font-size: 11pt;
        font-weight: bold;
        color: #17191b;
        margin: 2px 0 5px 0;
    }}

    .sw-column-title {{
        font-size: 5.2pt;
        color: #777f88;
        text-transform: uppercase;
        margin: 4px 0 2px 0;
    }}

    .sw-item {{
        border: 1px solid #e1e5e8;
        padding: 4px 6px;
        margin-bottom: 3px;
    }}

    .sw-strength {{
        border-left: 3px solid #4f8b62;
    }}

    .sw-weakness {{
        border-left: 3px solid #a85a5a;
    }}

    .sw-item-title {{
        font-size: 6.3pt;
        font-weight: bold;
        color: #202327;
    }}

    .sw-item-metric {{
        font-size: 6.8pt;
        font-weight: bold;
        color: #17191b;
        margin-top: 1px;
    }}

    .sw-item-text {{
        font-size: 4.8pt;
        color: #777f88;
        margin-top: 1px;
        line-height: 1.15;
    }}

    .matchup-grid {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 8px 0;
        margin-top: 4px;
    }}

    .matchup-grid td {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 7px 8px;
        vertical-align: top;
    }}

    .matchup-a {{
        border-top: 3px solid #2f6fa3 !important;
    }}

    .matchup-b {{
        border-top: 3px solid #6f42c1 !important;
    }}

    .matchup-heading {{
        font-size: 6pt;
        font-weight: bold;
        color: #202327;
        margin-bottom: 4px;
    }}

    .matchup-pair {{
        border-bottom: 1px solid #eceff1;
        padding: 3px 0;
    }}

    .matchup-pair:last-child {{
        border-bottom: none;
    }}

    .matchup-pair-title {{
        font-size: 5.6pt;
        font-weight: bold;
        color: #202327;
    }}

    .matchup-pair-metric {{
        font-size: 5.2pt;
        color: #666e76;
        margin-top: 1px;
    }}

    .matchup-arrow {{
        color: #8b9299;
        font-weight: normal;
    }}


    .pf-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 3px 0 5px 0;
    }}

    .pf-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 7px 9px;
        vertical-align: top;
    }}

    .pf-a {{ border-top: 4px solid #2f6fa3; }}
    .pf-b {{ border-top: 4px solid #6f42c1; }}

    .pf-team {{
        font-size: 11pt;
        font-weight: bold;
        color: #17191b;
        margin: 2px 0 5px 0;
    }}

    .pf-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 2px;
    }}

    .pf-table th {{
        background: #f1f3f5;
        color: #626a72;
        border: 1px solid #dfe3e7;
        font-size: 4.5pt;
        padding: 2.5px;
    }}

    .pf-table td {{
        border: 1px solid #e3e6e9;
        font-size: 5pt;
        padding: 2.5px;
        text-align: center;
    }}

    .pf-table td:first-child {{
        text-align: left;
        font-weight: bold;
    }}

    .pf-facts {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 6px 0;
        margin-top: 4px;
    }}

    .pf-facts td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 4px 5px;
        vertical-align: top;
    }}

    .pf-fact-label {{
        color: #777f88;
        font-size: 4.4pt;
        text-transform: uppercase;
    }}

    .pf-fact-value {{
        color: #17191b;
        font-size: 8pt;
        font-weight: bold;
        margin-top: 1px;
    }}

    .pf-compare {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 7px 0;
        margin-top: 5px;
    }}

    .pf-compare td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 5px 6px;
        vertical-align: top;
    }}

    .pf-compare-label {{
        font-size: 4.5pt;
        color: #777f88;
        text-transform: uppercase;
    }}

    .pf-compare-value {{
        font-size: 8.3pt;
        font-weight: bold;
        color: #17191b;
        margin-top: 1px;
    }}


    .h2h-summary {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 7px 0;
        margin: 5px 0 8px 0;
    }}

    .h2h-summary td {{
        width: 20%;
        border: 1px solid #dfe3e7;
        padding: 7px 8px;
        vertical-align: top;
    }}

    .h2h-label {{
        color: #777f88;
        font-size: 4.8pt;
        text-transform: uppercase;
    }}

    .h2h-value {{
        color: #17191b;
        font-size: 10pt;
        font-weight: bold;
        margin-top: 2px;
    }}

    .h2h-balance {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 4px 0 7px 0;
    }}

    .h2h-balance td {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 8px 10px;
        vertical-align: top;
    }}

    .h2h-a {{
        border-top: 4px solid #2f6fa3 !important;
    }}

    .h2h-b {{
        border-top: 4px solid #6f42c1 !important;
    }}

    .h2h-team {{
        color: #17191b;
        font-size: 11pt;
        font-weight: bold;
        margin-bottom: 5px;
    }}

    .h2h-record {{
        width: 100%;
        border-collapse: collapse;
    }}

    .h2h-record td {{
        border-bottom: 1px solid #eceff1;
        padding: 3px 2px;
    }}

    .h2h-record-label {{
        font-size: 5.3pt;
        color: #69717a;
    }}

    .h2h-record-value {{
        font-size: 7.6pt;
        font-weight: bold;
        color: #17191b;
        text-align: right;
    }}

    .h2h-games {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 3px;
    }}

    .h2h-games th {{
        background: #f1f3f5;
        color: #626a72;
        border: 1px solid #dfe3e7;
        font-size: 4.8pt;
        padding: 3px;
    }}

    .h2h-games td {{
        border: 1px solid #e3e6e9;
        font-size: 5.3pt;
        padding: 3px;
        text-align: center;
    }}

    .h2h-games td:nth-child(3) {{
        text-align: left;
    }}

    .h2h-empty {{
        border: 1px solid #dfe3e7;
        padding: 18px;
        margin-top: 12px;
        font-size: 7pt;
        color: #69717a;
        text-align: center;
    }}


    .scout-top {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 8px 0;
        margin: 4px 0 6px 0;
    }}

    .scout-top td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 6px 7px;
        vertical-align: top;
    }}

    .scout-label {{
        font-size: 4.6pt;
        color: #777f88;
        text-transform: uppercase;
    }}

    .scout-value {{
        font-size: 8.6pt;
        font-weight: bold;
        color: #17191b;
        margin-top: 2px;
    }}

    .scout-layout {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 10px 0;
        margin: 4px 0 6px 0;
    }}

    .scout-panel {{
        width: 50%;
        border: 1px solid #dfe3e7;
        padding: 7px 9px;
        vertical-align: top;
    }}

    .scout-a {{ border-top: 4px solid #2f6fa3; }}
    .scout-b {{ border-top: 4px solid #6f42c1; }}

    .scout-team {{
        font-size: 10.8pt;
        font-weight: bold;
        color: #17191b;
        margin: 2px 0 4px 0;
    }}

    .scout-row {{
        border-bottom: 1px solid #eceff1;
        padding: 3px 0;
    }}

    .scout-row-title {{
        font-size: 5.2pt;
        color: #707880;
        text-transform: uppercase;
    }}

    .scout-row-value {{
        font-size: 6.4pt;
        font-weight: bold;
        color: #202327;
        margin-top: 1px;
    }}

    .scout-factors {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 7px 0;
        margin-top: 4px;
    }}

    .scout-factors td {{
        width: 25%;
        border: 1px solid #dfe3e7;
        padding: 6px 7px;
        vertical-align: top;
    }}

    .scout-factor-title {{
        font-size: 5.4pt;
        font-weight: bold;
        color: #202327;
    }}

    .scout-factor-text {{
        font-size: 4.8pt;
        color: #6f777f;
        margin-top: 2px;
        line-height: 1.18;
    }}

    .scout-conclusion {{
        border: 1px solid #dfe3e7;
        border-top: 3px solid #495057;
        padding: 8px 10px;
        margin-top: 6px;
    }}

    .scout-conclusion-title {{
        font-size: 6pt;
        font-weight: bold;
        color: #202327;
        margin-bottom: 3px;
    }}

    .scout-conclusion-text {{
        font-size: 6.2pt;
        font-weight: bold;
        color: #343a40;
        line-height: 1.15;
    }}

</style>
</head>
<body>
{page_one}
{page_two}
{page_three}
{page_four}
{page_five}
{page_six}
{page_seven}
{page_eight}
{page_nine}
{page_ten}
{page_eleven}
</body>
</html>
"""

    def _correct_headline_comparison(
        self,
        comparison: Any,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows = [
            dict(row)
            for row in comparison
            if isinstance(row, dict)
        ] if isinstance(comparison, list) else []

        consistency_a = self._section_facts(
            team_a,
            "consistency",
        )
        consistency_b = self._section_facts(
            team_b,
            "consistency",
        )

        ppg_range_a = consistency_a.get(
            "PPG-Spannweite",
            "-",
        )
        ppg_range_b = consistency_b.get(
            "PPG-Spannweite",
            "-",
        )

        for row in rows:
            if str(row.get("label", "")).strip() not in {
                "PPG-Spanne",
                "PPG-Spannweite",
            }:
                continue

            row["team_a"] = ppg_range_a
            row["team_b"] = ppg_range_b
            row["label"] = "PPG-Spannweite"
            break

        return rows

    def _render_executive_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        generated_text: str,
        comparison: Any,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        rows = []

        if isinstance(
            comparison,
            list,
        ):
            for row in comparison:
                if not isinstance(
                    row,
                    dict,
                ):
                    continue

                label = escape(
                    str(
                        row.get(
                            "label",
                            "-",
                        )
                    )
                )
                value_a = escape(
                    self._format_value(
                        row.get(
                            "team_a"
                        )
                    )
                )
                value_b = escape(
                    self._format_value(
                        row.get(
                            "team_b"
                        )
                    )
                )

                rows.append(
                    f"""
<tr>
    <td class="comparison-value value-left">{value_a}</td>
    <td class="comparison-label">{label}</td>
    <td class="comparison-value value-right">{value_b}</td>
</tr>
"""
                )

        form_a = self._overview_fact(
            team_a,
            "Form letzte 5",
        )
        form_b = self._overview_fact(
            team_b,
            "Form letzte 5",
        )

        position_a = self._overview_fact(
            team_a,
            "Tabellenplatz",
        )
        position_b = self._overview_fact(
            team_b,
            "Tabellenplatz",
        )

        return f"""
<div class="page">
    <div class="brand">
        KREISLIGAMANAGER · PREMATCH-REPORT
    </div>

    <table width="100%" class="matchup">
        <tr>
            <td class="team-name team-left">{team_a_name}</td>
            <td class="versus">VS.</td>
            <td class="team-name team-right">{team_b_name}</td>
        </tr>
    </table>

    <div class="meta">
        {competition_name} · Saison {season_name} ·
        Erstellt am {escape(generated_text)}
    </div>

    <div class="page-kicker">Seite 1 · Matchup</div>
    <div class="page-title">Executive Summary</div>

    <table width="100%" class="comparison-table">
        <tr>
            <th style="text-align:right;">{team_a_name}</th>
            <th style="text-align:center;">Vergleich</th>
            <th style="text-align:left;">{team_b_name}</th>
        </tr>
        {''.join(rows)}
    </table>

    <table width="100%" class="summary-row">
        <tr>
            <td class="summary-card">
                <div class="summary-team">{team_a_name}</div>
                <div class="summary-form">{escape(self._format_value(form_a))}</div>
                <div class="summary-note">
                    Tabellenplatz {escape(self._format_value(position_a))}.
                    Team A wird im Report als Heimteam betrachtet.
                </div>
            </td>
            <td class="summary-card">
                <div class="summary-team">{team_b_name}</div>
                <div class="summary-form">{escape(self._format_value(form_b))}</div>
                <div class="summary-note">
                    Tabellenplatz {escape(self._format_value(position_b))}.
                    Team B wird im Report als Auswärtsteam betrachtet.
                </div>
            </td>
        </tr>
    </table>
</div>
"""

    def _render_venue_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        venue: Any,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        venue = (
            venue
            if isinstance(
                venue,
                dict,
            )
            else {}
        )

        home_block = venue.get(
            "team_a",
            {}
        )
        away_block = venue.get(
            "team_b",
            {}
        )

        home_facts = self._block_facts(
            home_block
        )
        away_facts = self._block_facts(
            away_block
        )

        home_rows = self._render_fact_rows(
            home_facts
        )
        away_rows = self._render_fact_rows(
            away_facts
        )

        ppg_a = self._find_fact(
            home_facts,
            (
                "Punkte / Spiel",
                "Punkte pro Spiel",
                "PPG",
            ),
        )
        ppg_b = self._find_fact(
            away_facts,
            (
                "Punkte / Spiel",
                "Punkte pro Spiel",
                "PPG",
            ),
        )

        goals_a = self._rate_from_facts(
            facts=home_facts,
            value_keys=(
                "Tore",
            ),
            games_keys=(
                "Spiele",
            ),
        )
        goals_b = self._rate_from_facts(
            facts=away_facts,
            value_keys=(
                "Tore",
            ),
            games_keys=(
                "Spiele",
            ),
        )

        conceded_a = self._rate_from_facts(
            facts=home_facts,
            value_keys=(
                "Gegentore",
            ),
            games_keys=(
                "Spiele",
            ),
        )
        conceded_b = self._rate_from_facts(
            facts=away_facts,
            value_keys=(
                "Gegentore",
            ),
            games_keys=(
                "Spiele",
            ),
        )

        return f"""
<div class="page page-break">
    <div class="brand">
        KREISLIGAMANAGER · PREMATCH-REPORT
    </div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">
        Heimstärke ↔ Auswärtsstärke
    </div>

    <table width="100%" class="venue-layout">
        <tr>
            <td class="venue-card venue-card-home">
                <div class="venue-role">Heimteam · Heimbilanz</div>
                <div class="venue-team">{team_a_name}</div>
                <table width="100%" class="venue-facts">
                    {home_rows}
                </table>
            </td>
            <td class="venue-card venue-card-away">
                <div class="venue-role">Auswärtsteam · Auswärtsbilanz</div>
                <div class="venue-team">{team_b_name}</div>
                <table width="100%" class="venue-facts">
                    {away_rows}
                </table>
            </td>
        </tr>
    </table>

    <table width="100%" class="venue-bottom">
        <tr>
            <td>
                <div class="bottom-label">Punkte / Spiel</div>
                <div class="bottom-value">
                    {escape(self._format_value(ppg_a))}
                    ↔
                    {escape(self._format_value(ppg_b))}
                </div>
                <div class="bottom-note">
                    Heimleistung von Team A gegen
                    Auswärtsleistung von Team B.
                </div>
            </td>
            <td>
                <div class="bottom-label">Tore / Spiel</div>
                <div class="bottom-value">
                    {escape(self._format_value(goals_a))}
                    ↔
                    {escape(self._format_value(goals_b))}
                </div>
                <div class="bottom-note">
                    Venue-spezifische offensive Ausbeute.
                </div>
            </td>
            <td>
                <div class="bottom-label">Gegentore / Spiel</div>
                <div class="bottom-value">
                    {escape(self._format_value(conceded_a))}
                    ↔
                    {escape(self._format_value(conceded_b))}
                </div>
                <div class="bottom-note">
                    Venue-spezifische defensive Bilanz.
                </div>
            </td>
        </tr>
    </table>

    <div class="footer-note">
        Grundlage sind ausschließlich die bereits im
        KreisligaManager berechneten Wettbewerbsdaten.
    </div>
</div>
"""

    def _render_scouting_summary_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        overview_a = self._section_facts(team_a, "overview")
        overview_b = self._section_facts(team_b, "overview")
        patterns_a = self._section_facts(team_a, "patterns")
        patterns_b = self._section_facts(team_b, "patterns")
        control_a = self._section_facts(team_a, "control")
        control_b = self._section_facts(team_b, "control")
        consistency_a = self._section_facts(team_a, "consistency")
        consistency_b = self._section_facts(team_b, "consistency")
        attack_a = self._section_facts(team_a, "attack_defense")
        attack_b = self._section_facts(team_b, "attack_defense")

        sw_a = self._section_dict(team_a, "strengths_weaknesses")
        sw_b = self._section_dict(team_b, "strengths_weaknesses")
        strengths_a = self._sw_items(sw_a, "strengths")
        weaknesses_a = self._sw_items(sw_a, "weaknesses")
        strengths_b = self._sw_items(sw_b, "strengths")
        weaknesses_b = self._sw_items(sw_b, "weaknesses")

        venue_a = self._find_block_facts(team_a, "table_form", "Heimbilanz")
        venue_b = self._find_block_facts(team_b, "table_form", "Auswärtsbilanz")

        panel_a = self._render_scout_team_panel(
            team_name=team_a_name,
            venue_label="Heimbilanz",
            venue=venue_a,
            overview=overview_a,
            patterns=patterns_a,
            control=control_a,
            consistency=consistency_a,
            attack=attack_a,
            strengths=strengths_a,
            weaknesses=weaknesses_a,
        )
        panel_b = self._render_scout_team_panel(
            team_name=team_b_name,
            venue_label="Auswärtsbilanz",
            venue=venue_b,
            overview=overview_b,
            patterns=patterns_b,
            control=control_b,
            consistency=consistency_b,
            attack=attack_b,
            strengths=strengths_b,
            weaknesses=weaknesses_b,
        )

        factors = [
            (
                "Heim ↔ Auswärts",
                f"{team_a_name}: {self._fact_text(venue_a, 'Punkte / Spiel')} PPG zuhause · "
                f"{team_b_name}: {self._fact_text(venue_b, 'Punkte / Spiel')} PPG auswärts.",
            ),
            (
                "Torcharakter",
                f"Over 2,5: {self._fact_text(patterns_a, 'Over 2,5 %')} % ↔ "
                f"{self._fact_text(patterns_b, 'Over 2,5 %')} % · "
                f"Beide treffen: {self._fact_text(patterns_a, 'Beide treffen %')} % ↔ "
                f"{self._fact_text(patterns_b, 'Beide treffen %')} %.",
            ),
            (
                "Spielkontrolle",
                f"Punktausbeute aus Führungen: "
                f"{self._fact_text(control_a, 'Punktausbeute aus Führungen %')} % ↔ "
                f"{self._fact_text(control_b, 'Punktausbeute aus Führungen %')} %. "
                f"Comeback: {self._fact_text(control_a, 'Comeback-Quote %')} % ↔ "
                f"{self._fact_text(control_b, 'Comeback-Quote %')} %.",
            ),
            (
                "Konstanz",
                f"PPG-Spannweite: {self._fact_text(consistency_a, 'PPG-Spannweite')} ↔ "
                f"{self._fact_text(consistency_b, 'PPG-Spannweite')} · "
                f"Volatilität: {self._fact_text(consistency_a, 'Volatilität')} ↔ "
                f"{self._fact_text(consistency_b, 'Volatilität')}.",
            ),
        ]

        conclusion = (
            f"{team_a_name}: Heim-PPG {self._fact_text(venue_a, 'Punkte / Spiel')} · "
            f"{team_b_name}: Auswärts-PPG {self._fact_text(venue_b, 'Punkte / Spiel')} · "
            f"BTTS {self._fact_text(patterns_a, 'Beide treffen %')} % ↔ "
            f"{self._fact_text(patterns_b, 'Beide treffen %')} % · "
            f"Comeback {self._fact_text(control_a, 'Comeback-Quote %')} % ↔ "
            f"{self._fact_text(control_b, 'Comeback-Quote %')} %."
        )

        return f"""
<div class="page page-break">
    <div class="brand">KREISLIGAMANAGER · PREMATCH-REPORT</div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">Spielvorschau / Scouting-Fazit</div>

    <table width="100%" class="scout-top">
        <tr>
            {self._scout_top_card(
                "Punkte / Spiel",
                overview_a.get("Punkte / Spiel", "-"),
                overview_b.get("Punkte / Spiel", "-"),
            )}
            {self._scout_top_card(
                "Tore / Spiel",
                overview_a.get("Tore / Spiel", "-"),
                overview_b.get("Tore / Spiel", "-"),
            )}
            {self._scout_top_card(
                "Gegentore / Spiel",
                overview_a.get("Gegentore / Spiel", "-"),
                overview_b.get("Gegentore / Spiel", "-"),
            )}
            {self._scout_top_card(
                "Form letzte 5",
                overview_a.get("Form letzte 5", "-"),
                overview_b.get("Form letzte 5", "-"),
            )}
        </tr>
    </table>

    <table width="100%" class="scout-layout">
        <tr>
            <td class="scout-panel scout-a">{panel_a}</td>
            <td class="scout-panel scout-b">{panel_b}</td>
        </tr>
    </table>

    <div class="control-section-title">Schlüsselfaktoren</div>
    <table width="100%" class="scout-factors">
        <tr>
            {''.join(
                self._scout_factor_card(title, body)
                for title, body in factors
            )}
        </tr>
    </table>

    <div class="scout-conclusion">
        <div class="scout-conclusion-title">Scouting-Fazit</div>
        <div class="scout-conclusion-text">{escape(conclusion)}</div>
    </div>

    <div class="footer-note">
        Datenbasierte Scouting-Zusammenfassung · keine Ergebnisprognose.
    </div>
</div>
"""

    def _render_scout_team_panel(
        self,
        team_name: str,
        venue_label: str,
        venue: dict[str, Any],
        overview: dict[str, Any],
        patterns: dict[str, Any],
        control: dict[str, Any],
        consistency: dict[str, Any],
        attack: dict[str, Any],
        strengths: list[dict[str, Any]],
        weaknesses: list[dict[str, Any]],
    ) -> str:
        strength = strengths[0] if strengths else {}
        weakness = weaknesses[0] if weaknesses else {}

        rows = [
            (
                venue_label,
                f"{self._fact_text(venue, 'Punkte / Spiel')} PPG · "
                f"{self._fact_text(venue, 'Tore')}:{self._fact_text(venue, 'Gegentore')} Tore",
            ),
            (
                "Offensive",
                f"{self._fact_text(overview, 'Tore / Spiel')} Tore/Spiel · "
                f"{self._fact_text(attack, 'Mit eigenem Tor %')} % mit eigenem Tor",
            ),
            (
                "Defensive",
                f"{self._fact_text(overview, 'Gegentore / Spiel')} Gegentore/Spiel · "
                f"{self._fact_text(attack, 'Zu Null %')} % zu Null",
            ),
            (
                "Spielmuster",
                f"BTTS {self._fact_text(patterns, 'Beide treffen %')} % · "
                f"Over 2,5 {self._fact_text(patterns, 'Over 2,5 %')} %",
            ),
            (
                "Spielkontrolle",
                f"Führungsausbeute {self._fact_text(control, 'Punktausbeute aus Führungen %')} % · "
                f"Comeback {self._fact_text(control, 'Comeback-Quote %')} %",
            ),
            (
                "Konstanz",
                f"PPG-Spannweite {self._fact_text(consistency, 'PPG-Spannweite')} · "
                f"{self._fact_text(consistency, 'Volatilität')}",
            ),
            (
                "Top-Stärke",
                self._sw_short_text(strength),
            ),
            (
                "Top-Schwäche",
                self._sw_short_text(weakness),
            ),
        ]

        return f"""
<div class="attack-kicker">Scouting-Profil</div>
<div class="scout-team">{team_name}</div>
{''.join(
    self._scout_row(title, value)
    for title, value in rows
)}
"""

    def _scout_row(
        self,
        title: str,
        value: str,
    ) -> str:
        return f"""
<div class="scout-row">
    <div class="scout-row-title">{escape(title)}</div>
    <div class="scout-row-value">{escape(value)}</div>
</div>
"""

    def _scout_top_card(
        self,
        label: str,
        value_a: Any,
        value_b: Any,
    ) -> str:
        return f"""
<td>
    <div class="scout-label">{escape(label)}</div>
    <div class="scout-value">
        {escape(self._format_value(value_a))}
        ↔
        {escape(self._format_value(value_b))}
    </div>
</td>
"""

    def _scout_factor_card(
        self,
        title: str,
        body: str,
    ) -> str:
        return f"""
<td>
    <div class="scout-factor-title">{escape(title)}</div>
    <div class="scout-factor-text">{escape(body)}</div>
</td>
"""

    def _fact_text(
        self,
        facts: dict[str, Any],
        key: str,
    ) -> str:
        if not isinstance(facts, dict):
            return "-"
        return self._format_value(
            facts.get(key, "-")
        )

    def _sw_short_text(
        self,
        item: dict[str, Any],
    ) -> str:
        if not isinstance(item, dict) or not item:
            return "-"

        title = str(item.get("title", "-"))
        metric = str(item.get("metric", "")).strip()

        if metric:
            return f"{title}: {metric}"

        return title

    def _find_block_facts(
        self,
        team: dict[str, Any],
        section_name: str,
        block_title: str,
    ) -> dict[str, Any]:
        section = self._section_dict(
            team,
            section_name,
        )

        blocks = section.get("blocks", [])
        if not isinstance(blocks, list):
            return {}

        for block in blocks:
            if not isinstance(block, dict):
                continue
            if str(block.get("title", "")) != block_title:
                continue

            facts = block.get("facts", {})
            return facts if isinstance(facts, dict) else {}

        return {}

    def _render_h2h_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        h2h = self._build_h2h_data(
            team_a_name=team_a_name,
            team_b_name=team_b_name,
            team_a=team_a,
        )

        matches = h2h.get("matches", [])

        if not matches:
            content = f"""
<div class="h2h-empty">
    Für {escape(team_a_name)} und {escape(team_b_name)}
    sind im aktuellen Wettbewerb / in der ausgewählten Saison
    keine abgeschlossenen direkten Duelle vorhanden.
</div>
"""
        else:
            content = self._render_h2h_content(
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                h2h=h2h,
            )

        return f"""
<div class="page page-break">
    <div class="brand">KREISLIGAMANAGER · PREMATCH-REPORT</div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">Direkter Vergleich / H2H</div>

    {content}

    <div class="footer-note">
        Der direkte Vergleich berücksichtigt ausschließlich abgeschlossene
        Duelle, die im aktuell ausgewählten Wettbewerb und dessen
        Reportdaten vorhanden sind.
    </div>
</div>
"""

    def _build_h2h_data(
        self,
        team_a_name: str,
        team_b_name: str,
        team_a: dict[str, Any],
    ) -> dict[str, Any]:
        rows = self._section_table_rows(
            team_a,
            "results",
            "Alle Spiele",
        )

        if not rows:
            rows = self._section_table_rows(
                team_a,
                "results",
                "Letzte 10 Spiele",
            )

        norm_a = self._normalize_team_name_for_h2h(
            team_a_name
        )
        norm_b = self._normalize_team_name_for_h2h(
            team_b_name
        )

        matches: list[dict[str, Any]] = []

        for row in rows:
            if not isinstance(row, list) or len(row) < 5:
                continue

            fixture = str(row[2] or "").strip()
            score = str(row[3] or "").strip()

            teams = fixture.split(" - ", 1)
            if len(teams) != 2:
                continue

            home_name = teams[0].strip()
            away_name = teams[1].strip()

            home_norm = self._normalize_team_name_for_h2h(
                home_name
            )
            away_norm = self._normalize_team_name_for_h2h(
                away_name
            )

            is_direct = (
                home_norm == norm_a
                and away_norm == norm_b
            ) or (
                home_norm == norm_b
                and away_norm == norm_a
            )

            if not is_direct:
                continue

            score_parts = score.split(":", 1)
            if len(score_parts) != 2:
                continue

            try:
                home_goals = int(score_parts[0].strip())
                away_goals = int(score_parts[1].strip())
            except ValueError:
                continue

            team_a_is_home = home_norm == norm_a

            goals_a = (
                home_goals
                if team_a_is_home
                else away_goals
            )
            goals_b = (
                away_goals
                if team_a_is_home
                else home_goals
            )

            if goals_a > goals_b:
                result_a = "S"
            elif goals_a < goals_b:
                result_a = "N"
            else:
                result_a = "U"

            matches.append(
                {
                    "matchday": row[0],
                    "date": row[1],
                    "fixture": fixture,
                    "score": score,
                    "team_a_home": team_a_is_home,
                    "goals_a": goals_a,
                    "goals_b": goals_b,
                    "result_a": result_a,
                }
            )

        wins_a = sum(
            1 for match in matches
            if match["result_a"] == "S"
        )
        draws = sum(
            1 for match in matches
            if match["result_a"] == "U"
        )
        wins_b = sum(
            1 for match in matches
            if match["result_a"] == "N"
        )

        goals_a = sum(
            int(match["goals_a"])
            for match in matches
        )
        goals_b = sum(
            int(match["goals_b"])
            for match in matches
        )

        a_home_matches = [
            match
            for match in matches
            if match["team_a_home"]
        ]
        b_home_matches = [
            match
            for match in matches
            if not match["team_a_home"]
        ]

        return {
            "matches": matches,
            "wins_a": wins_a,
            "draws": draws,
            "wins_b": wins_b,
            "goals_a": goals_a,
            "goals_b": goals_b,
            "team_a_home_matches": len(a_home_matches),
            "team_b_home_matches": len(b_home_matches),
        }

    def _normalize_team_name_for_h2h(
        self,
        value: str,
    ) -> str:
        return " ".join(
            str(value or "")
            .casefold()
            .replace("–", "-")
            .replace("—", "-")
            .split()
        )

    def _render_h2h_content(
        self,
        team_a_name: str,
        team_b_name: str,
        h2h: dict[str, Any],
    ) -> str:
        matches = h2h.get("matches", [])
        wins_a = int(h2h.get("wins_a", 0))
        draws = int(h2h.get("draws", 0))
        wins_b = int(h2h.get("wins_b", 0))
        goals_a = int(h2h.get("goals_a", 0))
        goals_b = int(h2h.get("goals_b", 0))

        last_matches = list(matches)[-5:]
        last_matches.reverse()

        rows = []
        for match in last_matches:
            rows.append(
                f"""
<tr>
    <td>{escape(self._format_value(match.get("matchday", "-")))}</td>
    <td>{escape(str(match.get("date", "-")))}</td>
    <td>{escape(str(match.get("fixture", "-")))}</td>
    <td><b>{escape(str(match.get("score", "-")))}</b></td>
</tr>
"""
            )

        games_table = f"""
<table width="100%" class="h2h-games">
    <tr>
        <th>ST</th>
        <th>Datum</th>
        <th>Spiel</th>
        <th>Ergebnis</th>
    </tr>
    {''.join(rows)}
</table>
"""

        return f"""
<table width="100%" class="h2h-summary">
    <tr>
        {self._h2h_summary_card("Duelle", len(matches))}
        {self._h2h_summary_card(f"Siege {team_a_name}", wins_a)}
        {self._h2h_summary_card("Remis", draws)}
        {self._h2h_summary_card(f"Siege {team_b_name}", wins_b)}
        {self._h2h_summary_card("Torbilanz", f"{goals_a}:{goals_b}")}
    </tr>
</table>

<table width="100%" class="h2h-balance">
    <tr>
        <td class="h2h-a">
            <div class="h2h-team">{team_a_name}</div>
            <table width="100%" class="h2h-record">
                {self._h2h_record_row("Siege", wins_a)}
                {self._h2h_record_row("Remis", draws)}
                {self._h2h_record_row("Niederlagen", wins_b)}
                {self._h2h_record_row("Tore", goals_a)}
                {self._h2h_record_row(
                    "Duelle als Heimteam",
                    h2h.get("team_a_home_matches", 0),
                )}
            </table>
        </td>

        <td class="h2h-b">
            <div class="h2h-team">{team_b_name}</div>
            <table width="100%" class="h2h-record">
                {self._h2h_record_row("Siege", wins_b)}
                {self._h2h_record_row("Remis", draws)}
                {self._h2h_record_row("Niederlagen", wins_a)}
                {self._h2h_record_row("Tore", goals_b)}
                {self._h2h_record_row(
                    "Duelle als Heimteam",
                    h2h.get("team_b_home_matches", 0),
                )}
            </table>
        </td>
    </tr>
</table>

<div class="control-section-title">Letzte direkte Duelle</div>
{games_table}
"""

    def _h2h_summary_card(
        self,
        label: str,
        value: Any,
    ) -> str:
        return f"""
<td>
    <div class="h2h-label">{escape(str(label))}</div>
    <div class="h2h-value">{escape(self._format_value(value))}</div>
</td>
"""

    def _h2h_record_row(
        self,
        label: str,
        value: Any,
    ) -> str:
        return f"""
<tr>
    <td class="h2h-record-label">{escape(label)}</td>
    <td class="h2h-record-value">{escape(self._format_value(value))}</td>
</tr>
"""

    def _render_players_fairplay_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        players_a = self._section_table_rows(
            team_a,
            "players",
            "Spielerübersicht",
        )
        players_b = self._section_table_rows(
            team_b,
            "players",
            "Spielerübersicht",
        )

        discipline_a = self._section_dict(
            team_a,
            "discipline",
        )
        discipline_b = self._section_dict(
            team_b,
            "discipline",
        )

        discipline_facts_a = discipline_a.get("facts", {})
        discipline_facts_b = discipline_b.get("facts", {})
        if not isinstance(discipline_facts_a, dict):
            discipline_facts_a = {}
        if not isinstance(discipline_facts_b, dict):
            discipline_facts_b = {}

        cards_a = self._section_table_rows(
            team_a,
            "discipline",
            "Karten nach Spielern",
        )
        cards_b = self._section_table_rows(
            team_b,
            "discipline",
            "Karten nach Spielern",
        )

        panel_a = self._render_player_fairplay_panel(
            team_name=team_a_name,
            players=players_a,
            discipline_facts=discipline_facts_a,
            cards=cards_a,
        )
        panel_b = self._render_player_fairplay_panel(
            team_name=team_b_name,
            players=players_b,
            discipline_facts=discipline_facts_b,
            cards=cards_b,
        )

        return f"""
<div class="page page-break">
    <div class="brand">KREISLIGAMANAGER · PREMATCH-REPORT</div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">Schlüsselspieler & Fairplay</div>

    <table width="100%" class="pf-layout">
        <tr>
            <td class="pf-panel pf-a">{panel_a}</td>
            <td class="pf-panel pf-b">{panel_b}</td>
        </tr>
    </table>

    <div class="control-section-title">Direkter Vergleich</div>
    <table width="100%" class="pf-compare">
        <tr>
            {self._pf_compare_card(
                "Gelbe Karten",
                discipline_facts_a.get("Gelbe Karten", "-"),
                discipline_facts_b.get("Gelbe Karten", "-"),
            )}
            {self._pf_compare_card(
                "Gelb-Rote Karten",
                discipline_facts_a.get("Gelb-Rote Karten", "-"),
                discipline_facts_b.get("Gelb-Rote Karten", "-"),
            )}
            {self._pf_compare_card(
                "Rote Karten",
                discipline_facts_a.get("Rote Karten", "-"),
                discipline_facts_b.get("Rote Karten", "-"),
            )}
            {self._pf_compare_card(
                "Spieler mit Karten",
                discipline_facts_a.get("Spieler mit Karten", "-"),
                discipline_facts_b.get("Spieler mit Karten", "-"),
            )}
        </tr>
    </table>

    <div class="footer-note">
        Spielerwerte stammen aus den vorhandenen Einsatz-, Tor-, Assist-
        und Kartendaten. Es werden nur bereits erfasste Statistiken gezeigt.
    </div>
</div>
"""

    def _render_player_fairplay_panel(
        self,
        team_name: str,
        players: list[list[Any]],
        discipline_facts: dict[str, Any],
        cards: list[list[Any]],
    ) -> str:
        top_players = players[:5]

        player_rows = []
        for row in top_players:
            if not isinstance(row, list) or len(row) < 10:
                continue

            player_rows.append(
                f"""
<tr>
    <td>{escape(str(row[0]))}</td>
    <td>{escape(str(row[1]))}</td>
    <td>{escape(self._format_value(row[5]))}</td>
    <td>{escape(self._format_value(row[6]))}</td>
    <td>{escape(self._format_value(row[4]))}</td>
</tr>
"""
            )

        if player_rows:
            player_table = f"""
<table width="100%" class="pf-table">
    <tr>
        <th>Spieler</th>
        <th>Pos.</th>
        <th>Tore</th>
        <th>Assists</th>
        <th>Min.</th>
    </tr>
    {''.join(player_rows)}
</table>
"""
        else:
            player_table = '<div class="control-note">Keine Spielerstatistiken vorhanden.</div>'

        top_cards = cards[:4]
        card_rows = []
        for row in top_cards:
            if not isinstance(row, list) or len(row) < 4:
                continue

            card_rows.append(
                f"""
<tr>
    <td>{escape(str(row[0]))}</td>
    <td>{escape(self._format_value(row[1]))}</td>
    <td>{escape(self._format_value(row[2]))}</td>
    <td>{escape(self._format_value(row[3]))}</td>
</tr>
"""
            )

        if card_rows:
            card_table = f"""
<table width="100%" class="pf-table">
    <tr>
        <th>Spieler</th>
        <th>Gelb</th>
        <th>G-R</th>
        <th>Rot</th>
    </tr>
    {''.join(card_rows)}
</table>
"""
        else:
            card_table = '<div class="control-note">Keine Karten nach Spielern vorhanden.</div>'

        return f"""
<div class="attack-kicker">Spielerprofil</div>
<div class="pf-team">{team_name}</div>

<div class="control-section-title">Top-Spieler nach Toren / Assists</div>
{player_table}

<div class="control-section-title">Fairplay</div>
<table width="100%" class="pf-facts">
    <tr>
        {self._pf_fact_card("Gelb", discipline_facts.get("Gelbe Karten", "-"))}
        {self._pf_fact_card("Gelb-Rot", discipline_facts.get("Gelb-Rote Karten", "-"))}
        {self._pf_fact_card("Rot", discipline_facts.get("Rote Karten", "-"))}
        {self._pf_fact_card("Spieler", discipline_facts.get("Spieler mit Karten", "-"))}
    </tr>
</table>

<div class="control-section-title">Spieler mit Karten</div>
{card_table}
"""

    def _section_table_rows(
        self,
        team: dict[str, Any],
        section_name: str,
        table_title: str,
    ) -> list[list[Any]]:
        section = self._section_dict(
            team,
            section_name,
        )

        tables = section.get(
            "tables",
            [],
        )
        if not isinstance(tables, list):
            return []

        for table in tables:
            if not isinstance(table, dict):
                continue

            if str(table.get("title", "")) != table_title:
                continue

            rows = table.get(
                "rows",
                [],
            )
            return rows if isinstance(rows, list) else []

        return []

    def _pf_fact_card(
        self,
        label: str,
        value: Any,
    ) -> str:
        return f"""
<td>
    <div class="pf-fact-label">{escape(label)}</div>
    <div class="pf-fact-value">{escape(self._format_value(value))}</div>
</td>
"""

    def _pf_compare_card(
        self,
        label: str,
        value_a: Any,
        value_b: Any,
    ) -> str:
        return f"""
<td>
    <div class="pf-compare-label">{escape(label)}</div>
    <div class="pf-compare-value">
        {escape(self._format_value(value_a))}
        ↔
        {escape(self._format_value(value_b))}
    </div>
</td>
"""

    def _render_strengths_weaknesses_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        section_a = self._section_dict(
            team_a,
            "strengths_weaknesses",
        )
        section_b = self._section_dict(
            team_b,
            "strengths_weaknesses",
        )

        strengths_a = self._sw_items(section_a, "strengths")
        weaknesses_a = self._sw_items(section_a, "weaknesses")
        strengths_b = self._sw_items(section_b, "strengths")
        weaknesses_b = self._sw_items(section_b, "weaknesses")

        panel_a = self._render_sw_team_panel(
            team_a_name,
            strengths_a,
            weaknesses_a,
        )
        panel_b = self._render_sw_team_panel(
            team_b_name,
            strengths_b,
            weaknesses_b,
        )

        matchup_a = self._render_matchup_pairs(
            strengths_a,
            weaknesses_b,
        )
        matchup_b = self._render_matchup_pairs(
            strengths_b,
            weaknesses_a,
        )

        return f"""
<div class="page page-break">
    <div class="brand">KREISLIGAMANAGER · PREMATCH-REPORT</div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">Stärken ↔ Schwächen</div>

    <table width="100%" class="sw-layout">
        <tr>
            <td class="sw-team-panel sw-team-a">{panel_a}</td>
            <td class="sw-team-panel sw-team-b">{panel_b}</td>
        </tr>
    </table>

    <div class="control-section-title">Matchup-Analyse</div>

    <table width="100%" class="matchup-grid">
        <tr>
            <td class="matchup-a">
                <div class="matchup-heading">
                    {team_a_name}: Ansatzpunkte gegen {team_b_name}
                </div>
                {matchup_a}
            </td>
            <td class="matchup-b">
                <div class="matchup-heading">
                    {team_b_name}: Ansatzpunkte gegen {team_a_name}
                </div>
                {matchup_b}
            </td>
        </tr>
    </table>

    <div class="footer-note">
        Die Matchups stellen die bereits berechneten Top-Stärken
        eines Teams den Top-Schwächen des Gegners gegenüber.
        Sie sind eine Scouting-Gegenüberstellung und keine Prognose.
    </div>
</div>
"""

    def _section_dict(
        self,
        team: dict[str, Any],
        section_name: str,
    ) -> dict[str, Any]:
        sections = team.get("sections", {})
        if not isinstance(sections, dict):
            return {}

        section = sections.get(section_name, {})
        return section if isinstance(section, dict) else {}

    def _sw_items(
        self,
        section: dict[str, Any],
        key: str,
    ) -> list[dict[str, Any]]:
        items = section.get(key, [])
        if not isinstance(items, list):
            return []

        return [
            item
            for item in items[:3]
            if isinstance(item, dict)
        ]

    def _render_sw_team_panel(
        self,
        team_name: str,
        strengths: list[dict[str, Any]],
        weaknesses: list[dict[str, Any]],
    ) -> str:
        return f"""
<div class="attack-kicker">Teamprofil</div>
<div class="sw-team-name">{team_name}</div>

<div class="sw-column-title">Top-Stärken</div>
{self._render_sw_items(strengths, "sw-strength")}

<div class="sw-column-title">Top-Schwächen</div>
{self._render_sw_items(weaknesses, "sw-weakness")}
"""

    def _render_sw_items(
        self,
        items: list[dict[str, Any]],
        css_class: str,
    ) -> str:
        if not items:
            return '<div class="control-note">Keine Daten vorhanden.</div>'

        parts = []
        for item in items:
            title = escape(str(item.get("title", "-")))
            metric = escape(str(item.get("metric", "-")))
            description = escape(str(item.get("text", "")))
            source = escape(str(item.get("source", "")))

            parts.append(
                f"""
<div class="sw-item {css_class}">
    <div class="sw-item-title">{title}</div>
    <div class="sw-item-metric">{metric}</div>
    <div class="sw-item-text">
        {description}
        {f" · Quelle: {source}" if source else ""}
    </div>
</div>
"""
            )

        return "".join(parts)

    def _render_matchup_pairs(
        self,
        strengths: list[dict[str, Any]],
        opponent_weaknesses: list[dict[str, Any]],
    ) -> str:
        pairs = self._semantic_matchup_pairs(
            strengths,
            opponent_weaknesses,
        )

        if not pairs:
            return '<div class="control-note">Keine Matchup-Daten vorhanden.</div>'

        parts = []
        for strength, weakness in pairs:
            strength_title = escape(str(strength.get("title", "-")))
            strength_metric = escape(str(strength.get("metric", "-")))
            weakness_title = escape(str(weakness.get("title", "-")))
            weakness_metric = escape(str(weakness.get("metric", "-")))

            parts.append(
                f"""
<div class="matchup-pair">
    <div class="matchup-pair-title">
        {strength_title}
        <span class="matchup-arrow">↔</span>
        {weakness_title}
    </div>
    <div class="matchup-pair-metric">
        {strength_metric} ↔ {weakness_metric}
    </div>
</div>
"""
            )

        return "".join(parts)

    def _semantic_matchup_pairs(
        self,
        strengths: list[dict[str, Any]],
        weaknesses: list[dict[str, Any]],
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        strengths = [
            item for item in strengths[:3]
            if isinstance(item, dict)
        ]
        remaining = [
            item for item in weaknesses[:3]
            if isinstance(item, dict)
        ]

        pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []

        for strength in strengths:
            if not remaining:
                break

            best_index = max(
                range(len(remaining)),
                key=lambda index: self._matchup_similarity(
                    strength,
                    remaining[index],
                ),
            )

            pairs.append(
                (
                    strength,
                    remaining.pop(best_index),
                )
            )

        return pairs

    def _matchup_similarity(
        self,
        strength: dict[str, Any],
        weakness: dict[str, Any],
    ) -> int:
        strength_text = self._matchup_search_text(strength)
        weakness_text = self._matchup_search_text(weakness)

        categories = (
            ("heim", "auswärts", "home", "away"),
            ("tor", "tore", "treffer", "offensiv", "eigenem tor"),
            ("gegentor", "zu null", "clean sheet", "defensiv", "abwehr"),
            ("beide treffen", "btts"),
            ("over", "2,5", "3,5", "torreich"),
            ("führung", "führungen"),
            ("rückstand", "comeback", "gerettet"),
            ("form", "serie", "konstanz", "volatil", "ppg-spann"),
            ("knapp", "ein-tor", "klar", "tordifferenz"),
        )

        score = 0

        for words in categories:
            if (
                any(word in strength_text for word in words)
                and any(word in weakness_text for word in words)
            ):
                score += 10

        strength_source = str(
            strength.get("source", "")
        ).casefold().strip()
        weakness_source = str(
            weakness.get("source", "")
        ).casefold().strip()

        if (
            strength_source
            and weakness_source
            and strength_source == weakness_source
        ):
            score += 4

        score += len(
            set(strength_text.split())
            & set(weakness_text.split())
        )

        return score

    def _matchup_search_text(
        self,
        item: dict[str, Any],
    ) -> str:
        return " ".join(
            (
                str(item.get("title", "")),
                str(item.get("text", "")),
                str(item.get("source", "")),
            )
        ).casefold()

    def _render_consistency_progress_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        consistency_a = self._section_facts(team_a, "consistency")
        consistency_b = self._section_facts(team_b, "consistency")

        blocks_a = self._section_chart(team_a, "consistency", "form_blocks")
        blocks_b = self._section_chart(team_b, "consistency", "form_blocks")

        progress_a = self._section_chart(
            team_a, "season_progress", "position_progress"
        )
        progress_b = self._section_chart(
            team_b, "season_progress", "position_progress"
        )

        panel_a = self._render_consistency_panel(
            team_a_name, consistency_a, blocks_a
        )
        panel_b = self._render_consistency_panel(
            team_b_name, consistency_b, blocks_b
        )

        progress_table = self._render_progress_comparison(
            team_a_name,
            team_b_name,
            progress_a,
            progress_b,
        )

        return f"""
<div class="page page-break">
    <div class="brand">KREISLIGAMANAGER · PREMATCH-REPORT</div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">Konstanz & Saisonverlauf</div>

    <table width="100%" class="consistency-top">
        <tr>
            <td class="consistency-panel consistency-a">{panel_a}</td>
            <td class="consistency-panel consistency-b">{panel_b}</td>
        </tr>
    </table>

    <div class="control-section-title" style="margin:2px 0 1px 0;">Platzierungsverlauf</div>
    <div class="progress-wrap">
        {progress_table}
    </div>

    <table width="100%" class="consistency-compare">
        <tr>
            {self._consistency_compare_card(
                "PPG-Spannweite",
                consistency_a.get("PPG-Spannweite", "-"),
                consistency_b.get("PPG-Spannweite", "-"),
            )}
            {self._consistency_compare_card(
                "Knappe Spiele",
                consistency_a.get("Knappe Spiele %", "-"),
                consistency_b.get("Knappe Spiele %", "-"),
                "%",
            )}
            {self._consistency_compare_card(
                "Streuung Tordifferenz",
                consistency_a.get("Streuung Tordifferenz", "-"),
                consistency_b.get("Streuung Tordifferenz", "-"),
            )}
            {self._consistency_compare_card(
                "Volatilität",
                consistency_a.get("Volatilität", "-"),
                consistency_b.get("Volatilität", "-"),
            )}
        </tr>
    </table>

    <div class="footer-note">
        Die Formblöcke umfassen jeweils bis zu fünf Spiele.
        Der Platzierungsverlauf stammt aus dem bestehenden Saisonverlauf.
    </div>
</div>
"""

    def _render_consistency_panel(
        self,
        team_name: str,
        facts: dict[str, Any],
        form_blocks: list[dict[str, Any]],
    ) -> str:
        rows = [
            ("Spiele", facts.get("Spiele", "-"), ""),
            ("Knappe Spiele", facts.get("Knappe Spiele %", "-"), " %"),
            ("Ein-Tor-Spiele", facts.get("Ein-Tor-Spiele", "-"), ""),
            ("Klare Siege", facts.get("Klare Siege", "-"), ""),
            ("Klare Niederlagen", facts.get("Klare Niederlagen", "-"), ""),
            ("Ø Tordifferenz", facts.get("Ø Tordifferenz", "-"), ""),
            ("Streuung Tordifferenz", facts.get("Streuung Tordifferenz", "-"), ""),
            ("Volatilität", facts.get("Volatilität", "-"), ""),
            ("PPG-Spannweite", facts.get("PPG-Spannweite", "-"), ""),
        ]

        parts = []
        for label, value, suffix in rows:
            value_text = self._format_value(value)
            if value_text == "-":
                suffix = ""
            parts.append(
                f"""
<tr>
    <td class="consistency-label">{escape(label)}</td>
    <td class="consistency-value">{escape(value_text)}{suffix}</td>
</tr>
"""
            )

        block_html = self._render_form_blocks(form_blocks)

        return f"""
<div class="attack-kicker">Konstanzprofil</div>
<div class="consistency-team">{team_name}</div>
<table width="100%" class="consistency-grid">
    {''.join(parts)}
</table>
<div class="control-section-title">5-Spiele-Blöcke</div>
{block_html}
"""

    def _render_form_blocks(
        self,
        blocks: list[dict[str, Any]],
    ) -> str:
        if not blocks:
            return '<div class="control-note">Keine Formblöcke vorhanden.</div>'

        rows = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            rows.append(
                f"""
<tr>
    <td>{escape(str(block.get("label", "-")))}</td>
    <td>{escape(self._format_value(block.get("ppg", "-")))}</td>
    <td>{escape(self._format_value(block.get("points", "-")))}</td>
    <td>{escape(self._format_value(block.get("goal_difference", "-")))}</td>
</tr>
"""
            )

        return f"""
<table width="100%" class="form-block-table">
    <tr>
        <th>Block</th>
        <th>PPG</th>
        <th>Pkt.</th>
        <th>TD</th>
    </tr>
    {''.join(rows)}
</table>
"""

    def _section_chart(
        self,
        team: dict[str, Any],
        section_name: str,
        chart_name: str,
    ) -> list[dict[str, Any]]:
        sections = team.get("sections", {})
        if not isinstance(sections, dict):
            return []

        section = sections.get(section_name, {})
        if not isinstance(section, dict):
            return []

        charts = section.get("charts", {})
        if not isinstance(charts, dict):
            return []

        chart = charts.get(chart_name, [])
        return chart if isinstance(chart, list) else []

    def _render_progress_comparison(
        self,
        team_a_name: str,
        team_b_name: str,
        progress_a: list[dict[str, Any]],
        progress_b: list[dict[str, Any]],
    ) -> str:
        by_game_a = {
            int(row.get("played", 0)): row
            for row in progress_a
            if isinstance(row, dict) and int(row.get("played", 0)) > 0
        }
        by_game_b = {
            int(row.get("played", 0)): row
            for row in progress_b
            if isinstance(row, dict) and int(row.get("played", 0)) > 0
        }

        games = sorted(set(by_game_a) | set(by_game_b))
        if not games:
            return '<div class="control-note">Kein Platzierungsverlauf vorhanden.</div>'

        # Keep the page compact: show start, every fifth game, and the latest game.
        selected = [
            game for game in games
            if game == games[0] or game % 5 == 0 or game == games[-1]
        ]
        selected = sorted(set(selected))

        cells = []
        for game in selected:
            a = by_game_a.get(game, {}).get("position", "-")
            b = by_game_b.get(game, {}).get("position", "-")
            cells.append(
                f"""
<tr>
    <td>{game}</td>
    <td class="progress-a">{escape(self._format_value(a))}</td>
    <td class="progress-b">{escape(self._format_value(b))}</td>
</tr>
"""
            )

        return f"""
<table width="100%" class="progress-table">
    <tr>
        <th>Nach Spiel</th>
        <th>{team_a_name} · Platz</th>
        <th>{team_b_name} · Platz</th>
    </tr>
    {''.join(cells)}
</table>
"""

    def _consistency_compare_card(
        self,
        label: str,
        value_a: Any,
        value_b: Any,
        suffix: str = "",
    ) -> str:
        a = self._format_value(value_a)
        b = self._format_value(value_b)
        suffix_a = suffix if a != "-" else ""
        suffix_b = suffix if b != "-" else ""

        return f"""
<td>
    <div class="consistency-compare-label">{escape(label)}</div>
    <div class="consistency-compare-value">
        {escape(a)}{suffix_a} ↔ {escape(b)}{suffix_b}
    </div>
</td>
"""

    def _render_control_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        control_a = self._section_facts(
            team_a,
            "control",
        )
        control_b = self._section_facts(
            team_b,
            "control",
        )

        panel_a = self._render_control_panel(
            team_name=team_a_name,
            facts=control_a,
        )
        panel_b = self._render_control_panel(
            team_name=team_b_name,
            facts=control_b,
        )

        return f"""
<div class="page page-break">
    <div class="brand">
        KREISLIGAMANAGER · PREMATCH-REPORT
    </div>

    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>

    <div class="page-title">
        Spielkontrolle
    </div>

    <table width="100%" class="control-layout">
        <tr>
            <td class="control-panel control-panel-a">
                {panel_a}
            </td>
            <td class="control-panel control-panel-b">
                {panel_b}
            </td>
        </tr>
    </table>

    <div class="control-section-title">
        Direkter Vergleich
    </div>

    <table width="100%" class="control-matchups">
        <tr>
            {self._control_compare_card(
                "Punktausbeute aus Führungen",
                control_a.get("Punktausbeute aus Führungen %", "-"),
                control_b.get("Punktausbeute aus Führungen %", "-"),
                "%",
                "Wie viel des möglichen Punktepotenzials nach Führungen gesichert wurde.",
            )}
            {self._control_compare_card(
                "Führungen gewonnen",
                control_a.get("Führungen gewonnen %", "-"),
                control_b.get("Führungen gewonnen %", "-"),
                "%",
                "Anteil der Führungen, die am Ende tatsächlich zu einem Sieg führten.",
            )}
            {self._control_compare_card(
                "Comeback-Quote",
                control_a.get("Comeback-Quote %", "-"),
                control_b.get("Comeback-Quote %", "-"),
                "%",
                "Anteil der Rückstände, aus denen noch Sieg oder Remis erreicht wurde.",
            )}
            {self._control_compare_card(
                "Punkte nach Rückstand",
                control_a.get("Punkte nach Rückstand", "-"),
                control_b.get("Punkte nach Rückstand", "-"),
                "",
                "Gesicherte Punkte in Spielen, in denen die Mannschaft zurücklag.",
            )}
        </tr>
    </table>

    <div class="footer-note">
        Die Seite basiert ausschließlich auf den vorhandenen Führungs-
        und Rückstandsdaten des KreisligaManagers.
    </div>
</div>
"""

    def _render_control_panel(
        self,
        team_name: str,
        facts: dict[str, Any],
    ) -> str:
        lead_rows = [
            ("Führungen", facts.get("Führungen", "-"), ""),
            ("Siege nach Führung", facts.get("Siege nach Führung", "-"), ""),
            ("Remis nach Führung", facts.get("Remis nach Führung", "-"), ""),
            ("Niederlagen nach Führung", facts.get("Niederlagen nach Führung", "-"), ""),
            ("Führungen gewonnen", facts.get("Führungen gewonnen %", "-"), " %"),
            ("Punkte aus Führungen", facts.get("Punkte aus Führungen", "-"), ""),
            ("Punktepotenzial", facts.get("Punktepotenzial aus Führungen", "-"), ""),
            ("Punkte verloren", facts.get("Punkte nach Führung verloren", "-"), ""),
            ("Punktausbeute", facts.get("Punktausbeute aus Führungen %", "-"), " %"),
        ]

        trail_rows = [
            ("Rückstände", facts.get("Rückstände", "-"), ""),
            ("Siege nach Rückstand", facts.get("Siege nach Rückstand", "-"), ""),
            ("Remis nach Rückstand", facts.get("Remis nach Rückstand", "-"), ""),
            ("Niederlagen nach Rückstand", facts.get("Niederlagen nach Rückstand", "-"), ""),
            ("Gerettete Spiele", facts.get("Gerettete Spiele", "-"), ""),
            ("Comeback-Quote", facts.get("Comeback-Quote %", "-"), " %"),
            ("Punkte nach Rückstand", facts.get("Punkte nach Rückstand", "-"), ""),
        ]

        return f"""
<div class="attack-kicker">
    Führung & Rückstand
</div>
<div class="control-team">
    {team_name}
</div>

<div class="control-section-title">
    Führung verwalten
</div>
<table width="100%" class="control-grid">
    {self._control_rows_html(lead_rows)}
</table>

<div class="control-section-title">
    Rückstände drehen
</div>
<table width="100%" class="control-grid">
    {self._control_rows_html(trail_rows)}
</table>
"""

    def _control_rows_html(
        self,
        rows: list[tuple[str, Any, str]],
    ) -> str:
        parts: list[str] = []

        for label, value, suffix in rows:
            value_text = self._format_value(
                value
            )

            if value_text == "-":
                suffix = ""

            parts.append(
                f"""
<tr>
    <td class="control-label">
        {escape(label)}
    </td>
    <td class="control-value">
        {escape(value_text)}{suffix}
    </td>
</tr>
"""
            )

        return "".join(
            parts
        )

    def _control_compare_card(
        self,
        label: str,
        value_a: Any,
        value_b: Any,
        suffix: str,
        note: str,
    ) -> str:
        a = self._format_value(
            value_a
        )
        b = self._format_value(
            value_b
        )

        suffix_a = (
            suffix
            if a != "-"
            else ""
        )
        suffix_b = (
            suffix
            if b != "-"
            else ""
        )

        return f"""
<td>
    <div class="control-matchup-label">
        {escape(label)}
    </div>
    <div class="control-matchup-value">
        {escape(a)}{suffix_a}
        ↔
        {escape(b)}{suffix_b}
    </div>
    <div class="control-note">
        {escape(note)}
    </div>
</td>
"""

    def _render_halftime_phases_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        facts_a = self._section_facts(team_a, "halftime_phases")
        facts_b = self._section_facts(team_b, "halftime_phases")

        phases_a = self._extract_minute_phases(team_a)
        phases_b = self._extract_minute_phases(team_b)

        panel_a = self._render_halftime_team_panel(
            team_a_name, facts_a, "phase-team-a"
        )
        panel_b = self._render_halftime_team_panel(
            team_b_name, facts_b, "phase-team-b"
        )

        phase_table = self._render_minute_phase_table(
            team_a_name,
            team_b_name,
            phases_a,
            phases_b,
        )

        return f"""
<div class="page page-break">
    <div class="brand">KREISLIGAMANAGER · PREMATCH-REPORT</div>
    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>
    <div class="page-title">Torphasen & Halbzeiten</div>

    <table width="100%" class="phase-halves">
        <tr>
            <td class="phase-team phase-team-a">{panel_a}</td>
            <td class="phase-team phase-team-b">{panel_b}</td>
        </tr>
    </table>

    <div class="patterns-summary-title">15-Minuten-Torphasen</div>
    {phase_table}

    <table width="100%" class="phase-summary">
        <tr>
            {self._phase_summary_card("HZ-Führung gehalten",
                facts_a.get("Führung gehalten %", "-"),
                facts_b.get("Führung gehalten %", "-"), "%")}
            {self._phase_summary_card("Comeback nach HZ-Rückstand",
                facts_a.get("Comeback-Quote nach HZ %", "-"),
                facts_b.get("Comeback-Quote nach HZ %", "-"), "%")}
            {self._phase_summary_card("Punkte nach HZ-Rückstand",
                facts_a.get("Punkte nach HZ-Rückstand", "-"),
                facts_b.get("Punkte nach HZ-Rückstand", "-"), "")}
            {self._phase_summary_card("Sieg nach HZ-Remis",
                facts_a.get("Siegquote nach HZ-Remis %", "-"),
                facts_b.get("Siegquote nach HZ-Remis %", "-"), "%")}
        </tr>
    </table>

    <div class="footer-note">
        Halbzeitwerte basieren auf Spielen mit vorhandenem Halbzeitstand.
        15-Minuten-Werte werden nur angezeigt, wenn entsprechende
        Ereignis-/Minutendaten im Report vorhanden sind.
    </div>
</div>
"""

    def _render_halftime_team_panel(
        self,
        team_name: str,
        facts: dict[str, Any],
        css_class: str,
    ) -> str:
        first_for = facts.get("Tore 1. HZ", "-")
        first_against = facts.get("Gegentore 1. HZ", "-")
        second_for = facts.get("Tore 2. HZ", "-")
        second_against = facts.get("Gegentore 2. HZ", "-")

        states = (
            f'Führung <b>{escape(self._format_value(facts.get("Halbzeitführung", "-")))}</b>'
            f' · Remis <b>{escape(self._format_value(facts.get("Halbzeitremis", "-")))}</b>'
            f' · Rückstand <b>{escape(self._format_value(facts.get("Halbzeitrückstand", "-")))}</b>'
        )

        return f"""
<div class="attack-kicker">Halbzeitprofil</div>
<div class="phase-team-name">{team_name}</div>
<table width="100%" class="half-grid">
    <tr>
        <td class="half-card">
            <div class="half-title">1. Halbzeit · Tore : Gegentore</div>
            <div class="half-score">
                {escape(self._format_value(first_for))}
                :
                {escape(self._format_value(first_against))}
            </div>
        </td>
        <td class="half-card">
            <div class="half-title">2. Halbzeit · Tore : Gegentore</div>
            <div class="half-score">
                {escape(self._format_value(second_for))}
                :
                {escape(self._format_value(second_against))}
            </div>
        </td>
    </tr>
</table>
<div class="half-note">
    Spiele mit Halbzeitstand:
    <b>{escape(self._format_value(facts.get("Spiele mit Halbzeitstand", "-")))}</b>
    · {states}
</div>
"""

    def _extract_minute_phases(
        self,
        team: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        intervals = [
            "0-15", "16-30", "31-45",
            "46-60", "61-75", "76-90",
        ]
        result = {
            label: {"for": None, "against": None}
            for label in intervals
        }

        sections = team.get("sections", {})
        if not isinstance(sections, dict):
            return result

        def normalize_label(value: Any) -> str:
            label = str(value or "").replace("–", "-").replace("—", "-")
            label = label.replace("'", "").replace("Min.", "").strip()
            return label

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                label = normalize_label(
                    value.get("label")
                    or value.get("interval")
                    or value.get("phase")
                    or value.get("minute_range")
                )
                matched = next(
                    (x for x in intervals if x in label),
                    None,
                )
                if matched:
                    for_key = next(
                        (
                            k for k in (
                                "goals_for", "goals", "scored",
                                "goals_scored", "for",
                            )
                            if k in value
                        ),
                        None,
                    )
                    against_key = next(
                        (
                            k for k in (
                                "goals_against", "conceded",
                                "goals_conceded", "against",
                            )
                            if k in value
                        ),
                        None,
                    )
                    if for_key:
                        result[matched]["for"] = value.get(for_key)
                    if against_key:
                        result[matched]["against"] = value.get(against_key)

                for child in value.values():
                    walk(child)

            elif isinstance(value, list):
                for child in value:
                    walk(child)

        for section_name in (
            "goals",
            "match_flow",
            "halftime_phases",
        ):
            if section_name in sections:
                walk(sections[section_name])

        return result

    def _render_minute_phase_table(
        self,
        team_a_name: str,
        team_b_name: str,
        phases_a: dict[str, dict[str, Any]],
        phases_b: dict[str, dict[str, Any]],
    ) -> str:
        intervals = [
            "0-15", "16-30", "31-45",
            "46-60", "61-75", "76-90",
        ]

        available = any(
            phases_a[x]["for"] is not None
            or phases_a[x]["against"] is not None
            or phases_b[x]["for"] is not None
            or phases_b[x]["against"] is not None
            for x in intervals
        )

        if not available:
            return """
<div class="margin-text">
    Keine ausreichend vollständigen 15-Minuten-Ereignisdaten vorhanden.
</div>
"""

        rows = []
        for interval in intervals:
            a = phases_a[interval]
            b = phases_b[interval]

            a_for = self._format_value(a["for"]) if a["for"] is not None else "-"
            a_against = self._format_value(a["against"]) if a["against"] is not None else "-"
            b_for = self._format_value(b["for"]) if b["for"] is not None else "-"
            b_against = self._format_value(b["against"]) if b["against"] is not None else "-"

            rows.append(
                f"""
<tr>
    <td><b>{interval}</b></td>
    <td>{escape(a_for)}</td>
    <td>{escape(a_against)}</td>
    <td>{escape(b_for)}</td>
    <td>{escape(b_against)}</td>
</tr>
"""
            )

        return f"""
<table width="100%" class="phase-table">
    <tr>
        <th>Minute</th>
        <th>{team_a_name} · Tore</th>
        <th>{team_a_name} · Gegentore</th>
        <th>{team_b_name} · Tore</th>
        <th>{team_b_name} · Gegentore</th>
    </tr>
    {''.join(rows)}
</table>
"""

    def _phase_summary_card(
        self,
        label: str,
        value_a: Any,
        value_b: Any,
        suffix: str,
    ) -> str:
        a = self._format_value(value_a)
        b = self._format_value(value_b)
        suffix_a = suffix if a != "-" else ""
        suffix_b = suffix if b != "-" else ""

        return f"""
<td>
    <div class="phase-summary-label">{escape(label)}</div>
    <div class="phase-summary-value">
        {escape(a)}{suffix_a} ↔ {escape(b)}{suffix_b}
    </div>
</td>
"""

    def _render_patterns_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        patterns_a = self._section_facts(
            team_a,
            "patterns",
        )
        patterns_b = self._section_facts(
            team_b,
            "patterns",
        )

        panel_a = self._render_patterns_panel(
            team_name=team_a_name,
            facts=patterns_a,
        )
        panel_b = self._render_patterns_panel(
            team_name=team_b_name,
            facts=patterns_b,
        )

        btts_a = patterns_a.get(
            "Beide treffen %",
            "-",
        )
        btts_b = patterns_b.get(
            "Beide treffen %",
            "-",
        )
        over25_a = patterns_a.get(
            "Over 2,5 %",
            "-",
        )
        over25_b = patterns_b.get(
            "Over 2,5 %",
            "-",
        )
        scored_first_a = patterns_a.get(
            "Erstes Tor erzielt %",
            "-",
        )
        scored_first_b = patterns_b.get(
            "Erstes Tor erzielt %",
            "-",
        )

        margins_a = self._result_margin_summary(
            team_a
        )
        margins_b = self._result_margin_summary(
            team_b
        )

        return f"""
<div class="page page-break">
    <div class="brand">
        KREISLIGAMANAGER · PREMATCH-REPORT
    </div>

    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>

    <div class="page-title">
        Spielmuster & Torcharakter
    </div>

    <table width="100%" class="patterns-layout">
        <tr>
            <td class="patterns-panel patterns-panel-a">
                {panel_a}
            </td>
            <td class="patterns-panel patterns-panel-b">
                {panel_b}
            </td>
        </tr>
    </table>

    <div class="patterns-summary-title">
        Direkte Matchup-Perspektive
    </div>

    <table width="100%" class="patterns-summary">
        <tr>
            <td>
                <div class="patterns-summary-label">
                    Beide treffen
                </div>
                <div class="patterns-summary-value">
                    {escape(self._format_value(btts_a))} %
                    ↔
                    {escape(self._format_value(btts_b))} %
                </div>
                <div class="patterns-summary-note">
                    Wie häufig beide Mannschaften in den
                    jeweiligen Spielen getroffen haben.
                </div>
            </td>

            <td>
                <div class="patterns-summary-label">
                    Over 2,5
                </div>
                <div class="patterns-summary-value">
                    {escape(self._format_value(over25_a))} %
                    ↔
                    {escape(self._format_value(over25_b))} %
                </div>
                <div class="patterns-summary-note">
                    Anteil der Spiele mit mindestens drei Toren.
                </div>
            </td>

            <td>
                <div class="patterns-summary-label">
                    Erstes Tor erzielt
                </div>
                <div class="patterns-summary-value">
                    {escape(self._format_value(scored_first_a))} %
                    ↔
                    {escape(self._format_value(scored_first_b))} %
                </div>
                <div class="patterns-summary-note">
                    Anteil der Spiele, in denen das Team
                    die Partie mit dem ersten Treffer eröffnet hat.
                </div>
            </td>
        </tr>
    </table>

    <table width="100%" class="margin-row">
        <tr>
            <td>
                <div class="margin-title">{team_a_name} · Ergebnismargen</div>
                <div class="margin-text">{margins_a}</div>
            </td>
            <td>
                <div class="margin-title">{team_b_name} · Ergebnismargen</div>
                <div class="margin-text">{margins_b}</div>
            </td>
        </tr>
    </table>

    <div class="footer-note">
        Grundlage sind die vorhandenen Spielmuster- und
        Toreröffnungsdaten des Teamreports.
    </div>
</div>
"""

    def _render_patterns_panel(
        self,
        team_name: str,
        facts: dict[str, Any],
    ) -> str:
        rows = [
            (
                "Beide treffen",
                facts.get("Beide treffen %", "-"),
                " %",
            ),
            (
                "Over 1,5",
                facts.get("Over 1,5 %", "-"),
                " %",
            ),
            (
                "Over 2,5",
                facts.get("Over 2,5 %", "-"),
                " %",
            ),
            (
                "Over 3,5",
                facts.get("Over 3,5 %", "-"),
                " %",
            ),
            (
                "Erstes Tor erzielt",
                facts.get("Erstes Tor erzielt %", "-"),
                " %",
            ),
            (
                "Erstes Tor kassiert",
                facts.get("Erstes Tor kassiert %", "-"),
                " %",
            ),
            (
                "Ohne eigenes Tor",
                facts.get("Ohne eigenes Tor %", "-"),
                " %",
            ),
            (
                "Zu Null",
                facts.get("Zu Null %", "-"),
                " %",
            ),
            (
                "Ø Gesamttore / Spiel",
                facts.get("Ø Gesamttore / Spiel", "-"),
                "",
            ),
        ]

        row_parts: list[str] = []

        for label, value, suffix in rows:
            value_text = self._format_value(
                value
            )

            if value_text == "-":
                suffix = ""

            row_parts.append(
                f"""
<tr>
    <td class="patterns-grid-label">
        {escape(label)}
    </td>
    <td class="patterns-grid-value">
        {escape(value_text)}{suffix}
    </td>
</tr>
"""
            )

        return f"""
<div class="attack-kicker">
    Spielmuster
</div>
<div class="patterns-team">
    {team_name}
</div>
<table width="100%" class="patterns-grid">
    {''.join(row_parts)}
</table>
"""

    def _result_margin_summary(
        self,
        team: dict[str, Any],
    ) -> str:
        sections = team.get(
            "sections",
            {},
        )

        if not isinstance(
            sections,
            dict,
        ):
            return "-"

        patterns = sections.get(
            "patterns",
            {},
        )

        if not isinstance(
            patterns,
            dict,
        ):
            return "-"

        blocks = patterns.get(
            "blocks",
            [],
        )

        if not isinstance(
            blocks,
            list,
        ):
            return "-"

        margin_facts: dict[str, Any] = {}

        for block in blocks:
            if not isinstance(
                block,
                dict,
            ):
                continue

            if str(
                block.get(
                    "title",
                    "",
                )
            ) != "Ergebnismargen":
                continue

            facts = block.get(
                "facts",
                {},
            )

            if isinstance(
                facts,
                dict,
            ):
                margin_facts = facts
            break

        if not margin_facts:
            return "-"

        order = [
            "Siege mit 1 Tor",
            "Siege mit 2+ Toren",
            "Remis",
            "Niederlagen mit 1 Tor",
            "Niederlagen mit 2+ Toren",
        ]

        parts: list[str] = []

        for label in order:
            if label not in margin_facts:
                continue

            parts.append(
                f"{escape(label)}: "
                f"<b>{escape(self._format_value(margin_facts[label]))}</b>"
            )

        return " · ".join(
            parts
        ) if parts else "-"

    def _render_attack_defense_page(
        self,
        team_a_name: str,
        team_b_name: str,
        competition_name: str,
        season_name: str,
        team_a: dict[str, Any],
        team_b: dict[str, Any],
    ) -> str:
        attack_a = self._section_facts(
            team_a,
            "attack_defense",
        )
        attack_b = self._section_facts(
            team_b,
            "attack_defense",
        )
        overview_a = self._section_facts(
            team_a,
            "overview",
        )
        overview_b = self._section_facts(
            team_b,
            "overview",
        )

        goals_a = overview_a.get("Tore / Spiel", "-")
        goals_b = overview_b.get("Tore / Spiel", "-")
        conceded_a = overview_a.get("Gegentore / Spiel", "-")
        conceded_b = overview_b.get("Gegentore / Spiel", "-")

        panel_a = self._render_attack_panel(
            team_name=team_a_name,
            goals_per_game=goals_a,
            conceded_per_game=conceded_a,
            facts=attack_a,
        )
        panel_b = self._render_attack_panel(
            team_name=team_b_name,
            goals_per_game=goals_b,
            conceded_per_game=conceded_b,
            facts=attack_b,
        )

        multi_a = attack_a.get(
            "Mind. 2 eigene Tore %",
            "-",
        )
        multi_b = attack_b.get(
            "Mind. 2 eigene Tore %",
            "-",
        )

        return f"""
<div class="page page-break">
    <div class="brand">
        KREISLIGAMANAGER · PREMATCH-REPORT
    </div>

    <div class="page-kicker">
        {team_a_name} vs. {team_b_name} ·
        {competition_name} · Saison {season_name}
    </div>

    <div class="page-title">
        Offensive ↔ Defensive
    </div>

    <table width="100%" class="attack-layout">
        <tr>
            <td class="attack-panel attack-panel-a">
                {panel_a}
            </td>
            <td class="attack-panel attack-panel-b">
                {panel_b}
            </td>
        </tr>
    </table>

    <div class="attack-matchup-title">
        Direkte Matchup-Perspektive
    </div>

    <table width="100%" class="attack-matchups">
        <tr>
            <td>
                <div class="attack-matchup-label">
                    {team_a_name} Angriff ↔ {team_b_name} Defensive
                </div>
                <div class="attack-matchup-value">
                    {escape(self._format_value(goals_a))}
                    ↔
                    {escape(self._format_value(conceded_b))}
                </div>
                <div class="attack-matchup-note">
                    Eigene Tore/Spiel von Team A gegen
                    Gegentore/Spiel von Team B.
                </div>
            </td>

            <td>
                <div class="attack-matchup-label">
                    {team_b_name} Angriff ↔ {team_a_name} Defensive
                </div>
                <div class="attack-matchup-value">
                    {escape(self._format_value(goals_b))}
                    ↔
                    {escape(self._format_value(conceded_a))}
                </div>
                <div class="attack-matchup-note">
                    Eigene Tore/Spiel von Team B gegen
                    Gegentore/Spiel von Team A.
                </div>
            </td>

            <td>
                <div class="attack-matchup-label">
                    Mindestens zwei eigene Tore
                </div>
                <div class="attack-matchup-value">
                    {escape(self._format_value(multi_a))} %
                    ↔
                    {escape(self._format_value(multi_b))} %
                </div>
                <div class="attack-matchup-note">
                    Anteil der Spiele mit mindestens zwei
                    eigenen Treffern.
                </div>
            </td>
        </tr>
    </table>

    <div class="footer-note">
        Grundlage ist das bestehende Offensiv-/Defensivprofil
        des Teamreports. Es werden keine Prognosewerte erfunden.
    </div>
</div>
"""

    def _render_attack_panel(
        self,
        team_name: str,
        goals_per_game: Any,
        conceded_per_game: Any,
        facts: dict[str, Any],
    ) -> str:
        rows = [
            ("Tore / Spiel", goals_per_game, ""),
            ("Gegentore / Spiel", conceded_per_game, ""),
            (
                "Mit eigenem Tor",
                facts.get("Mit eigenem Tor %", "-"),
                " %",
            ),
            (
                "Mind. 2 eigene Tore",
                facts.get("Mind. 2 eigene Tore %", "-"),
                " %",
            ),
            (
                "Zu Null",
                facts.get("Zu Null %", "-"),
                " %",
            ),
            (
                "Max. 1 Gegentor",
                facts.get("Max. 1 Gegentor %", "-"),
                " %",
            ),
            (
                "Mind. 3 Gegentore",
                facts.get("Mind. 3 Gegentore %", "-"),
                " %",
            ),
            (
                "PPG bei 2 Toren",
                facts.get("PPG bei 2 Toren", "-"),
                "",
            ),
            (
                "PPG bei 3+ Toren",
                facts.get("PPG bei 3+ Toren", "-"),
                "",
            ),
        ]

        row_parts: list[str] = []

        for label, value, suffix in rows:
            value_text = self._format_value(
                value
            )

            if value_text == "-":
                suffix = ""

            row_parts.append(
                f"""
<tr>
    <td class="attack-metric-label">
        {escape(label)}
    </td>
    <td class="attack-metric-value">
        {escape(value_text)}{suffix}
    </td>
</tr>
"""
            )

        return f"""
<div class="attack-kicker">
    Offensiv- & Defensivprofil
</div>
<div class="attack-team">
    {team_name}
</div>
<table width="100%" class="attack-metric-grid">
    {''.join(row_parts)}
</table>
"""

    def _section_facts(
        self,
        team: dict[str, Any],
        section_name: str,
    ) -> dict[str, Any]:
        sections = team.get(
            "sections",
            {},
        )

        if not isinstance(
            sections,
            dict,
        ):
            return {}

        section = sections.get(
            section_name,
            {},
        )

        if not isinstance(
            section,
            dict,
        ):
            return {}

        facts = section.get(
            "facts",
            {},
        )

        if not isinstance(
            facts,
            dict,
        ):
            return {}

        return facts

    def _overview_fact(
        self,
        team: dict[str, Any],
        key: str,
    ) -> Any:
        sections = team.get(
            "sections",
            {}
        )

        if not isinstance(
            sections,
            dict,
        ):
            return "-"

        overview = sections.get(
            "overview",
            {}
        )

        if not isinstance(
            overview,
            dict,
        ):
            return "-"

        facts = overview.get(
            "facts",
            {}
        )

        if not isinstance(
            facts,
            dict,
        ):
            return "-"

        return facts.get(
            key,
            "-",
        )

    def _block_facts(
        self,
        block: Any,
    ) -> dict[str, Any]:
        if not isinstance(
            block,
            dict,
        ):
            return {}

        facts = block.get(
            "facts"
        )

        if isinstance(
            facts,
            dict,
        ):
            return facts

        rows = block.get(
            "rows"
        )

        if isinstance(
            rows,
            list,
        ):
            result: dict[str, Any] = {}

            for row in rows:
                if isinstance(
                    row,
                    dict,
                ):
                    label = (
                        row.get(
                            "label"
                        )
                        or row.get(
                            "name"
                        )
                    )
                    value = row.get(
                        "value"
                    )

                    if label is not None:
                        result[
                            str(
                                label
                            )
                        ] = value

            return result

        return {}

    def _render_fact_rows(
        self,
        facts: dict[str, Any],
    ) -> str:
        if not facts:
            return """
<tr>
    <td class="venue-fact-label">
        Keine Venue-Daten
    </td>
    <td class="venue-fact-value">-</td>
</tr>
"""

        rows = []

        for label, value in list(
            facts.items()
        )[:10]:
            rows.append(
                f"""
<tr>
    <td class="venue-fact-label">
        {escape(str(label))}
    </td>
    <td class="venue-fact-value">
        {escape(self._format_value(value))}
    </td>
</tr>
"""
            )

        return "".join(
            rows
        )

    def _find_fact(
        self,
        facts: dict[str, Any],
        candidates: tuple[str, ...],
    ) -> Any:
        for candidate in candidates:
            if candidate in facts:
                return facts[
                    candidate
                ]

        return "-"

    @staticmethod
    def _rate_from_facts(
        facts: dict[str, Any],
        value_keys: tuple[str, ...],
        games_keys: tuple[str, ...],
    ) -> float | str:
        value: Any = None
        games: Any = None

        for key in value_keys:
            if key in facts:
                value = facts.get(
                    key
                )
                break

        for key in games_keys:
            if key in facts:
                games = facts.get(
                    key
                )
                break

        try:
            numeric_value = float(
                value
            )
            numeric_games = float(
                games
            )
        except (
            TypeError,
            ValueError,
        ):
            return "-"

        if numeric_games <= 0:
            return "-"

        return round(
            numeric_value
            / numeric_games,
            2,
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

        return str(
            value
        )
