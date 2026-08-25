# -*- coding: utf-8 -*-
"""ქართული სახელების მქონე ფაილების მასობრივი გადარქმევა ლათინურ ტრანსლიტერაციაზე.

მიეთითება საქაღალდე; ხელსაწყო პოულობს ყველა ფაილს, რომლის სახელშიც ქართული
ასოებია (მაგ. shapefile-ის ყველა თანმხლები: .shp/.shx/.dbf/.prj/.cpg/.sbn/
.sbx/.shp.xml და ა.შ.) და გადაარქმევს:
  • ქართული ასოები → ლათინური (მაგ. „საყრდენი“ → „sayrdeni“, ყ → y)
  • სფეისი → ქვედა ტირე „_“
  • გაფართოებები უცვლელი რჩება

„არსებული საყრდენი.shp“  →  „arsebuli_sayrdeni.shp“

გადარქმევა შეუქცევადია, ამიტომ ჯერ ჩნდება წინასწარი სია (Preview), შემდეგ —
დადასტურება. კონფლიქტები (ორი სახელი ერთსა და იმავე ლათინურ სახელს იძლევა, ან
სამიზნე უკვე არსებობს) გამოტოვდება და ცალკე მოინიშნება.
"""

import os
import re

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from tools.base import ToolFrame


# ---- ქართული → ლათინური ცხრილი --------------------------------------------
# ყ → y (მომხმარებლის მაგალითის მიხედვით: „საყრდენი“ → „sayrdeni“).
GEO2LAT = {
    "ა": "a", "ბ": "b", "გ": "g", "დ": "d", "ე": "e", "ვ": "v", "ზ": "z",
    "თ": "t", "ი": "i", "კ": "k", "ლ": "l", "მ": "m", "ნ": "n", "ო": "o",
    "პ": "p", "ჟ": "zh", "რ": "r", "ს": "s", "ტ": "t", "უ": "u", "ფ": "f",
    "ქ": "k", "ღ": "gh", "ყ": "y", "შ": "sh", "ჩ": "ch", "ც": "ts", "ძ": "dz",
    "წ": "ts", "ჭ": "ch", "ხ": "kh", "ჯ": "j", "ჰ": "h",
    # არქაული / იშვიათი
    "ჱ": "e", "ჲ": "y", "ჳ": "w", "ჴ": "q", "ჵ": "o", "ჶ": "f",
}
GEO_RANGE = re.compile(r"[Ⴀ-ჿ]")   # ქართული ასოს არსებობის შემოწმება


def transliterate(name):
    """ფაილის სახელი → ლათინური.

    • ქართული ასო → ლათინური შესაბამისობა
    • ლათინური ასო, ციფრი და წერტილი (გაფართოებისთვის) — უცვლელი
    • ნებისმიერი სხვა სიმბოლო (სფეისი, მძიმე, ტირე, ფრჩხილი და ა.შ.) → „_“

    ზედიზედ მრავალი „_“ ერთამდე იკუმშება; წერტილის წინ და კიდეებში „_“ იშლება.
    """
    out = []
    for ch in name:
        if ch in GEO2LAT:
            out.append(GEO2LAT[ch])
        elif ch.isascii() and (ch.isalnum() or ch == "."):
            out.append(ch)               # ლათინური/ციფრი/წერტილი — უცვლელი
        else:
            out.append("_")              # სფეისი, მძიმე, ნებისმიერი სხვა სიმბოლო
    s = re.sub(r"_{2,}", "_", "".join(out))
    s = re.sub(r"_+\.", ".", s)          # წერტილის წინ „_“ არ დავტოვოთ
    return s.strip("_")


# ---- თარგმანები ------------------------------------------------------------
RTR = {
    "heading":   {"en": "Rename files → Latin",
                  "ka": "ფაილების გადარქმევა → ლათინური"},
    "desc":      {"en": "Point to a folder. Every file whose name contains "
                        "Georgian letters is renamed to Latin; spaces, commas and "
                        "any other symbol become “_”. The extension is kept. All "
                        "sidecar files are handled.",
                  "ka": "მიუთითე საქაღალდე. ყველა ფაილს, რომლის სახელშიც ქართული "
                        "ასოებია, გადაერქმევა ლათინურად; სფეისი, მძიმე და ნებისმიერი "
                        "სხვა სიმბოლო ხდება „_“. გაფართოება უცვლელი რჩება. ყველა "
                        "თანმხლები ფაილი მუშავდება."},
    "folder":    {"en": "Folder:", "ka": "საქაღალდე:"},
    "browse":    {"en": "Browse…", "ka": "დათვალიერება…"},
    "recursive": {"en": "Include subfolders", "ka": "ქვესაქაღალდეებიც"},
    "preview":   {"en": "Preview", "ka": "წინასწარი სია"},
    "rename":    {"en": "Rename", "ka": "გადარქმევა"},
    "col_hint":  {"en": "old  →  new   (⚠ = will be skipped)",
                  "ka": "ძველი  →  ახალი   (⚠ = გამოტოვდება)"},
    "warn_folder": {"en": "Specify a valid folder.",
                    "ka": "მიუთითე არსებული საქაღალდე."},
    "none":      {"en": "No files with Georgian names found.",
                  "ka": "ქართული სახელის მქონე ფაილი ვერ მოიძებნა."},
    "scan_n":    {"en": "Found {n} file(s) to rename"
                        " ({c} conflict(s) will be skipped).",
                  "ka": "საგადარქმევოა {n} ფაილი"
                        " ({c} კონფლიქტი გამოტოვდება)."},
    "confirm_t": {"en": "Confirm rename", "ka": "გადარქმევის დადასტურება"},
    "confirm_m": {"en": "Rename {n} file(s)? This cannot be undone.",
                  "ka": "გადავარქვათ {n} ფაილს? მოქმედება შეუქცევადია."},
    "st_conflict": {"en": "duplicate name — skipped",
                    "ka": "დუბლი სახელი — გამოტოვდა"},
    "st_exists": {"en": "target exists — skipped",
                  "ka": "სამიზნე არსებობს — გამოტოვდა"},
    "done":      {"en": "Done — renamed {ok}, skipped {sk}.",
                  "ka": "დასრულდა — გადაერქვა {ok}, გამოტოვდა {sk}."},
    "nothing":   {"en": "Nothing to rename — run Preview first.",
                  "ka": "გადასარქმევი არაფერია — ჯერ „წინასწარი სია“ გაუშვი."},
    "err":       {"en": "Error", "ka": "შეცდომა"},
}


class RenameTransliterateTool(ToolFrame):
    tid = "rename_translit"

    def tr(self, key, **fmt):
        entry = RTR.get(key, {})
        s = entry.get(self.app.lang) or entry.get("en") or key
        return s.format(**fmt) if fmt else s

    def _state(self):
        return self.app.tool_state.setdefault(self.tid, {})

    def build(self):
        pal = self.app.palette
        st = self._state()
        saved = self.app.get_tool_config(self.tid)
        self._plan = []

        ttk.Label(self, text=self.tr("heading"),
                  font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(self, text=self.tr("desc"), foreground=pal["muted"],
                  wraplength=620, justify="left").pack(anchor="w", pady=(0, 12))

        # საქაღალდე
        row = ttk.Frame(self)
        row.pack(fill="x")
        ttk.Label(row, text=self.tr("folder")).pack(side="left")
        self.folder_var = tk.StringVar(value=st.get("folder") or saved.get("folder") or "")
        ttk.Entry(row, textvariable=self.folder_var).pack(
            side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(row, text=self.tr("browse"), command=self._pick).pack(side="left")

        opt = ttk.Frame(self)
        opt.pack(fill="x", pady=(8, 8))
        self.recursive_var = tk.BooleanVar(value=st.get("recursive", False))
        ttk.Checkbutton(opt, text=self.tr("recursive"),
                        variable=self.recursive_var).pack(side="left")
        ttk.Button(opt, text=self.tr("preview"), command=self._preview).pack(
            side="left", padx=(16, 4))
        ttk.Button(opt, text=self.tr("rename"), command=self._rename).pack(side="left")

        ttk.Label(self, text=self.tr("col_hint"),
                  foreground=pal["muted"]).pack(anchor="w")
        self.preview = scrolledtext.ScrolledText(
            self, height=16, font=("Consolas", 10), state="disabled",
            bg=pal["log_bg"], fg=pal["log_fg"], relief="flat", borderwidth=0)
        self.preview.pack(fill="both", expand=True, pady=(2, 0))

    def save_state(self):
        st = self._state()
        st["folder"] = self.folder_var.get()
        st["recursive"] = self.recursive_var.get()

    def _pick(self):
        d = filedialog.askdirectory(title=self.tr("folder"),
                                    initialdir=self.folder_var.get() or None)
        if d:
            self.folder_var.set(os.path.normpath(d))
            self.app.set_tool_config(self.tid, {"folder": os.path.normpath(d)})

    # ---- გეგმის აგება ----
    def _iter_files(self, folder):
        if self.recursive_var.get():
            for root, _dirs, files in os.walk(folder):
                for f in files:
                    yield root, f
        else:
            for f in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, f)):
                    yield folder, f

    def _build_plan(self, folder):
        """დააბრუნებს (plan, conflicts). plan: dict-ების სია
        {dir, old, new, status}. status: ok / conflict / exists."""
        items = []
        target_count = {}
        for d, name in self._iter_files(folder):
            if not GEO_RANGE.search(name):
                continue                       # ქართული ასო არ არის — გამოტოვება
            new = transliterate(name)
            if new == name:
                continue                       # უცვლელი
            items.append({"dir": d, "old": name, "new": new, "status": "ok"})
            key = (os.path.normcase(d), os.path.normcase(new))
            target_count[key] = target_count.get(key, 0) + 1

        for it in items:
            key = (os.path.normcase(it["dir"]), os.path.normcase(it["new"]))
            dst = os.path.join(it["dir"], it["new"])
            if target_count[key] > 1:
                it["status"] = "conflict"
            elif os.path.exists(dst) and \
                    os.path.normcase(dst) != os.path.normcase(os.path.join(it["dir"], it["old"])):
                it["status"] = "exists"
        return items

    def _preview(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("GIS_BOX", self.tr("warn_folder"))
            return
        self._plan = self._build_plan(folder)
        self._show_plan()
        n_ok = sum(1 for it in self._plan if it["status"] == "ok")
        n_bad = len(self._plan) - n_ok
        if not self._plan:
            self.app.log("— " + self.tr("none"))
        else:
            self.app.log("— " + self.tr("scan_n", n=n_ok, c=n_bad))

    def _show_plan(self):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        if not self._plan:
            self.preview.insert("end", self.tr("none") + "\n")
        for it in self._plan:
            if it["status"] == "ok":
                self.preview.insert("end", f"{it['old']}   →   {it['new']}\n")
            else:
                note = self.tr("st_conflict") if it["status"] == "conflict" \
                    else self.tr("st_exists")
                self.preview.insert("end",
                                    f"⚠ {it['old']}   →   {it['new']}   [{note}]\n")
        self.preview.configure(state="disabled")

    # ---- გადარქმევა ----
    def _rename(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("GIS_BOX", self.tr("warn_folder"))
            return
        # ყოველთვის ხელახლა ვასკანერებთ (ფაილები შესაძლოა შეცვლილიყო)
        self._plan = self._build_plan(folder)
        doable = [it for it in self._plan if it["status"] == "ok"]
        self._show_plan()
        if not doable:
            messagebox.showinfo("GIS_BOX", self.tr("nothing"))
            return
        if not messagebox.askyesno(self.tr("confirm_t"),
                                   self.tr("confirm_m", n=len(doable))):
            return

        ok = 0
        skipped = len(self._plan) - len(doable)
        for it in doable:
            src = os.path.join(it["dir"], it["old"])
            dst = os.path.join(it["dir"], it["new"])
            try:
                os.rename(src, dst)
                self.app.log(f"✓ {it['old']} → {it['new']}")
                ok += 1
            except OSError as e:
                self.app.log(f"✗ {it['old']}: {e}")
                skipped += 1

        self.app.log("— " + self.tr("done", ok=ok, sk=skipped))
        messagebox.showinfo("GIS_BOX", self.tr("done", ok=ok, sk=skipped))
        # გადარქმევის შემდეგ სია განახლდეს
        self._plan = self._build_plan(folder)
        self._show_plan()
