# -*- coding: utf-8 -*-
"""ტესტები — კოდის ველის შერჩევა (CADCODE_ID → CADCODE ბაგის რეგრესია)."""

from tools.fields import pick_code_field

FIELDS = ["CADCODE_ID", "CADCODE", "REGNUMBER", "STATUS"]


def test_keeps_valid_code_field():
    assert pick_code_field(FIELDS, "CADCODE") == "CADCODE"


def test_heals_id_to_code():
    # ჩარჩენილი CADCODE_ID → CADCODE (კოდი string-ველშია, არა ID-ში)
    assert pick_code_field(FIELDS, "CADCODE_ID") == "CADCODE"


def test_guess_prefers_exact_cadcode_over_id():
    # როცა მიმდინარე აღარ არსებობს — CADCODE და არა CADCODE_ID
    assert pick_code_field(FIELDS, "NOPE") == "CADCODE"


def test_guess_non_id_cad_when_no_exact():
    fields = ["MYCAD_ID", "MYCADVAL", "X"]
    assert pick_code_field(fields, "NONE", default="CADCODE") == "MYCADVAL"


def test_keeps_deliberate_non_code_field():
    # REGNUMBER მოქმედია — არ შევცვალოთ
    assert pick_code_field(FIELDS, "REGNUMBER") == "REGNUMBER"


def test_fallback_first_field():
    assert pick_code_field(["A", "B"], "NONE", default="CADCODE") == "A"


def test_empty():
    assert pick_code_field([], "X") == ""
