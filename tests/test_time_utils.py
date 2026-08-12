from datetime import datetime

from win_monitor.time_utils import next_candle_close, within_trading_hours


def test_next_candle_close_is_future_boundary() -> None:
    now = datetime(2026, 8, 12, 10, 7, 35)
    assert next_candle_close(now, 5) == datetime(2026, 8, 12, 10, 10, 2)


def test_exact_boundary_moves_to_next_candle() -> None:
    now = datetime(2026, 8, 12, 10, 10, 0)
    assert next_candle_close(now, 5) == datetime(2026, 8, 12, 10, 15, 2)


def test_trading_hours() -> None:
    assert within_trading_hours(datetime(2026, 8, 12, 12, 0), "09:05", "17:25")
    assert not within_trading_hours(datetime(2026, 8, 12, 18, 0), "09:05", "17:25")
