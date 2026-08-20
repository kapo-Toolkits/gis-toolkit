# -*- coding: utf-8 -*-
"""კოორდინატების ამომღები / Map Coordinate Extractor — GIS_BOX-ის ხელსაწყო.

ეს ფაილი ახვევს ``coordextract`` პაკეტს ``ToolFrame``-ში ისე, რომ მისი მთელი
UI (OCR ცხრილი + გეო-რეფერენსი) ჩაშენდეს GIS_BOX-ის მთავარ ფანჯარაში.
მძიმე იმპორტები (cv2, PIL, coordextract) ხდება build()-ის შიგნით, ანუ
ხელსაწყო იტვირთება მხოლოდ პირველად არჩევისას (lazy).
"""

from tkinter import ttk

from tools.base import ToolFrame


class CoordExtractorTool(ToolFrame):
    """GIS_BOX-ის ხელსაწყო — რუკის სურათიდან კოორდინატების ამოღება."""

    def build(self):
        # ttk widget-ები საერთო თემას (clam + პალიტრა) ავტომატურად აიღებენ;
        # coordextract-ის canvas ინარჩუნებს საკუთარ მუქ ფონს (რუკის სანახავად).
        from .coordextract.app import CoordExtractorApp

        # container = ეს frame, toplevel = მთავარი Tk (after / dialogs / screen-grab),
        # lang = მიმდინარე ენა (GIS_BOX ენის ცვლილებაზე frame თავიდან შენდება).
        self._impl = CoordExtractorApp(self, self.app, lang=self.app.lang)
