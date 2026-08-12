from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BacktestTrade:
    result_points: float
    mae_points: float | None = None
    mfe_points: float | None = None


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_points: float
    expectancy_points: float
    average_win_points: float
    average_loss_points: float
    payoff: float | None
    profit_factor: float | None
    max_drawdown_points: float
    average_mae_points: float | None
    average_mfe_points: float | None


def calculate_metrics(trades: list[BacktestTrade]) -> BacktestMetrics:
    if not trades:
        return BacktestMetrics(
            trades=0,
            wins=0,
            losses=0,
            win_rate=0.0,
            net_points=0.0,
            expectancy_points=0.0,
            average_win_points=0.0,
            average_loss_points=0.0,
            payoff=None,
            profit_factor=None,
            max_drawdown_points=0.0,
            average_mae_points=None,
            average_mfe_points=None,
        )

    wins = [trade.result_points for trade in trades if trade.result_points > 0]
    losses = [trade.result_points for trade in trades if trade.result_points < 0]
    net = sum(trade.result_points for trade in trades)
    average_win = sum(wins) / len(wins) if wins else 0.0
    average_loss = abs(sum(losses) / len(losses)) if losses else 0.0
    payoff = average_win / average_loss if average_loss > 0 else None
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in trades:
        equity += trade.result_points
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)

    mae_values = [trade.mae_points for trade in trades if trade.mae_points is not None]
    mfe_values = [trade.mfe_points for trade in trades if trade.mfe_points is not None]
    average_mae = math.fsum(mae_values) / len(mae_values) if mae_values else None
    average_mfe = math.fsum(mfe_values) / len(mfe_values) if mfe_values else None

    return BacktestMetrics(
        trades=len(trades),
        wins=len(wins),
        losses=len(losses),
        win_rate=len(wins) / len(trades),
        net_points=net,
        expectancy_points=net / len(trades),
        average_win_points=average_win,
        average_loss_points=average_loss,
        payoff=payoff,
        profit_factor=profit_factor,
        max_drawdown_points=max_drawdown,
        average_mae_points=average_mae,
        average_mfe_points=average_mfe,
    )
