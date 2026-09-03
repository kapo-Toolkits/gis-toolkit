# -*- coding: utf-8 -*-
"""ფაილების შეგროვება — საწყისი ხიდან ერთ ბრტყელ საქაღალდეში კოპირება.

მიეთითება საწყისი საქაღალდე (არჩევით ქვესაქაღალდეებითურთ) და სამიზნე. ხელსაწყო
პოულობს მითითებული გაფართოების ფაილებს (ნაგულისხმევად Word: .docx/.doc) და
აკოპირებს ერთ საქაღალდეში; სახელის დამთხვევისას ამატებს _1, _2 … სუფიქსს.
ორიგინალები არ იშლება. სუფთა ლოგიკა ``file_gather_core``-შია (ტესტირებადი).
"""

import os
import queue
import subprocess
import sys
import threading

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from tools.base import ToolFrame
from tools.tooltip import add_tip
from tools.file_gather_core import gather, iter_matches, norm_exts


# ---- თარგმანები ------------------------------------------------------------
GTR = {
    "heading":   {"en": "Collect files into one folder",
                  "ka": "ფაილების შეგროვება ერთ საქაღალდეში"},
    "desc":      {"en": "Pick a source folder; every matching file inside it "
                        "(and its subfolders) is copied into one flat destination "
                        "folder. Duplicate names get _1, _2 … Originals are kept.",
                  "ka": "აირჩიე საწყისი საქაღალდე; მასში (და ქვესაქაღალდეებში) "
                        "მოძებნილი შესაბამისი ფაილები ერთ, ბრტყელ სამიზნე "
                        "საქაღალდეში კოპირდება. დამთხვეული სახელები იღებს _1, _2 … "
                        "ორიგინალები რჩება."},
    "source":    {"en": "Source:", "ka": "საწყისი:"},
    "dest":      {"en": "Destination:", "ka": "სამიზნე:"},
    "browse":    {"en": "Browse…", "ka": "დათვალიერება…"},
    "exts":      {"en": "File types:", "ka": "ფაილის ტიპები:"},
    "recursive": {"en": "Include subfolders", "ka": "ქვესაქაღალდეებიც"},
    "btn_count": {"en": "Count", "ka": "დათვლა"},
    "btn_gather": {"en": "Collect", "ka": "შეგროვება"},
    "btn_gather_busy": {"en": "Collecting…", "ka": "მიმდინარეობს…"},
    "btn_cancel": {"en": "✖ Cancel", "ka": "✖ გაუქმება"},
    "btn_open_dest": {"en": "Open destination", "ka": "სამიზნის გახსნა"},

    # შეტყობინებები
    "warn_source": {"en": "Specify a valid source folder.",
                    "ka": "მიუთითე არსებული საწყისი საქაღალდე."},
    "warn_dest":  {"en": "Specify a destination folder.",
                   "ka": "მიუთითე სამიზნე საქაღალდე."},
    "warn_same":  {"en": "Source and destination must be different.",
                   "ka": "საწყისი და სამიზნე ერთი და იგივე ვერ იქნება."},
    "warn_inside": {"en": "The destination is inside the source — that would copy "
                          "files into themselves. Pick a destination outside it.",
                    "ka": "სამიზნე საწყისის შიგნითაა — ეს ფაილებს თავის თავში "
                          "დააკოპირებდა. აირჩიე საწყისის გარეთ მყოფი სამიზნე."},
    "count_n":    {"en": "{n} file(s) match ({t}).",
                   "ka": "შესაბამისია {n} ფაილი ({t})."},
    "count_none": {"en": "No matching files in the source ({t}).",
                   "ka": "საწყისში შესაბამისი ფაილი არაა ({t})."},
    "confirm_t":  {"en": "Confirm collect", "ka": "შეგროვების დადასტურება"},
    "confirm_m":  {"en": "Copy {n} file(s) into:\n{dest}?",
                   "ka": "დავაკოპირო {n} ფაილი:\n{dest}?"},
    "start":      {"en": "Collecting {n} file(s)…",
                   "ka": "გროვდება {n} ფაილი…"},
    "progress":   {"en": "Copied {i}/{n}", "ka": "დაკოპირდა {i}/{n}"},
    "done":       {"en": "Done — copied {ok}, skipped {sk}. → {dest}",
                   "ka": "დასრულდა — დაკოპირდა {ok}, გამოტოვდა {sk}. → {dest}"},
    "cancelling": {"en": "Cancelling…", "ka": "უქმდება…"},
    "cancelled":  {"en": "Collecting cancelled — {ok} copied before stop.",
                   "ka": "შეგროვება გაუქმდა — შეჩერებამდე დაკოპირდა {ok}."},
    "err":        {"en": "Error", "ka": "შეცდომა"},

    # tooltip-ები
    "tip_src":    {"en": "Folder to gather files from (searched recursively).",
                   "ka": "საქაღალდე, საიდანაც ფაილები გროვდება (ხე მთლიანად)."},
    "tip_dest":   {"en": "Folder to copy all matching files into.",
                   "ka": "საქაღალდე, სადაც ყველა შესაბამისი ფაილი გროვდება."},
    "tip_exts":   {"en": "Comma-separated extensions to collect, e.g. “docx, doc”. "
                         "Leave empty to collect every file.",
                   "ka": "მძიმით გამოყოფილი გაფართოებები, მაგ. „docx, doc“. "
                         "ცარიელი — ყველა ფაილი."},
    "tip_recursive": {"en": "Also search files in subfolders.",
                      "ka": "ქვესაქაღალდეების ფაილებიც მოძებნოს."},
    "tip_count":  {"en": "Count matching files without copying anything.",
                   "ka": "შესაბამისი ფაილების დათვლა კოპირების გარეშე."},
    "tip_gather": {"en": "Copy all matching files into the destination "
                         "(with confirmation).",
                   "ka": "ყველა შესაბამისი ფაილის კოპირება სამიზნეში "
                         "(დადასტურებით)."},
    "tip_cancel": {"en": "Stop the running collection.",
                   "ka": "მიმდინარე შეგროვების შეჩერება."},
    "tip_open_dest": {"en": "Open the destination folder.",
                      "ka": "სამიზნე საქაღალდის გახსნა."},
}


class FileGatherTool(ToolFrame):
    tid = "file_gather"
    CATALOG = GTR

    def _state(self):
        return self.app.tool_state.setdefault(self.tid, {})

    def build(self):
        pal = self.app.palette
        st = self._state()
        saved = self.app.get_tool_config(self.tid)

        self.busy = False
        self.msg_queue = queue.Queue()
        self._cancel_event = threading.Event()

        ttk.Label(self, text=self.tr("heading"),
                  font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(self, text=self.tr("desc"), foreground=pal["muted"],
                  wraplength=760, justify="left").pack(anchor="w", pady=(0, 12))

        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        # --- საწყისი ---
        ttk.Label(grid, text=self.tr("source")).grid(row=0, column=0, sticky="w")
        self.src_var = tk.StringVar(
            value=st.get("source") or saved.get("source") or "")
        ttk.Entry(grid, textvariable=self.src_var).grid(
            row=0, column=1, sticky="ew", padx=(6, 6), pady=2)
        add_tip(ttk.Button(grid, text=self.tr("browse"),
                           command=lambda: self._pick(self.src_var, "source")),
                self.tr("tip_src")).grid(row=0, column=2)

        # --- სამიზნე ---
        ttk.Label(grid, text=self.tr("dest")).grid(row=1, column=0, sticky="w")
        self.dst_var = tk.StringVar(
            value=st.get("dest") or saved.get("dest") or "")
        ttk.Entry(grid, textvariable=self.dst_var).grid(
            row=1, column=1, sticky="ew", padx=(6, 6), pady=2)
        add_tip(ttk.Button(grid, text=self.tr("browse"),
                           command=lambda: self._pick(self.dst_var, "dest")),
                self.tr("tip_dest")).grid(row=1, column=2)

        # --- გაფართოებები ---
        ttk.Label(grid, text=self.tr("exts")).grid(row=2, column=0, sticky="w",
                                                   pady=(6, 0))
        self.exts_var = tk.StringVar(value=st.get("exts", "docx, doc"))
        add_tip(ttk.Entry(grid, textvariable=self.exts_var, width=30),
                self.tr("tip_exts")).grid(row=2, column=1, sticky="w",
                                          padx=(6, 6), pady=(6, 0))

        # --- პარამეტრები + ღილაკები ---
        opt = ttk.Frame(self)
        opt.pack(fill="x", pady=(10, 4))
        self.recursive_var = tk.BooleanVar(value=st.get("recursive", True))
        add_tip(ttk.Checkbutton(opt, text=self.tr("recursive"),
                                variable=self.recursive_var),
                self.tr("tip_recursive")).pack(side="left")
        add_tip(ttk.Button(opt, text=self.tr("btn_count"), command=self._count),
                self.tr("tip_count")).pack(side="left", padx=(16, 4))
        self.gather_btn = ttk.Button(opt, text=self.tr("btn_gather"),
                                     command=self._start_gather)
        self.gather_btn.pack(side="left", padx=(0, 4))
        add_tip(self.gather_btn, self.tr("tip_gather"))
        self.cancel_btn = ttk.Button(opt, text=self.tr("btn_cancel"),
                                     command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=(0, 4))
        add_tip(self.cancel_btn, self.tr("tip_cancel"))
        add_tip(ttk.Button(opt, text=self.tr("btn_open_dest"),
                           command=self._open_dest),
                self.tr("tip_open_dest")).pack(side="left")

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", pady=(6, 2))

        self.status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status,
                  foreground=pal["muted"]).pack(anchor="w", pady=(0, 4))

        self.after(100, self._poll_queue)

    def save_state(self):
        st = self._state()
        st["source"] = self.src_var.get()
        st["dest"] = self.dst_var.get()
        st["exts"] = self.exts_var.get()
        st["recursive"] = self.recursive_var.get()

    # ---- საქაღალდის არჩევა ----
    def _pick(self, var, key):
        d = filedialog.askdirectory(initialdir=var.get() or None)
        if d:
            d = os.path.normpath(d)
            var.set(d)
            self.app.set_tool_config(self.tid, {key: d})

    def _open_dest(self):
        d = self.dst_var.get().strip()
        if not d or not os.path.isdir(d):
            messagebox.showwarning("GIS_BOX", self.tr("warn_dest"))
            return
        try:
            if sys.platform == "win32":
                os.startfile(d)                       # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", d])
            else:
                subprocess.Popen(["xdg-open", d])
        except Exception as e:                        # noqa: BLE001
            messagebox.showerror(self.tr("err"), str(e))

    # ---- ვალიდაცია ----
    def _validate(self):
        """აბრუნებს (source, dest, exts) ან None (გაფრთხილებით)."""
        source = self.src_var.get().strip()
        dest = self.dst_var.get().strip()
        if not source or not os.path.isdir(source):
            messagebox.showwarning("GIS_BOX", self.tr("warn_source"))
            return None
        if not dest:
            messagebox.showwarning("GIS_BOX", self.tr("warn_dest"))
            return None
        src_n = os.path.normcase(os.path.abspath(source))
        dst_n = os.path.normcase(os.path.abspath(dest))
        if src_n == dst_n:
            messagebox.showwarning("GIS_BOX", self.tr("warn_same"))
            return None
        # სამიზნე საწყისის შიგნით — რეკურსიულ კოპირებას თავს დაასხამდა
        if self.recursive_var.get() and \
                (dst_n + os.sep).startswith(src_n + os.sep):
            messagebox.showwarning("GIS_BOX", self.tr("warn_inside"))
            return None
        return source, dest, norm_exts(self.exts_var.get())

    # ---- დათვლა (კოპირების გარეშე) ----
    def _count(self):
        v = self._validate()
        if not v:
            return
        source, _dest, exts = v
        n = len(iter_matches(source, exts, self.recursive_var.get()))
        label = ", ".join(exts) if exts else "*"
        key = "count_n" if n else "count_none"
        msg = self.tr(key, n=n, t=label)
        self.status.set(msg)
        self.app.log(msg)

    # ---- შეგროვება (ფონურ ნაკადში) ----
    def _start_gather(self):
        if self.busy:
            return
        v = self._validate()
        if not v:
            return
        source, dest, exts = v
        n = len(iter_matches(source, exts, self.recursive_var.get()))
        if n == 0:
            label = ", ".join(exts) if exts else "*"
            messagebox.showinfo("GIS_BOX", self.tr("count_none", t=label))
            return
        if not messagebox.askyesno(self.tr("confirm_t"),
                                   self.tr("confirm_m", n=n, dest=dest)):
            return
        self.app.set_tool_config(self.tid,
                                 {"source": source, "dest": dest})

        self.busy = True
        self._cancel_event.clear()
        self.gather_btn.configure(state="disabled",
                                  text=self.tr("btn_gather_busy"))
        self.cancel_btn.configure(state="normal")
        self.progress.configure(value=0, maximum=n)
        self.status.set(self.tr("start", n=n))
        self.app.log("— " + self.tr("start", n=n))

        t = threading.Thread(
            target=self._worker,
            args=(source, dest, exts, self.recursive_var.get()),
            daemon=True,
        )
        t.start()

    def _worker(self, source, dest, exts, recursive):
        result = gather(
            source, dest, exts, recursive,
            log=lambda m: self.msg_queue.put(("log", m)),
            progress=lambda i, n: self.msg_queue.put(("progress", (i, n))),
            is_cancelled=self._cancel_event.is_set,
        )
        result["dest"] = dest
        self.msg_queue.put(("done", result))

    def _cancel(self):
        if self.busy:
            self._cancel_event.set()
            self.cancel_btn.configure(state="disabled")
            self.status.set(self.tr("cancelling"))

    def _poll_queue(self):
        if not self.winfo_exists():
            return
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "log":
                    self.app.log(payload)
                elif kind == "progress":
                    i, n = payload
                    self.progress.configure(maximum=max(1, n), value=i)
                    self.status.set(self.tr("progress", i=i, n=n))
                elif kind == "done":
                    self._on_done(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _on_done(self, result):
        self.busy = False
        self.gather_btn.configure(state="normal", text=self.tr("btn_gather"))
        self.cancel_btn.configure(state="disabled")

        if result.get("cancelled"):
            msg = self.tr("cancelled", ok=result["copied"])
            self.status.set(msg)
            self.app.log("— " + msg)
            return

        self.progress.configure(value=result["total"])
        msg = self.tr("done", ok=result["copied"], sk=result["skipped"],
                      dest=result["dest"])
        self.status.set(msg)
        self.app.log("— " + msg)
        messagebox.showinfo("GIS_BOX", self.tr("done", ok=result["copied"],
                                               sk=result["skipped"],
                                               dest=result["dest"]))
