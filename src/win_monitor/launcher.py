from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from win_monitor.config import Settings, app_home, load_dotenv
from win_monitor.region_selector import CaptureRegionSelector
from win_monitor.service import MonitorService


class LauncherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("WIN Monitor - Modo Estudo")
        self.root.geometry("820x680")
        self.root.minsize(720, 600)
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.home = app_home()
        self.env_path = self.home / ".env"
        load_dotenv(self.env_path)
        self.entries: dict[str, tk.Entry] = {}
        self._build_ui()
        self._load_values()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="WIN Monitor",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="Fase 1: leitura, registro e Telegram. Nenhuma ordem e executada.",
        ).pack(anchor="w", pady=(0, 14))

        form = ttk.Frame(outer)
        form.pack(fill="x")
        fields = [
            ("ANTHROPIC_API_KEY", "Chave Anthropic", True),
            ("TELEGRAM_BOT_TOKEN", "Token do bot Telegram", True),
            ("TELEGRAM_CHAT_ID", "Chat ID Telegram", False),
            ("ANTHROPIC_MODEL", "Modelo de visao", False),
            ("ANALISE_INTERVALO_MIN", "Intervalo em minutos", False),
            ("HORARIO_INICIO", "Horario inicial (HH:MM)", False),
            ("HORARIO_FIM", "Horario final (HH:MM)", False),
            ("MAX_CONTRATOS", "Maximo de contratos (1-5)", False),
            (
                "RISCO_MAXIMO_BRL",
                "Risco maximo por operacao em R$ (opcional)",
                False,
            ),
            (
                "REGIAO_CAPTURA",
                "Regiao x1,y1,x2,y2 (vazio = tela inteira)",
                False,
            ),
        ]
        for row, (key, label, secret) in enumerate(fields):
            ttk.Label(form, text=label).grid(
                row=row,
                column=0,
                sticky="w",
                pady=4,
            )
            entry = ttk.Entry(
                form,
                show="*" if secret else "",
                width=58,
            )
            entry.grid(
                row=row,
                column=1,
                sticky="ew",
                padx=(12, 0),
                pady=4,
            )
            self.entries[key] = entry
        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=14)
        ttk.Button(
            buttons,
            text="Salvar configuracao",
            command=self.save,
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Selecionar area",
            command=self.select_capture_region,
        ).pack(side="left", padx=8)
        ttk.Button(
            buttons,
            text="Testar Telegram",
            command=self.test_telegram,
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Iniciar monitor",
            command=self.start,
        ).pack(side="left", padx=8)
        ttk.Button(
            buttons,
            text="Parar",
            command=self.stop,
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Abrir pasta de dados",
            command=self.open_data_dir,
        ).pack(side="right")

        self.status = ttk.Label(
            outer,
            text="Parado",
            foreground="#9a6700",
        )
        self.status.pack(anchor="w", pady=(0, 8))
        self.log_widget = tk.Text(
            outer,
            height=16,
            wrap="word",
            state="disabled",
        )
        self.log_widget.pack(fill="both", expand=True)

    def _load_values(self) -> None:
        defaults = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            "TELEGRAM_CHAT_ID": os.environ.get("TELEGRAM_CHAT_ID", ""),
            "ANTHROPIC_MODEL": os.environ.get(
                "ANTHROPIC_MODEL",
                "claude-sonnet-5",
            ),
            "ANALISE_INTERVALO_MIN": os.environ.get("ANALISE_INTERVALO_MIN", "5"),
            "HORARIO_INICIO": os.environ.get("HORARIO_INICIO", "09:05"),
            "HORARIO_FIM": os.environ.get("HORARIO_FIM", "17:25"),
            "MAX_CONTRATOS": os.environ.get("MAX_CONTRATOS", "5"),
            "RISCO_MAXIMO_BRL": os.environ.get("RISCO_MAXIMO_BRL", ""),
            "REGIAO_CAPTURA": os.environ.get("REGIAO_CAPTURA", ""),
        }
        for key, value in defaults.items():
            self.entries[key].insert(0, value)

    def save(self) -> bool:
        self.home.mkdir(parents=True, exist_ok=True)
        lines = [
            f"{key}={entry.get().strip()}"
            for key, entry in self.entries.items()
        ]
        lines.append("ENVIAR_TELEGRAM_PARA=ENTRADA,QUASE")
        self.env_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        for key, entry in self.entries.items():
            os.environ[key] = entry.get().strip()
        os.environ["ENVIAR_TELEGRAM_PARA"] = "ENTRADA,QUASE"
        self._log(f"Configuracao salva em {self.env_path}")
        return True

    def select_capture_region(self) -> None:
        region = CaptureRegionSelector(self.root).select()
        if region is None:
            self._log("Selecao de area cancelada.")
            return

        value = ",".join(str(coordinate) for coordinate in region)
        entry = self.entries["REGIAO_CAPTURA"]
        entry.delete(0, "end")
        entry.insert(0, value)
        self._log(f"Area de captura selecionada: {value}")

    def _settings(self) -> Settings:
        self.save()
        return Settings.load(self.env_path)

    def test_telegram(self) -> None:
        try:
            settings = self._settings()
            missing = settings.missing_credentials()
            if missing:
                raise ValueError("Credenciais ausentes: " + ", ".join(missing))
            service = MonitorService(settings, log=self._log)
            threading.Thread(
                target=self._test_telegram_worker,
                args=(service,),
                daemon=True,
            ).start()
            self._log("Mensagem de teste solicitada ao Telegram.")
        except Exception as exc:
            messagebox.showerror("Configuracao", str(exc))

    def _test_telegram_worker(self, service: MonitorService) -> None:
        try:
            service.telegram.test_connection()
            self._log("Telegram respondeu com sucesso.")
        except Exception as exc:
            self._log(f"Falha ao testar Telegram: {exc}")

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            self._log("O monitor ja esta em execucao.")
            return

        try:
            settings = self._settings()
            missing = settings.missing_credentials()
            if missing:
                raise ValueError("Credenciais ausentes: " + ", ".join(missing))
            service = MonitorService(settings, log=self._log)
        except Exception as exc:
            messagebox.showerror("Nao foi possivel iniciar", str(exc))
            return

        self.stop_event = threading.Event()
        self.worker = threading.Thread(
            target=service.run_forever,
            args=(self.stop_event,),
            daemon=True,
        )
        self.worker.start()
        self.status.configure(
            text="Monitor em execucao",
            foreground="#137333",
        )
        self._log("Monitor iniciado. Deixe M60, M15 e M5 visiveis na tela.")

    def stop(self) -> None:
        self.stop_event.set()
        self.status.configure(
            text="Parando...",
            foreground="#9a6700",
        )
        self._log("Solicitacao de parada enviada.")

    def open_data_dir(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(self.home)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(self.home)])
        else:
            subprocess.Popen(["xdg-open", str(self.home)])

    def _log(self, message: str) -> None:
        def append() -> None:
            self.log_widget.configure(state="normal")
            self.log_widget.insert("end", message + "\n")
            self.log_widget.see("end")
            self.log_widget.configure(state="disabled")

        self.root.after(0, append)

    def _on_close(self) -> None:
        self.stop_event.set()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
