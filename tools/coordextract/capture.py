"""Bring a PDF (or anything on screen) into the tool as an image.

Two entry points:

  * open_pdf / render_page   -- rasterise a PDF page with PyMuPDF (no system
                                binary needed). Best quality; needs the file.
  * grab_screen_region       -- draw a rectangle over ANY window on screen
                                (browser, Adobe Acrobat, any app) and capture
                                those pixels. Universal bridge to an open PDF.
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Tuple

import numpy as np


def _pymupdf():
    """Import PyMuPDF under its current or legacy module name."""
    try:
        import pymupdf  # PyMuPDF >= 1.24
        return pymupdf
    except ImportError:
        import fitz  # older PyMuPDF
        return fitz


# --------------------------------------------------------------------- PDF --

def open_pdf(path: str):
    """Open a PDF and return a PyMuPDF document (caller keeps it and closes it)."""
    return _pymupdf().open(path)


def render_page(doc, index: int, dpi: int = 200) -> np.ndarray:
    """Render page `index` of an open document to a BGR numpy image."""
    import cv2
    fitz = _pymupdf()

    index = max(0, min(index, doc.page_count - 1))
    page = doc.load_page(index)
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:  # n == 3, RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return np.ascontiguousarray(img)


# ------------------------------------------------------------ Screen grab --

def enable_dpi_awareness() -> None:
    """Make Tk coordinates match physical pixels so screen grabs align (Windows)."""
    if sys.platform != "win32":
        return
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _virtual_screen_bounds(root: tk.Misc) -> Tuple[int, int, int, int]:
    """(x, y, w, h) of the whole virtual desktop (all monitors)."""
    if sys.platform == "win32":
        import ctypes
        u = ctypes.windll.user32
        SM = (76, 77, 78, 79)  # X, Y, CX, CY VIRTUALSCREEN
        x, y, w, h = (u.GetSystemMetrics(i) for i in SM)
        if w and h:
            return x, y, w, h
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


class _ScreenGrabber:
    def __init__(self, root: tk.Tk, hint: Optional[str] = None):
        self.root = root
        self.hint = hint or "Drag a rectangle over the PDF area to capture  —  Esc to cancel"
        self.result: Optional[np.ndarray] = None
        self.start: Optional[Tuple[int, int]] = None

        self.vx, self.vy, self.vw, self.vh = _virtual_screen_bounds(root)

        root.withdraw()  # hide the app so it doesn't cover the target
        root.update()

        top = self.top = tk.Toplevel(root)
        top.overrideredirect(True)
        top.geometry(f"{self.vw}x{self.vh}+{self.vx}+{self.vy}")
        top.attributes("-topmost", True)
        try:
            top.attributes("-alpha", 0.25)
        except tk.TclError:
            pass
        self.canvas = tk.Canvas(top, bg="black", cursor="cross", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_text(
            self.vw // 2, 30,
            text=self.hint,
            fill="white", font=("", 14, "bold"),
        )
        self.canvas.bind("<ButtonPress-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._move)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        top.bind("<Escape>", lambda e: self._cancel())
        top.focus_force()

    def _down(self, e):
        self.start = (e.x, e.y)

    def _move(self, e):
        if self.start is None:
            return
        self.canvas.delete("sel")
        self.canvas.create_rectangle(self.start[0], self.start[1], e.x, e.y,
                                     outline="#00e0ff", width=2, tags="sel")

    def _up(self, e):
        if self.start is None:
            return self._cancel()
        x0, y0 = self.start
        x1, y1 = e.x, e.y
        # to absolute screen coords
        sx0, sx1 = sorted((self.vx + x0, self.vx + x1))
        sy0, sy1 = sorted((self.vy + y0, self.vy + y1))
        self.top.destroy()
        self.root.deiconify()
        self.root.update()
        if sx1 - sx0 < 8 or sy1 - sy0 < 8:
            self.result = None
            return
        self.result = self._grab(sx0, sy0, sx1, sy1)

    def _cancel(self):
        self.top.destroy()
        self.root.deiconify()
        self.result = None

    @staticmethod
    def _grab(x0, y0, x1, y1) -> Optional[np.ndarray]:
        import cv2
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
        arr = np.array(img)[:, :, :3]  # RGB
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def grab_screen_region(root: tk.Tk, hint: Optional[str] = None) -> Optional[np.ndarray]:
    """Interactive screen snip. Returns a BGR image, or None if cancelled."""
    g = _ScreenGrabber(root, hint=hint)
    root.wait_window(g.top)
    return g.result
