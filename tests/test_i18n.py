# -*- coding: utf-8 -*-
"""ტესტები — საერთო თარგმანის lookup (tools/i18n.translate)."""

from tools.i18n import translate, COMMON

CAT = {
    "hi": {"en": "Hello", "ka": "გამარჯობა"},
    "n":  {"en": "N={n}", "ka": "N={n}"},
}


def test_lang_selection():
    assert translate(CAT, "hi", "ka") == "გამარჯობა"
    assert translate(CAT, "hi", "en") == "Hello"


def test_missing_lang_falls_back_to_en():
    assert translate(CAT, "hi", "fr") == "Hello"


def test_missing_key_returns_key():
    assert translate(CAT, "nope", "en") == "nope"


def test_format_kwargs():
    assert translate(CAT, "n", "en", n=5) == "N=5"


def test_common_fallback():
    # key არაა CATALOG-ში, მაგრამ არის COMMON-ში
    assert translate({}, "err", "ka") == COMMON["err"]["ka"]
    # CATALOG უპირატესია COMMON-ზე
    assert translate({"err": {"en": "E", "ka": "ე"}}, "err", "en") == "E"
