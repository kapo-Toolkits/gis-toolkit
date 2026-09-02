# -*- coding: utf-8 -*-
"""ტესტები — CF_HTML clipboard wrapper-ის offset-ები."""

import re

from tools.clipboard_html import _build_cf_html


def test_cf_html_offsets():
    frag = "<table><tr><td>ქუდი</td></tr></table>"
    raw = _build_cf_html(frag)
    text = raw.decode("utf-8")
    sh = int(re.search(r"StartHTML:(\d+)", text).group(1))
    eh = int(re.search(r"EndHTML:(\d+)", text).group(1))
    sf = int(re.search(r"StartFragment:(\d+)", text).group(1))
    ef = int(re.search(r"EndFragment:(\d+)", text).group(1))
    # offset-ები ბაიტებშია და ზუსტად ფრაგმენტს უნდა შემოწერონ
    assert raw[sh:sh + 6] == b"<html>"
    assert raw[sf:ef].decode("utf-8") == frag
    assert eh == len(raw)
