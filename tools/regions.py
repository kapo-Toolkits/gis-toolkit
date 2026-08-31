# -*- coding: utf-8 -*-
"""CadData.gdb-ის დათასეთების კოდები → საქართველოს რეგიონები.

სუფთა ლოგიკა (დამოკიდებულებების გარეშე), რომ ცალკე ტესტირებადი იყოს. აქედან
იმპორტს აკეთებს ``tools.parcel_search`` შრეების ჩამონათვალის „სანიშნეებისთვის“.
"""

REGION_CODES = {
    "R02": "ქვემო ქართლი",
    "R03": "მცხეთა-მთიანეთი",
    "R04": "აჭარა",
    "R05": "სამეგრელო-ზემო სვანეთი",
    "R06": "კახეთი",
    "R07": "შიდა ქართლი",
    "R08": "გურია",
    "R09": "სამცხე-ჯავახეთი",
    "R10": "იმერეთი",
    "R11": "რაჭა ლეჩხუმი-ქვემო სვანეთი",
    "R12": "აფხაზეთი",
    "Z01": "თბილისი",
}


def region_name(raw):
    """შრის ნამდვილი სახელიდან რეგიონის დასახელება (ან None)."""
    if not raw:
        return None
    up = raw.upper()
    if up in REGION_CODES:
        return REGION_CODES[up]
    for code, name in REGION_CODES.items():          # პრეფიქსით (მაგ. R02_Parcels)
        if up.startswith(code):
            return name
    return None


def layer_display(raw):
    """შრის სახელი ჩამონათვალისთვის: „R02 — ქვემო ქართლი“ (თუ რეგიონია)."""
    name = region_name(raw)
    return f"{raw} — {name}" if name else raw


def layer_code(display):
    """ჩამონათვალის ჩანაწერიდან შრის ნამდვილი სახელი (რეგიონის სუფიქსის გარეშე)."""
    return display.split(" — ", 1)[0].strip() if display else display
