# -*- coding: utf-8 -*-
"""ერთიანი ორენოვანი (en/ka) თარგმანის დამხმარე — ერთი lookup-ლოგიკა ყველა
ხელსაწყოსთვის.

თითო ხელსაწყო ინახავს თავის ``CATALOG``-ს (scoped, collision-safe); ხშირად
გამეორებადი გასაღებები ``COMMON``-შია (fallback). ლოგიკა (ენა → en → key,
``.format(**fmt)``) აქ ერთ ადგილას ცხოვრობს — აღარ დუბლირდება ხელსაწყოებში.
"""

DEFAULT_LANG = "en"

# საერთო, ხშირად გამეორებადი გასაღებები — fallback ნებისმიერი ხელსაწყოსთვის.
COMMON = {
    "browse": {"en": "Browse…", "ka": "დათვალიერება…"},
    "err":    {"en": "Error", "ka": "შეცდომა"},
    "done":   {"en": "done", "ka": "დასრულდა"},
}


def translate(catalog, key, lang, common=COMMON, **fmt):
    """თარგმანი: ჯერ ხელსაწყოს CATALOG, მერე COMMON; ენა → en → key.

    fmt-ის არსებობისას ედება ``.format(**fmt)`` (როგორც ძველ tr()-ებში)."""
    entry = catalog.get(key)
    if entry is None and common:
        entry = common.get(key)
    if entry is None:
        return key
    s = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    return s.format(**fmt) if fmt else s
