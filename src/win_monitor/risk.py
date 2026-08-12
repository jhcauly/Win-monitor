from __future__ import annotations

import math

from win_monitor.models import AnalysisResult, ScenarioType, SignalDirection, TradeRisk

WIN_POINT_VALUE_BRL = 0.20
WIN_TICK_POINTS = 5
DEFAULT_MIN_RR = 1.0


def calculate_trade_risk(
    analysis: AnalysisResult,
    *,
    max_contracts: int = 5,
    max_risk_brl: float | None = None,
) -> TradeRisk | None:
    if analysis.scenario_type is not ScenarioType.ENTRY:
        return None
    if analysis.suggested_entry is None or analysis.suggested_stop is None:
        return None

    risk_points = abs(analysis.suggested_entry - analysis.suggested_stop)
    if risk_points <= 0:
        return None

    risk_per_contract = risk_points * WIN_POINT_VALUE_BRL
    recommended = max_contracts
    if max_risk_brl is not None:
        recommended = min(
            max_contracts,
            math.floor(max_risk_brl / risk_per_contract),
        )
    recommended = max(0, recommended)
    return TradeRisk(
        risk_points=risk_points,
        risk_per_contract_brl=risk_per_contract,
        risk_five_contracts_brl=risk_per_contract * 5,
        recommended_contracts=recommended,
        recommended_risk_brl=risk_per_contract * recommended,
    )


def risk_reward_ratio(analysis: AnalysisResult) -> float | None:
    entry = analysis.suggested_entry
    stop = analysis.suggested_stop
    target = analysis.suggested_target1
    if entry is None or stop is None or target is None:
        return None

    if analysis.signal is SignalDirection.BUY:
        risk_points = entry - stop
        reward_points = target - entry
    elif analysis.signal is SignalDirection.SELL:
        risk_points = stop - entry
        reward_points = entry - target
    else:
        return None

    if risk_points <= 0 or reward_points <= 0:
        return None
    return reward_points / risk_points


def enforce_minimum_rr(
    analysis: AnalysisResult,
    minimum: float = DEFAULT_MIN_RR,
) -> float | None:
    if analysis.scenario_type is not ScenarioType.ENTRY:
        return None

    rr = risk_reward_ratio(analysis)
    if rr is not None and rr >= minimum:
        return rr

    analysis.scenario_type = ScenarioType.ALMOST
    analysis.missing_confirmation_code = "RR_INSUFICIENTE"
    if rr is None:
        analysis.missing_confirmation = (
            "Nao foi possivel validar risco/retorno positivo com entrada, stop e alvo."
        )
    else:
        analysis.missing_confirmation = (
            f"Risco/retorno {rr:.2f}:1 abaixo do piso tecnico {minimum:.2f}:1."
        )
    analysis.rationale = (
        f"{analysis.rationale} Entrada bloqueada pela validacao de risco/retorno."
    )
    return rr
