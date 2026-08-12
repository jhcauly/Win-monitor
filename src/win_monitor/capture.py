from __future__ import annotations

import io

from PIL import ImageGrab


class ScreenCapture:
    def __init__(self, region: tuple[int, int, int, int] | None = None) -> None:
        self.region = region

    def capture_png(self) -> bytes:
        image = ImageGrab.grab(bbox=self.region)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
