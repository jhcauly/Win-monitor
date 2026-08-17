from __future__ import annotations

import argparse
from pathlib import Path

from win_monitor.config import Settings
from win_monitor.service import MonitorService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WIN Monitor em modo estudo")
    parser.add_argument("--env", type=Path, help="Caminho opcional para arquivo .env")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa uma unica captura e analise",
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Envia mensagem de teste e encerra",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        settings = Settings.load(args.env)
    except ValueError as exc:
        raise SystemExit(f"Configuracao invalida: {exc}") from exc

    missing = settings.missing_credentials()
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Credenciais ausentes: {names}. Use a interface grafica ou .env."
        )

    service = MonitorService(settings)
    if args.test_telegram:
        service.telegram.test_connection()
        print("Telegram testado com sucesso.")
        return

    if args.once:
        service.process_once()
        return

    service.run_forever()


if __name__ == "__main__":
    main()
