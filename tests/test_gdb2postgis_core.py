# -*- coding: utf-8 -*-
"""ტესტები — GDB → PostGIS ძრავის სუფთა ფუნქციები (subprocess-ის გარეშე)."""

import os

from tools.gdb2postgis_core import list_sources, PgConfig


def test_list_sources_picks_gdb_and_mdb(tmp_path):
    (tmp_path / "a.gdb").mkdir()
    (tmp_path / "b.mdb").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "plain").mkdir()
    got = sorted(os.path.basename(p) for p in list_sources(str(tmp_path)))
    assert got == ["a.gdb", "b.mdb"]


def test_list_sources_missing_dir():
    assert list_sources(os.path.join("no", "such", "dir")) == []


def test_pgconfig_conn_string():
    s = PgConfig(host="h", port=5433, dbname="d", user="u",
                 password="p", schema="s").pg_conn_string()
    assert "host=h" in s and "port=5433" in s
    assert "dbname=d" in s and "active_schema=s" in s
