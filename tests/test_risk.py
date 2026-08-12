from win_monitor.models import AnalysisResult, Confidence, ScenarioType, SignalDirection
from win_monitor.risk import calculate_trade_risk


def make_entry() -> AnalysisResult:
    return AnalysisResult(scenario_type=ScenarioType.ENTRY, signal=SignalDirection.BUY, confidence=Confidence.HIGH, suggested_entry=130000, suggested_stop=129700, suggested_target1=130300)


def test_risk_for_five_contracts() -> None:
    risk = calculate_trade_risk(make_entry(), max_contracts=5)
    assert risk is not None
    assert risk.risk_points == 300
    assert risk.risk_per_contract_brl == 60
    assert risk.risk_five_contracts_brl == 300
    assert risk.recommended_contracts == 5


def test_position_size_respects_financial_limit() -> None:
    risk = calculate_trade_risk(make_entry(), max_contracts=5, max_risk_brl=200)
    assert risk is not None
    assert risk.recommended_contracts == 3
    assert risk.recommended_risk_brl == 180
