from pathlib import Path

from win_monitor.backtest_data import (
    load_profit_intraday_csv,
    resample_candles,
    summarize_candles,
)


def test_load_profit_intraday_layout(tmp_path: Path) -> None:
    path = tmp_path / "win.csv"
    path.write_text(
        "Ativo;Data;Tempo;Numero de Negocios;Fechamento;Minima;Maxima;Abertura;Volume;Quantidade\n"
        "WINQ26;12/08/2026;09:00;100;128.450;128.300;128.500;128.350;1000000;5000\n"
        "WINQ26;12/08/2026;09:05;120;128.600;128.400;128.650;128.450;1200000;6000\n",
        encoding="utf-8",
    )
    candles = load_profit_intraday_csv(path)
    assert len(candles) == 2
    assert candles[0].open == 128350
    assert candles[1].close == 128600
    assert summarize_candles(candles).symbol == "WINQ26"


def test_resample_5m_to_15m(tmp_path: Path) -> None:
    path = tmp_path / "win.csv"
    path.write_text(
        "Ativo;Data;Tempo;Fechamento;Minima;Maxima;Abertura\n"
        "WINQ26;12/08/2026;09:00;128400;128300;128450;128350\n"
        "WINQ26;12/08/2026;09:05;128500;128350;128550;128400\n"
        "WINQ26;12/08/2026;09:10;128600;128450;128650;128500\n",
        encoding="utf-8",
    )
    candles = load_profit_intraday_csv(path)
    result = resample_candles(candles, 15)
    assert len(result) == 1
    assert result[0].open == 128350
    assert result[0].high == 128650
    assert result[0].low == 128300
    assert result[0].close == 128600
