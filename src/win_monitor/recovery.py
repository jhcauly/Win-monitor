from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from win_monitor.models import SignalDirection


class TradeMode(StrEnum):
    TREND = "TREND"
    RECOVERY = "RECOVERY"
    NO_TRADE = "NO_TRADE"


@dataclass(slots=True)
class RecoverySetup:
    direction: SignalDirection
    price: float
    ma8_m60: float
    ma20_m60: float
    m60_closed_beyond_ma8: bool
    m15_confirmed: bool
    m5_pivot_low: float | None
    m5_pivot_high: float | None
    m5_pullback_price: float | None
    m5_ma20: float | None
    m5_resumption_confirmed: bool
    stop_price: float | None
    projection_target: float | None = None


@dataclass(slots=True)
class RecoveryDecision:
    mode: TradeMode
    allowed: bool
    direction: SignalDirection
    available_space_points: float
    pivot_projection_points: float | None
    risk_points: float | None
    rr: float | None
    reason: str


def evaluate_recovery(
    setup: RecoverySetup,
    *,
    minimum_available_space_points: float = 400.0,
    minimum_rr: float = 1.5,
    ma20_touch_tolerance_points: float = 80.0,
) -> RecoveryDecision:
    """Avalia uma operacao de recuperacao contra a tendencia principal do M60.

    A MM20/M60 deixa de ser um bloqueio absoluto e passa a funcionar como
    barreira/espaco disponivel. A operacao so e permitida depois de:
    - fechamento do M60 alem da MM8 na direcao da recuperacao;
    - confirmacao do M15;
    - pivô M5 identificado;
    - correcao do M5 ate proximo da MM20/M5;
    - retomada/rompimento do topo (compra) ou fundo (venda) do pivô;
    - espaco e risco/retorno minimos.
    """
    direction = setup.direction
    if direction not in {SignalDirection.BUY, SignalDirection.SELL}:
        return _blocked(direction, "DIRECAO_INVALIDA")

    if not setup.m60_closed_beyond_ma8:
        return _blocked(direction, "M60_NAO_FECHOU_ALEM_DA_MA8")

    if not setup.m15_confirmed:
        return _blocked(direction, "M15_NAO_CONFIRMOU")

    if setup.m5_pivot_low is None or setup.m5_pivot_high is None:
        return _blocked(direction, "PIVO_M5_INCOMPLETO")

    if setup.m5_pullback_price is None or setup.m5_ma20 is None:
        return _blocked(direction, "PULLBACK_M5_NAO_MEDIDO")

    if abs(setup.m5_pullback_price - setup.m5_ma20) > ma20_touch_tolerance_points:
        return _blocked(direction, "PULLBACK_LONGE_DA_MA20_M5")

    if not setup.m5_resumption_confirmed:
        return _blocked(direction, "RETOMADA_M5_NAO_CONFIRMADA")

    available_space = _available_space(setup)
    if available_space < minimum_available_space_points:
        return RecoveryDecision(
            mode=TradeMode.NO_TRADE,
            allowed=False,
            direction=direction,
            available_space_points=available_space,
            pivot_projection_points=_pivot_projection_points(setup),
            risk_points=_risk_points(setup),
            rr=_rr(setup),
            reason="ESPACO_INSUFICIENTE_ATE_MA20_M60",
        )

    risk = _risk_points(setup)
    projection = _pivot_projection_points(setup)
    rr = _rr(setup)
    if risk is None or projection is None or rr is None:
        return RecoveryDecision(
            mode=TradeMode.NO_TRADE,
            allowed=False,
            direction=direction,
            available_space_points=available_space,
            pivot_projection_points=projection,
            risk_points=risk,
            rr=rr,
            reason="PLANO_INCOMPLETO",
        )

    if rr < minimum_rr:
        return RecoveryDecision(
            mode=TradeMode.NO_TRADE,
            allowed=False,
            direction=direction,
            available_space_points=available_space,
            pivot_projection_points=projection,
            risk_points=risk,
            rr=rr,
            reason="RR_INSUFICIENTE",
        )

    return RecoveryDecision(
        mode=TradeMode.RECOVERY,
        allowed=True,
        direction=direction,
        available_space_points=available_space,
        pivot_projection_points=projection,
        risk_points=risk,
        rr=rr,
        reason="RECOVERY_CONFIRMADO",
    )


def _available_space(setup: RecoverySetup) -> float:
    if setup.direction is SignalDirection.BUY:
        return max(0.0, setup.ma20_m60 - setup.price)
    return max(0.0, setup.price - setup.ma20_m60)


def _pivot_projection_points(setup: RecoverySetup) -> float | None:
    if setup.m5_pivot_low is None or setup.m5_pivot_high is None:
        return None
    amplitude = abs(setup.m5_pivot_high - setup.m5_pivot_low)
    if amplitude <= 0:
        return None
    return amplitude


def _risk_points(setup: RecoverySetup) -> float | None:
    if setup.stop_price is None:
        return None
    risk = abs(setup.price - setup.stop_price)
    return risk if risk > 0 else None


def _rr(setup: RecoverySetup) -> float | None:
    risk = _risk_points(setup)
    target = setup.projection_target
    if risk is None or target is None:
        return None

    if setup.direction is SignalDirection.BUY:
        reward = target - setup.price
    else:
        reward = setup.price - target

    if reward <= 0:
        return None
    return reward / risk


def _blocked(direction: SignalDirection, reason: str) -> RecoveryDecision:
    return RecoveryDecision(
        mode=TradeMode.NO_TRADE,
        allowed=False,
        direction=direction,
        available_space_points=0.0,
        pivot_projection_points=None,
        risk_points=None,
        rr=None,
        reason=reason,
    )
