from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def app_home() -> Path:
    override = os.environ.get("WIN_MONITOR_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "WinMonitor"
    return Path.home() / ".win_monitor"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _parse_int(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser inteiro") from exc


def _parse_float(name: str) -> float | None:
    value = os.environ.get(name, "").strip().replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser numerico") from exc


def _parse_region(value: str) -> tuple[int, int, int, int] | None:
    value = value.strip()
    if not value:
        return None

    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("REGIAO_CAPTURA deve ter x1,y1,x2,y2")

    region = tuple(int(part) for part in parts)
    x1, y1, x2, y2 = region
    if x2 <= x1 or y2 <= y1:
        raise ValueError("REGIAO_CAPTURA possui dimensoes invalidas")
    return region


@dataclass(slots=True)
class Settings:
    anthropic_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    model: str = "claude-sonnet-5"
    interval_minutes: int = 5
    start_time: str = "09:05"
    end_time: str = "17:25"
    telegram_scenarios: set[str] = field(
        default_factory=lambda: {"ENTRADA", "QUASE"}
    )
    capture_region: tuple[int, int, int, int] | None = None
    max_contracts: int = 5
    max_risk_brl: float | None = None
    data_dir: Path = field(default_factory=app_home)

    @classmethod
    def load(cls, env_path: Path | None = None) -> Settings:
        home = app_home()
        candidates = [env_path] if env_path else [Path.cwd() / ".env", home / ".env"]
        for candidate in candidates:
            if candidate:
                load_dotenv(candidate)

        send_for = {
            item.strip().upper()
            for item in os.environ.get(
                "ENVIAR_TELEGRAM_PARA",
                "ENTRADA,QUASE",
            ).split(",")
            if item.strip()
        }
        settings = cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "").strip(),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip(),
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5").strip(),
            interval_minutes=_parse_int("ANALISE_INTERVALO_MIN", 5),
            start_time=os.environ.get("HORARIO_INICIO", "09:05").strip(),
            end_time=os.environ.get("HORARIO_FIM", "17:25").strip(),
            telegram_scenarios=send_for,
            capture_region=_parse_region(os.environ.get("REGIAO_CAPTURA", "")),
            max_contracts=_parse_int("MAX_CONTRATOS", 5),
            max_risk_brl=_parse_float("RISCO_MAXIMO_BRL"),
            data_dir=home,
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.interval_minutes <= 0:
            raise ValueError("ANALISE_INTERVALO_MIN deve ser maior que zero")
        if not 1 <= self.max_contracts <= 5:
            raise ValueError("MAX_CONTRATOS deve ficar entre 1 e 5")
        if len(self.start_time) != 5 or len(self.end_time) != 5:
            raise ValueError("HORARIO_INICIO e HORARIO_FIM devem usar HH:MM")
        if self.max_risk_brl is not None and self.max_risk_brl <= 0:
            raise ValueError("RISCO_MAXIMO_BRL deve ser maior que zero")

    def missing_credentials(self) -> list[str]:
        missing: list[str] = []
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        return missing

    @property
    def env_path(self) -> Path:
        return self.data_dir / ".env"
