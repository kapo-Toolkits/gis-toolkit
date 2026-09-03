# -*- coding: utf-8 -*-
"""ფაილების შეგროვება ერთ საქაღალდეში — სუფთა ლოგიკა (tkinter-ის გარეშე).

საწყისი საქაღალდის ხიდან (არჩევით ქვესაქაღალდეებითურთ) აგროვებს მითითებული
გაფართოების ფაილებს ერთ, ბრტყელ სამიზნე საქაღალდეში. სახელის დამთხვევისას
ამატებს ინკრემენტულ სუფიქსს: „name.docx“ → „name_1.docx“ → „name_2.docx“ …

ცალკე მოდულში, რომ ტესტირებადი იყოს UI-ის გარეშე. UI: ``tools.file_gather``.
"""

import os
import shutil


def norm_exts(text):
    """ გაფართოებების ტექსტი → ნორმალიზებული ცხრილი.

    მიიღება მძიმით/სფეისით გამოყოფილი სია (მაგ. „docx, doc“, „.pdf .txt“);
    აბრუნებს lower-case, წერტილიან, უნიკალურ tuple-ს: ('.docx', '.doc').
    ცარიელი შემოსვლა → ცარიელი tuple (= ყველა ფაილი).
    """
    out = []
    for part in str(text or "").replace(",", " ").split():
        e = part.strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        if e not in out:
            out.append(e)
    return tuple(out)


def iter_matches(source_dir, exts, recursive=True):
    """საწყისი ხიდან შესაბამისი ფაილების სრული გზები (დალაგებული)."""
    exts = tuple(e.lower() for e in exts)
    hits = []
    if recursive:
        walker = os.walk(source_dir)
    else:
        walker = [(source_dir, [], [f for f in os.listdir(source_dir)
                                    if os.path.isfile(os.path.join(source_dir, f))])]
    for root, _dirs, files in walker:
        for name in files:
            if not exts or name.lower().endswith(exts):
                hits.append(os.path.join(root, name))
    hits.sort(key=lambda p: (os.path.dirname(p).lower(), os.path.basename(p).lower()))
    return hits


def unique_dest(dest_dir, filename, taken):
    """დანიშნულებაში კონფლიქტის-გარეშე გზა.

    თუ „name.ext“ უკვე დევს (დისკზე ან ამ გაშვების ``taken`` სიმრავლეში),
    ცდის „name_1.ext“, „name_2.ext“ … ``taken`` — normcase-ული გზების set,
    რომელიც ამ ფუნქციამ ავსდის (რომ ერთ გაშვებაში ორმა ფაილმა ერთი სახელი
    არ დაიკავოს, ფაქტობრივი კოპირების დაძახებამდეც).
    """
    base, ext = os.path.splitext(filename)
    cand = os.path.join(dest_dir, filename)
    counter = 1
    while os.path.normcase(cand) in taken or os.path.exists(cand):
        cand = os.path.join(dest_dir, "{}_{}{}".format(base, counter, ext))
        counter += 1
    taken.add(os.path.normcase(cand))
    return cand


def gather(source_dir, dest_dir, exts, recursive=True,
           log=None, progress=None, is_cancelled=None):
    """ფაილების შეგროვება. აბრუნებს dict-ს შედეგებით.

    ``log(msg)`` — თითო სტრიქონი; ``progress(i, n)`` — მიმდინარეობა;
    ``is_cancelled()`` — True თუ უნდა შევჩერდეთ. მეტამონაცემები shutil.copy2-ით
    (თარიღები) ნარჩუნდება.
    """
    log = log or (lambda _m: None)
    progress = progress or (lambda _i, _n: None)
    is_cancelled = is_cancelled or (lambda: False)

    matches = iter_matches(source_dir, exts, recursive)
    n = len(matches)
    os.makedirs(dest_dir, exist_ok=True)

    taken = set()
    copied = skipped = 0
    errors = []
    for i, src in enumerate(matches, 1):
        if is_cancelled():
            return {"copied": copied, "skipped": skipped, "total": n,
                    "errors": errors, "cancelled": True}
        dst = unique_dest(dest_dir, os.path.basename(src), taken)
        try:
            shutil.copy2(src, dst)
            copied += 1
            log("✓ {}  →  {}".format(os.path.basename(src),
                                              os.path.basename(dst)))
        except Exception as e:                       # noqa: BLE001
            skipped += 1
            errors.append((src, str(e)))
            log("✗ {}: {}".format(os.path.basename(src), e))
        progress(i, n)

    return {"copied": copied, "skipped": skipped, "total": n,
            "errors": errors, "cancelled": False}
