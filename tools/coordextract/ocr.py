"""Table OCR: read a printed coordinate table (No / X / Y) from an image crop.

Backends are pluggable and auto-detected, in order of convenience:

  1. rapidocr-onnxruntime  -- pip install, no system binary, works offline (default)
  2. pytesseract           -- needs the Tesseract binary installed separately
  3. easyocr               -- heavy (torch) but self-contained

Nothing here is destructive; if no backend is available we raise a clear error
telling the user what to `pip install`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


class OCRUnavailable(Exception):
    """Raised when no OCR backend could be imported."""


@dataclass
class CoordRow:
    label: str          # the "No" cell, e.g. "1"
    x: Optional[float]  # parsed X (easting)
    y: Optional[float]  # parsed Y (northing)
    raw: str = ""       # the raw OCR line, for debugging / manual fix


@dataclass
class OCRResult:
    rows: List[CoordRow] = field(default_factory=list)
    raw_text: str = ""
    backend: str = ""


# --------------------------------------------------------------------------- #
# Backend detection
# --------------------------------------------------------------------------- #

def available_backends() -> List[str]:
    found = []
    try:
        import rapidocr_onnxruntime  # noqa: F401
        found.append("rapidocr")
    except Exception:
        pass
    try:
        import pytesseract  # noqa: F401
        # pytesseract imports fine even without the binary; check the binary too.
        try:
            pytesseract.get_tesseract_version()
            found.append("tesseract")
        except Exception:
            pass
    except Exception:
        pass
    try:
        import easyocr  # noqa: F401
        found.append("easyocr")
    except Exception:
        pass
    return found


_RAPIDOCR_ENGINE = None
_EASYOCR_READER = None


def _preprocess(bgr: np.ndarray) -> np.ndarray:
    """Upscale + grayscale + adaptive threshold to help OCR on small print."""
    import cv2

    if bgr.ndim == 3:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = bgr
    # Upscale small crops so digits are big enough for the recognizer.
    h, w = gray.shape[:2]
    scale = max(1.0, 1000.0 / max(w, 1))
    if scale > 1.0:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.bilateralFilter(gray, 5, 40, 40)
    return gray


def _raw_lines_rapidocr(bgr: np.ndarray) -> List[str]:
    global _RAPIDOCR_ENGINE
    from rapidocr_onnxruntime import RapidOCR

    if _RAPIDOCR_ENGINE is None:
        _RAPIDOCR_ENGINE = RapidOCR()
    result, _ = _RAPIDOCR_ENGINE(bgr)
    if not result:
        return []
    # result: list of [box, text, score]; group into rows by vertical position.
    items = []
    for box, text, _score in result:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append((min(ys), min(xs), text))
    items.sort(key=lambda t: (round(t[0] / 15.0), t[1]))
    lines: List[str] = []
    current_key = None
    buf: List[str] = []
    for ytop, _x, text in items:
        key = round(ytop / 15.0)
        if current_key is None or key == current_key:
            buf.append(text)
            current_key = key
        else:
            lines.append(" ".join(buf))
            buf = [text]
            current_key = key
    if buf:
        lines.append(" ".join(buf))
    return lines


def _raw_lines_tesseract(bgr: np.ndarray) -> List[str]:
    import pytesseract

    gray = _preprocess(bgr)
    config = "--psm 6"  # assume a uniform block of text
    text = pytesseract.image_to_string(gray, config=config)
    return [ln for ln in text.splitlines() if ln.strip()]


def _raw_lines_easyocr(bgr: np.ndarray) -> List[str]:
    global _EASYOCR_READER
    import easyocr

    if _EASYOCR_READER is None:
        _EASYOCR_READER = easyocr.Reader(["en"], gpu=False)
    result = _EASYOCR_READER.readtext(bgr)
    items = []
    for box, text, _score in result:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append((min(ys), min(xs), text))
    items.sort(key=lambda t: (round(t[0] / 15.0), t[1]))
    return [t[2] for t in items]


_NUM_RE = re.compile(r"-?\d[\d.,]*\d|\d")


def _clean_number(token: str) -> Optional[float]:
    t = token.strip().replace(" ", "")
    # Treat both , and . as possible decimal or thousands separators; coordinates
    # in these maps are integers, so drop separators used as thousands grouping.
    if t.count(",") == 1 and t.count(".") == 0 and len(t.split(",")[1]) != 3:
        t = t.replace(",", ".")
    t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def parse_rows(lines: List[str]) -> List[CoordRow]:
    """Turn OCR text lines into (label, X, Y) rows.

    Heuristic: a data row is a line containing at least two large integers
    (the coordinates). The first small integer, if present, is the row label.
    """
    rows: List[CoordRow] = []
    for line in lines:
        nums = [m.group(0) for m in _NUM_RE.finditer(line)]
        vals = [(_clean_number(n), n) for n in nums]
        vals = [(v, raw) for v, raw in vals if v is not None]
        if len(vals) < 2:
            continue

        # Coordinates are the large-magnitude numbers (>= 1000 here). The label
        # is a small leading integer.
        big = [(v, raw) for v, raw in vals if abs(v) >= 1000]
        small = [(v, raw) for v, raw in vals if abs(v) < 1000]

        if len(big) >= 2:
            x_val = big[0][0]
            y_val = big[1][0]
            label = small[0][1] if small else str(len(rows) + 1)
            rows.append(CoordRow(label=label.strip(), x=x_val, y=y_val, raw=line))
    return rows


def extract_table(bgr: np.ndarray, backend: Optional[str] = None) -> OCRResult:
    """Run OCR on a BGR image crop and parse it into coordinate rows."""
    backends = available_backends()
    if not backends:
        raise OCRUnavailable(
            "No OCR backend found. Install one of:\n"
            "  pip install rapidocr-onnxruntime   (recommended, no system binary)\n"
            "  pip install pytesseract            (also install the Tesseract binary)\n"
            "  pip install easyocr                (large download)"
        )

    chosen = backend if backend in backends else backends[0]

    if chosen == "rapidocr":
        lines = _raw_lines_rapidocr(bgr)
    elif chosen == "tesseract":
        lines = _raw_lines_tesseract(bgr)
    elif chosen == "easyocr":
        lines = _raw_lines_easyocr(bgr)
    else:  # pragma: no cover
        raise OCRUnavailable(f"unknown backend: {chosen}")

    rows = parse_rows(lines)
    return OCRResult(rows=rows, raw_text="\n".join(lines), backend=chosen)
