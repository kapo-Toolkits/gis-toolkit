# -*- coding: utf-8 -*-
"""საკადასტრო კოდების ძებნის ხელსაწყო — GIS_BOX-ის ხელსაწყო (ორენოვანი en/ka).

ეძებს საკადასტრო კოდებს File Geodatabase-ის შრეში და ნაპოვნებზე ქმნის
Shapefile-ს + GeoPackage-ს. ვერ ნაპოვნ კოდებს ცალკე გამოაქვს სიის სახით.

მოთხოვნები: geopandas, pyogrio, pandas, openpyxl (Excel-ისთვის).
ენა იკითხება GIS_BOX-ის მთავარი აპლიკაციიდან (self.app.lang).
"""

import os
import re
import threading
import queue
import traceback

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import pandas as pd
import pyogrio

from tools.base import ToolFrame


# ---------------------------------------------------------------------------
# თარგმანები / translations (en/ka)
# ---------------------------------------------------------------------------
PTR = {
    "sec_db":        {"en": "1. Database", "ka": "1. მონაცემთა ბაზა"},
    "lbl_gdb":       {"en": "GDB database:", "ka": "GDB ბაზა:"},
    "btn_read_layers": {"en": "Read layers", "ka": "შრეების წაკითხვა"},
    "btn_db_remove": {"en": "🗑 Remove DB", "ka": "🗑 ბაზის წაშლა"},
    "db_remove_q":   {"en": "Remove this database from the list?",
                      "ka": "წავშალო ეს ბაზა სიიდან?"},
    "btn_remember":  {"en": "💾 Remember settings", "ka": "💾 პარამეტრების დამახსოვრება"},
    "cfg_saved":     {"en": "Settings saved — they will be remembered next time.",
                      "ka": "პარამეტრები შენახულია — მომდევნო გაშვებაზეც დაიმახსოვრდება."},
    "cfg_hint":      {"en": "Enter your database path once and click Remember; it is stored "
                            "locally (not in the code / repository).",
                      "ka": "ერთხელ შეიყვანე ბაზის გზა და დააჭირე „დამახსოვრებას“; ის ინახება "
                            "ლოკალურად (არა კოდში / რეპოზიტორიაში)."},
    "lbl_layer":     {"en": "Layer:", "ka": "შრე:"},
    "lbl_field":     {"en": "Code field:", "ka": "კოდის ველი:"},
    "sec_codes":     {"en": "2. Search codes", "ka": "2. საძებნი კოდები"},
    "lbl_enter":     {"en": "Enter codes (one per line or comma-separated):",
                      "ka": "ჩაწერე კოდები (თითო ხაზზე ან მძიმით):"},
    "btn_load":      {"en": "Load from CSV/Excel", "ka": "CSV/Excel-იდან ატვირთვა"},
    "btn_clear":     {"en": "Clear", "ka": "გასუფთავება"},
    "sec_out":       {"en": "3. Output file", "ka": "3. შედეგის ფაილი"},
    "btn_search":    {"en": "🔍  Search", "ka": "🔍  ძებნა"},
    "btn_search_busy": {"en": "Working…", "ka": "მიმდინარეობს…"},
    "out_create":    {"en": "💾 Create:", "ka": "💾 შექმნა:"},
    "chk_shp":       {"en": "Shapefile (.shp)", "ka": "Shapefile (.shp)"},
    "chk_gpkg":      {"en": "GeoPackage (.gpkg)", "ka": "GeoPackage (.gpkg)"},
    "sec_result":    {"en": "4. Result", "ka": "4. შედეგი"},
    "btn_save_nf":   {"en": "Save not-found codes (.txt)",
                      "ka": "ვერ ნაპოვნი კოდების შენახვა (.txt)"},
    "ready":         {"en": "Ready.", "ka": "მზადაა."},
    "searching":     {"en": "Searching…", "ka": "ძებნა…"},

    # dialogs
    "err":           {"en": "Error", "ka": "შეცდომა"},
    "err_gdb":       {"en": "Database path not found.", "ka": "ბაზის მისამართი ვერ მოიძებნა."},
    "err_layer_field": {"en": "Select a layer and code field.",
                        "ka": "აირჩიე შრე და კოდის ველი."},
    "err_out":       {"en": "Specify the output file path.",
                      "ka": "მიუთითე შედეგის ფაილის მისამართი."},
    "err_codes_empty": {"en": "Search codes are empty.", "ka": "საძებნი კოდები ცარიელია."},
    "empty_title":   {"en": "Empty", "ka": "ცარიელი"},
    "no_layers":     {"en": "No layers found in the database.",
                      "ka": "ბაზაში შრეები ვერ მოიძებნა."},
    "pick_gdb":      {"en": "Select a .gdb database", "ka": "აირჩიე .gdb ბაზა"},
    "pick_file":     {"en": "Select a CSV or Excel file", "ka": "აირჩიე CSV ან Excel ფაილი"},
    "ft_tables":     {"en": "Spreadsheets", "ka": "ცხრილები"},
    "ft_all":        {"en": "All files", "ka": "ყველა"},
    "ft_txt":        {"en": "Text", "ka": "ტექსტი"},
    "file_read_err": {"en": "Could not read the file:\n{e}", "ka": "ფაილი ვერ წაიკითხა:\n{e}"},
    "pick_col_title": {"en": "Choose the code column", "ka": "აირჩიე კოდების სვეტი"},
    "pick_col_q":    {"en": "Which column has the cadastral codes?",
                      "ka": "რომელ სვეტშია საკადასტრო კოდები?"},
    "out_file_title": {"en": "Output file", "ka": "შედეგის ფაილი"},
    "save_nf_title": {"en": "Save not-found codes", "ka": "ვერ ნაპოვნი კოდების შენახვა"},
    "info":          {"en": "Info", "ka": "ინფო"},
    "ok":            {"en": "OK", "ka": "დიახ"},
    "no_nf":         {"en": "There are no not-found codes.", "ka": "ვერ ნაპოვნი კოდები არ არის."},
    "saved_title":   {"en": "Saved", "ka": "შენახულია"},
    "saved_n":       {"en": "Wrote {n} codes.", "ka": "ჩაიწერა {n} კოდი."},

    # log (UI)
    "log_layers":    {"en": "Layers found: {layers}", "ka": "ბაზაში ნაპოვნია შრეები: {layers}"},
    "log_loaded":    {"en": "Loaded {n} codes from file (column: {col}).",
                      "ka": "ფაილიდან ჩაიტვირთა {n} კოდი (სვეტი: {col})."},

    # log (run_search)
    "rs_count":      {"en": "Codes to search: {n}", "ka": "საძებნი კოდი: {n}"},
    "rs_db":         {"en": "Database: {gdb}", "ka": "ბაზა: {gdb}"},
    "rs_layer":      {"en": "Layer: {layer} | field: {field}", "ka": "შრე: {layer} | ველი: {field}"},
    "rs_searching":  {"en": "Searching…", "ka": "ძებნა მიმდინარეობს…"},
    "rs_block":      {"en": "  block {i}/{n} — {k} unique codes found so far",
                      "ka": "  ბლოკი {i}/{n} — ნაპოვნია სულ {k} უნიკ. კოდი"},
    "rs_writing":    {"en": "Writing {n} features…", "ka": "ვწერ {n} ობიექტს…"},
    "rs_none":       {"en": "No codes found — no files created.",
                      "ka": "ვერცერთი კოდი ვერ მოიძებნა — ფაილები არ შეიქმნა."},
    "rs_search_only":{"en": "Search only — {n} features matched, files not created.",
                      "ka": "მხოლოდ ძებნა — {n} ობიექტი დაემთხვა, ფაილები არ შექმნილა."},
    "sum_search_only": {"en": "Search only — no files created.",
                        "ka": "მხოლოდ ძებნა — ფაილები არ შექმნილა."},
    "rs_empty_list": {"en": "Empty list — no codes could be read.",
                      "ka": "ცარიელი სია — ვერცერთი კოდი ვერ წავიკითხე."},

    # summary (_on_done)
    "done_err_hdr":  {"en": "--- Error ---", "ka": "--- შეცდომა ---"},
    "sum_total":     {"en": "Total requested: {n}", "ka": "სულ საძებნი: {n}"},
    "sum_found":     {"en": "Found:       {n}", "ka": "ნაპოვნია:    {n}"},
    "sum_nf":        {"en": "Not found:   {n}", "ka": "ვერ ნაპოვნი: {n}"},
    "sum_written":   {"en": "Features written: {n}", "ka": "ჩაწერილი ობიექტი: {n}"},
    "sum_file":      {"en": "File: {p}", "ka": "ფაილი: {p}"},
    "nf_list_hdr":   {"en": "Not-found codes:", "ka": "ვერ ნაპოვნი კოდები:"},
    "done_status":   {"en": "Done — found {f}, not found {nf}.",
                      "ka": "დასრულდა — ნაპოვნი {f}, ვერ ნაპოვნი {nf}."},
    "nf_saved":      {"en": "Not-found codes saved: {p}", "ka": "ვერ ნაპოვნი კოდები შენახულია: {p}"},
}


# ---------------------------------------------------------------------------
# ნაგულისხმევი პარამეტრები — config.txt იკითხება GIS_BOX-ის ძირეული საქაღალდიდან
# (თითო ხაზი: KEY=VALUE — GDB=..., LAYER=RegParcels, FIELD=CADCODE).
# config.txt .gitignore-შია და GitHub-ზე არ აიტვირთება.
# ---------------------------------------------------------------------------
def _load_config():
    cfg = {"GDB": "", "LAYER": "RegParcels", "FIELD": "CADCODE"}
    # tools/parcel_search.py -> ../ = GIS_BOX ძირი
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(app_dir, "config.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip().upper()] = v.strip()
    except FileNotFoundError:
        pass
    return cfg


_CFG = _load_config()
DEFAULT_GDB = _CFG["GDB"]
DEFAULT_LAYER = _CFG["LAYER"]
DEFAULT_FIELD = _CFG["FIELD"]
# არჩევითი: რამდენიმე ბაზა config.txt-ში — GDBS=path1;path2;path3
DEFAULT_GDBS = [p.strip() for p in re.split(r"[;\n]+", _CFG.get("GDBS", ""))
                if p.strip()]
CHUNK_SIZE = 1000  # რამდენ კოდს ვეძებთ ერთ მოთხოვნაში

# CadData.gdb-ის დათასეთების კოდები → რეგიონები (სუფთა ლოგიკა ცალკე მოდულში)
from tools.regions import REGION_CODES, region_name, layer_display, layer_code
from tools.fields import pick_code_field


# ---------------------------------------------------------------------------
# დამხმარე ფუნქციები
# ---------------------------------------------------------------------------
def normalize(code):
    """საკადასტრო კოდის სტანდარტიზება CADCODE-ის ფორმატში (NN.NN.NN.NNN).

    სხვადასხვა ფორმით ჩაწერილი კოდი — ჰარეებით, წერტილებით ან შერეულად
    ('71 63 80 094', '71.63 .80 094', '71,63,80,094') — ერთ კანონიკურ,
    წერტილებით გამოყოფილ ფორმას მიჰყავს, რომ CADCODE სვეტს ზუსტად დაემთხვეს.
    ჯგუფებად დაყოფა ხდება ციფრების მიხედვით; წამყვანი ნულები რჩება.
    """
    if code is None:
        return ""
    s = str(code).strip()
    if not s:
        return ""
    groups = re.findall(r"\d+", s)
    if not groups:
        return s
    # უგამყოფოდ ჩაწერილი კოდი სტანდარტული სიგრძით — დავყოთ 2.2.2.3(.3) ჯგუფებად
    if len(groups) == 1:
        d = groups[0]
        if len(d) == 9:       # NN.NN.NN.NNN
            groups = [d[0:2], d[2:4], d[4:6], d[6:9]]
        elif len(d) == 12:    # NN.NN.NN.NNN.NNN (ქვენაკვეთი)
            groups = [d[0:2], d[2:4], d[4:6], d[6:9], d[9:12]]
    return ".".join(groups)


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def parse_manual_codes(text):
    """ხელით ჩაწერილი ტექსტიდან კოდების ამოღება (ხაზი, მძიმე, წერტილ-მძიმე, ტაბი)."""
    parts = re.split(r"[\r\n,;\t]+", text)
    seen = set()
    result = []
    for p in parts:
        c = normalize(p)
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


# ---------------------------------------------------------------------------
# ძებნის ლოგიკა (მუშაობს ცალკე thread-ში) — tr აპლიკაციის მიმდინარე ენას იყენებს
# ---------------------------------------------------------------------------
def run_search(gdb, layer, field, codes, out_path, log, done, tr, formats=("shp", "gpkg")):
    """
    log(msg)  -> სტატუსის ჩაწერა
    done(result_dict) -> დასრულებისას გამოძახება
    tr(key, **fmt) -> თარგმანი
    formats -> რომელი ფაილები შეიქმნას: ("shp", "gpkg"); ცარიელი => მხოლოდ ძებნა
    """
    formats = set(formats or ())
    try:
        # უნიკალური, ნორმალიზებული კოდები, თანმიმდევრობის შენარჩუნებით
        requested = []
        seen = set()
        for c in codes:
            n = normalize(c)
            if n and n not in seen:
                seen.add(n)
                requested.append(n)

        if not requested:
            done({"error": tr("rs_empty_list")})
            return

        log(tr("rs_count", n=len(requested)))
        log(tr("rs_db", gdb=gdb))
        log(tr("rs_layer", layer=layer, field=field))
        log(tr("rs_searching"))

        frames = []
        found_norm = set()
        total_chunks = (len(requested) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for idx, chunk in enumerate(chunked(requested, CHUNK_SIZE), start=1):
            vals = ",".join("'" + c.replace("'", "''") + "'" for c in chunk)
            where = f'"{field}" IN ({vals})'
            gdf = pyogrio.read_dataframe(gdb, layer=layer, where=where)
            if len(gdf) > 0:
                frames.append(gdf)
                for v in gdf[field].tolist():
                    found_norm.add(normalize(v))
            log(tr("rs_block", i=idx, n=total_chunks, k=len(found_norm)))

        not_found = [c for c in requested if c not in found_norm]
        found_list = [c for c in requested if c in found_norm]

        # შედეგის ჩაწერა — ორივე ფორმატში (Shapefile + GeoPackage), თუ მოთხოვნილია
        written = 0
        matched = 0
        out_files = []
        result_out_path = None
        if frames:
            import warnings
            import geopandas as gpd
            result = pd.concat(frames, ignore_index=True)
            result = gpd.GeoDataFrame(result, geometry="geometry", crs=frames[0].crs)
            matched = len(result)

            if formats:
                base = os.path.splitext(out_path)[0]
                os.makedirs(os.path.dirname(base), exist_ok=True)
                log(tr("rs_writing", n=matched))

                # GeoPackage — სრული ინფო, უჭრელი
                if "gpkg" in formats:
                    gpkg_path = base + ".gpkg"
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        result.to_file(gpkg_path, driver="GPKG", encoding="utf-8")
                    out_files.append(gpkg_path)
                    result_out_path = gpkg_path
                    log(f"  ✓ GeoPackage: {gpkg_path}")

                # Shapefile
                if "shp" in formats:
                    shp_path = base + ".shp"
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        result.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")
                    out_files.append(shp_path)
                    result_out_path = shp_path  # ვერ ნაპოვნის .txt ამის გვერდით შეინახება
                    log(f"  ✓ Shapefile:  {shp_path}")

                written = matched
            else:
                log(tr("rs_search_only", n=matched))
        else:
            log(tr("rs_none"))

        done({
            "requested": requested,
            "found_list": found_list,
            "not_found": not_found,
            "written": written,
            "matched": matched,
            "out_path": result_out_path,
            "out_files": out_files,
            "search_only": not formats,
        })

    except Exception as e:
        done({"error": f"{e}\n\n{traceback.format_exc()}"})


# ---------------------------------------------------------------------------
# ხელსაწყო (ToolFrame) — UI ჩაშენებულია GIS_BOX-ის მთავარ ფანჯარაში
# ---------------------------------------------------------------------------
class ParcelSearchTool(ToolFrame):
    tid = "parcel_search"

    def tr(self, key, **fmt):
        """თარგმანი GIS_BOX-ის მიმდინარე ენით."""
        entry = PTR.get(key, {})
        s = entry.get(self.app.lang) or entry.get("en") or key
        return s.format(**fmt) if fmt else s

    def _state(self):
        return self.app.tool_state.setdefault(self.tid, {})

    def build(self):
        self.msg_queue = queue.Queue()
        self.searching = False
        self.last_not_found = []
        st = self._state()                       # transient (სესიის ფარგლებში)
        saved = self.app.get_tool_config(self.tid)  # მუდმივი (git-ignored ფაილი)
        tr = self.tr

        # საწყისი მნიშვნელობა: სესიის მდგომარეობა → შენახული კონფიგი → ნაგულისხმევი
        def initial(key, default):
            return st.get(key) or saved.get(key) or default

        pad = {"padx": 8, "pady": 4}

        # --- ბაზის პარამეტრები ---
        db = ttk.LabelFrame(self, text=tr("sec_db"))
        db.pack(fill="x", **pad)

        # შენახული ბაზების სია: მუდმივი კონფიგი → config.txt (GDBS) → ერთი DEFAULT_GDB
        self._databases = list(saved.get("databases") or DEFAULT_GDBS
                               or ([DEFAULT_GDB] if DEFAULT_GDB else []))

        ttk.Label(db, text=tr("lbl_gdb")).grid(row=0, column=0, sticky="w", padx=6, pady=3)
        self.gdb_var = tk.StringVar(value=initial("gdb", DEFAULT_GDB)
                                    or (self._databases[0] if self._databases else ""))
        # ჩამოსაშლელი — რამდენიმე ბაზას შორის გადართვა (რედაქტირებადი: ახლის ჩაწერაც შეიძლება)
        self.gdb_combo = ttk.Combobox(db, textvariable=self.gdb_var,
                                      values=self._databases, width=68)
        self.gdb_combo.grid(row=0, column=1, sticky="we", padx=6)
        self.gdb_combo.bind("<<ComboboxSelected>>", lambda e: self._on_db_selected())
        ttk.Button(db, text="...", width=3, command=self._browse_gdb).grid(row=0, column=2, padx=4)
        ttk.Button(db, text=tr("btn_read_layers"), command=self._load_layers).grid(row=0, column=3, padx=6)
        ttk.Button(db, text=tr("btn_db_remove"), command=self._remove_db).grid(row=0, column=4, padx=(0, 6))

        ttk.Label(db, text=tr("lbl_layer")).grid(row=1, column=0, sticky="w", padx=6, pady=3)
        self.layer_var = tk.StringVar(value=initial("layer", DEFAULT_LAYER))
        self.layer_combo = ttk.Combobox(db, textvariable=self.layer_var,
                                        values=[self.layer_var.get()], state="readonly", width=30)
        self.layer_combo.grid(row=1, column=1, sticky="w", padx=6)
        self.layer_combo.bind("<<ComboboxSelected>>", lambda e: self._load_fields())

        ttk.Label(db, text=tr("lbl_field")).grid(row=1, column=2, sticky="e", padx=6)
        self.field_var = tk.StringVar(value=initial("field", DEFAULT_FIELD))
        self.field_combo = ttk.Combobox(db, textvariable=self.field_var,
                                        values=[self.field_var.get()], state="readonly", width=22)
        self.field_combo.grid(row=1, column=3, sticky="w", padx=6)

        # --- დამახსოვრება (მუდმივი კონფიგი) ---
        ttk.Button(db, text=tr("btn_remember"), command=self._remember).grid(
            row=2, column=1, sticky="w", padx=6, pady=(2, 4))
        ttk.Label(db, text=tr("cfg_hint"), foreground=self.app.palette["muted"],
                  wraplength=560, justify="left").grid(
            row=3, column=0, columnspan=4, sticky="w", padx=6, pady=(0, 4))

        db.columnconfigure(1, weight=1)

        # --- შეყვანა ---
        inp = ttk.LabelFrame(self, text=tr("sec_codes"))
        inp.pack(fill="both", expand=True, **pad)

        bar = ttk.Frame(inp)
        bar.pack(fill="x", padx=6, pady=4)
        ttk.Label(bar, text=tr("lbl_enter")).pack(side="left")
        ttk.Button(bar, text=tr("btn_load"), command=self._load_file).pack(side="right")
        ttk.Button(bar, text=tr("btn_clear"), command=lambda: self.codes_text.delete("1.0", "end")).pack(side="right", padx=4)

        self.codes_text = scrolledtext.ScrolledText(inp, height=8, font=("Consolas", 10))
        self.codes_text.pack(fill="both", expand=True, padx=6, pady=4)
        if st.get("codes"):
            self.codes_text.insert("1.0", st["codes"])

        # --- გამომავალი ფაილი ---
        out = ttk.LabelFrame(self, text=tr("sec_out"))
        out.pack(fill="x", **pad)
        default_out = os.path.join(os.path.expanduser("~"), "Desktop", "found_parcels.shp")
        self.out_var = tk.StringVar(value=initial("out", default_out))
        ttk.Entry(out, textvariable=self.out_var, width=70).grid(row=0, column=0, sticky="we", padx=6, pady=6)
        ttk.Button(out, text="...", width=3, command=self._browse_out).grid(row=0, column=1, padx=6)
        # ფორმატები — თითოეული ცალკე თოლიით (არცერთი => მხოლოდ ძებნა, ფაილების გარეშე)
        fmt_row = ttk.Frame(out)
        fmt_row.grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 6))
        ttk.Label(fmt_row, text=tr("out_create")).pack(side="left")
        self.shp_var = tk.BooleanVar(value=st.get("shp", True))
        self.gpkg_var = tk.BooleanVar(value=st.get("gpkg", True))
        ttk.Checkbutton(fmt_row, text=tr("chk_shp"), variable=self.shp_var).pack(side="left", padx=(8, 4))
        ttk.Checkbutton(fmt_row, text=tr("chk_gpkg"), variable=self.gpkg_var).pack(side="left")
        out.columnconfigure(0, weight=1)

        # --- ღილაკი ---
        self.search_btn = ttk.Button(self, text=tr("btn_search"), command=self._start_search)
        self.search_btn.pack(fill="x", padx=8, pady=6)

        # --- შედეგები / ლოგი ---
        res = ttk.LabelFrame(self, text=tr("sec_result"))
        res.pack(fill="both", expand=True, **pad)
        self.log_text = scrolledtext.ScrolledText(res, height=10, font=("Consolas", 10), state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=4)
        ttk.Button(res, text=tr("btn_save_nf"), command=self._save_not_found).pack(side="right", padx=6, pady=4)

        self.status = tk.StringVar(value=tr("ready"))
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom")

        self.after(100, self._poll_queue)

        # გაშვებისთანავე — ბაზის ყველა შრის ავტომატური წაკითხვა (popup-ის გარეშე),
        # კონკრეტული შრე/ველი ნაგულისხმევად რჩება.
        if self.gdb_var.get().strip():
            self.after(0, lambda: self._load_layers(silent=True))

    def save_state(self):
        st = self._state()
        st["gdb"] = self.gdb_var.get()
        st["layer"] = self._layer_code(self.layer_var.get())
        st["field"] = self.field_var.get()
        st["out"] = self.out_var.get()
        st["codes"] = self.codes_text.get("1.0", "end").strip()
        if hasattr(self, "shp_var"):
            st["shp"] = self.shp_var.get()
            st["gpkg"] = self.gpkg_var.get()

    def _remember(self):
        """მიმდინარე ბაზის პარამეტრების მუდმივად შენახვა (git-ignored ფაილში).

        მიმდინარე ბაზა ემატება ჩამოსაშლელი სიის (databases) მუდმივ ნაკრებს."""
        gdb = self.gdb_var.get().strip()
        if gdb and gdb not in self._databases:
            self._databases.append(gdb)
            self.gdb_combo["values"] = self._databases
        self.app.set_tool_config(self.tid, {
            "gdb": gdb,
            "layer": self._layer_code(self.layer_var.get().strip()),
            "field": self.field_var.get().strip(),
            "out": self.out_var.get().strip(),
            "databases": self._databases,
        })
        self.save_state()
        messagebox.showinfo(self.tr("saved_title"), self.tr("cfg_saved"))

    def _on_db_selected(self):
        """ჩამოსაშლელიდან ბაზის არჩევისას — ყველა შრის ავტომატური, ჩუმი წაკითხვა
        (popup-ის გარეშე). „Read layers“ ღილაკი კი ცხად შეცდომას აჩვენებს."""
        if self.gdb_var.get().strip():
            self._load_layers(silent=True)

    def _remove_db(self):
        """მიმდინარე ბაზის ამოღება ჩამოსაშლელი სიიდან (მუდმივადაც)."""
        gdb = self.gdb_var.get().strip()
        if gdb not in self._databases:
            return
        if not messagebox.askyesno("GIS_BOX", f"{self.tr('db_remove_q')}\n\n{gdb}"):
            return
        self._databases.remove(gdb)
        self.gdb_combo["values"] = self._databases
        cfg = self.app.get_tool_config(self.tid)
        cfg["databases"] = self._databases
        self.app.set_tool_config(self.tid, cfg)
        self.gdb_var.set(self._databases[0] if self._databases else "")

    # ---- ბაზის დამხმარეები ----
    def _browse_gdb(self):
        p = filedialog.askdirectory(title=self.tr("pick_gdb"))
        if p:
            self.gdb_var.set(p)
            self._load_layers()

    def _load_layers(self, silent=False):
        """ბაზიდან ყველა შრის წაკითხვა ჩამონათვალში. კონკრეტული (კონფიგში
        მითითებული) შრე რჩება ნაგულისხმევად, თუ ბაზაში არსებობს; თუ არა —
        პირველი. silent=True — popup-ების გარეშე (გაშვებისთანავე ავტოწაკითხვა)."""
        gdb = self.gdb_var.get().strip()
        if not os.path.exists(gdb):
            if not silent:
                messagebox.showerror(self.tr("err"), self.tr("err_gdb"))
            return
        try:
            layers = [row[0] for row in pyogrio.list_layers(gdb)]
            if not layers:
                if not silent:
                    messagebox.showwarning(self.tr("empty_title"), self.tr("no_layers"))
                return
            # ჩამონათვალში კოდის გვერდით რეგიონი: „R02 — ქვემო ქართლი“
            displays = [self._layer_display(l) for l in layers]
            self.layer_combo["values"] = displays       # ყველა შრე
            # ნაგულისხმევის შენარჩუნება ნამდვილი სახელით (და არა display-ით)
            cur = self._layer_code(self.layer_var.get())
            match = next((d for d, l in zip(displays, layers) if l == cur), None)
            self.layer_var.set(match or displays[0])
            self._load_fields(silent=silent)
            self._log(self.tr("log_layers", layers=", ".join(displays)))
        except Exception as e:
            if not silent:
                messagebox.showerror(self.tr("err"), str(e))

    _layer_display = staticmethod(layer_display)
    _layer_code = staticmethod(layer_code)

    def _load_fields(self, silent=False):
        gdb = self.gdb_var.get().strip()
        layer = self._layer_code(self.layer_var.get().strip())
        try:
            info = pyogrio.read_info(gdb, layer=layer)
            fields = list(info["fields"])
            self.field_combo["values"] = fields
            self.field_var.set(pick_code_field(fields, self.field_var.get(),
                                               DEFAULT_FIELD))
        except Exception as e:
            if not silent:
                messagebox.showerror(self.tr("err"), str(e))

    # ---- შეყვანის დამხმარეები ----
    def _load_file(self):
        path = filedialog.askopenfilename(
            title=self.tr("pick_file"),
            filetypes=[(self.tr("ft_tables"), "*.csv *.xlsx *.xls"), (self.tr("ft_all"), "*.*")],
        )
        if not path:
            return
        try:
            if path.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(path, dtype=str)
            else:
                df = pd.read_csv(path, dtype=str, sep=None, engine="python")
        except Exception as e:
            messagebox.showerror(self.tr("err"), self.tr("file_read_err", e=e))
            return

        col = self._ask_column(list(df.columns))
        if not col:
            return
        codes = [normalize(v) for v in df[col].tolist() if normalize(v)]
        self.codes_text.delete("1.0", "end")
        self.codes_text.insert("1.0", "\n".join(codes))
        self._log(self.tr("log_loaded", n=len(codes), col=col))

    def _ask_column(self, columns):
        """დიალოგი სვეტის ასარჩევად."""
        dlg = tk.Toplevel(self)
        dlg.title(self.tr("pick_col_title"))
        dlg.geometry("360x140")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        ttk.Label(dlg, text=self.tr("pick_col_q")).pack(padx=12, pady=10)
        var = tk.StringVar(value=columns[0] if columns else "")
        cb = ttk.Combobox(dlg, textvariable=var, values=columns, state="readonly")
        cb.pack(padx=12, pady=6, fill="x")
        result = {"col": None}
        def ok():
            result["col"] = var.get()
            dlg.destroy()
        ttk.Button(dlg, text=self.tr("ok"), command=ok).pack(pady=10)
        self.wait_window(dlg)
        return result["col"]

    def _browse_out(self):
        p = filedialog.asksaveasfilename(
            title=self.tr("out_file_title"),
            defaultextension=".shp",
            filetypes=[("Shapefile", "*.shp"), ("GeoPackage", "*.gpkg")],
        )
        if p:
            self.out_var.set(p)

    # ---- ძებნის გაშვება ----
    def _start_search(self):
        if self.searching:
            return
        gdb = self.gdb_var.get().strip()
        layer = self._layer_code(self.layer_var.get().strip())   # ნამდვილი შრის სახელი
        field = self.field_var.get().strip()
        out_path = self.out_var.get().strip()

        if not os.path.exists(gdb):
            messagebox.showerror(self.tr("err"), self.tr("err_gdb"))
            return
        if not (layer and field):
            messagebox.showerror(self.tr("err"), self.tr("err_layer_field"))
            return
        formats = []
        if self.shp_var.get():
            formats.append("shp")
        if self.gpkg_var.get():
            formats.append("gpkg")
        # გამომავალი გზა საჭიროა მხოლოდ მაშინ, თუ რომელიმე ფაილს ვქმნით
        if formats and not out_path:
            messagebox.showerror(self.tr("err"), self.tr("err_out"))
            return

        codes = parse_manual_codes(self.codes_text.get("1.0", "end"))
        if not codes:
            messagebox.showerror(self.tr("err"), self.tr("err_codes_empty"))
            return

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self.searching = True
        self.search_btn.configure(state="disabled", text=self.tr("btn_search_busy"))
        self.status.set(self.tr("searching"))

        t = threading.Thread(
            target=run_search,
            args=(gdb, layer, field, codes, out_path,
                  lambda m: self.msg_queue.put(("log", m)),
                  lambda r: self.msg_queue.put(("done", r)),
                  self.tr, formats),
            daemon=True,
        )
        t.start()

    # ---- queue / ლოგი ----
    def _poll_queue(self):
        # frame შესაძლოა განადგურდეს ენის/თემის ცვლილებისას — მაშინ ვჩერდებით.
        if not self.winfo_exists():
            return
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "done":
                    self._on_done(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.app.log(msg)  # საერთო ლოგშიც

    def _on_done(self, result):
        self.searching = False
        self.search_btn.configure(state="normal", text=self.tr("btn_search"))

        if "error" in result:
            self.status.set(self.tr("err") + ".")
            self._log(self.tr("done_err_hdr"))
            self._log(result["error"])
            messagebox.showerror(self.tr("err"), result["error"].split("\n")[0])
            return

        found = result["found_list"]
        not_found = result["not_found"]
        self.last_not_found = not_found

        self._log("")
        self._log("=" * 50)
        self._log(self.tr("sum_total", n=len(result['requested'])))
        self._log(self.tr("sum_found", n=len(found)))
        self._log(self.tr("sum_nf", n=len(not_found)))
        if result.get("search_only"):
            self._log(self.tr("sum_search_only"))
        else:
            self._log(self.tr("sum_written", n=result['written']))
            for fp in result.get("out_files", []):
                self._log(self.tr("sum_file", p=fp))
        self._log("=" * 50)

        if not_found:
            self._log("")
            self._log(self.tr("nf_list_hdr"))
            for c in not_found:
                self._log(f"  ✗ {c}")

        self.status.set(self.tr("done_status", f=len(found), nf=len(not_found)))

        # ვერ ნაპოვნის ავტომატური შენახვა shapefile-ის გვერდით
        if not_found and result["out_path"]:
            side = os.path.splitext(result["out_path"])[0] + "_NOT_FOUND.txt"
            try:
                with open(side, "w", encoding="utf-8") as f:
                    f.write("\n".join(not_found))
                self._log(self.tr("nf_saved", p=side))
            except Exception:
                pass

    def _save_not_found(self):
        if not self.last_not_found:
            messagebox.showinfo(self.tr("info"), self.tr("no_nf"))
            return
        p = filedialog.asksaveasfilename(
            title=self.tr("save_nf_title"),
            defaultextension=".txt",
            filetypes=[(self.tr("ft_txt"), "*.txt"), ("CSV", "*.csv")],
        )
        if not p:
            return
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(self.last_not_found))
        messagebox.showinfo(self.tr("saved_title"), self.tr("saved_n", n=len(self.last_not_found)))
