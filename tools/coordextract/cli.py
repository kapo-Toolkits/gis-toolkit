"""Headless table OCR — scriptable counterpart to the GUI's OCR tab.

    python -m coordextract.cli map.png --table 90,1000,540,1290 -o coords.csv
    python -m coordextract.cli map.png                 # OCR the whole image

--table is an optional pixel crop x0,y0,x1,y1 (same box you'd drag in the GUI).
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from . import export
from .ocr import OCRUnavailable, available_backends, extract_table


def _read_image(path: str) -> np.ndarray:
    import cv2
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"could not read image: {path}")
    return img


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Extract a No/X/Y coordinate table from a map image.")
    p.add_argument("image")
    p.add_argument("--table", help="crop as x0,y0,x1,y1 in pixels")
    p.add_argument("--backend", choices=["rapidocr", "tesseract", "easyocr"])
    p.add_argument("-o", "--out", help="output file (.csv or .json). Default: stdout as CSV")
    args = p.parse_args(argv)

    if not available_backends():
        print("No OCR backend installed. Try: pip install rapidocr-onnxruntime", file=sys.stderr)
        return 2

    img = _read_image(args.image)
    if args.table:
        try:
            x0, y0, x1, y1 = (int(v) for v in args.table.split(","))
        except ValueError:
            raise SystemExit("--table must be x0,y0,x1,y1 integers")
        img = img[y0:y1, x0:x1]

    try:
        result = extract_table(img, backend=args.backend)
    except OCRUnavailable as e:
        print(str(e), file=sys.stderr)
        return 2

    rows = [(r.label, "" if r.x is None else r.x, "" if r.y is None else r.y) for r in result.rows]

    if not args.out:
        print("No,X,Y")
        for r in rows:
            print(",".join(str(v) for v in r))
    elif args.out.lower().endswith(".json"):
        export.rows_to_json(args.out, rows)
        print(f"wrote {len(rows)} rows -> {args.out}")
    elif args.out.lower().endswith(".xlsx"):
        export.rows_to_xlsx(args.out, rows)
        print(f"wrote {len(rows)} rows -> {args.out}")
    else:
        export.rows_to_csv(args.out, rows)
        print(f"wrote {len(rows)} rows -> {args.out}")

    print(f"(backend: {result.backend})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
