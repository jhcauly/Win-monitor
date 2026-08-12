from __future__ import annotations

import math

from win_monitor.models import AnalysisResult, ScenarioType, TradeRisk

WIN_POINT_VALUE_BRL = 0.20
WIN_TICK_POINTS = 5


def calculate_trade_risk(analysis: AnalysisResult, *, max_contracts: int = 5, max_risk_brl: float | None = None) -> TradeRisk | None:
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
        recommended = min(max_contracts, math.floor(max_risk_brl / risk_per_contract))
    recommended = max(0, recommended)
    return TradeRisk(risk_points=risk_points, risk_per_contract_brl=risk_per_contract, risk_five_contracts_brl=risk_per_contract * 5, recommended_contracts=recommended, recommended_risk_brl=risk_per_contract * recommended)
