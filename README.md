# GIS_BOX

პატარა GIS ინსტრუმენტების კრებული ერთ ფანჯარაში (tkinter).
A small collection of GIS tools in one window (tkinter).

ინტერფეისი **ორენოვანია** — ქართული / English (ზედა ზოლის გადამრთველი).
The UI is **bilingual** — Georgian / English (top-bar switch).

---

## ინსტრუმენტები / Tools

| ინსტრუმენტი | აღწერა |
|---|---|
| **შაბლონის კოპირება** / Template copy | კოპირებს შაბლონურ shapefile-ს ყველა თანმხლები ფაილით (`.shp/.shx/.dbf/.prj/…`), ზრდადი სუფიქსით. რამდენიმე ნაკრები (მდინარის ნაპირი, გაზსადენის გადაკვეთა, დაცვის ზონა, UTM ბადე) — ახლის დამატება ერთი ჩანაწერით. |
| **ნაკვეთის ძებნა** / Parcel search | ეძებს საკადასტრო კოდებს File Geodatabase-ში და ქმნის Shapefile + GeoPackage; ვერ ნაპოვნ კოდებს ცალკე ინახავს. **რამდენიმე ბაზა** ჩამოსაშლელ სიაში; შრეები ავტომატურად იკითხება (CadData-ის რეგიონები ქართული სახელით — „R02 — ქვემო ქართლი“), შრე და კოდის ველი არჩევადია. |
| **კოორდინატების ამომღები** / Coordinate extractor | რუკის სურათიდან/PDF-იდან ამოიღებს კოორდინატების ცხრილს (OCR) ან გეო-რეფერენსით ითვლის პოლიგონის წვეროებსა და ფართობს; Excel-ში გატანა და ფორმატირება. |
| **სახელების გადარქმევა** / Rename → Latin | საქაღალდის ქართულ-სახელიან shapefile-ებს გადაარქმევს ლათინურად (სფეისი/სიმბოლო → `_`), წინასწარი სიით. ასევე ამოწმებს რომელ shapefile-ში დევს მასალა და რომელი ცარიელია. |
| **Shp → კოორდინატები** / Shp → coordinates | წერტილოვანი shapefile-იდან კითხულობს X/Y-ს UTM ზონით (37/38, .prj-დან ან ხელით), წინასწარი ცხრილით; გააქვს დაფორმატებულ Excel-ში — ტექსტური ქუდი, `№/X/Y`, არჩევითი „გადაკვეთის კუთხე“ (°), center+borders. **Batch** — საქაღალდის ყველა წერტილოვანი shapefile ერთბაშად. |

---

## ჩამოტვირთვა (მზა ბილდი) / Download (prebuilt)

Python-ის გარეშე გასაშვებად იხილე **[Releases](https://github.com/kapo-Toolkits/gis-toolkit/releases)** —
`v*` ტეგზე CI ავტომატურად აწყობს დამოუკიდებელ ბილდებს:

For a no-Python run, see the **[Releases](https://github.com/kapo-Toolkits/gis-toolkit/releases)** page —
each `v*` tag builds standalone artifacts:

| პლატფორმა | ფაილი |
|---|---|
| Windows | `GIS_BOX-windows-x64.zip` (გახსენი და გაუშვი `GIS_BOX.exe`) |
| Linux | `GIS_BOX-linux-x64.tar.gz`, `.deb`, `.rpm`, `.AppImage` |

ლოკალურად ასაწყობად: `pip install pyinstaller -r requirements.txt && pyinstaller gis_box.spec`
(გამოსავალი — `dist/GIS_BOX/`).

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

რამდენიმე ბაზა ერთბაშად — `config.txt`-ში: `GDBS=path1;path2;path3` (ან ხელსაწყოში
თითო ბაზა დაამატე „💾 დამახსოვრებით“). ხელსაწყო ჩამოსაშლელ სიაში გადაგირთავს.

Several databases at once — in `config.txt`: `GDBS=path1;path2;path3` (or add each one in the
tool via “💾 Remember”). The tool switches between them via the dropdown.

---

## პროექტის სტრუქტურა / Project layout

```
GIS_BOX/
├─ gis_box.py                # მთავარი აპლიკაცია / main app (sidebar + lazy loading)
├─ tools/
│  ├─ base.py                # ToolFrame ბაზისური კლასი
│  ├─ parcel_search.py       # ნაკვეთის ძებნა (მრავალი ბაზა)
│  ├─ rename_transliterate.py# სახელების გადარქმევა + მასალის შემოწმება
│  ├─ shp_coords.py          # Shp → კოორდინატები (Excel, batch)
│  ├─ coord_tool.py          # კოორდინატების ამომღების wrapper
│  ├─ coordextract/          # OCR + გეო-რეფერენსის პაკეტი
│  ├─ translit.py            # ქართული→ლათინური (სუფთა ლოგიკა)
│  ├─ fields.py              # კოდის ველის ავტო-შერჩევა
│  ├─ regions.py             # CadData რეგიონების სახელები
│  └─ xlsx_format.py         # საერთო Excel-ფორმატირება
├─ tests/                    # pytest — სუფთა ლოგიკის ტესტები
├─ packaging/                # nfpm (.deb/.rpm) + .desktop
├─ gis_box.spec              # PyInstaller — დამოუკიდებელი ბილდი
├─ shp/                      # შაბლონური shapefile-ები (ცარიელი / საჯარო UTM ბადე)
├─ config.example.txt        # კონფიგის ნიმუში (config.txt git-ignored)
├─ GIS_BOX.bat / .command / .desktop  # გამშვებები Windows / macOS / Linux
├─ requirements.txt          # ხელსაწყოების დამოკიდებულებები
└─ requirements-dev.txt      # ტესტების/დეველოპმენტის დამოკიდებულებები
```

ახალი ხელსაწყოს დასამატებლად: შექმენი `ToolFrame`-ის მემკვიდრე კლასი და დაარეგისტრირე
`gis_box.py`-ის `_build_tool_specs()`-ში. სუფთა ლოგიკა (გამოთვლა/ფორმატირება) ცალკე
მოდულში გაიტანე (`tools/`-ში), რომ GUI-ს გარეშე დატესტვადი იყოს.

To add a new tool: subclass `ToolFrame` and register it in `_build_tool_specs()` in `gis_box.py`.
Keep pure logic (computation/formatting) in a separate module so it is testable without the GUI.

---

## ტესტები / Tests

სუფთა ლოგიკა (ტრანსლიტერაცია, ველის შერჩევა, რეგიონები, Excel-ფორმატირება) დაფარულია
pytest-ით; CI ყოველ push/PR-ზე უშვებს მათ Python 3.11/3.12-ზე.

Pure logic (transliteration, field selection, regions, Excel formatting) is covered by pytest;
CI runs it on every push/PR (Python 3.11/3.12).

```bash
pip install -r requirements-dev.txt
pytest
```

---

## ლიცენზია / License

MIT — იხ. [LICENSE](LICENSE).
