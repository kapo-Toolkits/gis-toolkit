# -*- coding: utf-8 -*-
"""GDB/MDB → PostGIS — GIS_BOX-ის ხელსაწყო (tkinter UI ძრავ core-ზე).

ESRI File/Personal Geodatabase-ის (`.gdb`/`.mdb`) შრეებს ატანს PostgreSQL/
PostGIS-ში `ogr2ogr`-ით. ძრავა (`tools.gdb2postgis_core`) GUI-სგან თავისუფალია
და აღებულია დამოუკიდებელი gdb2postgis პროექტიდან (MIT).

მოთხოვნა (runtime): GDAL-ის `ogr2ogr`/`ogrinfo` (მაგ. QGIS / OSGeo4W) და
PostgreSQL/PostGIS ბაზა. კავშირის პარამეტრები ინახება ლოკალურ, git-ignored
პარამეტრებში; პაროლი ნაგულისხმევად მხოლოდ სესიაშია (არ ინახება).
"""

import os
import queue
import threading

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from tools.base import ToolFrame
from tools import gdb2postgis_core as core


CATALOG = {
    "heading":  {"en": "GDB/MDB → PostGIS", "ka": "GDB/MDB → PostGIS"},
    "desc":     {"en": "Load Geodatabase (.gdb/.mdb) layers into PostgreSQL/PostGIS "
                       "with ogr2ogr. Needs GDAL (QGIS/OSGeo4W) and a PostGIS database.",
                 "ka": "Geodatabase-ის (.gdb/.mdb) შრეების ატანა PostgreSQL/PostGIS-ში "
                       "ogr2ogr-ით. სჭირდება GDAL (QGIS/OSGeo4W) და PostGIS ბაზა."},
    "gdal":     {"en": "GDAL (ogr2ogr):", "ka": "GDAL (ogr2ogr):"},
    "gdal_ok":  {"en": "found — {v}", "ka": "ნაპოვნია — {v}"},
    "gdal_missing": {"en": "not found — set the ogr2ogr path",
                     "ka": "ვერ მოიძებნა — მიუთითე ogr2ogr-ის გზა"},
    "source_dir": {"en": "Source folder:", "ka": "წყარო საქაღალდე:"},
    "browse":   {"en": "Browse…", "ka": "დათვალიერება…"},
    "source":   {"en": "Source (.gdb/.mdb):", "ka": "წყარო (.gdb/.mdb):"},
    "no_sources": {"en": "No .gdb/.mdb found in the folder.",
                   "ka": "საქაღალდეში .gdb/.mdb ვერ მოიძებნა."},
    "layers":   {"en": "Layers (select to import):",
                 "ka": "შრეები (მონიშნე ასატანი):"},
    "sel_all":  {"en": "Select all", "ka": "ყველა"},
    "sel_none": {"en": "None", "ka": "არცერთი"},
    "conn":     {"en": "PostGIS connection", "ka": "PostGIS კავშირი"},
    "host":     {"en": "Host", "ka": "ჰოსტი"},
    "port":     {"en": "Port", "ka": "პორტი"},
    "dbname":   {"en": "Database", "ka": "ბაზა"},
    "user":     {"en": "User", "ka": "მომხმარებელი"},
    "password": {"en": "Password", "ka": "პაროლი"},
    "schema":   {"en": "Schema", "ka": "სქემა"},
    "remember_pw": {"en": "remember password (local)", "ka": "პაროლის დამახსოვრება (ლოკალურად)"},
    "test_conn":{"en": "Test connection", "ka": "კავშირის შემოწმება"},
    "conn_ok":  {"en": "Connection OK.", "ka": "კავშირი წარმატებულია."},
    "conn_fail":{"en": "Connection failed:", "ka": "კავშირი ვერ დამყარდა:"},
    "opts":     {"en": "Options", "ka": "პარამეტრები"},
    "mode":     {"en": "Mode", "ka": "რეჟიმი"},
    "reproj":   {"en": "Reproject (e.g. EPSG:4326)", "ka": "რეპროექცია (მაგ. EPSG:4326)"},
    "prefix":   {"en": "Table prefix", "ka": "ცხრილის პრეფიქსი"},
    "promote":  {"en": "Promote to multi", "ka": "Promote to multi"},
    "gist":     {"en": "Spatial index (GiST)", "ka": "სივრცული ინდექსი (GiST)"},
    "copy":     {"en": "Fast COPY", "ka": "სწრაფი COPY"},
    "import":   {"en": "▶ Import", "ka": "▶ იმპორტი"},
    "cancel":   {"en": "✖ Cancel", "ka": "✖ გაუქმება"},
    "remember": {"en": "💾 Remember settings", "ka": "💾 პარამეტრების დამახსოვრება"},
    "saved":    {"en": "Settings saved (password not stored unless ticked).",
                 "ka": "პარამეტრები შენახულია (პაროლი მხოლოდ თოლიის მონიშვნისას)."},
    "warn_gdal":{"en": "ogr2ogr / ogrinfo not found. Set a valid GDAL path.",
                 "ka": "ogr2ogr / ogrinfo ვერ მოიძებნა. მიუთითე GDAL-ის გზა."},
    "warn_source": {"en": "Choose a source (.gdb/.mdb).", "ka": "აირჩიე წყარო (.gdb/.mdb)."},
    "warn_layers": {"en": "Select at least one layer.", "ka": "მონიშნე მინიმუმ ერთი შრე."},
    "running":  {"en": "Importing…", "ka": "მიმდინარეობს იმპორტი…"},
    "done":     {"en": "Done — OK {ok}, failed {fail}.", "ka": "დასრულდა — OK {ok}, ჩავარდა {fail}."},
    "cancelled":{"en": "Cancelled.", "ka": "გაუქმდა."},
}


class Gdb2PostgisTool(ToolFrame):
    tid = "gdb2postgis"
    CATALOG = CATALOG

    def _state(self):
        return self.app.tool_state.setdefault(self.tid, {})

    def build(self):
        pal = self.app.palette
        saved = self.app.get_tool_config(self.tid)
        self.msg_queue = queue.Queue()
        self.running = False
        self._cancel_event = threading.Event()
        self._sources = {}                 # basename -> full path

        def cfg(key, default=""):
            return saved.get(key, default)

        ttk.Label(self, text=self.tr("heading"),
                  font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(self, text=self.tr("desc"), foreground=pal["muted"],
                  wraplength=680, justify="left").grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # --- GDAL ---
        ttk.Label(self, text=self.tr("gdal")).grid(row=2, column=0, sticky="w")
        self.ogr2ogr_var = tk.StringVar(value=cfg("ogr2ogr"))
        ttk.Entry(self, textvariable=self.ogr2ogr_var).grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=6)
        ttk.Button(self, text=self.tr("browse"), command=self._pick_ogr).grid(row=2, column=3, sticky="ew")
        self.gdal_status = ttk.Label(self, text="", foreground=pal["muted"])
        self.gdal_status.grid(row=3, column=1, columnspan=3, sticky="w", pady=(0, 8))

        # --- Source ---
        ttk.Label(self, text=self.tr("source_dir")).grid(row=4, column=0, sticky="w")
        self.dir_var = tk.StringVar(value=cfg("source_dir"))
        ttk.Entry(self, textvariable=self.dir_var).grid(row=4, column=1, columnspan=2, sticky="ew", padx=6)
        ttk.Button(self, text=self.tr("browse"), command=self._pick_dir).grid(row=4, column=3, sticky="ew")

        ttk.Label(self, text=self.tr("source")).grid(row=5, column=0, sticky="w", pady=(6, 0))
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(self, textvariable=self.source_var, state="readonly")
        self.source_combo.grid(row=5, column=1, columnspan=3, sticky="ew", padx=6, pady=(6, 0))
        self.source_combo.bind("<<ComboboxSelected>>", lambda e: self._load_layers())

        # --- Layers ---
        lay = ttk.Frame(self)
        lay.grid(row=6, column=0, columnspan=4, sticky="nsew", pady=(8, 8))
        ttk.Label(lay, text=self.tr("layers")).pack(anchor="w")
        box = ttk.Frame(lay)
        box.pack(fill="both", expand=True)
        self.layers_list = tk.Listbox(box, selectmode="extended", height=6,
                                      bg=pal["field_bg"], fg=pal["field_fg"],
                                      exportselection=False)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.layers_list.yview)
        self.layers_list.configure(yscrollcommand=sb.set)
        self.layers_list.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        selbtns = ttk.Frame(lay)
        selbtns.pack(anchor="w", pady=(4, 0))
        ttk.Button(selbtns, text=self.tr("sel_all"),
                   command=lambda: self.layers_list.selection_set(0, "end")).pack(side="left")
        ttk.Button(selbtns, text=self.tr("sel_none"),
                   command=lambda: self.layers_list.selection_clear(0, "end")).pack(side="left", padx=(4, 0))

        # --- PostGIS connection ---
        conn = ttk.LabelFrame(self, text=self.tr("conn"), padding=8)
        conn.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        self.host_var = tk.StringVar(value=cfg("host", "localhost"))
        self.port_var = tk.StringVar(value=str(cfg("port", "5432")))
        self.db_var = tk.StringVar(value=cfg("dbname", "postgis"))
        self.user_var = tk.StringVar(value=cfg("user", "postgres"))
        self.pw_var = tk.StringVar(value=cfg("password", ""))
        self.schema_var = tk.StringVar(value=cfg("schema", "public"))
        grid = [("host", self.host_var, 0, 0, 16), ("port", self.port_var, 0, 2, 8),
                ("dbname", self.db_var, 1, 0, 16), ("schema", self.schema_var, 1, 2, 12),
                ("user", self.user_var, 2, 0, 16)]
        for key, var, r, c, w in grid:
            ttk.Label(conn, text=self.tr(key)).grid(row=r, column=c, sticky="w", padx=4, pady=2)
            ttk.Entry(conn, textvariable=var, width=w).grid(row=r, column=c + 1, sticky="w", padx=4)
        ttk.Label(conn, text=self.tr("password")).grid(row=2, column=2, sticky="w", padx=4)
        ttk.Entry(conn, textvariable=self.pw_var, show="•", width=16).grid(row=2, column=3, sticky="w", padx=4)
        self.remember_pw = tk.BooleanVar(value=bool(cfg("password")))
        ttk.Checkbutton(conn, text=self.tr("remember_pw"), variable=self.remember_pw).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 0))
        ttk.Button(conn, text=self.tr("test_conn"), command=self._test_conn).grid(
            row=3, column=2, columnspan=2, sticky="e", padx=4, pady=(4, 0))

        # --- Options ---
        opts = ttk.LabelFrame(self, text=self.tr("opts"), padding=8)
        opts.grid(row=8, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        ttk.Label(opts, text=self.tr("mode")).grid(row=0, column=0, sticky="w", padx=4)
        self.mode_var = tk.StringVar(value=cfg("mode", "overwrite"))
        ttk.Combobox(opts, textvariable=self.mode_var, state="readonly", width=12,
                     values=["overwrite", "append", "update"]).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(opts, text=self.tr("reproj")).grid(row=0, column=2, sticky="w", padx=4)
        self.tsrs_var = tk.StringVar(value=cfg("t_srs", ""))
        ttk.Entry(opts, textvariable=self.tsrs_var, width=14).grid(row=0, column=3, sticky="w", padx=4)
        ttk.Label(opts, text=self.tr("prefix")).grid(row=1, column=0, sticky="w", padx=4, pady=(4, 0))
        self.prefix_var = tk.StringVar(value=cfg("prefix", ""))
        ttk.Entry(opts, textvariable=self.prefix_var, width=14).grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))
        self.promote_var = tk.BooleanVar(value=cfg("promote", True))
        self.gist_var = tk.BooleanVar(value=cfg("gist", True))
        self.copy_var = tk.BooleanVar(value=cfg("copy", True))
        ttk.Checkbutton(opts, text=self.tr("promote"), variable=self.promote_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=4)
        ttk.Checkbutton(opts, text=self.tr("gist"), variable=self.gist_var).grid(row=2, column=2, sticky="w", padx=4)
        ttk.Checkbutton(opts, text=self.tr("copy"), variable=self.copy_var).grid(row=2, column=3, sticky="w", padx=4)

        # --- Actions ---
        act = ttk.Frame(self)
        act.grid(row=9, column=0, columnspan=4, sticky="ew")
        self.import_btn = ttk.Button(act, text=self.tr("import"), command=self._start_import)
        self.import_btn.pack(side="left")
        self.cancel_btn = ttk.Button(act, text=self.tr("cancel"), command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=(6, 0))
        ttk.Button(act, text=self.tr("remember"), command=self._remember).pack(side="left", padx=(12, 0))
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=10, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(6, weight=1)

        self._refresh_gdal()
        if self.dir_var.get():
            self._scan_sources()
        self.after(100, self._poll)

    # ---- GDAL ----
    def _tools(self):
        ogr2ogr = core.find_tool("ogr2ogr", self.ogr2ogr_var.get().strip() or None)
        ogrinfo = core.find_tool("ogrinfo", self.ogr2ogr_var.get().strip() or None)
        return ogr2ogr, ogrinfo

    def _refresh_gdal(self):
        ogr2ogr, _ = self._tools()
        if ogr2ogr:
            self.gdal_status.configure(text=self.tr("gdal_ok", v=core.gdal_version(ogr2ogr)))
        else:
            self.gdal_status.configure(text=self.tr("gdal_missing"))

    def _pick_ogr(self):
        p = filedialog.askopenfilename(title="ogr2ogr",
                                       filetypes=[("ogr2ogr", "ogr2ogr*"), ("All", "*.*")])
        if p:
            self.ogr2ogr_var.set(os.path.normpath(p))
            self._refresh_gdal()

    # ---- Source / layers ----
    def _pick_dir(self):
        d = filedialog.askdirectory(title=self.tr("source_dir"), initialdir=self.dir_var.get() or None)
        if d:
            self.dir_var.set(os.path.normpath(d))
            self._scan_sources()

    def _scan_sources(self):
        d = self.dir_var.get().strip()
        if not d or not os.path.isdir(d):
            return
        try:
            srcs = core.list_sources(d)
        except Exception:
            srcs = []
        self._sources = {os.path.basename(s): s for s in srcs}
        self.source_combo["values"] = list(self._sources)
        if self._sources:
            self.source_var.set(next(iter(self._sources)))
            self._load_layers()
        else:
            self.source_var.set("")
            self.layers_list.delete(0, "end")
            self.app.log("— " + self.tr("no_sources"))

    def _load_layers(self):
        src = self._sources.get(self.source_var.get())
        _, ogrinfo = self._tools()
        self.layers_list.delete(0, "end")
        self._layer_names = []
        if not src or not ogrinfo:
            return
        try:
            layers = core.list_layers(ogrinfo, src)
        except Exception as e:
            messagebox.showerror(self.tr("err"), str(e))
            return
        for li in layers:
            label = li.name + (f"  ({li.geom_type})" if li.geom_type else "")
            self.layers_list.insert("end", label)
            self._layer_names.append(li.name)      # ნამდვილი სახელი (label-ის გარეშე)

    def _selected_layers(self):
        return [self._layer_names[i] for i in self.layers_list.curselection()
                if i < len(getattr(self, "_layer_names", []))]

    # ---- connection ----
    def _pg(self):
        try:
            port = int(self.port_var.get().strip() or "5432")
        except ValueError:
            port = 5432
        return core.PgConfig(host=self.host_var.get().strip(), port=port,
                             dbname=self.db_var.get().strip(), user=self.user_var.get().strip(),
                             password=self.pw_var.get(), schema=self.schema_var.get().strip() or "public")

    def _test_conn(self):
        _, ogrinfo = self._tools()
        if not ogrinfo:
            messagebox.showwarning("GIS_BOX", self.tr("warn_gdal"))
            return
        ok, msg = core.test_pg_connection(ogrinfo, self._pg())
        if ok:
            messagebox.showinfo("GIS_BOX", self.tr("conn_ok"))
        else:
            messagebox.showerror(self.tr("err"), f"{self.tr('conn_fail')}\n{msg}")

    # ---- options / persistence ----
    def _opts(self):
        return core.ImportOptions(
            mode=self.mode_var.get(), t_srs=self.tsrs_var.get().strip(),
            prefix=self.prefix_var.get().strip(), promote_to_multi=self.promote_var.get(),
            spatial_index=self.gist_var.get(), use_copy=self.copy_var.get())

    def _remember(self):
        data = {
            "ogr2ogr": self.ogr2ogr_var.get().strip(), "source_dir": self.dir_var.get().strip(),
            "host": self.host_var.get().strip(), "port": self.port_var.get().strip(),
            "dbname": self.db_var.get().strip(), "user": self.user_var.get().strip(),
            "schema": self.schema_var.get().strip(), "mode": self.mode_var.get(),
            "t_srs": self.tsrs_var.get().strip(), "prefix": self.prefix_var.get().strip(),
            "promote": self.promote_var.get(), "gist": self.gist_var.get(), "copy": self.copy_var.get(),
        }
        if self.remember_pw.get():          # პაროლი მხოლოდ თოლიის მონიშვნისას
            data["password"] = self.pw_var.get()
        self.app.set_tool_config(self.tid, data)
        messagebox.showinfo("GIS_BOX", self.tr("saved"))

    # ---- import (thread) ----
    def _start_import(self):
        if self.running:
            return
        ogr2ogr, ogrinfo = self._tools()
        if not (ogr2ogr and ogrinfo):
            messagebox.showwarning("GIS_BOX", self.tr("warn_gdal"))
            return
        src = self._sources.get(self.source_var.get())
        if not src:
            messagebox.showwarning("GIS_BOX", self.tr("warn_source"))
            return
        layers = self._selected_layers()
        if not layers:
            messagebox.showwarning("GIS_BOX", self.tr("warn_layers"))
            return

        self.running = True
        self._cancel_event.clear()
        self.import_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.start(12)
        self.app.log("— " + self.tr("running"))

        pg, opt = self._pg(), self._opts()

        def log_cb(level, message):
            self.msg_queue.put(("log", f"{level}: {message}"))

        def worker():
            try:
                res = core.run_import(ogr2ogr, src, layers, pg, opt, log_cb,
                                      should_cancel=self._cancel_event.is_set,
                                      ogrinfo_path=ogrinfo)
                self.msg_queue.put(("done", res))
            except Exception as e:
                self.msg_queue.put(("done", e))

        threading.Thread(target=worker, daemon=True).start()

    def _cancel(self):
        if self.running:
            self._cancel_event.set()
            self.cancel_btn.configure(state="disabled")

    def _poll(self):
        if not self.winfo_exists():
            return
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "log":
                    self.app.log(payload)
                elif kind == "done":
                    self._on_done(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _on_done(self, payload):
        self.running = False
        self.progress.stop()
        self.import_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        if isinstance(payload, Exception):
            messagebox.showerror(self.tr("err"), str(payload))
            return
        if self._cancel_event.is_set():
            self.app.log("— " + self.tr("cancelled"))
        msg = self.tr("done", ok=payload.ok_count, fail=payload.fail_count)
        self.app.log("— " + msg)
        messagebox.showinfo("GIS_BOX", msg)
