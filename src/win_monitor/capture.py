from __future__ import annotations

import io

from PIL import ImageGrab


class ScreenCapture:
    """Capture the complete Windows desktop used by the trading layout.

    The old implementation honored a saved crop region. That could silently keep
    an obsolete partial region and omit M5/M15/M60. For the visual monitor the
    complete desktop is now authoritative; region is retained only for backward
    constructor compatibility.
    """

    def __init__(self, region: tuple[int, int, int, int] | None = None) -> None:
        self.region = region

    def capture_png(self) -> bytes:
        image = ImageGrab.grab(all_screens=True)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
