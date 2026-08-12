from __future__ import annotations

import requests


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 20) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_text(self, message: str) -> None:
        response = requests.post(f"{self.base_url}/sendMessage", json={"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}, timeout=self.timeout)
        self._ensure_ok(response)

    def send_photo(self, image_bytes: bytes, caption: str) -> None:
        response = requests.post(f"{self.base_url}/sendPhoto", data={"chat_id": self.chat_id, "caption": caption[:1024], "parse_mode": "HTML"}, files={"photo": ("analise.png", image_bytes, "image/png")}, timeout=self.timeout)
        self._ensure_ok(response)

    def test_connection(self) -> None:
        self.send_text("✅ WIN Monitor conectado ao Telegram em modo estudo.")

    @staticmethod
    def _ensure_ok(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:300]
        raise TelegramError(f"Telegram respondeu {response.status_code}: {detail}")
