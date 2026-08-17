from win_monitor.models import SignalDirection
from win_monitor.recovery import RecoverySetup, TradeMode, evaluate_recovery


def test_buy_recovery_is_allowed_with_space_pullback_and_confirmation():
    setup = RecoverySetup(
        direction=SignalDirection.BUY,
        price=168800,
        ma8_m60=168600,
        ma20_m60=169730,
        m60_closed_beyond_ma8=True,
        m15_confirmed=True,
        m5_pivot_low=168100,
        m5_pivot_high=168800,
        m5_pullback_price=168420,
        m5_ma20=168400,
        m5_resumption_confirmed=True,
        stop_price=168350,
        projection_target=169500,
    )

    decision = evaluate_recovery(setup)

    assert decision.allowed is True
    assert decision.mode is TradeMode.RECOVERY
    assert decision.available_space_points > 400
    assert decision.rr is not None and decision.rr >= 1.5


def test_recovery_is_blocked_when_m60_has_not_closed_beyond_ma8():
    setup = RecoverySetup(
        direction=SignalDirection.BUY,
        price=168.80,
        ma8_m60=168.90,
        ma20_m60=169.73,
        m60_closed_beyond_ma8=False,
        m15_confirmed=True,
        m5_pivot_low=168.10,
        m5_pivot_high=168.80,
        m5_pullback_price=168.42,
        m5_ma20=168.40,
        m5_resumption_confirmed=True,
        stop_price=168.35,
        projection_target=169.50,
    )

    decision = evaluate_recovery(setup)

    assert decision.allowed is False
    assert decision.reason == "M60_NAO_FECHOU_ALEM_DA_MA8"


def test_recovery_is_blocked_without_m15_confirmation():
    setup = RecoverySetup(
        direction=SignalDirection.BUY,
        price=168.80,
        ma8_m60=168.60,
        ma20_m60=169.73,
        m60_closed_beyond_ma8=True,
        m15_confirmed=False,
        m5_pivot_low=168.10,
        m5_pivot_high=168.80,
        m5_pullback_price=168.42,
        m5_ma20=168.40,
        m5_resumption_confirmed=True,
        stop_price=168.35,
        projection_target=169.50,
    )

    decision = evaluate_recovery(setup)

    assert decision.allowed is False
    assert decision.reason == "M15_NAO_CONFIRMOU"
