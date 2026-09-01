# -*- coding: utf-8 -*-
"""ბაზისური ინსტრუმენტის კლასი / base tool class.

ცალკე მოდულში, რომ ხელსაწყოებმა (parcel_search, coord_tool) და მთავარმა
აპლიკაციამ (gis_box) ერთი და იგივე ``ToolFrame`` გამოიყენონ ``gis_box``-ის
(როგორც __main__) ხელახლა იმპორტის გარეშე.
"""

from tkinter import ttk

from tools.i18n import translate


class ToolFrame(ttk.Frame):
    key = "tool"          # თარგმანის key სათაურისთვის
    CATALOG = {}          # ხელსაწყოს თარგმანების catalog (თითო ხელსაწყო აყენებს)

    def __init__(self, master, app):
        super().__init__(master, padding=16)
        self.app = app
        self.build()

    def build(self):
        raise NotImplementedError

    def save_state(self):
        """UI-ის ხელახლა აწყობამდე მდგომარეობის შენახვა."""
        pass

    # მოკლე დამხმარეები
    def t(self, key):
        return self.app.t(key)

    def tr(self, key, **fmt):
        """ხელსაწყოს CATALOG-ის თარგმანი მიმდინარე ენით (COMMON fallback-ით)."""
        return translate(self.CATALOG, key, self.app.lang, **fmt)

    def log(self, msg):
        self.app.log(msg)
