# -*- coding: utf-8 -*-
"""ბაზისური ინსტრუმენტის კლასი / base tool class.

ცალკე მოდულში, რომ ხელსაწყოებმა (parcel_search, coord_tool) და მთავარმა
აპლიკაციამ (gis_box) ერთი და იგივე ``ToolFrame`` გამოიყენონ ``gis_box``-ის
(როგორც __main__) ხელახლა იმპორტის გარეშე.
"""

from tkinter import ttk


class ToolFrame(ttk.Frame):
    key = "tool"          # თარგმანის key სათაურისთვის

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

    def log(self, msg):
        self.app.log(msg)
