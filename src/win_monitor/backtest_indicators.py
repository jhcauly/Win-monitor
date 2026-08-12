from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from win_monitor.backtest_data import Candle


class MovingAverageKind(StrEnum):
    SIMPLE = "SMA"
    EXPONENTIAL = "EMA"


class PivotKind(StrEnum):
    HIGH = "TOPO"
    LOW = "FUNDO"


@dataclass(frozen=True, slots=True)
class ConfirmedPivot:
    kind: PivotKind
    pivot_index: int
    confirmed_at_index: int
    price: float


def moving_average(
    values: list[float],
    period: int,
    kind: MovingAverageKind,
) -> list[float | None]:
    if period <= 0:
        raise ValueError("Periodo da media deve ser positivo")
    if kind is MovingAverageKind.SIMPLE:
        return _sma(values, period)
    if kind is MovingAverageKind.EXPONENTIAL:
        return _ema(values, period)
    raise ValueError(f"Tipo de media nao suportado: {kind}")


def moving_average_slope(
    averages: list[float | None],
    lookback: int = 1,
) -> list[float | None]:
    if lookback <= 0:
        raise ValueError("Lookback deve ser positivo")
    result: list[float | None] = [None] * len(averages)
    for index in range(lookback, len(averages)):
        current = averages[index]
        previous = averages[index - lookback]
        if current is not None and previous is not None:
            result[index] = current - previous
    return result


def confirmed_pivots(
    candles: list[Candle],
    *,
    left: int = 2,
    right: int = 2,
) -> list[ConfirmedPivot]:
    if left <= 0 or right <= 0:
        raise ValueError("left e right devem ser positivos")
    if len(candles) < left + right + 1:
        return []

    pivots: list[ConfirmedPivot] = []
    for index in range(left, len(candles) - right):
        current = candles[index]
        neighbors = candles[index - left : index] + candles[index + 1 : index + right + 1]
        if all(current.high > item.high for item in neighbors):
            pivots.append(
                ConfirmedPivot(
                    kind=PivotKind.HIGH,
                    pivot_index=index,
                    confirmed_at_index=index + right,
                    price=current.high,
                )
            )
        if all(current.low < item.low for item in neighbors):
            pivots.append(
                ConfirmedPivot(
                    kind=PivotKind.LOW,
                    pivot_index=index,
                    confirmed_at_index=index + right,
                    price=current.low,
                )
            )
    return pivots


def pivot_state_by_index(
    candles: list[Candle],
    *,
    left: int = 2,
    right: int = 2,
) -> list[tuple[float | None, float | None]]:
    pivots = confirmed_pivots(candles, left=left, right=right)
    by_confirmation: dict[int, list[ConfirmedPivot]] = {}
    for pivot in pivots:
        by_confirmation.setdefault(pivot.confirmed_at_index, []).append(pivot)

    latest_high: float | None = None
    latest_low: float | None = None
    result: list[tuple[float | None, float | None]] = []
    for index in range(len(candles)):
        for pivot in by_confirmation.get(index, []):
            if pivot.kind is PivotKind.HIGH:
                latest_high = pivot.price
            else:
                latest_low = pivot.price
        result.append((latest_high, latest_low))
    return result


def _sma(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    running = 0.0
    for index, value in enumerate(values):
        running += value
        if index >= period:
            running -= values[index - period]
        if index >= period - 1:
            result[index] = running / period
    return result


def _ema(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result

    seed = sum(values[:period]) / period
    result[period - 1] = seed
    alpha = 2.0 / (period + 1)
    previous = seed
    for index in range(period, len(values)):
        previous = values[index] * alpha + previous * (1 - alpha)
        result[index] = previous
    return result
