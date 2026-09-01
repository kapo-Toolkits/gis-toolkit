# -*- coding: utf-8 -*-
"""ტესტები — ნაკვეთის ძებნის run_search: პროგრესი და გაუქმება."""

import tools.parcel_search as ps


class _FakePyogrio:
    """read_dataframe აბრუნებს ცარიელს — ბაზის გარეშე ტესტისთვის."""
    def read_dataframe(self, gdb, layer, where):
        return []          # len 0 → შედეგის ჩაწერის შტო არ ეშვება


def _codes(n):
    return [f"71.63.80.{i:03d}" for i in range(1, n + 1)]


def _tr(key, **fmt):
    return key


def test_run_search_reports_progress(monkeypatch):
    monkeypatch.setattr(ps, "pyogrio", _FakePyogrio())
    codes = _codes(2500)                       # > CHUNK_SIZE → რამდენიმე ბლოკი
    prog, done = [], {}
    ps.run_search("gdb", "L", "CADCODE", codes, "", lambda m: None,
                  lambda r: done.update(r), _tr, formats=(),
                  progress=lambda i, n: prog.append((i, n)),
                  cancel=lambda: False)
    n_chunks = (len(codes) + ps.CHUNK_SIZE - 1) // ps.CHUNK_SIZE
    assert n_chunks >= 2
    assert prog[-1] == (n_chunks, n_chunks)     # ბოლო ბლოკამდე მივიდა
    assert done.get("search_only") is True


def test_run_search_cancel(monkeypatch):
    monkeypatch.setattr(ps, "pyogrio", _FakePyogrio())
    done = {}
    ps.run_search("gdb", "L", "CADCODE", _codes(2500), "", lambda m: None,
                  lambda r: done.update(r), _tr, formats=(),
                  progress=lambda i, n: None,
                  cancel=lambda: True)          # მაშინვე გაუქმება
    assert done.get("cancelled") is True
