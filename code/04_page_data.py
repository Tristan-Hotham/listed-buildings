"""Step 4: compact files for the page and the main published table.

data/points.bin.gz   every list entry as columns (gzip, unpacked in the browser):
                     u32 cell offsets, u16 x, u16 y, u8 nation*4+tier, u8 type, u8 listed year-1900,
                     u8 built (decade index, (year-500)/10), u8 county index, u8 date source
data/names/NN.json.gz  [id, name] for the same points in the same order, in chunks
data/listed_buildings_uk.csv.gz  the harmonised table (one row per list entry)
data/counties.geojson  county and unitary authority outlines (ONS, simplified), with per head numbers
data/places.json     place names for labels and search (OS Open Names and GeoNames, via the takeaways project)
"""
import gzip, json, os, sys, pickle, csv, struct, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COUNTIES = os.environ.get("COUNTIES", "/home/claude/hist/takeaways/data/counties.geojson")
PLACES = os.environ.get("PLACES", "/home/claude/hist/takeaways/data/places.json")
A = pickle.load(gzip.open(os.path.join(ROOT, "work", "analysed.pkl.gz")))
rows, counties = A["rows"], A["counties"]
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]
TYPES = R["type_order"]
W, S, E, N = -8.75, 49.85, 1.85, 60.95
CELL = 0.1
NX, NY = int(round((E - W) / CELL)), int(round((N - S) / CELL))
CHUNK = 6000
SRC = {None: 0, "HE list entry text (sample)": 1, "HES list description (sample)": 1, "Cadw full report": 1,
       "NI Historic Buildings Record": 2, "Wikidata": 3}

pts = [r for r in rows if r["lat"] is not None and S <= r["lat"] < N and W <= r["lon"] < E]
dropped = len(rows) - len(pts)
cidx = {c["code"]: i for i, c in enumerate(counties)}
for r in pts:
    cx = int((r["lon"] - W) / CELL); cy = int((r["lat"] - S) / CELL)
    r["_cell"] = cy * NX + cx
pts.sort(key=lambda r: (r["_cell"], r["lat"], r["lon"]))
n = len(pts)
off = np.zeros(NX * NY + 1, dtype="<u4")
cnt = np.bincount([r["_cell"] for r in pts], minlength=NX * NY)
off[1:] = np.cumsum(cnt)
x = np.array([round((r["lon"] - W) / (E - W) * 65535) for r in pts], dtype="<u2")
y = np.array([round((r["lat"] - S) / (N - S) * 65535) for r in pts], dtype="<u2")
nt = np.array([NATIONS.index(r["nation"]) * 4 + r["tier"] for r in pts], dtype="u1")
ty = np.array([TYPES.index(r["type"]) for r in pts], dtype="u1")
ly = np.array([(r["list_year"] - 1900) if r["list_year"] else 0 for r in pts], dtype="u1")
by = np.array([max(1, min(255, round((r["built_year"] - 500) / 10))) if r["built_year"] else 0 for r in pts], dtype="u1")
co = np.array([cidx.get(r["county_code"], 255) for r in pts], dtype="u1")
sr = np.array([SRC[r["built_src"]] for r in pts], dtype="u1")
buf = off.tobytes() + x.tobytes() + y.tobytes() + nt.tobytes() + ty.tobytes() + ly.tobytes() + by.tobytes() + co.tobytes() + sr.tobytes()
with gzip.open(os.path.join(ROOT, "data", "points.bin.gz"), "wb", compresslevel=9) as f:
    f.write(buf)

nd = os.path.join(ROOT, "data", "names")
shutil.rmtree(nd, ignore_errors=True)
os.makedirs(nd)
for k in range(0, n, CHUNK):
    part = [[r["id"], (r["name"] or "")[:110]] for r in pts[k:k + CHUNK]]
    with gzip.open(os.path.join(nd, f"{k // CHUNK:03d}.json.gz"), "wt", encoding="utf-8", compresslevel=9) as f:
        json.dump(part, f, ensure_ascii=False, separators=(",", ":"))

meta = dict(n=n, bbox=[W, S, E, N], cell=CELL, nx=NX, ny=NY, chunk=CHUNK, nations=NATIONS, types=TYPES,
            dropped=dropped)
json.dump(meta, open(os.path.join(ROOT, "work", "points_meta.json"), "w"))

# counties geojson with numbers (copy of the ONS outlines used in the takeaways project, plus our fields)
gj = json.load(open(COUNTIES))
for i, f in enumerate(gj["features"]):
    c = counties[i]
    f["properties"] = dict(i=i, code=c["code"], name=c["name"], nation=c["nation"], pop=c["pop"], n=c["n"],
                           per_1000=c["per_1000"], top_pct=c["top_pct"])
    # round coordinates to 4 decimals (about 10 m)
    def rnd(o):
        return [rnd(v) for v in o] if isinstance(o[0], list) else [round(o[0], 4), round(o[1], 4)]
    f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
json.dump(gj, open(os.path.join(ROOT, "data", "counties.geojson"), "w"), separators=(",", ":"))
shutil.copy(PLACES, os.path.join(ROOT, "data", "places.json"))

# the main tables, one per nation (each under 9 MB)
cols = ["id", "name", "grade", "tier", "list_year", "type", "lat", "lon", "county_code", "bua22_code",
        "built_year", "built_source", "ni_date_band"]
SRCS = {"HE list entry text (sample)": "text", "HES list description (sample)": "text", "Cadw full report": "text",
        "NI Historic Buildings Record": "ni_band", "Wikidata": "wikidata"}
for f in os.listdir(os.path.join(ROOT, "data")):
    if f.startswith("listed_") and f.endswith(".csv.gz"):
        os.remove(os.path.join(ROOT, "data", f))
parts = [("england_part1", lambda r: r["nation"] == "England" and r["region"] in ("North East", "North West", "Yorkshire and The Humber", "East Midlands", "West Midlands")),
         ("england_part2", lambda r: r["nation"] == "England" and r["region"] not in ("North East", "North West", "Yorkshire and The Humber", "East Midlands", "West Midlands")),
         ("scotland", lambda r: r["nation"] == "Scotland"), ("wales", lambda r: r["nation"] == "Wales"),
         ("northern_ireland", lambda r: r["nation"] == "Northern Ireland")]
for nm, keep in parts:
    fn = os.path.join(ROOT, "data", "listed_" + nm + ".csv.gz")
    with gzip.open(fn, "wt", encoding="utf-8", newline="", compresslevel=9) as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            if not keep(r):
                continue
            w.writerow([r["id"], r["name"], r["grade"], r["tier"], r["list_year"] or "", r["type"],
                        r["lat"], r["lon"], r["county_code"] or "", r["bua"] or "", r["built_year"] or "",
                        SRCS.get(r["built_src"], ""), (r.get("ni_date") or "").strip()])
    print(fn, os.path.getsize(fn))
print("points", n, "dropped", dropped, "bin", os.path.getsize(os.path.join(ROOT, "data", "points.bin.gz")),
      "names", sum(os.path.getsize(os.path.join(nd, f)) for f in os.listdir(nd)), len(os.listdir(nd)))

# the parsed dates (no listing text): England and Scotland samples and every Welsh entry
DT = pickle.load(gzip.open(os.path.join(ROOT, "work", "dates.pkl.gz")))
with gzip.open(os.path.join(ROOT, "data", "build_dates_parsed.csv.gz"), "wt", encoding="utf-8", newline="", compresslevel=9) as f:
    w = csv.writer(f)
    w.writerow(["nation", "id", "in_sample", "year_estimate", "century", "kind", "matched_words", "basis", "earliest_year_in_text", "weight"])
    for nat in ("England", "Scotland", "Wales"):
        for x in DT["samples"][nat]:
            w.writerow([nat, x["id"], "random sample" if nat != "Wales" else "all", x.get("year", ""), x.get("century", ""),
                        x.get("kind", ""), (x.get("match") or "").replace("–", "-").replace("—", "-"), x.get("basis", ""),
                        x.get("earliest", ""), round(x.get("w", 1), 4)])
print("build_dates_parsed", os.path.getsize(os.path.join(ROOT, "data", "build_dates_parsed.csv.gz")))
