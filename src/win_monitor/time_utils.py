from __future__ import annotations

from datetime import datetime, timedelta


def within_trading_hours(now: datetime, start: str, end: str) -> bool:
    current = now.strftime("%H:%M")
    return start <= current <= end


def next_candle_close(now: datetime, interval_minutes: int, offset_seconds: int = 2) -> datetime:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes deve ser maior que zero")
    remainder = now.minute % interval_minutes
    minutes = interval_minutes - remainder if remainder else interval_minutes
    return (now + timedelta(minutes=minutes)).replace(second=offset_seconds, microsecond=0)
