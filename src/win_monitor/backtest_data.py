from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    trades: int | None = None
    quantity: float | None = None
    symbol: str | None = None


@dataclass(frozen=True, slots=True)
class CandleSeriesSummary:
    candles: int
    start: datetime
    end: datetime
    symbol: str | None


_COLUMN_ALIASES = {
    "symbol": {"ativo", "ticker", "symbol"},
    "date": {"data", "date"},
    "time": {"tempo", "hora", "time"},
    "trades": {"numero_de_negocios", "negocios", "trades"},
    "close": {"fechamento", "close"},
    "low": {"minima", "minimo", "low"},
    "high": {"maxima", "maximo", "high"},
    "open": {"abertura", "open"},
    "volume": {"volume", "volume_financeiro", "vol"},
    "quantity": {"quantidade", "volume_quantidade", "qty"},
}


def load_profit_intraday_csv(path: Path) -> list[Candle]:
    text = _read_text(path)
    if not text.strip():
        raise ValueError("CSV vazio")

    dialect = _detect_dialect(text)
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise ValueError("CSV sem cabecalho")

    columns = _resolve_columns(reader.fieldnames)
    required = {"date", "time", "open", "high", "low", "close"}
    missing = sorted(required - columns.keys())
    if missing:
        raise ValueError("Colunas obrigatorias ausentes: " + ", ".join(missing))

    candles: list[Candle] = []
    for row_number, row in enumerate(reader, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        try:
            candle = Candle(
                timestamp=_parse_datetime(
                    row[columns["date"]],
                    row[columns["time"]],
                ),
                open=_parse_number(row[columns["open"]]),
                high=_parse_number(row[columns["high"]]),
                low=_parse_number(row[columns["low"]]),
                close=_parse_number(row[columns["close"]]),
                volume=_optional_number(row, columns.get("volume")),
                trades=_optional_int(row, columns.get("trades")),
                quantity=_optional_number(row, columns.get("quantity")),
                symbol=_optional_text(row, columns.get("symbol")),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Linha {row_number} invalida: {exc}") from exc
        _validate_candle(candle, row_number)
        candles.append(candle)

    if not candles:
        raise ValueError("CSV nao contem candles validos")
    candles.sort(key=lambda item: item.timestamp)
    return candles


def resample_candles(candles: list[Candle], minutes: int) -> list[Candle]:
    if minutes <= 0 or 60 % minutes != 0:
        raise ValueError("Periodo deve dividir 60 minutos")
    if not candles:
        return []

    grouped: dict[tuple[str | None, datetime], list[Candle]] = {}
    for candle in candles:
        minute = (candle.timestamp.minute // minutes) * minutes
        bucket = candle.timestamp.replace(minute=minute, second=0, microsecond=0)
        grouped.setdefault((candle.symbol, bucket), []).append(candle)

    result: list[Candle] = []
    for (symbol, timestamp), items in sorted(
        grouped.items(),
        key=lambda item: item[0][1],
    ):
        items.sort(key=lambda item: item.timestamp)
        volumes = [item.volume for item in items if item.volume is not None]
        trades = [item.trades for item in items if item.trades is not None]
        quantities = [item.quantity for item in items if item.quantity is not None]
        result.append(
            Candle(
                timestamp=timestamp,
                open=items[0].open,
                high=max(item.high for item in items),
                low=min(item.low for item in items),
                close=items[-1].close,
                volume=sum(volumes) if volumes else None,
                trades=sum(trades) if trades else None,
                quantity=sum(quantities) if quantities else None,
                symbol=symbol,
            )
        )
    return result


def summarize_candles(candles: list[Candle]) -> CandleSeriesSummary:
    if not candles:
        raise ValueError("Serie vazia")
    symbols = {item.symbol for item in candles if item.symbol}
    symbol = next(iter(symbols)) if len(symbols) == 1 else None
    return CandleSeriesSummary(
        candles=len(candles),
        start=min(item.timestamp for item in candles),
        end=max(item.timestamp for item in candles),
        symbol=symbol,
    )


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Codificacao do CSV nao reconhecida")


def _detect_dialect(text: str) -> csv.Dialect:
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def _resolve_columns(fieldnames: list[str]) -> dict[str, str]:
    normalized = {_normalize_header(name): name for name in fieldnames}
    result: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                result[canonical] = normalized[alias]
                break
    return result


def _normalize_header(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.strip().lower().replace("#", "numero")
    return "_".join(text.replace("-", " ").split())


def _parse_datetime(date_value: str, time_value: str) -> datetime:
    date_text = str(date_value).strip()
    time_text = str(time_value).strip()
    for date_format in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y%m%d"):
        for time_format in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(
                    f"{date_text} {time_text}",
                    f"{date_format} {time_format}",
                )
            except ValueError:
                continue
    raise ValueError(f"data/hora nao reconhecida: {date_text} {time_text}")


def _parse_number(value: str | None) -> float:
    if value is None:
        raise ValueError("numero ausente")
    text = str(value).strip().replace(" ", "")
    if not text:
        raise ValueError("numero vazio")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") == 1:
        integer_part, decimal_part = text.split(".")
        if decimal_part.isdigit() and len(decimal_part) == 3:
            text = integer_part + decimal_part
    return float(text)


def _optional_number(row: dict[str, str], column: str | None) -> float | None:
    if column is None or not str(row.get(column) or "").strip():
        return None
    return _parse_number(row[column])


def _optional_int(row: dict[str, str], column: str | None) -> int | None:
    value = _optional_number(row, column)
    return int(value) if value is not None else None


def _optional_text(row: dict[str, str], column: str | None) -> str | None:
    if column is None:
        return None
    text = str(row.get(column) or "").strip()
    return text or None


def _validate_candle(candle: Candle, row_number: int) -> None:
    if candle.high < max(candle.open, candle.close):
        raise ValueError(f"linha {row_number}: maxima abaixo de abertura/fechamento")
    if candle.low > min(candle.open, candle.close):
        raise ValueError(f"linha {row_number}: minima acima de abertura/fechamento")
    if candle.high < candle.low:
        raise ValueError(f"linha {row_number}: maxima abaixo da minima")
