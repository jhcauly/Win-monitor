from win_monitor.backtest_metrics import BacktestTrade, calculate_metrics


def test_backtest_metrics() -> None:
    metrics = calculate_metrics(
        [
            BacktestTrade(100, mae_points=40, mfe_points=120),
            BacktestTrade(-50, mae_points=60, mfe_points=20),
            BacktestTrade(150, mae_points=30, mfe_points=180),
            BacktestTrade(-100, mae_points=110, mfe_points=10),
        ]
    )
    assert metrics.trades == 4
    assert metrics.wins == 2
    assert metrics.losses == 2
    assert metrics.win_rate == 0.5
    assert metrics.net_points == 100
    assert metrics.expectancy_points == 25
    assert metrics.payoff == 125 / 75
    assert metrics.profit_factor == 250 / 150
    assert metrics.max_drawdown_points == 100
    assert metrics.average_mae_points == 60
    assert metrics.average_mfe_points == 82.5
