# -*- coding: utf-8 -*-
"""ტესტები — ინკრემენტული სინქრონის watermark-ების შენახვა (SyncState)."""

from tools.gdb2postgis_state import SyncState, LayerState


def test_put_get_roundtrip(tmp_path):
    p = str(tmp_path / "state.json")
    s = SyncState(p)
    s.put("C:/data/x.gdb", "Parcels", LayerState(watermark="2026-01-01", rows_last=7))
    # ხელახლა ჩატვირთვა დისკიდან
    got = SyncState(p).get("C:/data/x.gdb", "Parcels")
    assert got.watermark == "2026-01-01"
    assert got.rows_last == 7


def test_missing_returns_empty(tmp_path):
    got = SyncState(str(tmp_path / "state.json")).get("C:/x.gdb", "L")
    assert got.watermark == "" and got.rows_last == 0


def test_reset(tmp_path):
    p = str(tmp_path / "state.json")
    s = SyncState(p)
    s.put("C:/x.gdb", "L", LayerState(watermark="w"))
    s.reset("C:/x.gdb", "L")
    assert SyncState(p).get("C:/x.gdb", "L").watermark == ""


def test_key_is_layer_scoped(tmp_path):
    s = SyncState(str(tmp_path / "state.json"))
    s.put("C:/x.gdb", "A", LayerState(watermark="a"))
    s.put("C:/x.gdb", "B", LayerState(watermark="b"))
    assert s.get("C:/x.gdb", "A").watermark == "a"
    assert s.get("C:/x.gdb", "B").watermark == "b"
