# GIS_BOX

პატარა GIS ინსტრუმენტების კრებული ერთ ფანჯარაში (tkinter).
A small collection of GIS tools in one window (tkinter).

ინტერფეისი **ორენოვანია** — ქართული / English (ზედა ზოლის გადამრთველი).
The UI is **bilingual** — Georgian / English (top-bar switch).

---

## ინსტრუმენტები / Tools

| ინსტრუმენტი | აღწერა |
|---|---|
| **შაბლონის კოპირება** / Template copy | კოპირებს შაბლონურ shapefile-ს ყველა თანმხლები ფაილით (`.shp/.shx/.dbf/.prj/…`), ზრდადი სუფიქსით. |
| **ნაკვეთის ძებნა** / Parcel search | ეძებს საკადასტრო კოდებს File Geodatabase-ში და ქმნის Shapefile + GeoPackage; ვერ ნაპოვნ კოდებს ცალკე ინახავს. |
| **კოორდინატების ამომღები** / Coordinate extractor | რუკის სურათიდან/PDF-იდან ამოიღებს კოორდინატების ცხრილს (OCR) ან გეო-რეფერენსით ითვლის პოლიგონის წვეროებსა და ფართობს. |

---

## გაშვება / Run

```bash
python gis_box.py
```

ან Windows-ზე ორმაგი დაწკაპუნებით: `GIS_BOX.bat`.
Or on Windows double-click `GIS_BOX.bat`.

### დამოკიდებულებები / Dependencies

ბაზისური ხელსაწყო (შაბლონის კოპირება) მხოლოდ სტანდარტულ ბიბლიოთეკას იყენებს.
დანარჩენი ხელსაწყოებისთვის:

The base tool (template copy) uses only the standard library. For the other tools:

```bash
pip install -r requirements.txt
```

თუ პაკეტი აკლია, GIS_BOX მაინც გაიხსნება — შესაბამისი ხელსაწყო უბრალოდ შეცდომას აჩვენებს.
If a package is missing, GIS_BOX still opens — the affected tool just shows an error.

---

## კონფიგურაცია / Configuration

**ნაკვეთის ძებნა** მოითხოვს შენი File Geodatabase-ის გზას. ეს გზა **კოდში არ იწერება**:

The **Parcel search** tool needs the path to your File Geodatabase. This path is **not stored in the code**:

1. ხელსაწყოში ჩაწერე GDB-ის გზა, შრე და კოდის ველი.
   Enter the GDB path, layer and code field in the tool.
2. დააჭირე **„💾 პარამეტრების დამახსოვრება“**.
   Click **“💾 Remember settings”**.
3. პარამეტრები შეინახება ლოკალურ `gis_box_settings.json`-ში და მომდევნო გაშვებაზეც დაიმახსოვრდება.
   Settings are saved to the local `gis_box_settings.json` and remembered next time.

`gis_box_settings.json` და `config.txt` **`.gitignore`-შია** და GitHub-ზე არ აიტვირთება.
`gis_box_settings.json` and `config.txt` are **git-ignored** and never uploaded to GitHub.

ალტერნატივა (არასავალდებულო): დააკოპირე `config.example.txt` → `config.txt` და ჩაწერე გზა.
Alternative (optional): copy `config.example.txt` → `config.txt` and set your path.

---

## პროექტის სტრუქტურა / Project layout

```
GIS_BOX/
├─ gis_box.py            # მთავარი აპლიკაცია / main app (sidebar + lazy loading)
├─ tools/
│  ├─ base.py            # ToolFrame ბაზისური კლასი
│  ├─ parcel_search.py   # ნაკვეთის ძებნა
│  ├─ coord_tool.py      # კოორდინატების ამომღების wrapper
│  └─ coordextract/      # OCR + გეო-რეფერენსის პაკეტი
├─ shp/                  # შაბლონური shapefile-ები (ცარიელი / საჯარო UTM ბადე)
├─ config.example.txt    # კონფიგის ნიმუში (config.txt git-ignored)
└─ requirements.txt
```

ახალი ხელსაწყოს დასამატებლად: შექმენი `ToolFrame`-ის მემკვიდრე კლასი და დაარეგისტრირე
`gis_box.py`-ის `_build_tool_specs()`-ში.

To add a new tool: subclass `ToolFrame` and register it in `_build_tool_specs()` in `gis_box.py`.

---

## ლიცენზია / License

MIT — იხ. [LICENSE](LICENSE).
