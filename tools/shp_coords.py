# -*- coding: utf-8 -*-
"""წერტილოვანი shapefile-იდან კოორდინატების Excel-ში გატანა და ფორმატირება.

მიეთითება საქაღალდე → იძებნება წერტილოვანი shapefile-ები. ცნობილი სახელის
მსგავსი (Gas_Pipe_Crossing…) ავტომატურად აირჩევა; სხვა შემთხვევაში მომხმარებელი
ირჩევს. UTM ზონა (37/38) ცნობდება .prj-დან (EPSG:32637/32638); თუ ვერ ცნობს —
მომხმარებელი უთითებს. კოორდინატები გაიტანება Excel-ში ორ ბლოკად:

  • A:D — ArcGIS-ის ნედლი ცხრილი (FID, Id, POINT_X, POINT_Y), ხელუხლებელი;
  • E-დან — გასუფთავებული ასლი: არჩევითი ტექსტური „ქუდი“, შემდეგ
    № / X / Y (+ არჩევით „გადაკვეთის კუთხე“ °-ით), ცენტრირებული, all-borders.

მოთხოვნები: geopandas, pyogrio, pyproj, openpyxl.
"""

import os
import re
import glob

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from tools.base import ToolFrame

# ცნობილი სახელის ნიმუშები, რომლებსაც ავტომატურად ვირჩევთ
AUTO_PATTERNS = ("gas_pipe_crossing", "gas_pipe_protzone_crossing", "crossing")

# ნაგულისხმევი ტექსტური შაბლონები („ქუდები“)
DEFAULT_TEMPLATES = [
    "nakveTis da dacvis zonis sazRvris kveTis koordinatebi",
    "ნაკვეთის და დაცვის ზონის საზღვრის კვეთის კოორდინატები",
]

# ---- განლაგების მუდმივები (მაგალითის მიხედვით) ----------------------------
# ნედლი ბლოკი A:D. ასლი იწყება G-დან — 2 ცარიელი სვეტი (E, F) დაშორებით,
# რომ დაკოპირებისას ორიგინალს არ დაედოს.
COPY_COL = 7        # G
TITLE_ROW = 6       # ტექსტური ქუდი (იწყება აქედან)
TITLE_ROWS = 3      # ქუდი = 3 რიგის სიმაღლის merge & center ბლოკი
HEADER_ROW_NO_TITLE = 6
TITLE_FONT = "Sylfaen"   # ქუდის ფონტი დეფოლტად
ANGLE_FMT = '0"°"'   # კუთხის სვეტის ფორმატი — მთელი რიცხვი + გრადუსი (წერტილის გარეშე)


RTR = {
    "heading":   {"en": "Shapefile → coordinates (Excel)",
                  "ka": "Shapefile → კოორდინატები (Excel)"},
    "desc":      {"en": "Pick a folder, choose a point shapefile, and export its "
                        "coordinates to a formatted Excel file.",
                  "ka": "მიუთითე საქაღალდე, აირჩიე წერტილოვანი shapefile და გაიტანე "
                        "მისი კოორდინატები დაფორმატებულ Excel ფაილში."},
    "folder":    {"en": "Folder:", "ka": "საქაღალდე:"},
    "browse":    {"en": "Browse…", "ka": "დათვალიერება…"},
    "shp":       {"en": "Point shapefile:", "ka": "წერტილოვანი shapefile:"},
    "rescan":    {"en": "Rescan", "ka": "თავიდან სკანირება"},
    "zone":      {"en": "UTM zone:", "ka": "UTM ზონა:"},
    "zone_auto": {"en": "auto ({z})", "ka": "ავტომატური ({z})"},
    "zone_unknown": {"en": "not detected", "ka": "ვერ ცნობა"},
    "vtype":     {"en": "Values:", "ka": "მნიშვნელობები:"},
    "v_int":     {"en": "Integer", "ka": "მთელი (integer)"},
    "v_dbl":     {"en": "Decimal (double)", "ka": "ათწილადი (double)"},
    "tmpl":      {"en": "Header template:", "ka": "ტექსტური ქუდი:"},
    "tmpl_none": {"en": "(none)", "ka": "(არცერთი)"},
    "tmpl_add":  {"en": "➕ Add…", "ka": "➕ დამატება…"},
    "tmpl_add_q":{"en": "New header template text:", "ka": "ახალი ქუდის ტექსტი:"},
    "tmpl_del":  {"en": "🗑 Delete", "ka": "🗑 წაშლა"},
    "tmpl_del_q":{"en": "Delete this header template?",
                  "ka": "წავშალო ეს ტექსტური ქუდი?"},
    "angle":     {"en": "Add “crossing angle” column (°)",
                  "ka": "„გადაკვეთის კუთხე“ სვეტი (°)"},
    "angle_hdr": {"en": "gadakveTis kuTxe", "ka": "გადაკვეთის კუთხე"},
    "angle_all": {"en": "same angle for all (optional):",
                  "ka": "ერთი კუთხე ყველასთვის (არჩევით):"},
    "export":    {"en": "Export & format (Excel)", "ka": "ექსპორტი და ფორმატირება (Excel)"},
    "apply_deg": {"en": "Add ° to angle column…", "ka": "° დაუმატე კუთხის სვეტს…"},
    "pick_xlsx": {"en": "Choose the Excel file", "ka": "აირჩიე Excel ფაილი"},
    "deg_done":  {"en": "° applied to {n} angle cell(s).",
                  "ka": "° დაემატა {n} კუთხის უჯრას."},
    "deg_nocol": {"en": "No “crossing angle” column found in the file.",
                  "ka": "ფაილში „გადაკვეთის კუთხე“ სვეტი ვერ მოიძებნა."},
    "no_folder": {"en": "Specify a valid folder.", "ka": "მიუთითე არსებული საქაღალდე."},
    "no_shp":    {"en": "No point shapefiles found in the folder.",
                  "ka": "საქაღალდეში წერტილოვანი shapefile ვერ მოიძებნა."},
    "pick_shp":  {"en": "Choose a point shapefile first.",
                  "ka": "ჯერ აირჩიე წერტილოვანი shapefile."},
    "need_zone": {"en": "Could not detect the UTM zone — please choose 37 or 38.",
                  "ka": "UTM ზონა ვერ ცნობა — აირჩიე 37 ან 38."},
    "no_points": {"en": "The shapefile has no points.",
                  "ka": "shapefile-ში წერტილები არ არის."},
    "found_shp": {"en": "Found {n} point shapefile(s).",
                  "ka": "ნაპოვნია {n} წერტილოვანი shapefile."},
    "detected":  {"en": "Selected: {name} | zone {z} | {n} point(s).",
                  "ka": "არჩეულია: {name} | ზონა {z} | {n} წერტილი."},
    "done":      {"en": "Exported {n} points → {path}",
                  "ka": "გაიტანა {n} წერტილი → {path}"},
    "save_title":{"en": "Save Excel", "ka": "Excel-ის შენახვა"},
    "err":       {"en": "Error", "ka": "შეცდომა"},
    "load_err":  {"en": "Could not read the shapefile:",
                  "ka": "shapefile ვერ წაიკითხა:"},
}


class ShpCoordsTool(ToolFrame):
    tid = "shp_coords"

    def tr(self, key, **fmt):
        entry = RTR.get(key, {})
        s = entry.get(self.app.lang) or entry.get("en") or key
        return s.format(**fmt) if fmt else s

    def _state(self):
        return self.app.tool_state.setdefault(self.tid, {})

    # ---- შენახული ტექსტური შაბლონები ----
    def _templates(self):
        saved = self.app.get_tool_config(self.tid)
        tmpls = saved.get("templates")
        if not tmpls:
            tmpls = list(DEFAULT_TEMPLATES)
        return tmpls

    def build(self):
        pal = self.app.palette
        st = self._state()
        saved = self.app.get_tool_config(self.tid)
        self._shp_map = {}         # basename -> full path
        self._detected_zone = None

        ttk.Label(self, text=self.tr("heading"),
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(self, text=self.tr("desc"), foreground=pal["muted"],
                  wraplength=620, justify="left").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # საქაღალდე
        ttk.Label(self, text=self.tr("folder")).grid(row=2, column=0, sticky="w")
        self.folder_var = tk.StringVar(value=st.get("folder") or saved.get("folder") or "")
        ttk.Entry(self, textvariable=self.folder_var).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        ttk.Button(self, text=self.tr("browse"), command=self._pick_folder).grid(
            row=3, column=2, sticky="ew", padx=(8, 0), pady=(2, 8))

        # shapefile არჩევა
        ttk.Label(self, text=self.tr("shp")).grid(row=4, column=0, sticky="w")
        self.shp_var = tk.StringVar()
        self.shp_combo = ttk.Combobox(self, textvariable=self.shp_var,
                                      state="readonly")
        self.shp_combo.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        self.shp_combo.bind("<<ComboboxSelected>>", lambda e: self._on_shp_selected())
        ttk.Button(self, text=self.tr("rescan"), command=self._scan).grid(
            row=5, column=2, sticky="ew", padx=(8, 0), pady=(2, 8))

        # UTM ზონა
        zrow = ttk.Frame(self)
        zrow.grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(zrow, text=self.tr("zone")).pack(side="left")
        self.zone_var = tk.StringVar(value=st.get("zone", "auto"))
        self.zone_auto_rb = ttk.Radiobutton(zrow, text=self.tr("zone_auto", z="—"),
                                            variable=self.zone_var, value="auto")
        self.zone_auto_rb.pack(side="left", padx=(6, 8))
        ttk.Radiobutton(zrow, text="37", variable=self.zone_var, value="37").pack(side="left")
        ttk.Radiobutton(zrow, text="38", variable=self.zone_var, value="38").pack(side="left", padx=(6, 0))

        # მნიშვნელობის ტიპი
        vrow = ttk.Frame(self)
        vrow.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(vrow, text=self.tr("vtype")).pack(side="left")
        self.vtype_var = tk.StringVar(value=st.get("vtype", "double"))
        ttk.Radiobutton(vrow, text=self.tr("v_dbl"), variable=self.vtype_var,
                        value="double").pack(side="left", padx=(6, 8))
        ttk.Radiobutton(vrow, text=self.tr("v_int"), variable=self.vtype_var,
                        value="int").pack(side="left")

        # ტექსტური ქუდი
        trow = ttk.Frame(self)
        trow.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        ttk.Label(trow, text=self.tr("tmpl")).pack(side="left")
        self.tmpl_var = tk.StringVar(value=st.get("template", self.tr("tmpl_none")))
        self.tmpl_combo = ttk.Combobox(trow, textvariable=self.tmpl_var, width=48)
        self.tmpl_combo.pack(side="left", fill="x", expand=True, padx=(6, 6))
        self._refresh_templates()
        ttk.Button(trow, text=self.tr("tmpl_add"), command=self._add_template).pack(side="left")
        ttk.Button(trow, text=self.tr("tmpl_del"), command=self._delete_template).pack(
            side="left", padx=(4, 0))

        # გადაკვეთის კუთხე
        arow = ttk.Frame(self)
        arow.grid(row=9, column=0, columnspan=3, sticky="w", pady=(0, 10))
        self.angle_var = tk.BooleanVar(value=st.get("angle", False))
        ttk.Checkbutton(arow, text=self.tr("angle"), variable=self.angle_var).pack(side="left")
        ttk.Label(arow, text=self.tr("angle_all")).pack(side="left", padx=(14, 4))
        self.angle_all_var = tk.StringVar(value=st.get("angle_all", ""))
        ttk.Entry(arow, textvariable=self.angle_all_var, width=8).pack(side="left")

        actions = ttk.Frame(self)
        actions.grid(row=10, column=0, columnspan=3, sticky="w")
        ttk.Button(actions, text=self.tr("export"), command=self._export).pack(side="left")
        ttk.Button(actions, text=self.tr("apply_deg"), command=self._apply_degree).pack(
            side="left", padx=(12, 0))

        self.columnconfigure(0, weight=1)

        if self.folder_var.get():
            self._scan()

    def save_state(self):
        st = self._state()
        st["folder"] = self.folder_var.get()
        st["zone"] = self.zone_var.get()
        st["vtype"] = self.vtype_var.get()
        st["template"] = self.tmpl_var.get()
        st["angle"] = self.angle_var.get()
        st["angle_all"] = self.angle_all_var.get()

    # ---- შაბლონები ----
    def _refresh_templates(self):
        vals = [self.tr("tmpl_none")] + self._templates()
        self.tmpl_combo["values"] = vals
        if self.tmpl_var.get() not in vals:
            self.tmpl_var.set(vals[0])

    def _add_template(self):
        txt = simpledialog.askstring("GIS_BOX", self.tr("tmpl_add_q"), parent=self)
        if not txt:
            return
        tmpls = self._templates()
        if txt not in tmpls:
            tmpls.append(txt)
        cfg = self.app.get_tool_config(self.tid)
        cfg["templates"] = tmpls
        self.app.set_tool_config(self.tid, cfg)
        self._refresh_templates()
        self.tmpl_var.set(txt)

    def _delete_template(self):
        cur = self.tmpl_var.get()
        if not cur or cur == self.tr("tmpl_none"):
            return
        tmpls = self._templates()
        if cur not in tmpls:
            return
        if not messagebox.askyesno("GIS_BOX",
                                   f"{self.tr('tmpl_del_q')}\n\n{cur}"):
            return
        tmpls.remove(cur)
        cfg = self.app.get_tool_config(self.tid)
        cfg["templates"] = tmpls
        self.app.set_tool_config(self.tid, cfg)
        self._refresh_templates()
        self.tmpl_var.set(self.tr("tmpl_none"))

    # ---- საქაღალდე / სკანირება ----
    def _pick_folder(self):
        d = filedialog.askdirectory(title=self.tr("folder"),
                                    initialdir=self.folder_var.get() or None)
        if d:
            self.folder_var.set(os.path.normpath(d))
            cfg = self.app.get_tool_config(self.tid)
            cfg["folder"] = os.path.normpath(d)
            self.app.set_tool_config(self.tid, cfg)
            self._scan()

    def _scan(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("GIS_BOX", self.tr("no_folder"))
            return
        import pyogrio
        self._shp_map = {}
        for shp in sorted(glob.glob(os.path.join(folder, "*.shp"))):
            try:
                info = pyogrio.read_info(shp)
            except Exception:
                continue
            if "Point" in str(info.get("geometry_type") or ""):
                self._shp_map[os.path.basename(shp)] = shp
        names = list(self._shp_map)
        self.shp_combo["values"] = names
        if not names:
            self.shp_var.set("")
            self.app.log("— " + self.tr("no_shp"))
            messagebox.showinfo("GIS_BOX", self.tr("no_shp"))
            return
        self.app.log("— " + self.tr("found_shp", n=len(names)))
        # ავტომატური არჩევა: ცნობილი ნიმუშის მსგავსი, თუ არა — პირველი
        auto = next((n for n in names
                     if any(p in n.lower() for p in AUTO_PATTERNS)), None)
        self.shp_var.set(auto or names[0])
        self._on_shp_selected()

    def _on_shp_selected(self):
        shp = self._shp_map.get(self.shp_var.get())
        if not shp:
            return
        self._detected_zone = self._detect_zone(shp)
        z = self._detected_zone
        self.zone_auto_rb.config(
            text=self.tr("zone_auto", z=(z if z else self.tr("zone_unknown"))))
        # თუ ავტორეჟიმია და ზონა ვერ ცნო — მომხმარებელს ვთხოვთ არჩევას
        n = self._count_points(shp)
        self.app.log(self.tr("detected", name=self.shp_var.get(),
                             z=(z or "?"), n=n))

    # ---- shapefile-ის კითხვა ----
    @staticmethod
    def _detect_zone(shp):
        try:
            import pyogrio, pyproj
            crs = pyogrio.read_info(shp).get("crs")
            if not crs:
                return None
            uz = pyproj.CRS.from_user_input(crs).utm_zone   # მაგ. '37N'
            if uz:
                m = re.match(r"(\d+)", uz)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return None

    @staticmethod
    def _count_points(shp):
        try:
            import pyogrio
            return int(pyogrio.read_info(shp).get("features") or 0)
        except Exception:
            return 0

    def _read_points(self, shp, zone):
        """დააბრუნებს [(id, x, y), …] მითითებული ზონის კოორდინატებში."""
        import geopandas as gpd
        gdf = gpd.read_file(shp)
        if gdf.crs is not None:
            try:
                gdf = gdf.to_crs(epsg=32600 + zone)
            except Exception:
                pass
        idcol = next((c for c in gdf.columns if c.lower() == "id"), None)
        pts = []
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            if geom.geom_type == "Point":
                coords = [(geom.x, geom.y)]
            elif geom.geom_type == "MultiPoint":
                coords = [(p.x, p.y) for p in geom.geoms]
            else:
                c = geom.centroid
                coords = [(c.x, c.y)]
            idv = row[idcol] if idcol is not None else 0
            for x, y in coords:
                pts.append((idv, x, y))
        return pts

    # ---- ექსპორტი ----
    def _export(self):
        shp = self._shp_map.get(self.shp_var.get())
        if not shp:
            messagebox.showwarning("GIS_BOX", self.tr("pick_shp"))
            return
        # ზონა
        if self.zone_var.get() == "auto":
            zone = self._detected_zone
        else:
            zone = int(self.zone_var.get())
        if zone not in (37, 38):
            messagebox.showwarning("GIS_BOX", self.tr("need_zone"))
            return

        try:
            points = self._read_points(shp, zone)
        except Exception as e:
            messagebox.showerror(self.tr("err"), f"{self.tr('load_err')}\n{e}")
            return
        if not points:
            messagebox.showwarning("GIS_BOX", self.tr("no_points"))
            return

        base = os.path.splitext(os.path.basename(shp))[0]
        path = filedialog.asksaveasfilename(
            title=self.tr("save_title"), defaultextension=".xlsx",
            initialfile=base + ".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return

        template = self.tmpl_var.get()
        if template == self.tr("tmpl_none"):
            template = ""
        angle_all = None
        raw = self.angle_all_var.get().strip().replace(",", ".")
        if self.angle_var.get() and raw:
            try:
                angle_all = float(raw)
                if angle_all.is_integer():
                    angle_all = int(angle_all)
            except ValueError:
                angle_all = None

        try:
            self._write_workbook(
                path, sheet_name=os.path.basename(shp), points=points,
                value_type=self.vtype_var.get(), template=template,
                angle_on=self.angle_var.get(), angle_all=angle_all)
        except Exception as e:
            messagebox.showerror(self.tr("err"), str(e))
            return

        self._last_xlsx = path
        msg = self.tr("done", n=len(points), path=path)
        self.app.log("— " + msg)
        messagebox.showinfo("GIS_BOX", msg)

    # ---- ° დამატება არსებულ ფაილში (რიცხვების ჩაწერის შემდეგ) ----
    def _apply_degree(self):
        """გახსნის Excel-ს, იპოვის „გადაკვეთის კუთხე“ სვეტს და ყველა მის
        (რიცხვით) უჯრას მიანიჭებს ° ფორმატს — ე.ი. მომხმარებელი ჯერ ჩაწერს
        რიცხვებს, მერე ერთი ღილაკით ყველას დაუმატებს გრადუსს."""
        from openpyxl import load_workbook

        initial = getattr(self, "_last_xlsx", "") or ""
        path = filedialog.askopenfilename(
            title=self.tr("pick_xlsx"),
            initialdir=os.path.dirname(initial) or None,
            initialfile=os.path.basename(initial),
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            wb = load_workbook(path)
        except Exception as e:
            messagebox.showerror(self.tr("err"), str(e))
            return

        targets = {"გადაკვეთის კუთხე", "gadakvetis kutxe", "gadakveTis kuTxe"}
        n = 0
        for ws in wb.worksheets:
            # ვიპოვოთ სათაურის უჯრა („…კუთხე“ / „…kuTxe“)
            hdr = None
            for row in ws.iter_rows():
                for cell in row:
                    v = cell.value
                    if isinstance(v, str) and (v.strip() in targets
                                               or "კუთხე" in v or "kutxe" in v.lower()):
                        hdr = cell
                        break
                if hdr:
                    break
            if not hdr:
                continue
            for r in range(hdr.row + 1, ws.max_row + 1):
                cell = ws.cell(row=r, column=hdr.column)
                left = ws.cell(row=r, column=hdr.column - 1).value   # Y სვეტი
                if cell.value is None and left is None:
                    continue
                # ტექსტად ჩაწერილი რიცხვი → რიცხვად
                if isinstance(cell.value, str):
                    s = cell.value.strip().replace("°", "").replace(",", ".")
                    try:
                        f = float(s)
                        cell.value = int(f) if f.is_integer() else f
                    except ValueError:
                        pass
                cell.number_format = ANGLE_FMT
                n += 1
        try:
            wb.save(path)
        except Exception as e:
            messagebox.showerror(self.tr("err"), str(e))
            return
        if n == 0:
            messagebox.showinfo("GIS_BOX", self.tr("deg_nocol"))
            return
        self._last_xlsx = path
        msg = self.tr("deg_done", n=n)
        self.app.log("— " + msg)
        messagebox.showinfo("GIS_BOX", msg)

    def _write_workbook(self, path, sheet_name, points, value_type,
                        template, angle_on, angle_all):
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, Border, Side
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = (sheet_name[:31] or "Coordinates")

        bold = Font(bold=True)
        hcenter = Alignment(horizontal="center")
        center = Alignment(horizontal="center", vertical="center")
        wrap = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin = Side(style="thin", color="000000")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # --- ნედლი ბლოკი A:D (FID, Id, POINT_X, POINT_Y) — ხელუხლებელი ---
        for c, name in enumerate(["FID", "Id", "POINT_X", "POINT_Y"], 1):
            cell = ws.cell(row=1, column=c, value=name)
            cell.font = bold
            cell.alignment = hcenter
        for i, (idv, x, y) in enumerate(points):
            ws.cell(row=2 + i, column=1, value=i)                       # FID
            ws.cell(row=2 + i, column=2, value=(idv if idv is not None else 0))
            ws.cell(row=2 + i, column=3, value=float(x))               # სრული სიზუსტე
            ws.cell(row=2 + i, column=4, value=float(y))

        # --- გასუფთავებული ასლი E-დან ---
        col = COPY_COL
        ncols = 4 if angle_on else 3
        # ასლის სვეტების სიგანე (გამოიყენება ქუდის სიმაღლის დასათვლელადაც).
        # „გადაკვეთის კუთხე“ — უფრო ფართო, რომ სათაური კომფორტულად ჩაჯდეს.
        copy_widths = [max(4, len(str(len(points)))) + 2, 14, 14] + ([22] if angle_on else [])

        if template:
            # ქუდი — 3 რიგის სიმაღლის, სვეტების სიგანის merge & center ბლოკი,
            # wrap text-ით, Sylfaen ფონტით და all-borders-ით.
            end_row = TITLE_ROW + TITLE_ROWS - 1
            end_col = col + ncols - 1
            ws.merge_cells(start_row=TITLE_ROW, start_column=col,
                           end_row=end_row, end_column=end_col)
            t = ws.cell(row=TITLE_ROW, column=col, value=template)
            t.font = Font(name=TITLE_FONT, bold=True, size=11)
            t.alignment = wrap
            # all borders — merge-ის შემდეგ დიაპაზონის იტერაციით (openpyxl სწორად
            # ინახავს გარე ჩარჩოს კიდეებს; შიდა ხაზები merge-ში ისედაც არ ჩანს).
            for rr in range(TITLE_ROW, end_row + 1):
                for cc in range(col, end_col + 1):
                    ws.cell(row=rr, column=cc).border = border
            # რიგის სიმაღლე ტექსტის საჭიროებისამებრ — რომ ნორმალურად ჩაჯდეს
            self._fit_title_rows(ws, template, TITLE_ROW, TITLE_ROWS,
                                 sum(copy_widths))
            header_row = TITLE_ROW + TITLE_ROWS      # 6 + 3 = 9
        else:
            header_row = HEADER_ROW_NO_TITLE

        headers = ["№", "X", "Y"] + ([self.tr("angle_hdr")] if angle_on else [])
        for j, name in enumerate(headers):
            cell = ws.cell(row=header_row, column=col + j, value=name)
            cell.font = bold
            cell.alignment = center
            cell.border = border

        for i, (idv, x, y) in enumerate(points, 1):
            r = header_row + i
            xv = int(round(x)) if value_type == "int" else float(x)
            yv = int(round(y)) if value_type == "int" else float(y)
            for j, val in enumerate((i, xv, yv)):
                cell = ws.cell(row=r, column=col + j, value=val)
                cell.alignment = center
                cell.border = border
            if angle_on:
                cell = ws.cell(row=r, column=col + 3, value=angle_all)
                cell.alignment = center
                cell.border = border
                cell.number_format = ANGLE_FMT          # რიცხვს გრადუსით აჩვენებს

        # --- სვეტების სიგანე ---
        for c in range(1, 5):
            ws.column_dimensions[get_column_letter(c)].width = 14
        for j, w in enumerate(copy_widths):
            ws.column_dimensions[get_column_letter(col + j)].width = w

        ws.freeze_panes = "A2"
        wb.save(path)

    @staticmethod
    def _fit_title_rows(ws, text, first_row, n_rows, total_width_chars):
        """ქუდის რიგების სიმაღლე ტექსტის სიგრძის მიხედვით — რომ wrap-ული
        ტექსტი merge-ბლოკში ნორმალურად ჩაჯდეს (merge-ს Excel ავტომატურად
        არ უსწორებს სიმაღლეს)."""
        import math
        per_line = max(10, int(total_width_chars) - 2)     # დაახლ. სიმბოლო/ხაზზე
        lines = max(1, math.ceil(len(str(text)) / per_line))
        needed = lines * 15.0 + 8                           # საჭირო სიმაღლე (pt)
        per_row = max(16.0, needed / n_rows)
        for r in range(first_row, first_row + n_rows):
            ws.row_dimensions[r].height = per_row
