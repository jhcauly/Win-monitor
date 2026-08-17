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


class SetupMode(StrEnum):
    TREND = "TREND"
    RECOVERY = "RECOVERY"
    NONE = "NENHUM"


@dataclass(slots=True)
class TechnicalObservation:
    readable: bool
    current_price: float | None

    ma20_slope: Slope
    price_vs_ma20: Position
    ma8_vs_ma20: Position

    ma20_slope_m15: Slope = Slope.UNKNOWN
    price_vs_ma20_m15: Position = Position.UNKNOWN
    context_m15: Slope = Slope.UNKNOWN

    ma20_slope_m5: Slope = Slope.UNKNOWN
    price_vs_ma20_m5: Position = Position.UNKNOWN
    ma8_slope: Slope = Slope.UNKNOWN
    ma8_cross: Cross = Cross.NONE
    breakout: Breakout = Breakout.UNKNOWN

    relevant_top: float | None = None
    relevant_bottom: float | None = None
    candle_closed: bool | None = None
    in_consolidation: bool | None = None
    swing_confirmed: bool | None = None
    pullback_to_ma20_m5: bool | None = None
    resumption_after_pullback_m5: bool | None = None

    closed_beyond_ma8_m60: bool | None = None
    distance_to_ma20_m60_points: float | None = None
    setup_mode: SetupMode = SetupMode.NONE

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
            ma20_slope_m15=_enum_or_default(Slope, payload.get("ma20_inclinacao_m15"), Slope.UNKNOWN),
            price_vs_ma20_m15=_enum_or_default(Position, payload.get("preco_vs_ma20_m15"), Position.UNKNOWN),
            context_m15=_enum_or_default(Slope, payload.get("contexto_m15"), Slope.UNKNOWN),
            ma20_slope_m5=_enum_or_default(Slope, payload.get("ma20_inclinacao_m5"), Slope.UNKNOWN),
            price_vs_ma20_m5=_enum_or_default(Position, payload.get("preco_vs_ma20_m5"), Position.UNKNOWN),
            ma8_slope=_enum_or_default(Slope, payload.get("ma8_inclinacao_m5"), Slope.UNKNOWN),
            ma8_cross=_enum_or_default(Cross, payload.get("ma8_cruzamento_m5"), Cross.UNKNOWN),
            breakout=_enum_or_default(Breakout, payload.get("rompimento_m5"), Breakout.UNKNOWN),
            relevant_top=_number_or_none(payload.get("topo_relevante")),
            relevant_bottom=_number_or_none(payload.get("fundo_relevante")),
            candle_closed=_bool_or_none(payload.get("candle_fechado")),
            in_consolidation=_bool_or_none(payload.get("consolidacao")),
            swing_confirmed=_bool_or_none(payload.get("pivo_confirmado")),
            pullback_to_ma20_m5=_bool_or_none(payload.get("retorno_ma20_m5")),
            resumption_after_pullback_m5=_bool_or_none(payload.get("retomada_apos_correcao_m5")),
            closed_beyond_ma8_m60=_bool_or_none(payload.get("fechou_alem_ma8_m60")),
            distance_to_ma20_m60_points=_number_or_none(payload.get("distancia_ma20_m60_pontos")),
            setup_mode=_enum_or_default(SetupMode, payload.get("modo_setup"), SetupMode.NONE),
            target1=_number_or_none(payload.get("alvo1_estrutural")),
            target2=_number_or_none(payload.get("alvo2_estrutural")),
            fib_context=str(payload.get("contexto_fibonacci") or "-"),
            notes=str(payload.get("notas") or "-"),
            moving_against_position=_bool_or_none(payload.get("movimento_contra_posicao")),
            visual_markers=_visual_markers(payload.get("marcacoes_visuais")),
        )


def evaluate_observation(o: TechnicalObservation) -> AnalysisResult:
    if not o.readable:
        return _no_setup(o, "LEITURA_INSUFICIENTE", "Nao foi possivel ler com seguranca o grafico M5 e as medias projetadas.")

    direction = _direction_from_m5(o)
    if direction is SignalDirection.NONE:
        return _no_setup(o, "M5_SEM_DIRECAO", "O M5 ainda nao formou direcao operacional clara.")

    if o.in_consolidation is True:
        return _almost(o, direction, "RANGE", "Consolidacao detectada no M5. Aguardar saida da faixa.", DecisionState.WAIT)

    if not _higher_timeframe_allows(o, direction):
        return _almost(
            o,
            direction,
            "CONTEXTO_MAIOR_NAO_CONFIRMA",
            "M15/M60 projetados no M5 ainda nao oferecem contexto ou espaco suficiente para esta direcao.",
            DecisionState.WAIT,
        )

    if o.swing_confirmed is not True:
        return _almost(o, direction, "PIVO_NAO_CONFIRMADO", "O pivo do M5 ainda nao esta confirmado com candles fechados.", DecisionState.PREPARE)

    if o.pullback_to_ma20_m5 is not True:
        return _almost(o, direction, "AGUARDAR_PULLBACK_MA20_M5", "Aguardar a correcao do M5 ate a MA20_M5 antes de perseguir o movimento.", DecisionState.PREPARE)

    if o.resumption_after_pullback_m5 is not True:
        return _almost(o, direction, "AGUARDAR_RETOMADA_M5", "O preco corrigiu na MA20_M5, mas a retomada ainda nao foi confirmada.", DecisionState.ARM)

    if o.candle_closed is not True:
        return _almost(o, direction, "CANDLE_NAO_FECHADO", "O candle do gatilho precisa fechar antes da entrada.", DecisionState.ARM)

    expected_breakout = Breakout.UP if direction is SignalDirection.BUY else Breakout.DOWN
    if o.breakout is not expected_breakout:
        return _almost(o, direction, "ROMPIMENTO_AUSENTE", "A retomada ainda nao rompeu o topo/fundo tecnico do gatilho.", DecisionState.ARM)

    stop = o.relevant_bottom if direction is SignalDirection.BUY else o.relevant_top
    if o.current_price is None or stop is None or o.target1 is None:
        return _almost(o, direction, "PLANO_INCOMPLETO", "Falta preco, stop tecnico ou alvo estrutural para montar o plano completo.", DecisionState.ARM)

    confidence = Confidence.HIGH if o.setup_mode is SetupMode.TREND else Confidence.MEDIUM
    return AnalysisResult(
        scenario_type=ScenarioType.ENTRY,
        signal=direction,
        confidence=confidence,
        current_price=o.current_price,
        bias_m60=_bias_text(o, direction),
        structure_m15=_m15_text(o),
        fib_zone_m5=_m5_text(o),
        suggested_entry=o.current_price,
        suggested_stop=stop,
        suggested_target1=o.target1,
        suggested_target2=o.target2,
        rationale=(
            f"Modo {o.setup_mode.value}: contexto maior permitido; M5 confirmou pivo, "
            "pullback na MA20, retomada e rompimento com candle fechado."
        ),
        decision_state=DecisionState.ENTER,
        visual_markers=o.visual_markers,
    )


def should_defensive_exit(o: TechnicalObservation, position: SignalDirection) -> bool:
    if position is SignalDirection.BUY:
        return o.price_vs_ma20_m5 is Position.BELOW or (o.moving_against_position is True and o.ma8_cross is Cross.DOWN)
    if position is SignalDirection.SELL:
        return o.price_vs_ma20_m5 is Position.ABOVE or (o.moving_against_position is True and o.ma8_cross is Cross.UP)
    return False


def _direction_from_m5(o: TechnicalObservation) -> SignalDirection:
    if o.ma8_slope is Slope.UP and o.price_vs_ma20_m5 in {Position.ABOVE, Position.TOUCHING}:
        return SignalDirection.BUY
    if o.ma8_slope is Slope.DOWN and o.price_vs_ma20_m5 in {Position.BELOW, Position.TOUCHING}:
        return SignalDirection.SELL
    return SignalDirection.NONE


def _higher_timeframe_allows(o: TechnicalObservation, direction: SignalDirection) -> bool:
    if o.setup_mode is SetupMode.TREND:
        if direction is SignalDirection.BUY:
            return (
                o.ma20_slope is Slope.UP
                and o.context_m15 is Slope.UP
                and o.price_vs_ma20 in {Position.ABOVE, Position.TOUCHING}
            )
        return (
            o.ma20_slope is Slope.DOWN
            and o.context_m15 is Slope.DOWN
            and o.price_vs_ma20 in {Position.BELOW, Position.TOUCHING}
        )

    if o.setup_mode is SetupMode.RECOVERY:
        if o.closed_beyond_ma8_m60 is not True:
            return False
        if o.distance_to_ma20_m60_points is None or o.distance_to_ma20_m60_points < 400:
            return False
        if direction is SignalDirection.BUY:
            return o.context_m15 is Slope.UP
        return o.context_m15 is Slope.DOWN

    return False


def _no_setup(o: TechnicalObservation, code: str, reason: str) -> AnalysisResult:
    return AnalysisResult(
        scenario_type=ScenarioType.NO_SETUP,
        signal=SignalDirection.NONE,
        confidence=Confidence.LOW,
        current_price=o.current_price,
        bias_m60=_bias_text(o, SignalDirection.NONE),
        structure_m15=_m15_text(o),
        fib_zone_m5=_m5_text(o),
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
        structure_m15=_m15_text(o),
        fib_zone_m5=_m5_text(o),
        missing_confirmation_code=code,
        missing_confirmation=reason,
        rationale=reason,
        decision_state=state,
        visual_markers=o.visual_markers,
    )


def _bias_text(o: TechnicalObservation, direction: SignalDirection) -> str:
    return (
        f"Modo={o.setup_mode.value}; direcao={direction.value}; MA20_M60={o.ma20_slope.value}; "
        f"preco_vs_MA20_M60={o.price_vs_ma20.value}; MA8_M60_vs_MA20_M60={o.ma8_vs_ma20.value}; "
        f"distancia_MA20_M60={o.distance_to_ma20_m60_points}."
    )


def _m15_text(o: TechnicalObservation) -> str:
    return (
        f"contexto={o.context_m15.value}; MA20_M15={o.ma20_slope_m15.value}; "
        f"preco_vs_MA20_M15={o.price_vs_ma20_m15.value}."
    )


def _m5_text(o: TechnicalObservation) -> str:
    return (
        f"MA8_M5={o.ma8_slope.value}; MA20_M5={o.ma20_slope_m5.value}; "
        f"preco_vs_MA20_M5={o.price_vs_ma20_m5.value}; pullback_MA20={o.pullback_to_ma20_m5}; "
        f"retomada={o.resumption_after_pullback_m5}; rompimento={o.breakout.value}; "
        f"topo={o.relevant_top}; fundo={o.relevant_bottom}."
    )


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
