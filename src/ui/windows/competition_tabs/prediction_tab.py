from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.prediction.prediction_service import (
    PredictionMode,
    PredictionService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionPredictionTab(QWidget):

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.competition_id: int | None = None
        self.connection: sqlite3.Connection | None = None
        self.service: PredictionService | None = None

        self._setup_ui()
        self._reset_view()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_content = QWidget()

        self.scroll_content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        main_layout = QVBoxLayout(
            self.scroll_content
        )

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(12)

        self.scroll_area.setWidget(
            self.scroll_content
        )

        root_layout.addWidget(
            self.scroll_area
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        title = QLabel(
            "🔮 Spielprognose"
        )

        title.setObjectName(
            "PageTitle"
        )

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Prognose auf Basis ausschließlich bereits "
            "bekannter Spieldaten."
        )

        subtitle.setWordWrap(
            True
        )

        main_layout.addWidget(
            subtitle
        )

        # -------------------------------------------------
        # CONTROLS
        # -------------------------------------------------

        controls_frame = QFrame()

        controls_frame.setObjectName(
            "PredictionControls"
        )

        controls_layout = QGridLayout(
            controls_frame
        )

        controls_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        controls_layout.setHorizontalSpacing(
            12
        )

        controls_layout.setVerticalSpacing(
            10
        )

        matchday_label = QLabel(
            "Spieltag"
        )

        controls_layout.addWidget(
            matchday_label,
            0,
            0,
        )

        self.matchday_combo = QComboBox()

        self.matchday_combo.setMinimumWidth(
            130
        )

        self.matchday_combo.currentIndexChanged.connect(
            self._matchday_changed
        )

        controls_layout.addWidget(
            self.matchday_combo,
            0,
            1,
        )

        match_label = QLabel(
            "Spiel"
        )

        controls_layout.addWidget(
            match_label,
            0,
            2,
        )

        self.match_combo = QComboBox()

        self.match_combo.setMinimumWidth(
            320
        )

        self.match_combo.currentIndexChanged.connect(
            self._match_changed
        )

        controls_layout.addWidget(
            self.match_combo,
            0,
            3,
        )

        mode_label = QLabel(
            "Modus"
        )

        controls_layout.addWidget(
            mode_label,
            1,
            0,
        )

        self.mode_combo = QComboBox()

        self.mode_combo.addItem(
            "PREMATCH",
            PredictionMode.PREMATCH,
        )

        self.mode_combo.addItem(
            "LINEUP",
            PredictionMode.LINEUP,
        )

        self.mode_combo.currentIndexChanged.connect(
            self._mode_changed
        )

        controls_layout.addWidget(
            self.mode_combo,
            1,
            1,
        )

        self.lineup_status_label = QLabel(
            ""
        )

        self.lineup_status_label.setWordWrap(
            True
        )

        controls_layout.addWidget(
            self.lineup_status_label,
            1,
            2,
        )

        self.predict_button = QPushButton(
            "Prognose berechnen"
        )

        self.predict_button.setMinimumWidth(
            180
        )

        self.predict_button.clicked.connect(
            self._calculate_prediction
        )

        controls_layout.addWidget(
            self.predict_button,
            1,
            3,
        )

        controls_layout.setColumnStretch(
            3,
            1,
        )

        main_layout.addWidget(
            controls_frame
        )

        # -------------------------------------------------
        # HINWEIS / STATUS
        # -------------------------------------------------

        self.info_label = QLabel(
            ""
        )

        self.info_label.setWordWrap(
            True
        )

        self.info_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.info_label.setMinimumHeight(
            24
        )

        main_layout.addWidget(
            self.info_label
        )

        # -------------------------------------------------
        # EXPECTED GOALS
        # -------------------------------------------------

        goals_frame = QFrame()

        goals_frame.setObjectName(
            "PredictionGoals"
        )

        goals_layout = QGridLayout(
            goals_frame
        )

        goals_layout.setContentsMargins(
            20,
            14,
            20,
            14,
        )

        goals_layout.setHorizontalSpacing(
            20
        )

        goals_layout.setVerticalSpacing(
            4
        )

        self.home_team_label = QLabel(
            "Heim"
        )

        self.home_team_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.home_team_label.setStyleSheet(
            "font-size: 15px; "
            "font-weight: 600;"
        )

        self.away_team_label = QLabel(
            "Auswärts"
        )

        self.away_team_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.away_team_label.setStyleSheet(
            "font-size: 15px; "
            "font-weight: 600;"
        )

        goals_layout.addWidget(
            self.home_team_label,
            0,
            0,
        )

        goals_layout.addWidget(
            self.away_team_label,
            0,
            2,
        )

        expected_title = QLabel(
            "Erwartete Tore"
        )

        expected_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        goals_layout.addWidget(
            expected_title,
            1,
            0,
            1,
            3,
        )

        self.home_expected_label = QLabel(
            "–"
        )

        self.home_expected_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.home_expected_label.setStyleSheet(
            "font-size: 34px; "
            "font-weight: 700;"
        )

        separator = QLabel(
            ":"
        )

        separator.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        separator.setStyleSheet(
            "font-size: 28px; "
            "font-weight: 700;"
        )

        self.away_expected_label = QLabel(
            "–"
        )

        self.away_expected_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.away_expected_label.setStyleSheet(
            "font-size: 34px; "
            "font-weight: 700;"
        )

        goals_layout.addWidget(
            self.home_expected_label,
            2,
            0,
        )

        goals_layout.addWidget(
            separator,
            2,
            1,
        )

        goals_layout.addWidget(
            self.away_expected_label,
            2,
            2,
        )

        goals_layout.setColumnStretch(
            0,
            1,
        )

        goals_layout.setColumnStretch(
            2,
            1,
        )

        main_layout.addWidget(
            goals_frame
        )

        # -------------------------------------------------
        # 1 / X / 2
        # -------------------------------------------------

        probability_title = QLabel(
            "Siegwahrscheinlichkeiten"
        )

        probability_title.setStyleSheet(
            "font-size: 16px; "
            "font-weight: 600;"
        )

        main_layout.addWidget(
            probability_title
        )

        probability_layout = QHBoxLayout()

        probability_layout.setSpacing(
            12
        )

        self.home_probability_widget = (
            self._create_probability_widget(
                "1",
                "Heimsieg",
            )
        )

        self.draw_probability_widget = (
            self._create_probability_widget(
                "X",
                "Unentschieden",
            )
        )

        self.away_probability_widget = (
            self._create_probability_widget(
                "2",
                "Auswärtssieg",
            )
        )

        probability_layout.addWidget(
            self.home_probability_widget
        )

        probability_layout.addWidget(
            self.draw_probability_widget
        )

        probability_layout.addWidget(
            self.away_probability_widget
        )

        main_layout.addLayout(
            probability_layout
        )

        # -------------------------------------------------
        # TOP RESULTS
        # -------------------------------------------------

        score_title = QLabel(
            "Wahrscheinlichste Ergebnisse"
        )

        score_title.setStyleSheet(
            "font-size: 16px; "
            "font-weight: 600;"
        )

        main_layout.addWidget(
            score_title
        )

        scores_layout = QHBoxLayout()

        scores_layout.setSpacing(
            10
        )

        self.score_widgets: list[
            tuple[QFrame, QLabel, QLabel]
        ] = []

        for index in range(5):
            score_widget = (
                self._create_score_widget(
                    index + 1
                )
            )

            self.score_widgets.append(
                score_widget
            )

            scores_layout.addWidget(
                score_widget[0]
            )

        main_layout.addLayout(
            scores_layout
        )

        # -------------------------------------------------
        # CUTOFF
        # -------------------------------------------------

        self.cutoff_label = QLabel(
            ""
        )

        self.cutoff_label.setWordWrap(
            True
        )

        self.cutoff_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.cutoff_label.setStyleSheet(
            "font-size: 12px;"
        )

        main_layout.addWidget(
            self.cutoff_label
        )

        # -------------------------------------------------
        # PROGNOSE-DETAILS
        # -------------------------------------------------

        details_title = QLabel("🔍 Prognose-Details")
        details_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        main_layout.addWidget(details_title)

        details_frame = QFrame()
        details_frame.setObjectName("PredictionDetails")
        details_layout = QGridLayout(details_frame)
        details_layout.setContentsMargins(16, 12, 16, 12)
        details_layout.setHorizontalSpacing(18)
        details_layout.setVerticalSpacing(6)

        self.details_data_label = QLabel("Noch keine Prognose berechnet.")
        self.details_data_label.setWordWrap(True)
        details_layout.addWidget(self.details_data_label, 0, 0, 1, 3)

        for column, text in ((1, "Heim"), (2, "Auswärts")):
            label = QLabel(text)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("font-weight: 600;")
            details_layout.addWidget(label, 1, column)

        self.detail_rows: dict[str, tuple[QLabel, QLabel]] = {}
        rows = (
            ("league", "Liga-Ø Tore"),
            ("team", "Teamstärke"),
            ("form", "nach Form"),
            ("opponent", "nach Gegnerstärke"),
            ("player", "nach Spielerstärke"),
            ("lineup", "nach Startelf"),
            ("final", "Erwartete Tore"),
        )

        for row_index, (key, description) in enumerate(rows, start=2):
            description_label = QLabel(description)
            home_value = QLabel("–")
            away_value = QLabel("–")
            home_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            away_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if key == "final":
                description_label.setStyleSheet("font-weight: 700;")
                home_value.setStyleSheet("font-weight: 700;")
                away_value.setStyleSheet("font-weight: 700;")

            details_layout.addWidget(description_label, row_index, 0)
            details_layout.addWidget(home_value, row_index, 1)
            details_layout.addWidget(away_value, row_index, 2)
            self.detail_rows[key] = (home_value, away_value)

        details_layout.setColumnStretch(0, 1)

        factor_title = QLabel("Einflussfaktoren")
        factor_title.setStyleSheet("font-weight: 600;")
        details_layout.addWidget(factor_title, 9, 0, 1, 3)

        self.factor_rows: dict[str, tuple[QLabel, QLabel]] = {}
        factor_rows = (
            ("form", "Form"),
            ("opponent", "Gegnerstärke"),
            ("player", "Spielerstärke"),
            ("lineup", "Startelf"),
        )

        for row_index, (key, description) in enumerate(factor_rows, start=10):
            description_label = QLabel(description)
            home_value = QLabel("–")
            away_value = QLabel("–")
            home_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            away_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            details_layout.addWidget(description_label, row_index, 0)
            details_layout.addWidget(home_value, row_index, 1)
            details_layout.addWidget(away_value, row_index, 2)
            self.factor_rows[key] = (home_value, away_value)

        factor_hint = QLabel(
            "< 1,00 senkt die erwarteten Tore  |  "
            "> 1,00 erhöht sie  |  1,00 ist neutral"
        )
        factor_hint.setWordWrap(True)
        factor_hint.setStyleSheet("font-size: 11px;")
        details_layout.addWidget(factor_hint, 14, 0, 1, 3)

        main_layout.addWidget(details_frame)

        main_layout.addStretch(
            1
        )

    def _create_probability_widget(
        self,
        outcome: str,
        description: str,
    ) -> QFrame:
        frame = QFrame()

        frame.setObjectName(
            "PredictionProbability"
        )

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        frame.setMinimumHeight(
            100
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        layout.setSpacing(
            2
        )

        outcome_label = QLabel(
            outcome
        )

        outcome_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        outcome_label.setStyleSheet(
            "font-size: 17px; "
            "font-weight: 700;"
        )

        probability_label = QLabel(
            "–"
        )

        probability_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        probability_label.setStyleSheet(
            "font-size: 28px; "
            "font-weight: 700;"
        )

        description_label = QLabel(
            description
        )

        description_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            outcome_label
        )

        layout.addWidget(
            probability_label
        )

        layout.addWidget(
            description_label
        )

        frame.probability_label = (
            probability_label
        )

        return frame

    def _create_score_widget(
        self,
        rank: int,
    ) -> tuple[
        QFrame,
        QLabel,
        QLabel,
    ]:
        frame = QFrame()

        frame.setObjectName(
            "PredictionScore"
        )

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        frame.setMinimumHeight(
            82
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        layout.setSpacing(
            2
        )

        rank_label = QLabel(
            f"#{rank}"
        )

        rank_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        rank_label.setStyleSheet(
            "font-size: 11px;"
        )

        score_label = QLabel(
            "–"
        )

        score_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        score_label.setStyleSheet(
            "font-size: 20px; "
            "font-weight: 700;"
        )

        probability_label = QLabel(
            "–"
        )

        probability_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        probability_label.setStyleSheet(
            "font-size: 13px;"
        )

        layout.addWidget(
            rank_label
        )

        layout.addWidget(
            score_label
        )

        layout.addWidget(
            probability_label
        )

        return (
            frame,
            score_label,
            probability_label,
        )

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        if (
            self.competition_id
            == competition_id
        ):
            return

        self.competition_id = (
            competition_id
        )

        self._close_connection()
        self._reset_view()

        if competition_id is None:
            return

        self._open_connection()
        self._load_matchdays()

    def refresh(
        self,
    ) -> None:
        if self.competition_id is None:
            return

        current_matchday = (
            self.matchday_combo.currentData()
        )

        self._load_matchdays()

        if current_matchday is not None:
            index = (
                self.matchday_combo.findData(
                    current_matchday
                )
            )

            if index >= 0:
                self.matchday_combo.setCurrentIndex(
                    index
                )

    def _open_connection(
        self,
    ) -> None:
        if not DATABASE_PATH.exists():
            raise FileNotFoundError(
                f"Datenbank nicht gefunden: "
                f"{DATABASE_PATH}"
            )

        self.connection = sqlite3.connect(
            DATABASE_PATH
        )

        self.service = PredictionService(
            self.connection
        )

    def _close_connection(
        self,
    ) -> None:
        if self.connection is not None:
            self.connection.close()

        self.connection = None
        self.service = None

    def _load_matchdays(
        self,
    ) -> None:
        self.matchday_combo.blockSignals(
            True
        )

        self.matchday_combo.clear()

        if (
            self.connection is None
            or self.competition_id is None
        ):
            self.matchday_combo.blockSignals(
                False
            )

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
            (
                self.competition_id,
            ),
        )

        for row in cursor.fetchall():
            matchday = int(
                row[0]
            )

            self.matchday_combo.addItem(
                f"Spieltag {matchday}",
                matchday,
            )

        self.matchday_combo.blockSignals(
            False
        )

        if self.matchday_combo.count() > 0:
            self.matchday_combo.setCurrentIndex(
                0
            )

            self._matchday_changed()

    def _matchday_changed(
        self,
    ) -> None:
        matchday = (
            self.matchday_combo.currentData()
        )

        self._load_matches(
            matchday
        )

    def _load_matches(
        self,
        matchday: int | None,
    ) -> None:
        self.match_combo.blockSignals(
            True
        )

        self.match_combo.clear()

        if (
            self.connection is None
            or self.competition_id is None
            or matchday is None
        ):
            self.match_combo.blockSignals(
                False
            )

            self._reset_prediction()

            return

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                match_id,
                home_team_id,
                away_team_id
            FROM matches
            WHERE
                competition_id = ?
                AND matchday = ?
            ORDER BY match_id;
            """,
            (
                self.competition_id,
                matchday,
            ),
        )

        rows = cursor.fetchall()

        for row in rows:
            match_id = int(
                row[0]
            )

            home_team_id = int(
                row[1]
            )

            away_team_id = int(
                row[2]
            )

            home_name = self._team_name(
                home_team_id
            )

            away_name = self._team_name(
                away_team_id
            )

            self.match_combo.addItem(
                f"{home_name} – {away_name}",
                match_id,
            )

        self.match_combo.blockSignals(
            False
        )

        if self.match_combo.count() > 0:
            self.match_combo.setCurrentIndex(
                0
            )

            self._match_changed()

        else:
            self._reset_prediction()

    def _match_changed(
        self,
    ) -> None:
        self._reset_prediction()
        self._update_prediction_state()

    def _mode_changed(
        self,
    ) -> None:
        self._reset_prediction()
        self._update_prediction_state()

    def _update_prediction_state(
        self,
    ) -> None:
        match_id = (
            self.match_combo.currentData()
        )

        matchday = (
            self.matchday_combo.currentData()
        )

        if (
            match_id is None
            or self.service is None
        ):
            self.lineup_status_label.setText(
                ""
            )

            self.info_label.setText(
                ""
            )

            self.predict_button.setEnabled(
                False
            )

            return

        if (
            matchday is not None
            and int(matchday) <= 1
        ):
            self.lineup_status_label.setText(
                ""
            )

            self.info_label.setText(
                "Für Spieltag 1 ist noch keine "
                "historische Datengrundlage vorhanden."
            )

            self.predict_button.setEnabled(
                False
            )

            return

        self.info_label.setText(
            ""
        )

        try:
            home_count, away_count = (
                self.service.get_lineup_coverage(
                    int(match_id)
                )
            )

            self.lineup_status_label.setText(
                "Startelf: "
                f"Heim {home_count}/11  |  "
                f"Auswärts {away_count}/11"
            )

            mode = (
                self.mode_combo.currentData()
            )

            if (
                mode == PredictionMode.LINEUP
                and (
                    home_count <= 0
                    or away_count <= 0
                )
            ):
                self.info_label.setText(
                    "LINEUP-Prognose nicht verfügbar: "
                    "Für mindestens eine Mannschaft "
                    "fehlt die Startelf."
                )

                self.predict_button.setEnabled(
                    False
                )

            else:
                self.predict_button.setEnabled(
                    True
                )

        except Exception as exc:
            self.lineup_status_label.setText(
                "Startelfstatus nicht verfügbar"
            )

            self.info_label.setText(
                str(exc)
            )

            self.predict_button.setEnabled(
                False
            )

    def _calculate_prediction(
        self,
    ) -> None:
        if self.service is None:
            return

        match_id = (
            self.match_combo.currentData()
        )

        mode = (
            self.mode_combo.currentData()
        )

        if match_id is None:
            return

        try:
            prediction = (
                self.service.predict_match(
                    match_id=int(
                        match_id
                    ),
                    mode=mode,
                )
            )

            breakdown = (
                self.service.get_prediction_breakdown(
                    match_id=int(
                        match_id
                    ),
                    mode=mode,
                )
            )

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Prognose",
                str(exc),
            )

            return

        self.home_team_label.setText(
            prediction.home_team_name
        )

        self.away_team_label.setText(
            prediction.away_team_name
        )

        self.home_expected_label.setText(
            f"{prediction.expected_home_goals:.2f}"
        )

        self.away_expected_label.setText(
            f"{prediction.expected_away_goals:.2f}"
        )

        self.home_probability_widget.probability_label.setText(
            f"{prediction.home_win_probability * 100:.1f} %"
        )

        self.draw_probability_widget.probability_label.setText(
            f"{prediction.draw_probability * 100:.1f} %"
        )

        self.away_probability_widget.probability_label.setText(
            f"{prediction.away_win_probability * 100:.1f} %"
        )

        self._reset_scores()

        for index, score in enumerate(
            prediction.most_likely_scores[:5]
        ):
            _, score_label, probability_label = (
                self.score_widgets[index]
            )

            score_label.setText(
                score.score
            )

            probability_label.setText(
                f"{score.probability * 100:.1f} %"
            )

        previous_matchday = (
            prediction.cutoff_matchday - 1
        )

        if previous_matchday == 1:
            history_text = (
                "Spieltag 1"
            )

        else:
            history_text = (
                f"Spieltage 1–{previous_matchday}"
            )

        mode_text = (
            "PREMATCH"
            if mode == PredictionMode.PREMATCH
            else "LINEUP"
        )

        self.cutoff_label.setText(
            f"Modus: {mode_text}  |  "
            f"Datengrundlage: {history_text}  |  "
            f"Keine Ergebnisse ab Spieltag "
            f"{prediction.cutoff_matchday} verwendet."
        )

        self._update_breakdown(
            breakdown
        )

    def _update_breakdown(
        self,
        breakdown,
    ) -> None:
        details = breakdown.details
        previous_matchday = breakdown.cutoff_matchday - 1
        history_text = (
            "Spieltag 1"
            if previous_matchday == 1
            else f"Spieltage 1–{previous_matchday}"
        )

        self.details_data_label.setText(
            f"Datenbasis: {breakdown.historical_matches} historische Spiele  |  "
            f"{history_text}  |  Modus: {breakdown.mode.value.upper()}"
        )

        self._set_detail_row(
            "league",
            details.league_average_home_goals,
            details.league_average_away_goals,
        )

        step_map = {step.name: step for step in details.steps}
        for key, step_name in (
            ("team", "Teamstärke"),
            ("form", "Form"),
            ("opponent", "Gegnerstärke"),
            ("player", "Spielerstärke"),
            ("lineup", "Startelf"),
        ):
            step = step_map.get(step_name)
            self._set_detail_row(
                key,
                step.home if step is not None else None,
                step.away if step is not None else None,
            )

        self._set_detail_row(
            "final",
            details.final_expected_goals.home,
            details.final_expected_goals.away,
        )

        self._set_factor_row(
            "form",
            details.home_form_factor,
            details.away_form_factor,
        )
        self._set_factor_row(
            "opponent",
            details.home_opponent_factor,
            details.away_opponent_factor,
        )
        self._set_factor_row(
            "player",
            details.home_player_factor,
            details.away_player_factor,
        )
        self._set_factor_row(
            "lineup",
            details.home_lineup_factor,
            details.away_lineup_factor,
        )

    def _set_factor_row(
        self,
        key: str,
        home_value: float | None,
        away_value: float | None,
    ) -> None:
        labels = self.factor_rows.get(key)
        if labels is None:
            return

        home_label, away_label = labels
        home_label.setText("–" if home_value is None else f"{home_value:.3f}")
        away_label.setText("–" if away_value is None else f"{away_value:.3f}")

    def _set_detail_row(
        self,
        key: str,
        home_value: float | None,
        away_value: float | None,
    ) -> None:
        labels = self.detail_rows.get(key)
        if labels is None:
            return

        home_label, away_label = labels
        home_label.setText("–" if home_value is None else f"{home_value:.2f}")
        away_label.setText("–" if away_value is None else f"{away_value:.2f}")

    def _reset_breakdown(self) -> None:
        self.details_data_label.setText("Noch keine Prognose berechnet.")
        for home_label, away_label in self.detail_rows.values():
            home_label.setText("–")
            away_label.setText("–")

        for home_label, away_label in self.factor_rows.values():
            home_label.setText("–")
            away_label.setText("–")

    def _team_name(
        self,
        team_id: int,
    ) -> str:
        if self.service is None:
            return f"Team {team_id}"

        return self.service._get_team_name(
            team_id
        )

    def _reset_scores(
        self,
    ) -> None:
        for (
            _,
            score_label,
            probability_label,
        ) in self.score_widgets:
            score_label.setText(
                "–"
            )

            probability_label.setText(
                "–"
            )

    def _reset_prediction(
        self,
    ) -> None:
        self.home_team_label.setText(
            "Heim"
        )

        self.away_team_label.setText(
            "Auswärts"
        )

        self.home_expected_label.setText(
            "–"
        )

        self.away_expected_label.setText(
            "–"
        )

        self.home_probability_widget.probability_label.setText(
            "–"
        )

        self.draw_probability_widget.probability_label.setText(
            "–"
        )

        self.away_probability_widget.probability_label.setText(
            "–"
        )

        self._reset_scores()

        self.cutoff_label.setText(
            ""
        )

        self._reset_breakdown()

    def _reset_view(
        self,
    ) -> None:
        self.matchday_combo.clear()
        self.match_combo.clear()

        self.mode_combo.setCurrentIndex(
            0
        )

        self.lineup_status_label.setText(
            ""
        )

        self.info_label.setText(
            ""
        )

        self.predict_button.setEnabled(
            False
        )

        self._reset_prediction()

    def closeEvent(
        self,
        event,
    ) -> None:
        self._close_connection()

        super().closeEvent(
            event
        )