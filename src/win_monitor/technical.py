from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from win_monitor.models import AnalysisResult, Confidence, ScenarioType, SignalDirection


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


def evaluate_observation(observation: TechnicalObservation) -> AnalysisResult:
    if not observation.readable:
        return _no_setup(
            observation,
            "LEITURA_INSUFICIENTE",
            "Nao foi possivel ler com seguranca os elementos obrigatorios.",
        )

    direction = _trend_direction(observation)
    if direction is SignalDirection.NONE:
        return _no_setup(
            observation,
            "M60_FRACO",
            "A inclinacao da MA20 e a posicao do preco/MA8 nao confirmam tendencia.",
        )

    if observation.in_consolidation is True:
        return _almost(
            observation,
            direction,
            "RANGE",
            "Consolidacao detectada; rompimentos dentro da faixa ficam bloqueados.",
        )

    if observation.swing_confirmed is not True:
        return _almost(
            observation,
            direction,
            "PIVO_NAO_CONFIRMADO",
            "O topo/fundo relevante ainda nao esta confirmado sem olhar candles futuros.",
        )

    if observation.candle_closed is not True:
        return _almost(
            observation,
            direction,
            "CANDLE_NAO_FECHADO",
            "O gatilho so vale depois do fechamento do candle.",
        )

    expected_slope = Slope.UP if direction is SignalDirection.BUY else Slope.DOWN
    if observation.ma8_slope is not expected_slope:
        return _almost(
            observation,
            direction,
            "MA8_SEM_INCLINACAO",
            "A MA8 ainda nao acompanha a direcao da tendencia principal.",
        )

    expected_breakout = (
        Breakout.UP if direction is SignalDirection.BUY else Breakout.DOWN
    )
    if observation.breakout is not expected_breakout:
        return _almost(
            observation,
            direction,
            "ROMPIMENTO_AUSENTE",
            "O topo/fundo tecnico relevante ainda nao foi rompido na direcao esperada.",
        )

    stop = (
        observation.relevant_bottom
        if direction is SignalDirection.BUY
        else observation.relevant_top
    )
    if observation.current_price is None or stop is None or observation.target1 is None:
        return _almost(
            observation,
            direction,
            "PLANO_INCOMPLETO",
            "Falta preco, stop tecnico ou alvo estrutural para montar o plano completo.",
        )

    return AnalysisResult(
        scenario_type=ScenarioType.ENTRY,
        signal=direction,
        confidence=Confidence.HIGH,
        current_price=observation.current_price,
        bias_m60=_bias_text(observation, direction),
        structure_m15=_structure_text(observation),
        fib_zone_m5=observation.fib_context,
        suggested_entry=observation.current_price,
        suggested_stop=stop,
        suggested_target1=observation.target1,
        suggested_target2=observation.target2,
        rationale=(
            "MA20 confirma a tendencia, MA8 acompanha e houve rompimento confirmado "
            "do nivel tecnico relevante com candle fechado."
        ),
    )


def should_defensive_exit(
    observation: TechnicalObservation,
    position: SignalDirection,
) -> bool:
    if position is SignalDirection.BUY:
        if observation.price_vs_ma20 is Position.BELOW:
            return True
        return (
            observation.moving_against_position is True
            and observation.ma8_cross is Cross.DOWN
        )

    if position is SignalDirection.SELL:
        if observation.price_vs_ma20 is Position.ABOVE:
            return True
        return (
            observation.moving_against_position is True
            and observation.ma8_cross is Cross.UP
        )

    return False


def _trend_direction(observation: TechnicalObservation) -> SignalDirection:
    buy_positions = {Position.ABOVE, Position.TOUCHING}
    sell_positions = {Position.BELOW, Position.TOUCHING}

    if (
        observation.ma20_slope is Slope.UP
        and observation.price_vs_ma20 in buy_positions
        and observation.ma8_vs_ma20 in buy_positions
    ):
        return SignalDirection.BUY

    if (
        observation.ma20_slope is Slope.DOWN
        and observation.price_vs_ma20 in sell_positions
        and observation.ma8_vs_ma20 in sell_positions
    ):
        return SignalDirection.SELL

    return SignalDirection.NONE


def _no_setup(
    observation: TechnicalObservation,
    code: str,
    reason: str,
) -> AnalysisResult:
    return AnalysisResult(
        scenario_type=ScenarioType.NO_SETUP,
        signal=SignalDirection.NONE,
        confidence=Confidence.LOW,
        current_price=observation.current_price,
        bias_m60="Sem vies confirmado",
        structure_m15=_structure_text(observation),
        fib_zone_m5=observation.fib_context,
        missing_confirmation_code=code,
        missing_confirmation=reason,
        rationale=reason,
    )


def _almost(
    observation: TechnicalObservation,
    direction: SignalDirection,
    code: str,
    reason: str,
) -> AnalysisResult:
    return AnalysisResult(
        scenario_type=ScenarioType.ALMOST,
        signal=direction,
        confidence=Confidence.MEDIUM,
        current_price=observation.current_price,
        bias_m60=_bias_text(observation, direction),
        structure_m15=_structure_text(observation),
        fib_zone_m5=observation.fib_context,
        missing_confirmation_code=code,
        missing_confirmation=reason,
        rationale=reason,
    )


def _bias_text(
    observation: TechnicalObservation,
    direction: SignalDirection,
) -> str:
    return (
        f"{direction.value}: MA20 {observation.ma20_slope.value}; "
        f"preco {observation.price_vs_ma20.value}; "
        f"MA8 {observation.ma8_vs_ma20.value}."
    )


def _structure_text(observation: TechnicalObservation) -> str:
    return (
        f"Topo={observation.relevant_top}; fundo={observation.relevant_bottom}; "
        f"rompimento={observation.breakout.value}; "
        f"consolidacao={observation.in_consolidation}."
    )
