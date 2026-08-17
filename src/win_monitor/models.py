from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ScenarioType(StrEnum):
    ENTRY = "ENTRADA"
    ALMOST = "QUASE"
    NO_SETUP = "SEM_SETUP"
    RESULT = "RESULTADO"


class SignalDirection(StrEnum):
    BUY = "COMPRA"
    SELL = "VENDA"
    NONE = "NENHUM"


class Confidence(StrEnum):
    HIGH = "ALTA"
    MEDIUM = "MEDIA"
    LOW = "BAIXA"


class DecisionState(StrEnum):
    WAIT = "AGUARDAR"
    PREPARE = "PREPARAR"
    ARM = "ARMAR"
    ENTER = "ENTRAR"
    MANAGE = "GERENCIAR"


@dataclass(slots=True)
class AnalysisResult:
    scenario_type: ScenarioType
    signal: SignalDirection
    confidence: Confidence
    current_price: float | None = None
    bias_m60: str = "-"
    structure_m15: str = "-"
    fib_zone_m5: str = "-"
    suggested_entry: float | None = None
    suggested_stop: float | None = None
    suggested_target1: float | None = None
    suggested_target2: float | None = None
    missing_confirmation_code: str | None = None
    missing_confirmation: str | None = None
    rationale: str = "-"
    decision_state: DecisionState = DecisionState.WAIT
    visual_markers: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> AnalysisResult:
        result = cls(
            scenario_type=_enum_or_default(
                ScenarioType,
                payload.get("tipo_cenario"),
                ScenarioType.NO_SETUP,
            ),
            signal=_enum_or_default(
                SignalDirection,
                payload.get("sinal"),
                SignalDirection.NONE,
            ),
            confidence=_enum_or_default(
                Confidence,
                payload.get("confianca"),
                Confidence.LOW,
            ),
            current_price=_number_or_none(payload.get("preco_atual")),
            bias_m60=str(payload.get("vies_m60") or "-"),
            structure_m15=str(payload.get("estrutura_m15") or "-"),
            fib_zone_m5=str(payload.get("zona_fibo_m5") or "-"),
            suggested_entry=_number_or_none(payload.get("entrada_sugerida")),
            suggested_stop=_number_or_none(payload.get("stop_sugerido")),
            suggested_target1=_number_or_none(payload.get("alvo1_sugerido")),
            suggested_target2=_number_or_none(payload.get("alvo2_sugerido")),
            missing_confirmation_code=_text_or_none(
                payload.get("motivo_nao_confirmou_codigo")
            ),
            missing_confirmation=_text_or_none(
                payload.get("motivo_nao_confirmou")
            ),
            rationale=str(payload.get("justificativa") or "-"),
            decision_state=_enum_or_default(
                DecisionState,
                payload.get("estado_decisao"),
                DecisionState.WAIT,
            ),
            visual_markers=_visual_markers(payload.get("marcacoes_visuais")),
        )
        return result.safety_normalized()

    def safety_normalized(self) -> AnalysisResult:
        required = (
            self.signal is not SignalDirection.NONE,
            self.suggested_entry is not None,
            self.suggested_stop is not None,
            self.suggested_target1 is not None,
        )
        if self.scenario_type is ScenarioType.ENTRY and not all(required):
            self.scenario_type = ScenarioType.ALMOST
            self.decision_state = DecisionState.PREPARE
            self.missing_confirmation_code = "PLANO_INCOMPLETO"
            self.missing_confirmation = (
                "A leitura indicou entrada, mas faltou direcao, entrada, stop ou alvo1."
            )
            self.rationale = (
                f"{self.rationale} Entrada bloqueada por plano incompleto."
            )
        return self


@dataclass(slots=True)
class OpenSignal:
    timestamp: str
    signal: SignalDirection
    entry: float
    stop: float
    target1: float
    target2: float | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> OpenSignal:
        return cls(
            timestamp=str(payload["timestamp"]),
            signal=SignalDirection(str(payload["sinal"])),
            entry=float(payload["entrada"]),
            stop=float(payload["stop"]),
            target1=float(payload["alvo1"]),
            target2=_number_or_none(payload.get("alvo2")),
        )

    def to_mapping(self) -> dict[str, Any]:
        result = asdict(self)
        return {
            "timestamp": result["timestamp"],
            "sinal": self.signal.value,
            "entrada": result["entry"],
            "stop": result["stop"],
            "alvo1": result["target1"],
            "alvo2": result["target2"],
        }


@dataclass(slots=True)
class TradeRisk:
    risk_points: float
    risk_per_contract_brl: float
    risk_five_contracts_brl: float
    recommended_contracts: int
    recommended_risk_brl: float


@dataclass(slots=True)
class SignalOutcome:
    signal: OpenSignal
    result: str
    observed_price: float
    observed_at: datetime


def _enum_or_default(enum_type: type, value: Any, default: Any) -> Any:
    try:
        return enum_type(str(value).upper())
    except (ValueError, TypeError):
        return default


def _number_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, int | float):
        return float(value)

    text = str(value).strip().replace(" ", "")
    if not text:
        return None

    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") == 1:
        integer_part, decimal_part = text.split(".")
        if decimal_part.isdigit() and len(decimal_part) == 3:
            text = integer_part + decimal_part

    try:
        return float(text)
    except ValueError:
        return None


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _visual_markers(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        x = item.get("x")
        y = item.get("y")
        if not isinstance(x, int | float) or not isinstance(y, int | float):
            continue
        result.append(
            {
                "tipo": str(item.get("tipo") or "PONTO").upper(),
                "rotulo": str(item.get("rotulo") or ""),
                "timeframe": str(item.get("timeframe") or ""),
                "x": max(0.0, min(1000.0, float(x))),
                "y": max(0.0, min(1000.0, float(y))),
            }
        )
    return result
