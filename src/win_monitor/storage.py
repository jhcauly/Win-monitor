from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from win_monitor.models import (
    AnalysisResult,
    OpenSignal,
    ScenarioType,
    SignalDirection,
    SignalOutcome,
)
from win_monitor.technical import TechnicalObservation


@dataclass(slots=True)
class StoragePaths:
    base_dir: Path

    @property
    def captures_dir(self) -> Path:
        return self.base_dir / "capturas"

    @property
    def log_csv(self) -> Path:
        return self.base_dir / "sinais_log.csv"

    @property
    def observations_jsonl(self) -> Path:
        return self.base_dir / "observacoes_visuais.jsonl"

    @property
    def open_signals_json(self) -> Path:
        return self.base_dir / "sinais_abertos.json"


class StudyStorage:
    def __init__(self, base_dir: Path) -> None:
        self.paths = StoragePaths(base_dir)
        self.paths.base_dir.mkdir(parents=True, exist_ok=True)
        self.paths.captures_dir.mkdir(parents=True, exist_ok=True)

    def save_study_image(
        self,
        image_bytes: bytes,
        analysis: AnalysisResult,
    ) -> Path:
        now = datetime.now()
        day_dir = self.paths.captures_dir / now.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / (
            f"{now.strftime('%H%M%S')}_{analysis.scenario_type.value}.png"
        )
        path.write_bytes(image_bytes)
        return path

    def append_observation(
        self,
        observation: TechnicalObservation,
        image_path: str,
    ) -> None:
        record = {
            "timestamp": datetime.now().isoformat(),
            "imagem": image_path,
            "observacao": asdict(observation),
        }
        with self.paths.observations_jsonl.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def append_analysis_log(
        self,
        analysis: AnalysisResult,
        image_path: str,
        result: str = "EM_ABERTO",
    ) -> None:
        new_file = not self.paths.log_csv.exists()
        with self.paths.log_csv.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if new_file:
                writer.writerow(
                    [
                        "timestamp",
                        "tipo_cenario",
                        "sinal",
                        "confianca",
                        "preco_atual",
                        "entrada",
                        "stop",
                        "alvo1",
                        "alvo2",
                        "resultado",
                        "imagem",
                        "motivo_codigo",
                        "justificativa",
                    ]
                )
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    analysis.scenario_type.value,
                    analysis.signal.value,
                    analysis.confidence.value,
                    analysis.current_price,
                    analysis.suggested_entry,
                    analysis.suggested_stop,
                    analysis.suggested_target1,
                    analysis.suggested_target2,
                    result,
                    image_path,
                    analysis.missing_confirmation_code,
                    analysis.rationale,
                ]
            )

    def load_open_signals(self) -> list[OpenSignal]:
        path = self.paths.open_signals_json
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return [OpenSignal.from_mapping(item) for item in payload]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            corrupt = path.with_suffix(f".corrupt-{timestamp}.json")
            path.replace(corrupt)
            return []

    def save_open_signals(self, signals: list[OpenSignal]) -> None:
        path = self.paths.open_signals_json
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                [signal.to_mapping() for signal in signals],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(tmp, path)

    def register_open_signal(self, analysis: AnalysisResult) -> bool:
        complete_plan = (
            analysis.scenario_type is ScenarioType.ENTRY
            and analysis.signal is not SignalDirection.NONE
            and analysis.suggested_entry is not None
            and analysis.suggested_stop is not None
            and analysis.suggested_target1 is not None
        )
        if not complete_plan:
            return False

        signals = self.load_open_signals()
        signals.append(
            OpenSignal(
                timestamp=datetime.now().isoformat(),
                signal=analysis.signal,
                entry=analysis.suggested_entry,
                stop=analysis.suggested_stop,
                target1=analysis.suggested_target1,
                target2=analysis.suggested_target2,
            )
        )
        self.save_open_signals(signals)
        return True

    def evaluate_open_signals(
        self,
        current_price: float | None,
    ) -> list[SignalOutcome]:
        if current_price is None:
            return []

        remaining: list[OpenSignal] = []
        outcomes: list[SignalOutcome] = []
        now = datetime.now()
        for signal in self.load_open_signals():
            result: str | None = None
            if signal.signal is SignalDirection.BUY:
                if current_price <= signal.stop:
                    result = "PERDEU (stop)"
                elif current_price >= signal.target1:
                    result = "GANHOU (alvo1)"
            elif signal.signal is SignalDirection.SELL:
                if current_price >= signal.stop:
                    result = "PERDEU (stop)"
                elif current_price <= signal.target1:
                    result = "GANHOU (alvo1)"

            if result:
                outcomes.append(
                    SignalOutcome(
                        signal=signal,
                        result=result,
                        observed_price=current_price,
                        observed_at=now,
                    )
                )
            else:
                remaining.append(signal)

        self.save_open_signals(remaining)
        return outcomes
