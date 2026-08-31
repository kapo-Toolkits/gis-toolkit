# -*- coding: utf-8 -*-
"""ტესტები — ქართული→ლათინური ტრანსლიტერაცია და shapefile-ის დათვლა."""

import struct

from tools.translit import transliterate, feature_count


def test_basic():
    assert transliterate("არსებული საყრდენი.shp") == "arsebuli_sayrdeni.shp"


def test_double_extension_preserved():
    assert transliterate("არსებული საყრდენი.shp.xml") == "arsebuli_sayrdeni.shp.xml"


def test_symbols_become_underscore():
    assert transliterate("ნაკვეთი, ბლოკი-2.dbf") == "nakveti_bloki_2.dbf"
    assert transliterate("გაზი (37).prj") == "gazi_37.prj"


def test_ya_maps_to_y():
    assert transliterate("საყრდენი") == "sayrdeni"


def test_already_latin_unchanged():
    assert transliterate("already_ok.shp") == "already_ok.shp"


def _write_dbf(path, nrec):
    """მინიმალური dBASE III header nrec ჩანაწერით."""
    hdr = bytearray(32)
    hdr[0] = 0x03
    struct.pack_into("<I", hdr, 4, nrec)      # ჩანაწერების რაოდენობა
    struct.pack_into("<H", hdr, 8, 32 + 32 + 1)
    struct.pack_into("<H", hdr, 10, 11)
    field = bytearray(32)
    field[0:2] = b"ID"
    field[11] = ord("C")
    field[16] = 10
    with open(path, "wb") as f:
        f.write(hdr)
        f.write(field)
        f.write(b"\x0D")


def _write_shp(path):
    with open(path, "wb") as f:
        f.write(b"\x00" * 100)


def test_feature_count_nonempty(tmp_path):
    base = str(tmp_path / "x")
    _write_shp(base + ".shp")
    _write_dbf(base + ".dbf", 5)
    assert feature_count(base + ".shp") == 5


def test_feature_count_empty(tmp_path):
    base = str(tmp_path / "e")
    _write_shp(base + ".shp")
    _write_dbf(base + ".dbf", 0)
    assert feature_count(base + ".shp") == 0


def test_feature_count_no_dbf_header_only(tmp_path):
    base = str(tmp_path / "h")
    _write_shp(base + ".shp")            # header-only, no .dbf → empty
    assert feature_count(base + ".shp") == 0
