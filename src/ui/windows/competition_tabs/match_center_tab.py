from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from src.services.prediction.prediction_service import (
    PredictionMode,
    PredictionService,
)

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class CompetitionMatchCenterTab(QWidget):

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.competition_id: int | None = None
        self.connection: sqlite3.Connection | None = None
        self.prediction_service: PredictionService | None = None

        self._setup_ui()
        self._reset_view()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_content = QWidget()
        self.scroll_content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        main_layout = QVBoxLayout(self.scroll_content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        self.scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.scroll_area)

        title = QLabel("⚽ Match-Center")
        title.setObjectName("PageTitle")
        main_layout.addWidget(title)

        subtitle = QLabel(
            "Alle wichtigen Informationen zu einem Spiel "
            "auf einen Blick."
        )
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)

        # -------------------------------------------------
        # AUSWAHL
        # -------------------------------------------------

        controls_frame = QFrame()
        controls_frame.setObjectName("MatchCenterControls")

        controls_layout = QGridLayout(controls_frame)
        controls_layout.setContentsMargins(16, 14, 16, 14)
        controls_layout.setHorizontalSpacing(12)
        controls_layout.setVerticalSpacing(10)

        controls_layout.addWidget(QLabel("Spieltag"), 0, 0)

        self.matchday_combo = QComboBox()
        self.matchday_combo.setMinimumWidth(130)
        self.matchday_combo.currentIndexChanged.connect(
            self._matchday_changed
        )
        controls_layout.addWidget(
            self.matchday_combo,
            0,
            1,
        )

        controls_layout.addWidget(QLabel("Spiel"), 0, 2)

        self.match_combo = QComboBox()
        self.match_combo.setMinimumWidth(360)
        self.match_combo.currentIndexChanged.connect(
            self._match_changed
        )
        controls_layout.addWidget(
            self.match_combo,
            0,
            3,
        )

        controls_layout.setColumnStretch(3, 1)
        main_layout.addWidget(controls_frame)

        # -------------------------------------------------
        # MATCH HEADER
        # -------------------------------------------------

        match_frame = QFrame()
        match_frame.setObjectName("MatchCenterHeader")

        match_layout = QGridLayout(match_frame)
        match_layout.setContentsMargins(24, 20, 24, 20)
        match_layout.setHorizontalSpacing(20)
        match_layout.setVerticalSpacing(8)

        self.matchday_header_label = QLabel("SPIEL")
        self.matchday_header_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.matchday_header_label.setStyleSheet(
            "font-size: 13px; font-weight: 600;"
        )
        match_layout.addWidget(
            self.matchday_header_label,
            0,
            0,
            1,
            3,
        )

        self.home_team_label = QLabel("Heim")
        self.home_team_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.home_team_label.setWordWrap(True)
        self.home_team_label.setStyleSheet(
            "font-size: 20px; font-weight: 700;"
        )

        separator = QLabel("–")
        separator.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        separator.setStyleSheet(
            "font-size: 22px; font-weight: 700;"
        )

        self.away_team_label = QLabel("Auswärts")
        self.away_team_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.away_team_label.setWordWrap(True)
        self.away_team_label.setStyleSheet(
            "font-size: 20px; font-weight: 700;"
        )

        match_layout.addWidget(
            self.home_team_label,
            1,
            0,
        )
        match_layout.addWidget(
            separator,
            1,
            1,
        )
        match_layout.addWidget(
            self.away_team_label,
            1,
            2,
        )

        self.home_position_label = QLabel("Platz –")
        self.home_position_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.away_position_label = QLabel("Platz –")
        self.away_position_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        match_layout.addWidget(
            self.home_position_label,
            2,
            0,
        )
        match_layout.addWidget(
            self.away_position_label,
            2,
            2,
        )

        self.match_info_label = QLabel("–")
        self.match_info_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.match_info_label.setWordWrap(True)
        match_layout.addWidget(
            self.match_info_label,
            3,
            0,
            1,
            3,
        )

        self.result_label = QLabel("")
        self.result_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.result_label.setStyleSheet(
            "font-size: 30px; font-weight: 700;"
        )
        match_layout.addWidget(
            self.result_label,
            4,
            0,
            1,
            3,
        )

        match_layout.setColumnStretch(0, 1)
        match_layout.setColumnStretch(2, 1)

        main_layout.addWidget(match_frame)

        # -------------------------------------------------
        # FORM + TABELLE VOR DEM SPIEL
        # -------------------------------------------------

        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(12)

        form_frame = QFrame()
        form_frame.setObjectName("MatchCenterForm")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(16, 12, 16, 12)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)

        form_title = QLabel("📈 Form")
        form_title.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        form_layout.addWidget(form_title, 0, 0, 1, 2)

        self.home_form_name_label = QLabel("Heim")
        self.home_form_name_label.setStyleSheet("font-weight: 600;")

        self.home_form_widget = QWidget()
        self.home_form_layout = QHBoxLayout(
            self.home_form_widget
        )
        self.home_form_layout.setContentsMargins(0, 0, 0, 0)
        self.home_form_layout.setSpacing(6)
        self.home_form_layout.addStretch(1)

        self.away_form_name_label = QLabel("Auswärts")
        self.away_form_name_label.setStyleSheet("font-weight: 600;")

        self.away_form_widget = QWidget()
        self.away_form_layout = QHBoxLayout(
            self.away_form_widget
        )
        self.away_form_layout.setContentsMargins(0, 0, 0, 0)
        self.away_form_layout.setSpacing(6)
        self.away_form_layout.addStretch(1)

        form_layout.addWidget(self.home_form_name_label, 1, 0)
        form_layout.addWidget(self.home_form_widget, 1, 1)
        form_layout.addWidget(self.away_form_name_label, 2, 0)
        form_layout.addWidget(self.away_form_widget, 2, 1)

        form_hint = QLabel("Letzte 5 Spiele vor diesem Spiel")
        form_hint.setStyleSheet("font-size: 11px;")
        form_layout.addWidget(form_hint, 3, 0, 1, 2)
        form_layout.setColumnStretch(0, 1)

        table_frame = QFrame()
        table_frame.setObjectName("MatchCenterTable")
        table_layout = QGridLayout(table_frame)
        table_layout.setContentsMargins(16, 12, 16, 12)
        table_layout.setHorizontalSpacing(12)
        table_layout.setVerticalSpacing(8)

        table_title = QLabel("📊 Tabelle")
        table_title.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        table_layout.addWidget(table_title, 0, 0, 1, 3)

        self.home_table_name_label = QLabel("Heim")
        self.home_table_name_label.setStyleSheet("font-weight: 600;")
        self.home_table_position_label = QLabel("Platz –")
        self.home_table_points_label = QLabel("– Punkte")

        self.away_table_name_label = QLabel("Auswärts")
        self.away_table_name_label.setStyleSheet("font-weight: 600;")
        self.away_table_position_label = QLabel("Platz –")
        self.away_table_points_label = QLabel("– Punkte")

        for label in (
            self.home_table_position_label,
            self.home_table_points_label,
            self.away_table_position_label,
            self.away_table_points_label,
        ):
            label.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

        table_layout.addWidget(self.home_table_name_label, 1, 0)
        table_layout.addWidget(self.home_table_position_label, 1, 1)
        table_layout.addWidget(self.home_table_points_label, 1, 2)

        table_layout.addWidget(self.away_table_name_label, 2, 0)
        table_layout.addWidget(self.away_table_position_label, 2, 1)
        table_layout.addWidget(self.away_table_points_label, 2, 2)

        table_hint = QLabel("Tabellenstand vor diesem Spieltag")
        table_hint.setStyleSheet("font-size: 11px;")
        table_layout.addWidget(table_hint, 3, 0, 1, 3)
        table_layout.setColumnStretch(0, 1)

        comparison_layout.addWidget(form_frame, 1)
        comparison_layout.addWidget(table_frame, 1)
        main_layout.addLayout(comparison_layout)

        # -------------------------------------------------
        # TEAMVERGLEICH
        # -------------------------------------------------

        comparison_title = QLabel("⚔️ Teamvergleich")
        comparison_title.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        main_layout.addWidget(comparison_title)

        self.team_comparison_frame = QFrame()
        self.team_comparison_frame.setObjectName(
            "MatchCenterTeamComparison"
        )

        self.team_comparison_layout = QGridLayout(
            self.team_comparison_frame
        )
        self.team_comparison_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )
        self.team_comparison_layout.setHorizontalSpacing(12)
        self.team_comparison_layout.setVerticalSpacing(10)

        self.comparison_home_header = QLabel("Heim")
        self.comparison_home_header.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.comparison_home_header.setStyleSheet(
            "font-weight: 700;"
        )

        comparison_metric_header = QLabel("Kennzahl")
        comparison_metric_header.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        comparison_metric_header.setStyleSheet(
            "font-weight: 700;"
        )

        self.comparison_away_header = QLabel("Auswärts")
        self.comparison_away_header.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.comparison_away_header.setStyleSheet(
            "font-weight: 700;"
        )

        self.team_comparison_layout.addWidget(
            self.comparison_home_header,
            0,
            0,
        )
        self.team_comparison_layout.addWidget(
            comparison_metric_header,
            0,
            1,
        )
        self.team_comparison_layout.addWidget(
            self.comparison_away_header,
            0,
            2,
        )

        self.comparison_rows: dict[str, dict] = {}

        comparison_metrics = (
            ("played", "Spiele"),
            ("points_per_game", "Punkte / Spiel"),
            ("goals_per_game", "Tore / Spiel"),
            (
                "goals_against_per_game",
                "Gegentore / Spiel",
            ),
            (
                "goal_difference",
                "Tordifferenz",
            ),
            ("wins", "Siege"),
            ("draws", "Unentschieden"),
            ("losses", "Niederlagen"),
            ("clean_sheets", "Zu Null"),
        )

        for row_index, (
            key,
            title_text,
        ) in enumerate(
            comparison_metrics,
            start=1,
        ):
            home_value = QLabel("–")
            home_value.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            metric_label = QLabel(title_text)
            metric_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            away_value = QLabel("–")
            away_value.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.team_comparison_layout.addWidget(
                home_value,
                row_index,
                0,
            )
            self.team_comparison_layout.addWidget(
                metric_label,
                row_index,
                1,
            )
            self.team_comparison_layout.addWidget(
                away_value,
                row_index,
                2,
            )

            self.comparison_rows[key] = {
                "home_value": home_value,
                "away_value": away_value,
            }

        self.team_comparison_layout.setColumnStretch(0, 1)
        self.team_comparison_layout.setColumnStretch(1, 0)
        self.team_comparison_layout.setColumnStretch(2, 1)

        comparison_hint = QLabel(
            "Alle Werte basieren ausschließlich auf Spielen "
            "vor diesem Spieltag."
        )
        comparison_hint.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        comparison_hint.setWordWrap(True)
        comparison_hint.setStyleSheet(
            "font-size: 11px;"
        )

        last_row = len(comparison_metrics) + 1
        self.team_comparison_layout.addWidget(
            comparison_hint,
            last_row,
            0,
            1,
            3,
        )

        main_layout.addWidget(
            self.team_comparison_frame
        )

        # -------------------------------------------------
        # KOMPAKTE PROGNOSE
        # -------------------------------------------------

        prediction_title = QLabel("🔮 Prognose")
        prediction_title.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        main_layout.addWidget(prediction_title)

        prediction_frame = QFrame()
        prediction_frame.setObjectName(
            "MatchCenterPrediction"
        )

        prediction_layout = QVBoxLayout(
            prediction_frame
        )
        prediction_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )
        prediction_layout.setSpacing(12)

        expected_caption = QLabel(
            "Erwartete Tore"
        )
        expected_caption.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        expected_caption.setStyleSheet(
            "font-weight: 600;"
        )
        prediction_layout.addWidget(
            expected_caption
        )

        self.prediction_expected_label = QLabel(
            "– : –"
        )
        self.prediction_expected_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.prediction_expected_label.setStyleSheet(
            "font-size: 24px; font-weight: 700;"
        )
        prediction_layout.addWidget(
            self.prediction_expected_label
        )

        probability_layout = QGridLayout()
        probability_layout.setHorizontalSpacing(24)

        probability_headers = (
            ("1", 0),
            ("X", 1),
            ("2", 2),
        )

        for title_text, column in probability_headers:
            label = QLabel(title_text)
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            label.setStyleSheet(
                "font-weight: 700;"
            )
            probability_layout.addWidget(
                label,
                0,
                column,
            )

        self.prediction_home_probability = QLabel("–")
        self.prediction_draw_probability = QLabel("–")
        self.prediction_away_probability = QLabel("–")

        for column, label in enumerate(
            (
                self.prediction_home_probability,
                self.prediction_draw_probability,
                self.prediction_away_probability,
            )
        ):
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            label.setStyleSheet(
                "font-size: 18px; font-weight: 700;"
            )
            probability_layout.addWidget(
                label,
                1,
                column,
            )
            probability_layout.setColumnStretch(
                column,
                1,
            )

        prediction_layout.addLayout(
            probability_layout
        )

        score_caption = QLabel(
            "Wahrscheinlichste Ergebnisse"
        )
        score_caption.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        score_caption.setStyleSheet(
            "font-weight: 600;"
        )
        prediction_layout.addWidget(
            score_caption
        )

        self.prediction_scores_label = QLabel("–")
        self.prediction_scores_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.prediction_scores_label.setWordWrap(True)
        prediction_layout.addWidget(
            self.prediction_scores_label
        )

        self.prediction_info_label = QLabel(
            "PREMATCH"
        )
        self.prediction_info_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.prediction_info_label.setWordWrap(True)
        self.prediction_info_label.setStyleSheet(
            "font-size: 11px;"
        )
        prediction_layout.addWidget(
            self.prediction_info_label
        )

        main_layout.addWidget(
            prediction_frame
        )

        # -------------------------------------------------
        # BASISDATEN
        # -------------------------------------------------

        section_title = QLabel("📋 Basisdaten")
        section_title.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        main_layout.addWidget(section_title)

        data_frame = QFrame()
        data_frame.setObjectName("MatchCenterData")

        data_layout = QGridLayout(data_frame)
        data_layout.setContentsMargins(16, 12, 16, 12)
        data_layout.setHorizontalSpacing(20)
        data_layout.setVerticalSpacing(8)

        self.data_rows: dict[str, QLabel] = {}

        rows = (
            ("status", "Status"),
            ("date", "Datum / Uhrzeit"),
            ("venue", "Spielort"),
            ("matchday", "Spieltag"),
            ("match_id", "Match-ID"),
        )

        for row_index, (key, description) in enumerate(rows):
            description_label = QLabel(description)
            description_label.setStyleSheet(
                "font-weight: 600;"
            )

            value_label = QLabel("–")
            value_label.setWordWrap(True)

            data_layout.addWidget(
                description_label,
                row_index,
                0,
            )
            data_layout.addWidget(
                value_label,
                row_index,
                1,
            )

            self.data_rows[key] = value_label

        data_layout.setColumnStretch(1, 1)
        main_layout.addWidget(data_frame)

        self.placeholder_label = QLabel(
            "Als Nächstes: Form, Tabelle, Teamvergleich, "
            "Heim/Auswärts, Torphasen und Prognose."
        )
        self.placeholder_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setStyleSheet(
            "font-size: 12px;"
        )
        main_layout.addWidget(
            self.placeholder_label
        )

        main_layout.addStretch(1)

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        if self.competition_id == competition_id:
            return

        self.competition_id = competition_id

        self._close_connection()
        self._reset_view()

        if competition_id is None:
            return

        self._open_connection()
        self._load_matchdays()

    def refresh(self) -> None:
        if self.competition_id is None:
            return

        current_matchday = (
            self.matchday_combo.currentData()
        )
        current_match = (
            self.match_combo.currentData()
        )

        self._load_matchdays()

        if current_matchday is not None:
            index = self.matchday_combo.findData(
                current_matchday
            )

            if index >= 0:
                self.matchday_combo.setCurrentIndex(
                    index
                )

        if current_match is not None:
            index = self.match_combo.findData(
                current_match
            )

            if index >= 0:
                self.match_combo.setCurrentIndex(
                    index
                )

    def _open_connection(self) -> None:
        if not DATABASE_PATH.exists():
            raise FileNotFoundError(
                f"Datenbank nicht gefunden: "
                f"{DATABASE_PATH}"
            )

        self.connection = sqlite3.connect(
            DATABASE_PATH
        )
        self.prediction_service = PredictionService(
            self.connection
        )

    def _close_connection(self) -> None:
        self.prediction_service = None

        if self.connection is not None:
            self.connection.close()

        self.connection = None

    def _load_matchdays(self) -> None:
        self.matchday_combo.blockSignals(True)
        self.matchday_combo.clear()

        if (
            self.connection is None
            or self.competition_id is None
        ):
            self.matchday_combo.blockSignals(False)
            return

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT DISTINCT matchday
            FROM matches
            WHERE
                competition_id = ?
                AND matchday IS NOT NULL
            ORDER BY matchday;
            """,
            (self.competition_id,),
        )

        for row in cursor.fetchall():
            matchday = int(row[0])
            self.matchday_combo.addItem(
                f"Spieltag {matchday}",
                matchday,
            )

        self.matchday_combo.blockSignals(False)

        if self.matchday_combo.count() > 0:
            self.matchday_combo.setCurrentIndex(0)
            self._matchday_changed()

    def _matchday_changed(self) -> None:
        matchday = (
            self.matchday_combo.currentData()
        )
        self._load_matches(matchday)

    def _load_matches(
        self,
        matchday: int | None,
    ) -> None:
        self.match_combo.blockSignals(True)
        self.match_combo.clear()

        if (
            self.connection is None
            or self.competition_id is None
            or matchday is None
        ):
            self.match_combo.blockSignals(False)
            self._reset_match()
            return

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                matches.match_id,
                home_team.name,
                away_team.name
            FROM matches
            INNER JOIN teams AS home_team
                ON home_team.team_id = matches.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = matches.away_team_id
            WHERE
                matches.competition_id = ?
                AND matches.matchday = ?
            ORDER BY matches.match_id;
            """,
            (
                self.competition_id,
                matchday,
            ),
        )

        for row in cursor.fetchall():
            match_id = int(row[0])
            home_name = str(row[1])
            away_name = str(row[2])

            self.match_combo.addItem(
                f"{home_name} – {away_name}",
                match_id,
            )

        self.match_combo.blockSignals(False)

        if self.match_combo.count() > 0:
            self.match_combo.setCurrentIndex(0)
            self._match_changed()
        else:
            self._reset_match()

    def _match_changed(self) -> None:
        match_id = (
            self.match_combo.currentData()
        )

        if match_id is None:
            self._reset_match()
            return

        self._load_match(int(match_id))

    def _load_match(
        self,
        match_id: int,
    ) -> None:
        if self.connection is None:
            return

        columns = self._table_columns("matches")

        required_columns = (
            "match_id",
            "matchday",
            "home_team_id",
            "away_team_id",
            "home_goals",
            "away_goals",
        )

        if not set(required_columns).issubset(columns):
            self._reset_match()
            return

        wanted_columns = list(required_columns)

        optional_columns = (
            "match_date",
            "date",
            "kickoff",
            "kickoff_time",
            "venue_id",
            "status",
        )

        for column in optional_columns:
            if column in columns:
                wanted_columns.append(column)

        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT
                {", ".join(wanted_columns)}
            FROM matches
            WHERE match_id = ?;
            """,
            (match_id,),
        )

        row = cursor.fetchone()

        if row is None:
            self._reset_match()
            return

        data = dict(
            zip(
                wanted_columns,
                row,
            )
        )

        home_team_id = int(
            data["home_team_id"]
        )
        away_team_id = int(
            data["away_team_id"]
        )

        home_name = self._team_name(
            home_team_id
        )
        away_name = self._team_name(
            away_team_id
        )

        matchday = data.get("matchday")

        self.matchday_header_label.setText(
            f"SPIELTAG {matchday}"
            if matchday is not None
            else "SPIEL"
        )

        self.home_team_label.setText(home_name)
        self.away_team_label.setText(away_name)

        self._update_prematch_context(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            matchday=(
                int(matchday)
                if matchday is not None
                else None
            ),
            home_name=home_name,
            away_name=away_name,
        )

        home_goals = data.get("home_goals")
        away_goals = data.get("away_goals")

        finished = (
            home_goals is not None
            and away_goals is not None
        )

        if finished:
            self.result_label.setText(
                f"{int(home_goals)} : "
                f"{int(away_goals)}"
            )
            status_text = "Beendet"
        else:
            self.result_label.setText("vs.")
            status_text = self._format_match_status(
                data.get("status")
            )

        raw_date_text = self._first_value(
            data,
            (
                "match_date",
                "date",
                "kickoff",
                "kickoff_time",
            ),
        )
        date_text = self._format_match_datetime(
            raw_date_text
        )

        venue_text = self._venue_text(
            data.get("venue_id")
        )

        info_parts = []

        if date_text != "–":
            info_parts.append(date_text)

        if venue_text != "–":
            info_parts.append(venue_text)

        self.match_info_label.setText(
            "  |  ".join(info_parts)
            if info_parts
            else "–"
        )

        self.data_rows["status"].setText(
            status_text
        )
        self.data_rows["date"].setText(
            date_text
        )
        self.data_rows["venue"].setText(
            venue_text
        )
        self.data_rows["matchday"].setText(
            str(matchday)
            if matchday is not None
            else "–"
        )
        self.data_rows["match_id"].setText(
            str(match_id)
        )

        self._update_prediction(
            match_id=match_id,
            matchday=(
                int(matchday)
                if matchday is not None
                else None
            ),
        )

    @staticmethod
    def _format_match_status(
        status: object,
    ) -> str:
        raw = str(status or "").strip()
        normalized = raw.lower()

        translations = {
            "scheduled": "Geplant",
            "finished": "Beendet",
            "cancelled": "Abgesagt",
            "canceled": "Abgesagt",
            "postponed": "Verschoben",
            "live": "Live",
        }

        if not raw:
            return "Noch nicht gespielt"

        return translations.get(
            normalized,
            raw,
        )

    @staticmethod
    def _format_match_datetime(
        value: object,
    ) -> str:
        raw = str(value or "").strip()

        if not raw or raw == "–":
            return "–"

        normalized = raw.replace("T", " ")

        for date_format in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ):
            try:
                parsed = datetime.strptime(
                    normalized,
                    date_format,
                )
            except ValueError:
                continue

            if date_format == "%Y-%m-%d":
                return parsed.strftime("%d.%m.%Y")

            return parsed.strftime(
                "%d.%m.%Y · %H:%M Uhr"
            )

        return raw

    def _update_prediction(
        self,
        match_id: int,
        matchday: int | None,
    ) -> None:
        self._reset_prediction()

        if matchday is None:
            self.prediction_info_label.setText(
                "Keine Spieltagsinformation vorhanden."
            )
            return

        if matchday <= 1:
            self.prediction_info_label.setText(
                "PREMATCH · Noch keine historische "
                "Datengrundlage vorhanden."
            )
            return

        if self.prediction_service is None:
            self.prediction_info_label.setText(
                "Prognoseservice nicht verfügbar."
            )
            return

        try:
            prediction = self.prediction_service.predict_match(
                match_id=match_id,
                mode=PredictionMode.PREMATCH,
            )
        except Exception as exc:
            self.prediction_info_label.setText(
                f"Prognose nicht verfügbar: {exc}"
            )
            return

        self.prediction_expected_label.setText(
            f"{prediction.expected_home_goals:.2f}"
            f" : "
            f"{prediction.expected_away_goals:.2f}"
        )

        self.prediction_home_probability.setText(
            self._format_probability(
                prediction.home_win_probability
            )
        )
        self.prediction_draw_probability.setText(
            self._format_probability(
                prediction.draw_probability
            )
        )
        self.prediction_away_probability.setText(
            self._format_probability(
                prediction.away_win_probability
            )
        )

        top_scores = prediction.most_likely_scores[:3]

        score_parts = [
            (
                f"{score.home_goals}:{score.away_goals}"
                f" · "
                f"{score.probability * 100.0:.1f} %"
            )
            for score in top_scores
        ]

        self.prediction_scores_label.setText(
            "    ".join(score_parts)
            if score_parts
            else "–"
        )

        self.prediction_info_label.setText(
            "PREMATCH · Datengrundlage Spieltage "
            f"1–{matchday - 1}"
        )

    @staticmethod
    def _format_probability(
        probability: float,
    ) -> str:
        return (
            f"{probability * 100.0:.1f} %"
        )

    def _reset_prediction(self) -> None:
        self.prediction_expected_label.setText(
            "– : –"
        )
        self.prediction_home_probability.setText(
            "–"
        )
        self.prediction_draw_probability.setText(
            "–"
        )
        self.prediction_away_probability.setText(
            "–"
        )
        self.prediction_scores_label.setText(
            "–"
        )
        self.prediction_info_label.setText(
            "PREMATCH"
        )

    def _update_prematch_context(
        self,
        home_team_id: int,
        away_team_id: int,
        matchday: int | None,
        home_name: str,
        away_name: str,
    ) -> None:
        self.home_form_name_label.setText(home_name)
        self.away_form_name_label.setText(away_name)
        self.home_table_name_label.setText(home_name)
        self.away_table_name_label.setText(away_name)

        if matchday is None:
            self._reset_prematch_context()
            return

        table = self._table_before_matchday(matchday)

        home_row = next(
            (
                row
                for row in table
                if row["team_id"] == home_team_id
            ),
            None,
        )
        away_row = next(
            (
                row
                for row in table
                if row["team_id"] == away_team_id
            ),
            None,
        )

        self._set_table_context(
            home_row=home_row,
            away_row=away_row,
        )

        self._update_team_comparison(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            matchday=matchday,
        )

        home_form = self._form_before_matchday(
            team_id=home_team_id,
            matchday=matchday,
            limit=5,
        )
        away_form = self._form_before_matchday(
            team_id=away_team_id,
            matchday=matchday,
            limit=5,
        )

        self._set_form_dots(
            self.home_form_layout,
            home_form,
        )
        self._set_form_dots(
            self.away_form_layout,
            away_form,
        )

    def _set_form_dots(
        self,
        layout: QHBoxLayout,
        results: list[str],
    ) -> None:
        self._clear_form_layout(layout)

        if not results:
            empty_label = QLabel("–")
            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            layout.addStretch(1)
            layout.addWidget(empty_label)
            return

        layout.addStretch(1)

        for result in results:
            label = QLabel(result)
            label.setFixedSize(26, 26)
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            label.setToolTip(
                {
                    "S": "Sieg",
                    "U": "Unentschieden",
                    "N": "Niederlage",
                }.get(result, result)
            )

            if result == "S":
                background = "#238636"
            elif result == "U":
                background = "#B7791F"
            else:
                background = "#D73A49"

            label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {background};
                    color: white;
                    border-radius: 13px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                """
            )

            layout.addWidget(label)

    @staticmethod
    def _clear_form_layout(
        layout: QHBoxLayout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _update_team_comparison(
        self,
        home_team_id: int,
        away_team_id: int,
        matchday: int,
    ) -> None:
        home_stats = self._team_stats_before_matchday(
            team_id=home_team_id,
            matchday=matchday,
        )
        away_stats = self._team_stats_before_matchday(
            team_id=away_team_id,
            matchday=matchday,
        )

        self.comparison_home_header.setText(
            self.home_team_label.text()
        )
        self.comparison_away_header.setText(
            self.away_team_label.text()
        )

        values = {
            "played": (
                float(home_stats["played"]),
                float(away_stats["played"]),
            ),
            "points_per_game": (
                home_stats["points_per_game"],
                away_stats["points_per_game"],
            ),
            "goals_per_game": (
                home_stats["goals_per_game"],
                away_stats["goals_per_game"],
            ),
            "goals_against_per_game": (
                home_stats["goals_against_per_game"],
                away_stats["goals_against_per_game"],
            ),
            "goal_difference": (
                float(home_stats["goal_difference"]),
                float(away_stats["goal_difference"]),
            ),
            "wins": (
                float(home_stats["wins"]),
                float(away_stats["wins"]),
            ),
            "draws": (
                float(home_stats["draws"]),
                float(away_stats["draws"]),
            ),
            "losses": (
                float(home_stats["losses"]),
                float(away_stats["losses"]),
            ),
            "clean_sheets": (
                float(home_stats["clean_sheets"]),
                float(away_stats["clean_sheets"]),
            ),
        }

        integer_keys = {
            "played",
            "wins",
            "draws",
            "losses",
            "clean_sheets",
            "goal_difference",
        }

        for key, (home_value, away_value) in values.items():
            row = self.comparison_rows[key]

            if key == "goal_difference":
                home_text = self._format_signed_integer(
                    int(home_value)
                )
                away_text = self._format_signed_integer(
                    int(away_value)
                )
            elif key in integer_keys:
                home_text = str(int(home_value))
                away_text = str(int(away_value))
            else:
                home_text = self._format_decimal(
                    home_value
                )
                away_text = self._format_decimal(
                    away_value
                )

            row["home_value"].setText(home_text)
            row["away_value"].setText(away_text)


    def _team_stats_before_matchday(
        self,
        team_id: int,
        matchday: int,
    ) -> dict:
        stats = {
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0,
            "goals_for": 0,
            "goals_against": 0,
            "clean_sheets": 0,
        }

        if (
            self.connection is None
            or self.competition_id is None
        ):
            return self._finish_team_stats(stats)

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND matchday IS NOT NULL
                AND matchday < ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
                AND (
                    home_team_id = ?
                    OR away_team_id = ?
                )
            ORDER BY
                matchday,
                match_id;
            """,
            (
                self.competition_id,
                matchday,
                team_id,
                team_id,
            ),
        )

        for (
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
        ) in cursor.fetchall():
            home_team_id = int(home_team_id)
            home_goals = int(home_goals)
            away_goals = int(away_goals)

            if team_id == home_team_id:
                goals_for = home_goals
                goals_against = away_goals
            else:
                goals_for = away_goals
                goals_against = home_goals

            stats["played"] += 1
            stats["goals_for"] += goals_for
            stats["goals_against"] += goals_against

            if goals_against == 0:
                stats["clean_sheets"] += 1

            if goals_for > goals_against:
                stats["wins"] += 1
                stats["points"] += 3
            elif goals_for < goals_against:
                stats["losses"] += 1
            else:
                stats["draws"] += 1
                stats["points"] += 1

        return self._finish_team_stats(stats)

    @staticmethod
    def _finish_team_stats(
        stats: dict,
    ) -> dict:
        played = int(stats["played"])

        stats["goal_difference"] = (
            int(stats["goals_for"])
            - int(stats["goals_against"])
        )

        if played <= 0:
            stats["points_per_game"] = 0.0
            stats["goals_per_game"] = 0.0
            stats["goals_against_per_game"] = 0.0
            return stats

        stats["points_per_game"] = (
            float(stats["points"]) / played
        )
        stats["goals_per_game"] = (
            float(stats["goals_for"]) / played
        )
        stats["goals_against_per_game"] = (
            float(stats["goals_against"]) / played
        )

        return stats

    @staticmethod
    def _format_decimal(
        value: float,
    ) -> str:
        return f"{value:.2f}".replace(".", ",")

    @staticmethod
    def _format_signed_integer(
        value: int,
    ) -> str:
        if value > 0:
            return f"+{value}"

        return str(value)

    def _reset_team_comparison(self) -> None:
        self.comparison_home_header.setText("Heim")
        self.comparison_away_header.setText("Auswärts")

        for row in self.comparison_rows.values():
            row["home_value"].setText("–")
            row["away_value"].setText("–")

    def _table_before_matchday(
        self,
        matchday: int,
    ) -> list[dict]:
        if (
            self.connection is None
            or self.competition_id is None
        ):
            return []

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name,
                teams.short_name
            FROM competition_teams
            INNER JOIN teams
                ON teams.team_id =
                   competition_teams.team_id
            WHERE
                competition_teams.competition_id = ?
            ORDER BY teams.name;
            """,
            (self.competition_id,),
        )

        standings: dict[int, dict] = {}

        for team_id, team_name, short_name in cursor.fetchall():
            standings[int(team_id)] = {
                "team_id": int(team_id),
                "team_name": short_name or team_name,
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
            }

        cursor.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND matchday IS NOT NULL
                AND matchday < ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday,
                match_id;
            """,
            (
                self.competition_id,
                matchday,
            ),
        )

        for (
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
        ) in cursor.fetchall():
            home_team_id = int(home_team_id)
            away_team_id = int(away_team_id)
            home_goals = int(home_goals)
            away_goals = int(away_goals)

            if (
                home_team_id not in standings
                or away_team_id not in standings
            ):
                continue

            self._apply_table_result(
                standings[home_team_id],
                home_goals,
                away_goals,
            )
            self._apply_table_result(
                standings[away_team_id],
                away_goals,
                home_goals,
            )

        for row in standings.values():
            row["goal_difference"] = (
                row["goals_for"]
                - row["goals_against"]
            )

        table = list(standings.values())
        table.sort(
            key=lambda row: (
                -row["points"],
                -row["goal_difference"],
                -row["goals_for"],
                str(row["team_name"]).lower(),
            )
        )

        for position, row in enumerate(table, start=1):
            row["position"] = position

        return table

    @staticmethod
    def _apply_table_result(
        team: dict,
        goals_for: int,
        goals_against: int,
    ) -> None:
        team["played"] += 1
        team["goals_for"] += goals_for
        team["goals_against"] += goals_against

        if goals_for > goals_against:
            team["wins"] += 1
            team["points"] += 3
        elif goals_for < goals_against:
            team["losses"] += 1
        else:
            team["draws"] += 1
            team["points"] += 1

    def _form_before_matchday(
        self,
        team_id: int,
        matchday: int,
        limit: int = 5,
    ) -> list[str]:
        if (
            self.connection is None
            or self.competition_id is None
        ):
            return []

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND matchday IS NOT NULL
                AND matchday < ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
                AND (
                    home_team_id = ?
                    OR away_team_id = ?
                )
            ORDER BY
                matchday DESC,
                match_date DESC,
                match_id DESC
            LIMIT ?;
            """,
            (
                self.competition_id,
                matchday,
                team_id,
                team_id,
                limit,
            ),
        )

        results: list[str] = []

        for (
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
        ) in cursor.fetchall():
            home_team_id = int(home_team_id)
            home_goals = int(home_goals)
            away_goals = int(away_goals)

            if team_id == home_team_id:
                goals_for = home_goals
                goals_against = away_goals
            else:
                goals_for = away_goals
                goals_against = home_goals

            if goals_for > goals_against:
                result = "S"
            elif goals_for < goals_against:
                result = "N"
            else:
                result = "U"

            results.append(result)

        results.reverse()
        return results

    def _set_table_context(
        self,
        home_row: dict | None,
        away_row: dict | None,
    ) -> None:
        if home_row is None:
            self.home_position_label.setText("Platz –")
            self.home_table_position_label.setText("Platz –")
            self.home_table_points_label.setText("– Punkte")
        else:
            position = int(home_row["position"])
            points = int(home_row["points"])

            self.home_position_label.setText(
                f"Platz {position}"
            )
            self.home_table_position_label.setText(
                f"Platz {position}"
            )
            self.home_table_points_label.setText(
                f"{points} Punkte"
            )

        if away_row is None:
            self.away_position_label.setText("Platz –")
            self.away_table_position_label.setText("Platz –")
            self.away_table_points_label.setText("– Punkte")
        else:
            position = int(away_row["position"])
            points = int(away_row["points"])

            self.away_position_label.setText(
                f"Platz {position}"
            )
            self.away_table_position_label.setText(
                f"Platz {position}"
            )
            self.away_table_points_label.setText(
                f"{points} Punkte"
            )

    def _reset_prematch_context(self) -> None:
        self.home_position_label.setText("Platz –")
        self.away_position_label.setText("Platz –")
        self._set_form_dots(
            self.home_form_layout,
            [],
        )
        self._set_form_dots(
            self.away_form_layout,
            [],
        )
        self.home_table_position_label.setText("Platz –")
        self.away_table_position_label.setText("Platz –")
        self.home_table_points_label.setText("– Punkte")
        self.away_table_points_label.setText("– Punkte")
        self._reset_team_comparison()

    def _table_columns(
        self,
        table_name: str,
    ) -> set[str]:
        if self.connection is None:
            return set()

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                f"PRAGMA table_info({table_name});"
            )
        except sqlite3.Error:
            return set()

        return {
            str(row[1])
            for row in cursor.fetchall()
        }

    def _team_name(
        self,
        team_id: int,
    ) -> str:
        if self.connection is None:
            return f"Team {team_id}"

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT name
            FROM teams
            WHERE team_id = ?;
            """,
            (team_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return f"Team {team_id}"

        return str(row[0])

    def _venue_text(
        self,
        venue_id,
    ) -> str:
        if (
            self.connection is None
            or venue_id is None
        ):
            return "–"

        columns = self._table_columns(
            "venues"
        )

        if not columns:
            return "–"

        name_column = None

        for candidate in (
            "name",
            "venue_name",
            "title",
        ):
            if candidate in columns:
                name_column = candidate
                break

        if name_column is None:
            return "–"

        id_column = None

        for candidate in (
            "venue_id",
            "id",
        ):
            if candidate in columns:
                id_column = candidate
                break

        if id_column is None:
            return "–"

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                f"""
                SELECT {name_column}
                FROM venues
                WHERE {id_column} = ?;
                """,
                (venue_id,),
            )
        except sqlite3.Error:
            return "–"

        row = cursor.fetchone()

        if (
            row is None
            or row[0] is None
        ):
            return "–"

        return str(row[0])

    @staticmethod
    def _first_value(
        data: dict,
        keys: tuple[str, ...],
    ) -> str:
        for key in keys:
            value = data.get(key)

            if value not in (
                None,
                "",
            ):
                return str(value)

        return "–"

    def _reset_match(self) -> None:
        self.matchday_header_label.setText("SPIEL")
        self.home_team_label.setText("Heim")
        self.away_team_label.setText("Auswärts")
        self.home_position_label.setText("Platz –")
        self.away_position_label.setText("Platz –")

        self.home_form_name_label.setText("Heim")
        self.away_form_name_label.setText("Auswärts")
        self.home_table_name_label.setText("Heim")
        self.away_table_name_label.setText("Auswärts")
        self._reset_prematch_context()

        self.match_info_label.setText("–")
        self.result_label.setText("")
        self._reset_prediction()

        for label in self.data_rows.values():
            label.setText("–")

    def _reset_view(self) -> None:
        self.matchday_combo.clear()
        self.match_combo.clear()
        self._reset_match()

    def closeEvent(
        self,
        event,
    ) -> None:
        self._close_connection()
        super().closeEvent(event)
