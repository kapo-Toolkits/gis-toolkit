# -*- coding: utf-8 -*-
"""ცხრილის (ქუდი + №/X/Y) სურათად რენდერი — ArcGIS Pro layout-ში ჩასაფეისთად.

აბრუნებს PIL.Image-ს: გაერთიანებული ტექსტური ქუდი (wrap), სათაურის რიგი და
მონაცემები — ჩარჩოებით, ცენტრირებით. Pillow-ს იყენებს (GIS_BOX-ს ისედ სჭირდება).
"""


def _font(size):
    from PIL import ImageFont
    for name in ("sylfaen.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), str(text), font=font)
    return r - l, b - t


def _wrap(draw, text, font, max_w):
    words = str(text).split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        if _text_size(draw, cur + " " + w, font)[0] <= max_w:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def render_table(title, headers, rows, scale=2):
    """ბლოკის სურათი. title — ქუდი ("" თუ არაა); headers/rows — ცხრილი."""
    from PIL import Image, ImageDraw

    fs = 17 * scale
    pad = 8 * scale
    font = _font(fs)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    ncols = len(headers)
    # სვეტების სიგანე — მაქს. ტექსტი header+data-ში
    col_w = []
    for j in range(ncols):
        w = _text_size(tmp, headers[j], font)[0]
        for row in rows:
            w = max(w, _text_size(tmp, row[j], font)[0])
        col_w.append(w + 2 * pad)
    total_w = sum(col_w)

    _, th = _text_size(tmp, "Ag", font)
    row_h = th + 2 * pad

    # ქუდი — wrap total_w-ზე
    title_lines = _wrap(tmp, title, font, total_w - 2 * pad) if title else []
    title_h = (len(title_lines) * row_h) if title_lines else 0

    height = title_h + row_h * (1 + len(rows))
    img = Image.new("RGB", (total_w + 1, height + 1), "white")
    d = ImageDraw.Draw(img)
    line = "#000000"

    def cell(x, y, w, h, text, bold=False):
        d.rectangle([x, y, x + w, y + h], outline=line, width=max(1, scale))
        tw, tht = _text_size(d, text, font)
        d.text((x + (w - tw) / 2, y + (h - tht) / 2 - 1), str(text),
               fill="#000000", font=font)

    y = 0
    if title_lines:
        d.rectangle([0, 0, total_w, title_h], outline=line, width=max(1, scale))
        ty = (title_h - len(title_lines) * row_h) / 2
        for i, ln in enumerate(title_lines):
            tw, _ = _text_size(d, ln, font)
            d.text(((total_w - tw) / 2, ty + i * row_h + pad / 2), ln,
                   fill="#000000", font=font)
        y = title_h

    # სათაურის რიგი
    x = 0
    for j in range(ncols):
        cell(x, y, col_w[j], row_h, headers[j], bold=True)
        x += col_w[j]
    y += row_h
    # მონაცემები
    for row in rows:
        x = 0
        for j in range(ncols):
            cell(x, y, col_w[j], row_h, row[j])
            x += col_w[j]
        y += row_h
    return img
