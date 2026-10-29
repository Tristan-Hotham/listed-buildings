"""Step 1: read the four national lists (and Wikidata, BUA22) from the browser bundle and
write one harmonised table, work/all.pkl.gz.

Inputs (read in place): RAW/lb18_core.json.gz (see README for sources and licences).
"""
import gzip, json, os, re, sys, pickle, datetime
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.strtree import STRtree
sys.path.insert(0, os.path.dirname(__file__))
from rules import building_type, ni_type, ni_date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.environ.get("RAW", "/home/claude/hist/_data18/listed-buildings")
COUNTIES = os.environ.get("COUNTIES", "/home/claude/hist/takeaways/data/counties.geojson")
COUNTY_CSV = os.environ.get("COUNTY_CSV", "/home/claude/hist/takeaways/data/counties.csv")

d = json.load(gzip.open(os.path.join(RAW, "lb18_core.json.gz")))
bng = Transformer.from_crs(27700, 4326, always_xy=True)
ig = Transformer.from_crs(29902, 4326, always_xy=True)


def clean(s):
    """Names as published: en and em dashes and double hyphens become plain hyphens."""
    s = (s or "").replace("\u2013", "-").replace("\u2014", "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip()


def ms_year(v):
    if v is None:
        return None
    return (datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=v)).year


rows = []  # nation, id, name, grade, list_year, type, rule, E, N, lon, lat, extra
for r in d["england"]["rows"]:
    le, name, grade, ld, ad, e, n = r
    t, rule = building_type(name)
    rows.append(dict(nation="England", id=str(le), name=clean(name), grade=grade, list_year=ms_year(ld),
                     type=t, rule=rule, E=e, N=n, url=f"https://historicengland.org.uk/listing/the-list/list-entry/{le}"))
# HES publishes one point per building ("entity"); a list entry (designation) can have several.
# Keep one row per designation, at its first entity, and count the entities.
sc_ent = {}
for r in d["scotland"]["rows"]:
    sc_ent[r[0]] = sc_ent.get(r[0], 0) + 1
seen = set()
for r in d["scotland"]["rows"]:
    ref, dt, et, cat, cl, des, la, par, x, y = r
    if ref in seen:
        continue
    seen.add(ref)
    if sc_ent[ref] > 1:
        et = None  # the entity name is one building of several; use the designation title
    t, rule = building_type(et or "")
    if t in ("other", "address"):
        t2, rule2 = building_type(dt or "")
        if t2 not in ("other", "address") or t == "other":
            t, rule = t2, rule2
    rows.append(dict(nation="Scotland", id=ref, name=clean(et or dt), grade=cat, list_year=ms_year(des),
                     type=t, rule=rule, E=x, N=y, url=f"https://portal.historicenvironment.scot/designation/{ref}",
                     council=la, parish=par, title=dt, n_entities=sc_ent[ref]))
for r in d["wales"]["rows"]:
    rec, name, dd, grade, bc, com, ua, e, n = r
    t, rule = building_type(name or "")
    rows.append(dict(nation="Wales", id=str(rec), name=clean(name), grade=grade,
                     list_year=int(dd[:4]) if dd else None, type=t, rule=rule, E=e, N=n,
                     url=f"https://cadwpublic-api.azurewebsites.net/reports/listedbuilding/FullReport?lang=en&id={rec}",
                     council=ua, community=com, broadclass=bc))
ni_kept = ni_drop = 0
for r in d["ni"]["rows"]:
    ref, gra, addr, dc, use, fuse, vern, thatch, der, town, council, x, y = r
    gra = (gra or "").strip()
    if gra not in ("A", "B+", "B1", "B2", "B") or ref in seen:
        ni_drop += 1
        continue
    ni_kept += 1
    seen.add(ref)
    t, rule = ni_type(use, addr)
    nm = clean(re.sub(r"\s+", " ", re.sub(r"\s*\n\s*", ", ", (addr or "").strip())).strip(" ,"))
    nd = ni_date(dc)
    rows.append(dict(nation="Northern Ireland", id=ref, name=nm, grade=gra, list_year=None, type=t, rule=rule,
                     X=x, Y=y, url="", council=council, ni_date=dc, ni_year=nd["year"] if nd else None,
                     ni_lo=nd["lo"] if nd else None, ni_hi=nd["hi"] if nd else None, use=use,
                     thatched=thatch, vernacular=vern, derelict=der))

# coordinates
for r in rows:
    if r["nation"] == "Northern Ireland":
        if r.get("X") is None:
            r["lon"] = r["lat"] = None
            continue
        lon, lat = ig.transform(r["X"], r["Y"])
    else:
        if r.get("E") is None:
            r["lon"] = r["lat"] = None
            continue
        lon, lat = bng.transform(r["E"], r["N"])
    r["lon"], r["lat"] = round(lon, 5), round(lat, 5)

# counties and unitary authorities (ONS Dec 2023, simplified, via the takeaways project)
gj = json.load(open(COUNTIES))
import csv
cty = list(csv.DictReader(open(COUNTY_CSV)))
geoms = [shape(f["geometry"]).buffer(0) for f in gj["features"]]
tree = STRtree(geoms)
for r in rows:
    r["county_i"] = None
    if r["lat"] is None:
        continue
    p = Point(r["lon"], r["lat"])
    hits = [i for i in tree.query(p) if geoms[i].contains(p)]
    if not hits:
        i = int(tree.nearest(p))
        if geoms[i].distance(p) < 0.05:  # about 3 to 5 km: coastal points outside the simplified outline
            hits = [i]
    if hits:
        r["county_i"] = int(hits[0])
for r in rows:
    i = r["county_i"]
    r["county_code"] = cty[i]["code"] if i is not None else None
    r["county"] = cty[i]["name"] if i is not None else None
    r["county_nation"] = cty[i]["nation"] if i is not None else None

# built-up areas (ONS BUA22, GB), in British National Grid
polys, bmeta = [], []
for code, nm, area, rings in d["bua22"]["rows"]:
    if not rings:
        continue
    # ArcGIS rings: outer rings clockwise, holes anticlockwise
    outers, holes = [], []
    for ring in rings:
        if len(ring) < 4:
            continue
        a = sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1))
        (outers if a < 0 else holes).append(ring)
    ps = []
    for o in outers:
        po = Polygon(o)
        hs = [h for h in holes if po.contains(Point(h[0]))]
        ps.append(Polygon(o, hs).buffer(0))
    if not ps:
        continue
    g = ps[0] if len(ps) == 1 else MultiPolygon([q for p in ps for q in (p.geoms if hasattr(p, "geoms") else [p])]).buffer(0)
    polys.append(g)
    bmeta.append((code, nm, area))
btree = STRtree(polys)
for r in rows:
    r["bua"] = r["bua_name"] = None
    if r["nation"] == "Northern Ireland" or r.get("E") is None:
        continue
    p = Point(r["E"], r["N"])
    hits = [i for i in btree.query(p) if polys[i].contains(p)]
    if hits:
        r["bua"], r["bua_name"] = bmeta[hits[0]][0], bmeta[hits[0]][1]

os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
meta = dict(scotland_entities=len(d["scotland"]["rows"]), scotland_entity_counts=sc_ent, source=d["source"], licence=d["licence"], retrieved=d["retrieved"][:10], ni_kept=ni_kept, ni_dropped=ni_drop,
            bua=[dict(code=c, name=n, area=a) for c, n, a in bmeta])
pickle.dump(dict(rows=rows, meta=meta, wikidata_tsv=d["wikidata_tsv"]), gzip.open(os.path.join(ROOT, "work", "all.pkl.gz"), "wb"))
from collections import Counter
print(len(rows), Counter(r["nation"] for r in rows), "ni dropped", ni_drop)
print("no county", sum(1 for r in rows if r["county"] is None), "in BUA", sum(1 for r in rows if r["bua"]))
print(Counter(r["type"] for r in rows).most_common())
