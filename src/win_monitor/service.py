from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime

from win_monitor.capture import ScreenCapture
from win_monitor.config import Settings
from win_monitor.formatters import telegram_caption
from win_monitor.models import AnalysisResult, Confidence, ScenarioType
from win_monitor.risk import calculate_trade_risk
from win_monitor.storage import StudyStorage
from win_monitor.study_image import StudyImageComposer
from win_monitor.telegram_client import TelegramClient
from win_monitor.time_utils import next_candle_close, within_trading_hours
from win_monitor.vision import AnthropicVisionAnalyzer


class MonitorService:
    def __init__(
        self,
        settings: Settings,
        *,
        log: Callable[[str], None] = print,
    ) -> None:
        self.settings = settings
        self.log = log
        self.capture = ScreenCapture(settings.capture_region)
        self.analyzer = AnthropicVisionAnalyzer(
            settings.anthropic_api_key,
            settings.model,
        )
        self.telegram = TelegramClient(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
        )
        self.storage = StudyStorage(settings.data_dir)
        self.composer = StudyImageComposer()

    def process_once(self) -> AnalysisResult:
        self.log(f"[{datetime.now().strftime('%H:%M:%S')}] Capturando e analisando...")
        screenshot = self.capture.capture_png()
        analysis = self.analyzer.analyze(screenshot)
        risk = calculate_trade_risk(
            analysis,
            max_contracts=self.settings.max_contracts,
            max_risk_brl=self.settings.max_risk_brl,
        )

        if risk and risk.recommended_contracts == 0:
            analysis.scenario_type = ScenarioType.ALMOST
            analysis.missing_confirmation_code = "RISCO_FINANCEIRO"
            analysis.missing_confirmation = (
                "O stop tecnico nao cabe no risco financeiro configurado nem com 1 contrato."
            )
            analysis.rationale = (
                f"{analysis.rationale} Entrada bloqueada pelo limite financeiro."
            )

        for outcome in self.storage.evaluate_open_signals(analysis.current_price):
            emoji = "✅" if "GANHOU" in outcome.result else "❌"
            self.telegram.send_text(
                f"{emoji} Resultado do sinal de {outcome.signal.timestamp}: "
                f"<b>{outcome.result}</b>\n"
                f"{outcome.signal.signal.value} | Entrada: {outcome.signal.entry} | "
                f"Preco observado: {outcome.observed_price}"
            )
            result_analysis = AnalysisResult(
                scenario_type=ScenarioType.RESULT,
                signal=outcome.signal.signal,
                confidence=Confidence.MEDIUM,
                current_price=outcome.observed_price,
                suggested_entry=outcome.signal.entry,
                suggested_stop=outcome.signal.stop,
                suggested_target1=outcome.signal.target1,
                suggested_target2=outcome.signal.target2,
                rationale=(
                    "Resultado aproximado, observado nos ciclos de 5 minutos, "
                    f"referente ao sinal de {outcome.signal.timestamp}."
                ),
            )
            self.storage.append_analysis_log(
                result_analysis,
                "-",
                outcome.result,
            )

        study_image = self.composer.compose(screenshot, analysis, risk)
        image_path = self.storage.save_study_image(study_image, analysis)
        self.storage.append_analysis_log(analysis, str(image_path))
        self.storage.register_open_signal(analysis)
        self.log(
            f"  -> {analysis.scenario_type.value}: "
            f"{analysis.rationale[:120]}"
        )

        if analysis.scenario_type.value in self.settings.telegram_scenarios:
            self.telegram.send_photo(
                study_image,
                telegram_caption(analysis, risk),
            )
        return analysis

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        stop_event = stop_event or threading.Event()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.telegram.send_text(
            "🚀 WIN Monitor iniciado em modo estudo. Nao executarei ordens; "
            "enviarei ENTRADA e QUASE para revisao."
        )
        self.log("WIN Monitor iniciado em modo estudo.")

        while not stop_event.is_set():
            now = datetime.now()
            if not within_trading_hours(
                now,
                self.settings.start_time,
                self.settings.end_time,
            ):
                stop_event.wait(30)
                continue

            target = next_candle_close(now, self.settings.interval_minutes)
            wait_seconds = max(
                0.0,
                (target - datetime.now()).total_seconds(),
            )
            if stop_event.wait(wait_seconds):
                break

            try:
                self.process_once()
            except Exception as exc:
                self.log(f"[ERRO] {exc}")
                try:
                    self.telegram.send_text(f"⚠️ Erro no monitor: {exc}")
                except Exception as telegram_exc:
                    self.log(f"[ERRO] Falha ao avisar Telegram: {telegram_exc}")
            stop_event.wait(2)
