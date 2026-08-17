from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from win_monitor.models import AnalysisResult, Confidence, DecisionState, ScenarioType, SignalDirection


class Slope(StrEnum):
    UP = "ALTA"
    DOWN = "BAIXA"
    FLAT = "LATERAL"
    UNKNOWN = "DESCONHECIDA"


class Position(StrEnum):
    ABOVE = "ACIMA"
    BELOW = "ABAIXO"
    TOUCHING = "TOCANDO"
    UNKNOWN = "DESCONHECIDA"


class Breakout(StrEnum):
    UP = "ROMPEU_CIMA"
    DOWN = "ROMPEU_BAIXO"
    NONE = "SEM_ROMPIMENTO"
    UNKNOWN = "DESCONHECIDO"


class Cross(StrEnum):
    UP = "CRUZOU_CIMA"
    DOWN = "CRUZOU_BAIXO"
    NONE = "SEM_CRUZAMENTO"
    UNKNOWN = "DESCONHECIDO"


@dataclass(slots=True)
class TechnicalObservation:
    readable: bool
    current_price: float | None
    ma20_slope: Slope
    price_vs_ma20: Position
    ma8_vs_ma20: Position
    ma8_slope: Slope
    breakout: Breakout
    relevant_top: float | None
    relevant_bottom: float | None
    candle_closed: bool | None
    in_consolidation: bool | None
    swing_confirmed: bool | None
    ma8_cross: Cross = Cross.NONE
    target1: float | None = None
    target2: float | None = None
    fib_context: str = "-"
    notes: str = "-"
    moving_against_position: bool | None = None
    visual_markers: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> TechnicalObservation:
        return cls(
            readable=_bool_or_none(payload.get("legivel")) is True,
            current_price=_number_or_none(payload.get("preco_atual")),
            ma20_slope=_enum_or_default(Slope, payload.get("ma20_inclinacao_m60"), Slope.UNKNOWN),
            price_vs_ma20=_enum_or_default(Position, payload.get("preco_vs_ma20_m60"), Position.UNKNOWN),
            ma8_vs_ma20=_enum_or_default(Position, payload.get("ma8_vs_ma20_m60"), Position.UNKNOWN),
            ma8_slope=_enum_or_default(Slope, payload.get("ma8_inclinacao_m5"), Slope.UNKNOWN),
            breakout=_enum_or_default(Breakout, payload.get("rompimento_m5"), Breakout.UNKNOWN),
            relevant_top=_number_or_none(payload.get("topo_relevante")),
            relevant_bottom=_number_or_none(payload.get("fundo_relevante")),
            candle_closed=_bool_or_none(payload.get("candle_fechado")),
            in_consolidation=_bool_or_none(payload.get("consolidacao")),
            swing_confirmed=_bool_or_none(payload.get("pivo_confirmado")),
            ma8_cross=_enum_or_default(Cross, payload.get("ma8_cruzamento_m5"), Cross.UNKNOWN),
            target1=_number_or_none(payload.get("alvo1_estrutural")),
            target2=_number_or_none(payload.get("alvo2_estrutural")),
            fib_context=str(payload.get("contexto_fibonacci") or "-"),
            notes=str(payload.get("notas") or "-"),
            moving_against_position=_bool_or_none(payload.get("movimento_contra_posicao")),
            visual_markers=_visual_markers(payload.get("marcacoes_visuais")),
        )


def evaluate_observation(o: TechnicalObservation) -> AnalysisResult:
    if not o.readable:
        return _no_setup(o, "LEITURA_INSUFICIENTE", "Nao foi possivel ler com seguranca os elementos obrigatorios.")

    direction = _trend_direction(o)
    if direction is SignalDirection.NONE:
        return _no_setup(o, "M60_FRACO", "A inclinacao da MA20 e a posicao do preco/MA8 nao confirmam tendencia.")
    if o.in_consolidation is True:
        return _almost(o, direction, "RANGE", "Consolidacao detectada; rompimentos dentro da faixa ficam bloqueados.", DecisionState.WAIT)
    if o.swing_confirmed is not True:
        return _almost(o, direction, "PIVO_NAO_CONFIRMADO", "O topo/fundo relevante ainda nao esta confirmado sem olhar candles futuros.", DecisionState.PREPARE)
    if o.candle_closed is not True:
        return _almost(o, direction, "CANDLE_NAO_FECHADO", "O gatilho so vale depois do fechamento do candle.", DecisionState.ARM)

    expected_slope = Slope.UP if direction is SignalDirection.BUY else Slope.DOWN
    if o.ma8_slope is not expected_slope:
        return _almost(o, direction, "MA8_SEM_INCLINACAO", "A MA8 ainda nao acompanha a direcao esperada.", DecisionState.PREPARE)
    if not _fast_trigger_confirmed(o, direction):
        return _almost(o, direction, "MA8_SEM_CRUZAMENTO", "A MA8 ainda nao confirmou o gatilho a favor.", DecisionState.PREPARE)

    expected_breakout = Breakout.UP if direction is SignalDirection.BUY else Breakout.DOWN
    if o.breakout is not expected_breakout:
        return _almost(o, direction, "ROMPIMENTO_AUSENTE", "O topo/fundo tecnico relevante ainda nao foi rompido.", DecisionState.ARM)

    stop = o.relevant_bottom if direction is SignalDirection.BUY else o.relevant_top
    if o.current_price is None or stop is None or o.target1 is None:
        return _almost(o, direction, "PLANO_INCOMPLETO", "Falta preco, stop tecnico ou alvo estrutural para montar o plano completo.", DecisionState.ARM)

    return AnalysisResult(
        scenario_type=ScenarioType.ENTRY,
        signal=direction,
        confidence=Confidence.HIGH,
        current_price=o.current_price,
        bias_m60=_bias_text(o, direction),
        structure_m15=_structure_text(o),
        fib_zone_m5=o.fib_context,
        suggested_entry=o.current_price,
        suggested_stop=stop,
        suggested_target1=o.target1,
        suggested_target2=o.target2,
        rationale="Contexto, estrutura, gatilho e rompimento confirmados com candle fechado.",
        decision_state=DecisionState.ENTER,
        visual_markers=o.visual_markers,
    )


def should_defensive_exit(o: TechnicalObservation, position: SignalDirection) -> bool:
    if position is SignalDirection.BUY:
        return o.price_vs_ma20 is Position.BELOW or (o.moving_against_position is True and o.ma8_cross is Cross.DOWN)
    if position is SignalDirection.SELL:
        return o.price_vs_ma20 is Position.ABOVE or (o.moving_against_position is True and o.ma8_cross is Cross.UP)
    return False


def _trend_direction(o: TechnicalObservation) -> SignalDirection:
    buy = {Position.ABOVE, Position.TOUCHING}
    sell = {Position.BELOW, Position.TOUCHING}
    if o.ma20_slope is Slope.UP and o.price_vs_ma20 in buy and o.ma8_vs_ma20 in buy:
        return SignalDirection.BUY
    if o.ma20_slope is Slope.DOWN and o.price_vs_ma20 in sell and o.ma8_vs_ma20 in sell:
        return SignalDirection.SELL
    return SignalDirection.NONE


def _fast_trigger_confirmed(o: TechnicalObservation, direction: SignalDirection) -> bool:
    if direction is SignalDirection.BUY:
        return o.ma8_vs_ma20 is Position.ABOVE or o.ma8_cross is Cross.UP
    if direction is SignalDirection.SELL:
        return o.ma8_vs_ma20 is Position.BELOW or o.ma8_cross is Cross.DOWN
    return False


def _no_setup(o: TechnicalObservation, code: str, reason: str) -> AnalysisResult:
    return AnalysisResult(
        scenario_type=ScenarioType.NO_SETUP,
        signal=SignalDirection.NONE,
        confidence=Confidence.LOW,
        current_price=o.current_price,
        bias_m60="Sem vies confirmado",
        structure_m15=_structure_text(o),
        fib_zone_m5=o.fib_context,
        missing_confirmation_code=code,
        missing_confirmation=reason,
        rationale=reason,
        decision_state=DecisionState.WAIT,
        visual_markers=o.visual_markers,
    )


def _almost(o: TechnicalObservation, direction: SignalDirection, code: str, reason: str, state: DecisionState) -> AnalysisResult:
    return AnalysisResult(
        scenario_type=ScenarioType.ALMOST,
        signal=direction,
        confidence=Confidence.MEDIUM,
        current_price=o.current_price,
        bias_m60=_bias_text(o, direction),
        structure_m15=_structure_text(o),
        fib_zone_m5=o.fib_context,
        missing_confirmation_code=code,
        missing_confirmation=reason,
        rationale=reason,
        decision_state=state,
        visual_markers=o.visual_markers,
    )


def _bias_text(o: TechnicalObservation, direction: SignalDirection) -> str:
    return f"{direction.value}: MA20 {o.ma20_slope.value}; preco {o.price_vs_ma20.value}; MA8 {o.ma8_vs_ma20.value}."


def _structure_text(o: TechnicalObservation) -> str:
    return f"Topo={o.relevant_top}; fundo={o.relevant_bottom}; rompimento={o.breakout.value}; consolidacao={o.in_consolidation}."


def _visual_markers(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if not isinstance(item, dict):
            continue
        x, y = item.get("x"), item.get("y")
        if not isinstance(x, int | float) or not isinstance(y, int | float):
            continue
        result.append({
            "tipo": str(item.get("tipo") or "PONTO").upper(),
            "rotulo": str(item.get("rotulo") or ""),
            "timeframe": str(item.get("timeframe") or ""),
            "x": max(0.0, min(1000.0, float(x))),
            "y": max(0.0, min(1000.0, float(y))),
        })
    return result


def _enum_or_default(enum_type: type, value: Any, default: Any) -> Any:
    try:
        return enum_type(str(value).strip().upper())
    except (TypeError, ValueError):
        return default


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "sim", "yes"}:
        return True
    if text in {"false", "0", "nao", "não", "no"}:
        return False
    return None


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
