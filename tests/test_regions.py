# -*- coding: utf-8 -*-
"""ტესტები — CadData რეგიონების სანიშნეები."""

from tools.regions import region_name, layer_display, layer_code


def test_exact_codes():
    assert region_name("R02") == "ქვემო ქართლი"
    assert region_name("Z01") == "თბილისი"
    assert region_name("R12") == "აფხაზეთი"


def test_prefix_match():
    assert region_name("R11_Parcels") == "რაჭა ლეჩხუმი-ქვემო სვანეთი"


def test_non_region_is_none():
    assert region_name("RegParcels") is None
    assert region_name("") is None


def test_display_and_code_roundtrip():
    d = layer_display("R04")
    assert d == "R04 — აჭარა"
    assert layer_code(d) == "R04"


def test_plain_layer_unchanged():
    assert layer_display("RegParcels") == "RegParcels"
    assert layer_code("RegParcels") == "RegParcels"
