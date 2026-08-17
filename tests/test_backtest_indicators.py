from datetime import datetime, timedelta

from win_monitor.backtest_data import Candle
from win_monitor.backtest_indicators import (
    MovingAverageKind,
    PivotKind,
    confirmed_pivots,
    moving_average,
    pivot_state_by_index,
)


def make_candles(highs: list[float], lows: list[float]) -> list[Candle]:
    start = datetime(2026, 8, 12, 9, 0)
    return [
        Candle(
            timestamp=start + timedelta(minutes=index * 5),
            open=(high + low) / 2,
            high=high,
            low=low,
            close=(high + low) / 2,
        )
        for index, (high, low) in enumerate(zip(highs, lows, strict=True))
    ]


def test_sma_and_ema_are_explicit_options() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    sma = moving_average(values, 3, MovingAverageKind.SIMPLE)
    ema = moving_average(values, 3, MovingAverageKind.EXPONENTIAL)
    assert sma == [None, None, 2.0, 3.0]
    assert ema == [None, None, 2.0, 3.0]


def test_pivot_is_available_only_after_confirmation_candles() -> None:
    candles = make_candles(
        [10, 11, 15, 12, 11, 13],
        [8, 9, 10, 9, 8, 10],
    )
    pivots = confirmed_pivots(candles, left=2, right=2)
    high = next(pivot for pivot in pivots if pivot.kind is PivotKind.HIGH)
    assert high.pivot_index == 2
    assert high.confirmed_at_index == 4

    states = pivot_state_by_index(candles, left=2, right=2)
    assert states[3][0] is None
    assert states[4][0] == 15
