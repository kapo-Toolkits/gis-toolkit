# -*- coding: utf-8 -*-
"""tools.file_gather_core — შეგროვების სუფთა ლოგიკის ტესტები."""

import os

from tools.file_gather_core import norm_exts, iter_matches, unique_dest, gather


def _touch(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ---- norm_exts ----
def test_norm_exts_variants():
    assert norm_exts("docx, doc") == (".docx", ".doc")
    assert norm_exts(".PDF .txt") == (".pdf", ".txt")
    assert norm_exts("docx,,  doc , docx") == (".docx", ".doc")   # დუბლი იშლება
    assert norm_exts("") == ()
    assert norm_exts(None) == ()


# ---- iter_matches ----
def test_iter_matches_filter_and_recursion(tmp_path):
    _touch(str(tmp_path / "a.docx"))
    _touch(str(tmp_path / "b.txt"))
    _touch(str(tmp_path / "sub" / "c.doc"))
    _touch(str(tmp_path / "sub" / "deep" / "d.docx"))

    exts = (".docx", ".doc")
    rec = iter_matches(str(tmp_path), exts, recursive=True)
    assert [os.path.basename(p) for p in rec] == ["a.docx", "c.doc", "d.docx"]

    flat = iter_matches(str(tmp_path), exts, recursive=False)
    assert [os.path.basename(p) for p in flat] == ["a.docx"]


def test_iter_matches_empty_exts_all_files(tmp_path):
    _touch(str(tmp_path / "a.docx"))
    _touch(str(tmp_path / "b.txt"))
    got = iter_matches(str(tmp_path), (), recursive=True)
    assert {os.path.basename(p) for p in got} == {"a.docx", "b.txt"}


# ---- unique_dest ----
def test_unique_dest_increments(tmp_path):
    dest = str(tmp_path)
    taken = set()
    p0 = unique_dest(dest, "x.docx", taken)
    assert os.path.basename(p0) == "x.docx"
    # იგივე სახელი ისევ — _1 (taken-ის წყალობით, დისკზე ჯერ არ არსებობს)
    p1 = unique_dest(dest, "x.docx", taken)
    assert os.path.basename(p1) == "x_1.docx"
    p2 = unique_dest(dest, "x.docx", taken)
    assert os.path.basename(p2) == "x_2.docx"


def test_unique_dest_respects_existing_file(tmp_path):
    dest = str(tmp_path)
    _touch(os.path.join(dest, "y.doc"))
    p = unique_dest(dest, "y.doc", set())
    assert os.path.basename(p) == "y_1.doc"


# ---- gather (integration) ----
def test_gather_flattens_and_dedupes(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "out"
    # ორ ქვესაქაღალდეში ერთი და იგივე სახელი — უნდა გახდეს report.docx + report_1.docx
    _touch(str(src / "2024" / "report.docx"), "a")
    _touch(str(src / "2025" / "report.docx"), "b")
    _touch(str(src / "2025" / "notes.doc"), "c")
    _touch(str(src / "skip.txt"), "d")

    res = gather(str(src), str(dst), (".docx", ".doc"), recursive=True)
    assert res["copied"] == 3
    assert res["skipped"] == 0
    assert res["total"] == 3
    assert not res["cancelled"]

    names = sorted(os.listdir(str(dst)))
    assert names == ["notes.doc", "report.docx", "report_1.docx"]


def test_gather_creates_dest_and_cancels(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "new_out"        # ჯერ არ არსებობს
    _touch(str(src / "a.docx"))
    _touch(str(src / "b.docx"))

    res = gather(str(src), str(dst), (".docx",), recursive=True,
                 is_cancelled=lambda: True)      # მაშინვე უქმდება
    assert res["cancelled"] is True
    assert res["copied"] == 0
    assert os.path.isdir(str(dst))               # საქაღალდე მაინც შეიქმნა
