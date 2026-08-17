from __future__ import annotations

import tkinter as tk

Point = tuple[int, int]
Region = tuple[int, int, int, int]


def normalize_bbox(start: Point, end: Point) -> Region:
    x1, y1 = start
    x2, y2 = end
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


class CaptureRegionSelector:
    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.result: Region | None = None
        self.overlay: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self.rectangle_id: int | None = None
        self.start_screen: Point | None = None
        self.start_canvas: Point | None = None

    def select(self) -> Region | None:
        self.parent.withdraw()
        overlay = tk.Toplevel(self.parent)
        self.overlay = overlay
        overlay.configure(bg="black")
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-alpha", 0.35)
        overlay.attributes("-topmost", True)

        canvas = tk.Canvas(
            overlay,
            bg="black",
            cursor="crosshair",
            highlightthickness=0,
        )
        self.canvas = canvas
        canvas.pack(fill="both", expand=True)
        canvas.create_text(
            24,
            24,
            anchor="nw",
            fill="white",
            font=("Segoe UI", 16, "bold"),
            text="Arraste sobre os graficos M60, M15 e M5. ESC cancela.",
        )
        canvas.bind("<ButtonPress-1>", self._on_press)
        canvas.bind("<B1-Motion>", self._on_drag)
        canvas.bind("<ButtonRelease-1>", self._on_release)
        overlay.bind("<Escape>", self._cancel)
        overlay.focus_force()
        overlay.wait_window()

        self.parent.deiconify()
        self.parent.lift()
        self.parent.focus_force()
        return self.result

    def _on_press(self, event: tk.Event) -> None:
        if self.canvas is None:
            return
        self.start_screen = (event.x_root, event.y_root)
        self.start_canvas = (event.x, event.y)
        if self.rectangle_id is not None:
            self.canvas.delete(self.rectangle_id)
        self.rectangle_id = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="white",
            width=3,
        )

    def _on_drag(self, event: tk.Event) -> None:
        if (
            self.canvas is None
            or self.rectangle_id is None
            or self.start_canvas is None
        ):
            return
        x1, y1 = self.start_canvas
        self.canvas.coords(self.rectangle_id, x1, y1, event.x, event.y)

    def _on_release(self, event: tk.Event) -> None:
        if self.start_screen is None:
            self._cancel()
            return
        region = normalize_bbox(
            self.start_screen,
            (event.x_root, event.y_root),
        )
        x1, y1, x2, y2 = region
        if x2 - x1 >= 20 and y2 - y1 >= 20:
            self.result = region
        self._close_overlay()

    def _cancel(self, _event: tk.Event | None = None) -> None:
        self.result = None
        self._close_overlay()

    def _close_overlay(self) -> None:
        if self.overlay is not None and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.overlay = None
