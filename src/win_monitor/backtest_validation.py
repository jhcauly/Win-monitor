from __future__ import annotations

from dataclasses import dataclass

from win_monitor.backtest_data import Candle


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    train: list[Candle]
    validation: list[Candle]
    test: list[Candle]


def chronological_split(
    candles: list[Candle],
    *,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    test_fraction: float = 0.20,
) -> DatasetSplit:
    total_fraction = train_fraction + validation_fraction + test_fraction
    if abs(total_fraction - 1.0) > 1e-9:
        raise ValueError("Fracoes de treino/validacao/teste devem somar 1")
    if min(train_fraction, validation_fraction, test_fraction) <= 0:
        raise ValueError("Todas as fracoes devem ser positivas")
    if len(candles) < 3:
        raise ValueError("Serie precisa de pelo menos 3 candles")

    ordered = sorted(candles, key=lambda item: item.timestamp)
    train_end = max(1, int(len(ordered) * train_fraction))
    validation_size = max(1, int(len(ordered) * validation_fraction))
    validation_end = min(len(ordered) - 1, train_end + validation_size)
    if validation_end <= train_end:
        validation_end = train_end + 1
    if validation_end >= len(ordered):
        validation_end = len(ordered) - 1

    return DatasetSplit(
        train=ordered[:train_end],
        validation=ordered[train_end:validation_end],
        test=ordered[validation_end:],
    )
