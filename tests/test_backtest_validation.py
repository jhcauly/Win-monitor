from datetime import datetime, timedelta

from win_monitor.backtest_data import Candle
from win_monitor.backtest_validation import chronological_split


def test_chronological_split_preserves_time_order() -> None:
    start = datetime(2026, 8, 12, 9, 0)
    candles = [
        Candle(
            timestamp=start + timedelta(minutes=index * 5),
            open=100 + index,
            high=101 + index,
            low=99 + index,
            close=100 + index,
        )
        for index in range(10)
    ]
    split = chronological_split(candles)
    assert len(split.train) == 6
    assert len(split.validation) == 2
    assert len(split.test) == 2
    assert split.train[-1].timestamp < split.validation[0].timestamp
    assert split.validation[-1].timestamp < split.test[0].timestamp
