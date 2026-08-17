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


class MarketSituation(StrEnum):
    TREND = "TENDENCIA"
    CORRECTION = "CORRECAO"
    RANGE = "RANGE"
    TRANSITION = "TRANSICAO"
    REJECTION = "REJEICAO"
    UNKNOWN = "DESCONHECIDA"


class Pattern(StrEnum):
    PIVOT_UP = "PIVO_ALTA"
    PIVOT_DOWN = "PIVO_BAIXA"
    FLAG_UP = "BANDEIRA_ALTA"
    FLAG_DOWN = "BANDEIRA_BAIXA"
    TRIANGLE = "TRIANGULO"
    CHANNEL_UP = "CANAL_ALTA"
    CHANNEL_DOWN = "CANAL_BAIXA"
    RANGE = "RANGE"
    FALSE_BREAKOUT = "FALSO_ROMPIMENTO"
    NONE = "NENHUM"
    UNKNOWN = "DESCONHECIDO"


@dataclass(slots=True)
class TechnicalObservation:
    readable: bool
    current_price: float | None

    ma20_slope: Slope
    price_vs_ma20: Position
    ma8_vs_ma20: Position

    market_situation: MarketSituation = MarketSituation.UNKNOWN
    impulse_direction: Slope = Slope.UNKNOWN
    impulse_start: float | None = None
    impulse_end: float | None = None
    impulse_points: float | None = None

    correction_identified: bool | None = None
    correction_start: float | None = None
    correction_end: float | None = None
    correction_percent: float | None = None
    correction_touched_ma8_m5: bool | None = None
    correction_touched_ma20_m5: bool | None = None
    correction_touched_ma20_m15: bool | None = None
    correction_touched_ma8_m60: bool | None = None
    correction_touched_ma20_m60: bool | None = None

    moving_average_wall: bool | None = None
    moving_average_wall_names: list[str] = field(default_factory=list)
    moving_average_wall_min: float | None = None
    moving_average_wall_max: float | None = None
    moving_average_wall_rejected: bool | None = None

    technical_pattern: Pattern = Pattern.UNKNOWN
    pattern_quality: str = "DESCONHECIDA"
    pullback_top: float | None = None
    pullback_bottom: float | None = None
    confirmation_level: float | None = None

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

    structural_entry: float | None = None
    structural_stop: float | None = None
    projection_100: float | None = None
    projection_1618: float | None = None
    main_barrier: float | None = None
    enough_space: bool | None = None

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
            market_situation=_enum_or_default(MarketSituation, payload.get("situacao_mercado"), MarketSituation.UNKNOWN),
            impulse_direction=_enum_or_default(Slope, payload.get("direcao_impulso"), Slope.UNKNOWN),
            impulse_start=_number_or_none(payload.get("impulso_inicio")),
            impulse_end=_number_or_none(payload.get("impulso_fim")),
            impulse_points=_number_or_none(payload.get("impulso_pontos")),
            correction_identified=_bool_or_none(payload.get("correcao_identificada")),
            correction_start=_number_or_none(payload.get("correcao_inicio")),
            correction_end=_number_or_none(payload.get("correcao_fim")),
            correction_percent=_number_or_none(payload.get("correcao_percentual")),
            correction_touched_ma8_m5=_bool_or_none(payload.get("correcao_tocou_ma8_m5")),
            correction_touched_ma20_m5=_bool_or_none(payload.get("correcao_tocou_ma20_m5")),
            correction_touched_ma20_m15=_bool_or_none(payload.get("correcao_tocou_ma20_m15")),
            correction_touched_ma8_m60=_bool_or_none(payload.get("correcao_tocou_ma8_m60")),
            correction_touched_ma20_m60=_bool_or_none(payload.get("correcao_tocou_ma20_m60")),
            moving_average_wall=_bool_or_none(payload.get("muralha_medias")),
            moving_average_wall_names=_string_list(payload.get("muralha_medias_nomes")),
            moving_average_wall_min=_number_or_none(payload.get("muralha_preco_min")),
            moving_average_wall_max=_number_or_none(payload.get("muralha_preco_max")),
            moving_average_wall_rejected=_bool_or_none(payload.get("muralha_rejeitada")),
            technical_pattern=_enum_or_default(Pattern, payload.get("padrao_tecnico"), Pattern.UNKNOWN),
            pattern_quality=str(payload.get("padrao_qualidade") or "DESCONHECIDA"),
            pullback_top=_number_or_none(payload.get("topo_pullback")),
            pullback_bottom=_number_or_none(payload.get("fundo_pullback")),
            confirmation_level=_number_or_none(payload.get("nivel_confirmacao")),
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
            structural_entry=_number_or_none(payload.get("entrada_estrutural")),
            structural_stop=_number_or_none(payload.get("stop_estrutural")),
            projection_100=_number_or_none(payload.get("projecao_100")),
            projection_1618=_number_or_none(payload.get("projecao_1618")),
            main_barrier=_number_or_none(payload.get("barreira_principal")),
            enough_space=_bool_or_none(payload.get("espaco_suficiente")),
            target1=_number_or_none(payload.get("alvo1_estrutural")),
            target2=_number_or_none(payload.get("alvo2_estrutural")),
            fib_context=str(payload.get("contexto_fibonacci") or "-"),
            notes=str(payload.get("notas") or "-"),
            moving_against_position=_bool_or_none(payload.get("movimento_contra_posicao")),
            visual_markers=_visual_markers(payload.get("marcacoes_visuais")),
        )


def evaluate_observation(o: TechnicalObservation) -> AnalysisResult:
    if not o.readable:
        return _no_setup(o, "LEITURA_INSUFICIENTE", "Nao foi possivel ler com seguranca a estrutura do grafico e as medias projetadas.")

    direction = _structural_direction(o)
    if direction is SignalDirection.NONE:
        return _no_setup(o, "SEM_PERNA_DIRECIONAL", "Nao ha uma perna estrutural clara para projetar continuacao.")

    if o.market_situation is MarketSituation.RANGE or o.in_consolidation is True:
        return _almost(o, direction, "RANGE", "Mercado em range. Aguardar uma nova perna e posterior correcao.", DecisionState.WAIT)

    if not _higher_timeframe_allows(o, direction):
        return _almost(o, direction, "CONTEXTO_MAIOR_NAO_CONFIRMA", "O contexto maior ainda nao oferece alinhamento ou espaco suficiente.", DecisionState.WAIT)

    if o.correction_identified is not True:
        return _almost(o, direction, "AGUARDAR_CORRECAO", "A perna existe, mas ainda falta uma correcao organizada antes de pensar em nova entrada.", DecisionState.PREPARE)

    if not _correction_reached_decision_zone(o):
        return _almost(o, direction, "CORRECAO_FORA_DA_ZONA", "A correcao ainda nao atingiu MA20_M5 ou uma muralha de medias relevante.", DecisionState.PREPARE)

    if o.moving_average_wall is True and o.moving_average_wall_rejected is not True:
        return _almost(o, direction, "MURALHA_SEM_REJEICAO", "O preco chegou a muralha de medias, mas ainda nao mostrou rejeicao/retomada.", DecisionState.ARM)

    if not _pattern_supports_direction(o, direction):
        return _almost(o, direction, "PADRAO_NAO_CONFIRMA", "A correcao ainda nao formou pivo, bandeira ou estrutura coerente com a retomada.", DecisionState.ARM)

    if o.resumption_after_pullback_m5 is not True:
        return _almost(o, direction, "AGUARDAR_RETOMADA", "A correcao esta montada, mas a retomada da perna principal ainda nao foi confirmada.", DecisionState.ARM)

    if o.candle_closed is not True:
        return _almost(o, direction, "CANDLE_GATILHO_ABERTO", "A confirmacao estrutural existe, mas o candle do rompimento ainda precisa fechar.", DecisionState.ARM)

    expected_breakout = Breakout.UP if direction is SignalDirection.BUY else Breakout.DOWN
    if o.breakout is not expected_breakout:
        return _almost(o, direction, "ROMPIMENTO_AUSENTE", "Ainda falta romper a microestrutura que confirma a retomada.", DecisionState.ARM)

    if o.enough_space is False:
        return _almost(o, direction, "ESPACO_INSUFICIENTE", "A projecao estrutural colide cedo demais com uma barreira maior.", DecisionState.WAIT)

    entry = o.structural_entry or o.confirmation_level or o.current_price
    stop = o.structural_stop or _fallback_stop(o, direction)
    target1 = o.projection_100 or o.target1
    target2 = o.projection_1618 or o.target2

    if entry is None or stop is None or target1 is None:
        return _almost(o, direction, "PLANO_INCOMPLETO", "A estrutura foi reconhecida, mas ainda falta entrada, stop ou projecao de alvo confiavel.", DecisionState.ARM)

    confidence = Confidence.HIGH if o.setup_mode is SetupMode.TREND else Confidence.MEDIUM
    return AnalysisResult(
        scenario_type=ScenarioType.ENTRY,
        signal=direction,
        confidence=confidence,
        current_price=o.current_price,
        bias_m60=_bias_text(o, direction),
        structure_m15=_m15_text(o),
        fib_zone_m5=_structure_text(o),
        suggested_entry=entry,
        suggested_stop=stop,
        suggested_target1=target1,
        suggested_target2=target2,
        rationale=_rationale(o, direction, entry, stop, target1, target2),
        decision_state=DecisionState.ENTER,
        visual_markers=o.visual_markers,
    )


def should_defensive_exit(o: TechnicalObservation, position: SignalDirection) -> bool:
    if position is SignalDirection.BUY:
        return o.price_vs_ma20_m5 is Position.BELOW or (o.moving_against_position is True and o.ma8_cross is Cross.DOWN)
    if position is SignalDirection.SELL:
        return o.price_vs_ma20_m5 is Position.ABOVE or (o.moving_against_position is True and o.ma8_cross is Cross.UP)
    return False


def _structural_direction(o: TechnicalObservation) -> SignalDirection:
    if o.impulse_direction is Slope.UP:
        return SignalDirection.BUY
    if o.impulse_direction is Slope.DOWN:
        return SignalDirection.SELL
    return SignalDirection.NONE


def _correction_reached_decision_zone(o: TechnicalObservation) -> bool:
    return any(
        value is True
        for value in (
            o.correction_touched_ma20_m5,
            o.correction_touched_ma20_m15,
            o.correction_touched_ma8_m60,
            o.correction_touched_ma20_m60,
            o.moving_average_wall,
        )
    )


def _pattern_supports_direction(o: TechnicalObservation, direction: SignalDirection) -> bool:
    if direction is SignalDirection.BUY:
        return o.technical_pattern in {
            Pattern.PIVOT_UP,
            Pattern.FLAG_UP,
            Pattern.CHANNEL_UP,
            Pattern.TRIANGLE,
        }
    if direction is SignalDirection.SELL:
        return o.technical_pattern in {
            Pattern.PIVOT_DOWN,
            Pattern.FLAG_DOWN,
            Pattern.CHANNEL_DOWN,
            Pattern.TRIANGLE,
        }
    return False


def _higher_timeframe_allows(o: TechnicalObservation, direction: SignalDirection) -> bool:
    if o.setup_mode is SetupMode.TREND:
        if direction is SignalDirection.BUY:
            return o.ma20_slope is Slope.UP and o.context_m15 is Slope.UP
        return o.ma20_slope is Slope.DOWN and o.context_m15 is Slope.DOWN

    if o.setup_mode is SetupMode.RECOVERY:
        if o.closed_beyond_ma8_m60 is not True:
            return False
        if o.distance_to_ma20_m60_points is None or o.distance_to_ma20_m60_points < 400:
            return False
        if direction is SignalDirection.BUY:
            return o.context_m15 is Slope.UP
        return o.context_m15 is Slope.DOWN

    return False


def _fallback_stop(o: TechnicalObservation, direction: SignalDirection) -> float | None:
    if direction is SignalDirection.BUY:
        return o.pullback_bottom or o.relevant_bottom
    return o.pullback_top or o.relevant_top


def _no_setup(o: TechnicalObservation, code: str, reason: str) -> AnalysisResult:
    return AnalysisResult(
        scenario_type=ScenarioType.NO_SETUP,
        signal=SignalDirection.NONE,
        confidence=Confidence.LOW,
        current_price=o.current_price,
        bias_m60=_bias_text(o, SignalDirection.NONE),
        structure_m15=_m15_text(o),
        fib_zone_m5=_structure_text(o),
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
        fib_zone_m5=_structure_text(o),
        missing_confirmation_code=code,
        missing_confirmation=reason,
        rationale=reason,
        decision_state=state,
        visual_markers=o.visual_markers,
    )


def _bias_text(o: TechnicalObservation, direction: SignalDirection) -> str:
    return (
        f"Modo={o.setup_mode.value}; direcao={direction.value}; MA20_M60={o.ma20_slope.value}; "
        f"preco_vs_MA20_M60={o.price_vs_ma20.value}; distancia_MA20_M60={o.distance_to_ma20_m60_points}."
    )


def _m15_text(o: TechnicalObservation) -> str:
    return (
        f"contexto={o.context_m15.value}; MA20_M15={o.ma20_slope_m15.value}; "
        f"preco_vs_MA20_M15={o.price_vs_ma20_m15.value}."
    )


def _structure_text(o: TechnicalObservation) -> str:
    wall = ",".join(o.moving_average_wall_names) if o.moving_average_wall_names else "-"
    return (
        f"situacao={o.market_situation.value}; impulso={o.impulse_direction.value}/{o.impulse_points}; "
        f"correcao={o.correction_percent}%; muralha={wall}; rejeitada={o.moving_average_wall_rejected}; "
        f"padrao={o.technical_pattern.value}; retomada={o.resumption_after_pullback_m5}; "
        f"confirmacao={o.confirmation_level}; proj100={o.projection_100}; proj161.8={o.projection_1618}."
    )


def _rationale(
    o: TechnicalObservation,
    direction: SignalDirection,
    entry: float,
    stop: float,
    target1: float,
    target2: float | None,
) -> str:
    wall = ", ".join(o.moving_average_wall_names) if o.moving_average_wall_names else "medias relevantes"
    return (
        f"{direction.value} estrutural em modo {o.setup_mode.value}: perna principal de "
        f"{o.impulse_points} pontos, correcao de aproximadamente {o.correction_percent}% ate {wall}, "
        f"padrao {o.technical_pattern.value} e retomada confirmada. Entrada {entry}; stop tecnico {stop}; "
        f"projecao 100% {target1}; projecao 161.8% {target2}."
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


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


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
