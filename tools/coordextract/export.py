"""Export coordinate rows to CSV / JSON / XLSX."""

from __future__ import annotations

import csv
import re
import json
from typing import Iterable, List, Sequence, Tuple


def _clean_number(v):
    """Turn a possibly messy cell into a plain number, free of errors.

    Strips spaces, letters and stray symbols (OCR noise), treats comma as the
    decimal separator, and returns int when whole. Returns None if nothing
    numeric is left."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v) if float(v).is_integer() else v
    s = str(v).strip().replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)          # drop spaces/letters/symbols
    if s in ("", "-", ".", "-."):
        return None
    try:
        f = float(s)
    except ValueError:
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        if not m:
            return None
        f = float(m.group())
    return int(f) if f.is_integer() else f


def format_xlsx(path: str, out_path: str | None = None,
                header: Sequence[str] = ("№", "X", "Y")) -> Tuple[str, int]:
    """Add a cleaned, formatted copy of the coordinate table to an .xlsx.

    The original block (header at A1, data from row 2, columns No/X/Y) is left
    untouched. A tidy copy is written starting two columns to the right of the
    original block and a few rows down (E6 for a 3-column original), with:
      • a numbering column headed “№” holding plain sequential numbers,
      • X/Y values cleaned to plain numbers,
      • all three columns centered (center + middle) with all-borders.

    Returns (saved_path, number_of_rows).
    """
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, Border, Side
    from openpyxl.utils import get_column_letter

    wb = load_workbook(path)
    ws = wb.active

    # --- ორიგინალის წაკითხვა: A1 სათაური, მონაცემები მე-2 რიგიდან (No/X/Y) ---
    ORIG_COLS = 3
    data = []
    r = 2
    while True:
        x = ws.cell(row=r, column=2).value
        y = ws.cell(row=r, column=3).value
        if x is None and y is None:          # კოორდინატები აღარ არის — ბოლო
            break
        data.append((x, y))
        r += 1

    # --- ასლის საწყისი პოზიცია: ბოლო სვეტიდან +2 (C→E), რამდენიმე რიგით ქვემოთ ---
    start_col = ORIG_COLS + 2                 # 3 + 2 = 5 (E)
    start_row = 6

    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center")
    bold = Font(bold=True)

    # სათაური
    for j, name in enumerate(header):
        cell = ws.cell(row=start_row, column=start_col + j, value=name)
        cell.font = bold
        cell.alignment = center
        cell.border = border

    # მონაცემები — ნუმერაცია თანმიმდევრული, X/Y გასუფთავებული
    for i, (x, y) in enumerate(data, start=1):
        rr = start_row + i
        for j, val in enumerate((i, _clean_number(x), _clean_number(y))):
            cell = ws.cell(row=rr, column=start_col + j, value=val)
            cell.alignment = center
            cell.border = border

    # სვეტების სიგანე
    widths = [len(str(header[0]))] + [7, 7]
    for x, y in data:
        widths[1] = max(widths[1], len(str(_clean_number(x))))
        widths[2] = max(widths[2], len(str(_clean_number(y))))
    for j, w in enumerate(widths):
        ws.column_dimensions[get_column_letter(start_col + j)].width = w + 4

    save = out_path or path
    wb.save(save)
    return save, len(data)


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
