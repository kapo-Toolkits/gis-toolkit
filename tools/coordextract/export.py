"""Export coordinate rows to CSV / JSON / XLSX."""

from __future__ import annotations

import csv
import json
from typing import Iterable, List, Sequence, Tuple


def _as_number(v):
    """Return an int/float if the value looks numeric, else the original string."""
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace(",", ".")
    if s == "":
        return ""
    try:
        f = float(s)
        return int(f) if f.is_integer() else f
    except ValueError:
        return v


def rows_to_csv(path: str, rows: Sequence[Tuple[str, object, object]],
                header: Sequence[str] = ("No", "X", "Y")) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def rows_to_json(path: str, rows: Sequence[Tuple[str, object, object]],
                 keys: Sequence[str] = ("no", "x", "y"),
                 extra: dict | None = None) -> None:
    data = {
        "points": [dict(zip(keys, r)) for r in rows],
    }
    if extra:
        data.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def rows_to_xlsx(path: str, rows: Sequence[Tuple[str, object, object]],
                 header: Sequence[str] = ("No", "X", "Y"),
                 sheet_name: str = "Coordinates",
                 note: str | None = None) -> None:
    """Write rows to a modern .xlsx workbook (numbers stored as numbers)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31] or "Coordinates"

    bold = Font(bold=True)
    center = Alignment(horizontal="center")
    for c, name in enumerate(header, 1):
        cell = ws.cell(row=1, column=c, value=name)
        cell.font = bold
        cell.alignment = center

    for r, row in enumerate(rows, 2):
        for c, val in enumerate(row, 1):
            out = _as_number(val) if c >= 2 else val  # keep label column as-is
            ws.cell(row=r, column=c, value=out)

    for c, name in enumerate(header, 1):
        width = max(len(str(name)), *(len(str(row[c - 1])) for row in rows)) if rows else len(str(name))
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = width + 4

    if note:
        ws.cell(row=len(rows) + 3, column=1, value=note)

    ws.freeze_panes = "A2"
    wb.save(path)
