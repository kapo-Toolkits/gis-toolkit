# -*- coding: utf-8 -*-
"""ტესტები — GDB → PostGIS აუდიტის ისტორია (SQLite AuditStore)."""

from tools.gdb2postgis_audit import AuditStore


def _rec(ts="2026-09-01T10:00:00", layer="Parcels", affected=2, deleted=1, ok=True):
    return {
        "ts": ts, "profile": "", "source": "C:/x.gdb", "layer": layer,
        "schema": "public", "target_table": layer.lower(), "key_field": "objectid",
        "mode": "incremental", "affected": affected, "deleted": deleted,
        "seconds": 1.0, "ok": ok, "message": "", "pg_host": "h", "pg_port": 5432, "pg_db": "d",
    }


def test_record_and_query(tmp_path):
    a = AuditStore(str(tmp_path / "audit.db"))
    rid = a.record(_rec(), upserted_ids=["10", "11"], deleted_ids=["9"])
    assert a.dates() == ["2026-09-01"]
    runs = a.runs_on("2026-09-01")
    assert len(runs) == 1 and runs[0]["affected"] == 2 and runs[0]["deleted"] == 1
    assert a.ids(rid, "upsert") == ["10", "11"]
    assert a.ids(rid, "delete") == ["9"]


def test_dates_sorted_desc(tmp_path):
    a = AuditStore(str(tmp_path / "audit.db"))
    a.record(_rec(ts="2026-08-30T09:00:00"))
    a.record(_rec(ts="2026-09-02T09:00:00"))
    assert a.dates() == ["2026-09-02", "2026-08-30"]


def test_delete_run(tmp_path):
    a = AuditStore(str(tmp_path / "audit.db"))
    rid = a.record(_rec(), upserted_ids=["1"])
    a.delete_run(rid)
    assert a.dates() == []
    assert a.ids(rid) == []
