# -*- coding: utf-8 -*-
"""ფორმატირებული ცხრილის გაცვლის ბუფერში კოპირება (Word/Excel-ში ჩასაფეისთად).

Windows-ზე იყენებს **CF_HTML** ("HTML Format") — ჩარჩოები, გაერთიანებული ქუდი
და ცენტრირება შენარჩუნდება ჩასმისას. პარალელურად დებს ჩვეულებრივ ტექსტსაც (TSV,
fallback). არა-Windows-ზე — მხოლოდ ტექსტი (tkinter clipboard-ით).

დამოკიდებულების გარეშე (მხოლოდ ctypes stdlib).
"""

import sys


def _build_cf_html(fragment):
    """CF_HTML-ის სრული ბაიტები (header-ით და offset-ებით)."""
    prefix = "<html><body><!--StartFragment-->"
    suffix = "<!--EndFragment--></body></html>"
    html = prefix + fragment + suffix
    header_tmpl = ("Version:0.9\r\n"
                   "StartHTML:{sh:010d}\r\n"
                   "EndHTML:{eh:010d}\r\n"
                   "StartFragment:{sf:010d}\r\n"
                   "EndFragment:{ef:010d}\r\n")
    header_len = len(header_tmpl.format(sh=0, eh=0, sf=0, ef=0).encode("utf-8"))
    sh = header_len
    eh = header_len + len(html.encode("utf-8"))
    sf = header_len + len(prefix.encode("utf-8"))
    ef = header_len + len((prefix + fragment).encode("utf-8"))
    header = header_tmpl.format(sh=sh, eh=eh, sf=sf, ef=ef)
    return (header + html).encode("utf-8")


def _set_windows_clipboard(fragment, text):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    GMEM_MOVEABLE = 0x0002
    CF_UNICODETEXT = 13

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]

    def _put(fmt, raw):
        size = len(raw)
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
        if not h:
            return
        p = kernel32.GlobalLock(h)
        ctypes.memmove(p, raw, size)
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(fmt, h)

    cf_html = user32.RegisterClipboardFormatW("HTML Format")
    if not user32.OpenClipboard(0):
        return False
    try:
        user32.EmptyClipboard()
        _put(cf_html, _build_cf_html(fragment) + b"\x00")
        _put(CF_UNICODETEXT, (text + "\x00").encode("utf-16-le"))
    finally:
        user32.CloseClipboard()
    return True


def copy_table(fragment, text, widget=None):
    """ცხრილის კოპირება: HTML (Windows) + ტექსტი. აბრუნებს True/False."""
    if sys.platform == "win32":
        try:
            if _set_windows_clipboard(fragment, text):
                return True
        except Exception:  # noqa: BLE001 — fallback ტექსტზე
            pass
    # fallback — მხოლოდ ტექსტი (tkinter)
    if widget is not None:
        try:
            widget.clipboard_clear()
            widget.clipboard_append(text)
            return True
        except Exception:  # noqa: BLE001
            return False
    return False
