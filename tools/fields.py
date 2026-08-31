# -*- coding: utf-8 -*-
"""კოდის ველის შერჩევის ლოგიკა (სუფთა, ტესტირებადი).

საკადასტრო კოდები string-ველშია (CADCODE), არა რიცხვით ID-ში (CADCODE_ID),
ამიტომ „*_ID“ ველი უნდა გასწორდეს მის არა-ID ანალოგზე.
"""


def pick_code_field(fields, current, default="CADCODE"):
    """დააბრუნებს კოდის ველს ``fields``-იდან:

    • მოქმედ არჩევანს ინარჩუნებს, მაგრამ „*_ID“-ს ასწორებს არა-ID ანალოგზე,
      თუ არსებობს (CADCODE_ID → CADCODE);
    • თუ არჩევანი აღარ არსებობს — ჯერ ზუსტი ცნობილი სახელი (``default`` /
      CADCODE), შემდეგ „CAD“-ის შემცველი არა-ID ველი, შემდეგ პირველი.
    """
    fields = list(fields)
    if current in fields:
        if current.upper().endswith("_ID"):
            base = current[:-3]
            if base in fields:
                return base
            for f in fields:
                if f.upper() == current.upper()[:-3]:
                    return f
        return current
    for pref in (default, "CADCODE"):
        if pref and pref in fields:
            return pref
    cad = [f for f in fields if "CAD" in f.upper()]
    non_id = [f for f in cad if not f.upper().endswith("ID")]
    if non_id:
        return non_id[0]
    if cad:
        return cad[0]
    return fields[0] if fields else ""
