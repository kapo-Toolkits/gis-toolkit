# -*- coding: utf-8 -*-
"""ქართული→ლათინური ტრანსლიტერაცია და shapefile-ის ობიექტების დათვლა.

სუფთა ლოგიკა — tkinter/GIS დამოკიდებულებების გარეშე, რომ ცალკე ტესტირებადი
იყოს. აქედან იმპორტს აკეთებს ``tools.rename_transliterate``.
"""

import os
import re

# ---- ქართული → ლათინური ცხრილი --------------------------------------------
# ყ → y (მომხმარებლის მაგალითის მიხედვით: „საყრდენი“ → „sayrdeni“).
GEO2LAT = {
    "ა": "a", "ბ": "b", "გ": "g", "დ": "d", "ე": "e", "ვ": "v", "ზ": "z",
    "თ": "t", "ი": "i", "კ": "k", "ლ": "l", "მ": "m", "ნ": "n", "ო": "o",
    "პ": "p", "ჟ": "zh", "რ": "r", "ს": "s", "ტ": "t", "უ": "u", "ფ": "f",
    "ქ": "k", "ღ": "gh", "ყ": "y", "შ": "sh", "ჩ": "ch", "ც": "ts", "ძ": "dz",
    "წ": "ts", "ჭ": "ch", "ხ": "kh", "ჯ": "j", "ჰ": "h",
    # არქაული / იშვიათი
    "ჱ": "e", "ჲ": "y", "ჳ": "w", "ჴ": "q", "ჵ": "o", "ჶ": "f",
}
GEO_RANGE = re.compile(r"[Ⴀ-ჿ]")   # ქართული ასოს არსებობის შემოწმება


def transliterate(name):
    """ფაილის სახელი → ლათინური.

    • ქართული ასო → ლათინური შესაბამისობა
    • ლათინური ასო, ციფრი და წერტილი (გაფართოებისთვის) — უცვლელი
    • ნებისმიერი სხვა სიმბოლო (სფეისი, მძიმე, ტირე, ფრჩხილი და ა.შ.) → „_“

    ზედიზედ მრავალი „_“ ერთამდე იკუმშება; წერტილის წინ და კიდეებში „_“ იშლება.
    """
    out = []
    for ch in name:
        if ch in GEO2LAT:
            out.append(GEO2LAT[ch])
        elif ch.isascii() and (ch.isalnum() or ch == "."):
            out.append(ch)               # ლათინური/ციფრი/წერტილი — უცვლელი
        else:
            out.append("_")              # სფეისი, მძიმე, ნებისმიერი სხვა სიმბოლო
    s = re.sub(r"_{2,}", "_", "".join(out))
    s = re.sub(r"_+\.", ".", s)          # წერტილის წინ „_“ არ დავტოვოთ
    return s.strip("_")


def _sibling(path, ext):
    """მოცემული ფაილის გვერდით მყოფი იმავე base-ის ფაილი მითითებული
    გაფართოებით (რეგისტრის მიუხედავად). აბრუნებს გზას ან None."""
    base = os.path.splitext(path)[0]
    for e in (ext.lower(), ext.upper()):
        cand = base + e
        if os.path.exists(cand):
            return cand
    return None


def feature_count(shp_path):
    """Shapefile-ის ობიექტების რაოდენობა — დამოკიდებულებების გარეშე.

    ObjectCount == .dbf-ის ჩანაწერების რაოდენობა (header-ის ბაიტები 4..7,
    little-endian uint32). თუ .dbf არ არის — .shp-ის header-ის სიგრძით
    ვადგენთ ცარიელობას (100 ბაიტი = მხოლოდ header, 0 გეომეტრია).
    აბრუნებს int-ს, ან None თუ ვერ წავიკითხეთ."""
    dbf = _sibling(shp_path, ".dbf")
    if dbf:
        try:
            with open(dbf, "rb") as f:
                head = f.read(8)
            if len(head) >= 8:
                return int.from_bytes(head[4:8], "little")
        except OSError:
            pass
    # fallback — .shp-ის header (ბაიტები 24..27, big-endian, 16-ბიტიან სიტყვებში)
    try:
        with open(shp_path, "rb") as f:
            head = f.read(100)
        if len(head) >= 28:
            words = int.from_bytes(head[24:28], "big")
            return 0 if words * 2 <= 100 else -1   # -1 = „მასალა დევს“, ზუსტი N უცნობია
    except OSError:
        pass
    return None
