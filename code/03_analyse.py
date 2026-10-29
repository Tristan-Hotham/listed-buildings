"""Step 3: every number. Writes data/results.json and the cleaned tables in data/."""
import gzip, json, os, sys, pickle, math, csv, random
from collections import Counter, defaultdict
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
from rules import TYPES, TYPE_LABEL

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ONSGEO = os.environ.get("ONSGEO", "/home/claude/hist/_data8/ons_geo.json")
LSOA_BUA = os.environ.get("LSOA_BUA", "/home/claude/hist/_data8/lsoa21_bua22_lookup.json")
TS001 = os.environ.get("TS001", "/home/claude/hist/_data8/census/census2021-ts001-lsoa.csv")
COUNTY_CSV = os.environ.get("COUNTY_CSV", "/home/claude/hist/takeaways/data/counties.csv")

D = pickle.load(gzip.open(os.path.join(ROOT, "work", "all.pkl.gz")))
rows, meta = D["rows"], D["meta"]
DT = pickle.load(gzip.open(os.path.join(ROOT, "work", "dates.pkl.gz")))
dates, samples, wd = DT["dates"], DT["samples"], DT["wikidata"]
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]
key = lambda r: r["nation"] + ":" + str(r["id"])
R = {}
pct = lambda a, b: round(100 * a / b, 1) if b else None


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


# ------------------------------------------------ grades
TOP = {"England": "I", "Wales": "I", "Scotland": "A", "Northern Ireland": "A"}
MID = {"England": "II*", "Wales": "II*", "Scotland": "B", "Northern Ireland": "B+"}
def tier(r):
    g = (r["grade"] or "").replace(" ", "")
    if g == TOP[r["nation"]]:
        return 1
    if g == MID[r["nation"]]:
        return 2
    return 3
for r in rows:
    r["tier"] = tier(r)
    r["type2"] = r["type"]

# ------------------------------------------------ populations
cty = list(csv.DictReader(open(COUNTY_CSV)))
cpop = {c["code"]: int(c["pop"]) for c in cty}
pop_year = cty[0]["pop_year"]
npop = Counter()
for c in cty:
    npop[c["nation"]] += int(c["pop"])

# England regions from the nearest MSOA population-weighted centroid (ONS)
og = json.load(open(ONSGEO))
look = {m["MSOA21CD"]: m for m in og["msoa21_bua22_lookup"]}
pts, regs = [], []
for m in og["msoa21_pwc"]:
    l = look.get(m["MSOA21CD"])
    if l and m["MSOA21CD"].startswith("E"):
        pts.append((m["_x"] * math.cos(math.radians(52.5)), m["_y"]))
        regs.append(l["RGN22NM"])
kt = cKDTree(np.array(pts))
eng = [r for r in rows if r["nation"] == "England" and r["lat"] is not None]
_, idx = kt.query(np.array([(r["lon"] * math.cos(math.radians(52.5)), r["lat"]) for r in eng]))
for r, i in zip(eng, idx):
    r["region"] = regs[i]
for r in rows:
    if r["nation"] != "England":
        r["region"] = r["nation"]

# BUA populations (England and Wales, Census 2021 usual residents by LSOA)
lpop = {}
with open(TS001) as f:
    for x in csv.reader(f):
        if x[2].startswith(("E01", "W01")):
            lpop[x[2]] = int(x[3])
bpop = Counter()
for l in json.load(open(LSOA_BUA)):
    if l.get("BUA22CD"):
        bpop[l["BUA22CD"]] += lpop.get(l["LSOA21CD"], 0)

# ------------------------------------------------ headline counts
R["retrieved"] = meta["retrieved"]
R["n_total"] = len(rows)
R["nations"] = {}
for n in NATIONS:
    rs = [r for r in rows if r["nation"] == n]
    g = Counter(r["grade"] for r in rs)
    t1 = sum(1 for r in rs if r["tier"] == 1)
    R["nations"][n] = dict(n=len(rs), pop=npop[n], per_1000=round(1000 * len(rs) / npop[n], 2),
                           grades={k: dict(n=v, pct=pct(v, len(rs))) for k, v in sorted(g.items(), key=lambda x: -x[1])},
                           top_grade=TOP[n], top_n=t1, top_pct=pct(t1, len(rs)),
                           mid_grade=MID[n], mid_n=sum(1 for r in rs if r["tier"] == 2),
                           mid_pct=pct(sum(1 for r in rs if r["tier"] == 2), len(rs)))
R["uk_pop"] = sum(npop.values())
R["uk_top_n"] = sum(1 for r in rows if r["tier"] == 1)
R["uk_top_pct"] = pct(R["uk_top_n"], len(rows))
R["uk_per_1000"] = round(1000 * len(rows) / R["uk_pop"], 2)
R["pop_year"] = pop_year
R["scotland_entities"] = meta["scotland_entities"]
R["ni_dropped_record_only"] = meta["ni_dropped"]
R["n_in_bua"] = sum(1 for r in rows if r["bua"])
R["gb_n"] = sum(1 for r in rows if r["nation"] != "Northern Ireland")
R["pct_in_bua_gb"] = pct(R["n_in_bua"], R["gb_n"])

# ------------------------------------------------ types
R["types"] = {}
order = [t[0] for t in TYPES if t[0] != "other"] + ["address", "other"]
TL = dict(TYPE_LABEL, address="Numbered street buildings (use not in name)", other="Named buildings (use not in name)")
R["type_order"] = order
R["type_labels"] = TL
for n in NATIONS + ["UK"]:
    rs = rows if n == "UK" else [r for r in rows if r["nation"] == n]
    c = Counter(r["type"] for r in rs)
    t1 = Counter(r["type"] for r in rs if r["tier"] == 1)
    nt1 = sum(t1.values())
    R["types"][n] = {k: dict(n=c[k], pct=pct(c[k], len(rs)), top_n=t1[k], top_pct=pct(t1[k], nt1),
                             top_rate=pct(t1[k], c[k])) for k in order}
# what share of the top grade is churches, in each nation
R["top_church_pct"] = {n: R["types"][n]["church"]["top_pct"] for n in NATIONS}
# check of the name rules against Cadw's broad classes (Wales)
BC = {"Domestic": {"house", "address"}, "Religious, Ritual and Funerary": {"church", "monument", "war_memorial"},
      "Agriculture and Subsistence": {"farm"}, "Transport": {"transport"}, "Industrial": {"industrial"},
      "Commercial": {"pub", "commercial", "address"}, "Gardens, Parks and Urban Spaces": {"garden", "wall", "street"},
      "Commemorative": {"war_memorial", "monument", "garden", "street"}, "Defence": {"defence"},
      "Education": {"civic"}, "Civil": {"civic"}, "Health and Welfare": {"civic", "house"},
      "Recreational": {"civic", "garden", "pub"}, "Maritime": {"transport"}, "Water Supply and Drainage": {"street", "industrial", "transport"},
      "Communications": {"street", "civic", "transport"}}
wal = [r for r in rows if r["nation"] == "Wales" and r.get("broadclass") in BC and r["type"] not in ("other", "address")]
agree = sum(1 for r in wal if r["type"] in BC[r["broadclass"]])
R["type_check_wales"] = dict(n=len(wal), agree=agree, agree_pct=pct(agree, len(wal)),
                             n_unclassified=sum(1 for r in rows if r["nation"] == "Wales" and r["type"] in ("other", "address")))
# The wall/gate class often sits under 'Domestic' in Cadw (garden walls of houses); report the stricter figure too
wal2 = [r for r in wal if r["type"] != "wall"]
R["type_check_wales"]["agree_pct_excl_walls"] = pct(sum(1 for r in wal2 if r["type"] in BC[r["broadclass"]]), len(wal2))

# ------------------------------------------------ war memorials, kiosks: small stories
R["n_k6"] = sum(1 for r in rows if "k6" in (r["name"] or "").lower() or "k 6" in (r["name"] or "").lower())
R["n_kiosk"] = sum(1 for r in rows if "kiosk" in (r["name"] or "").lower())
R["n_milestone"] = sum(1 for r in rows if any(w in (r["name"] or "").lower() for w in ("milestone", "milepost", "mile post", "mile stone")))
R["n_war_memorial"] = sum(1 for r in rows if r["type"] == "war_memorial")
R["n_chest_tomb"] = sum(1 for r in rows if "tomb" in (r["name"] or "").lower())

# ------------------------------------------------ counties and unitary authorities
ct = defaultdict(list)
for r in rows:
    if r["county_code"]:
        ct[r["county_code"]].append(r)
counties = []
for c in cty:
    rs = ct.get(c["code"], [])
    p = int(c["pop"])
    t1 = sum(1 for r in rs if r["tier"] == 1)
    tc = Counter(r["type"] for r in rs)
    counties.append(dict(code=c["code"], name=c["name"], nation=c["nation"], pop=p, n=len(rs),
                         per_1000=round(1000 * len(rs) / p, 2) if p else None, top_n=t1, top_pct=pct(t1, len(rs)),
                         **{"t_" + k: tc[k] for k in order}))
R["counties_n"] = len(counties)
big = [c for c in counties if c["pop"] >= 100000]
R["county_top_per_head"] = [dict(name=c["name"], nation=c["nation"], per_1000=c["per_1000"], n=c["n"], pop=c["pop"]) for c in sorted(counties, key=lambda c: -c["per_1000"])[:12]]
R["county_bottom_per_head"] = [dict(name=c["name"], nation=c["nation"], per_1000=c["per_1000"], n=c["n"], pop=c["pop"]) for c in sorted(big, key=lambda c: c["per_1000"])[:10]]
R["county_most"] = [dict(name=c["name"], nation=c["nation"], n=c["n"], per_1000=c["per_1000"]) for c in sorted(counties, key=lambda c: -c["n"])[:10]]
R["county_top_grade_share"] = [dict(name=c["name"], nation=c["nation"], top_pct=c["top_pct"], top_n=c["top_n"], n=c["n"]) for c in sorted([c for c in counties if c["n"] >= 500], key=lambda c: -c["top_pct"])[:10]]
lon_ = [c for c in counties if c["code"].startswith("E09")]
R["london"] = dict(n=sum(c["n"] for c in lon_), pop=sum(c["pop"] for c in lon_))
R["london"]["per_1000"] = round(1000 * R["london"]["n"] / R["london"]["pop"], 2)
R["london"]["westminster"] = next(dict(n=c["n"], per_1000=c["per_1000"]) for c in counties if c["name"] == "Westminster")

# ------------------------------------------------ regions of England
regn = Counter(r["region"] for r in rows if r["nation"] == "England")
R["regions"] = {k: dict(n=v) for k, v in regn.items()}

# ------------------------------------------------ towns (built-up areas)
bn = defaultdict(list)
for r in rows:
    if r["bua"]:
        bn[r["bua"]].append(r)
bname = {b["code"]: b["name"] for b in meta["bua"]}
towns = []
for code, rs in bn.items():
    p = bpop.get(code)
    towns.append(dict(code=code, name=bname[code], nation="Scotland" if code.startswith("S") else ("Wales" if code.startswith("W") else "England"),
                      pop=p, n=len(rs), per_1000=round(1000 * len(rs) / p, 2) if p else None,
                      top_n=sum(1 for r in rs if r["tier"] == 1)))
tw = [t for t in towns if t["pop"] and t["pop"] >= 10000]
R["towns_n_ew_10k"] = len(tw)
R["town_top_per_head"] = [dict(name=t["name"], nation=t["nation"], per_1000=t["per_1000"], n=t["n"], pop=t["pop"]) for t in sorted(tw, key=lambda t: -t["per_1000"])[:15]]
tw50 = [t for t in tw if t["pop"] >= 50000]
R["town50_top_per_head"] = [dict(name=t["name"], nation=t["nation"], per_1000=t["per_1000"], n=t["n"], pop=t["pop"]) for t in sorted(tw50, key=lambda t: -t["per_1000"])[:10]]
R["town50_bottom_per_head"] = [dict(name=t["name"], nation=t["nation"], per_1000=t["per_1000"], n=t["n"], pop=t["pop"]) for t in sorted(tw50, key=lambda t: t["per_1000"])[:10]]
R["town_most"] = [dict(name=t["name"], nation=t["nation"], n=t["n"], per_1000=t["per_1000"]) for t in sorted(towns, key=lambda t: -t["n"])[:12]]
smallp = [t for t in towns if t["pop"] and 1000 <= t["pop"] < 10000]
R["village_top_per_head"] = [dict(name=t["name"], nation=t["nation"], per_1000=t["per_1000"], n=t["n"], pop=t["pop"]) for t in sorted(smallp, key=lambda t: -t["per_1000"])[:10]]

# ------------------------------------------------ listing waves
R["list_years"] = {}
for n in ["England", "Scotland", "Wales"]:
    ys = Counter(r["list_year"] for r in rows if r["nation"] == n and r["list_year"])
    tot = sum(ys.values())
    dec = Counter()
    for y, v in ys.items():
        dec[(y // 10) * 10] += v
    peak = max(ys.items(), key=lambda x: x[1])
    R["list_years"][n] = dict(n=tot, by_year={str(k): v for k, v in sorted(ys.items())},
                              by_decade={str(k): dict(n=v, pct=pct(v, tot)) for k, v in sorted(dec.items())},
                              peak_year=peak[0], peak_n=peak[1], first=min(ys), last=max(ys),
                              since_2000_pct=pct(sum(v for y, v in ys.items() if y >= 2000), tot),
                              in_1980s_pct=pct(sum(v for y, v in ys.items() if 1980 <= y <= 1989), tot),
                              before_1970_pct=pct(sum(v for y, v in ys.items() if y < 1970), tot),
                              median=int(np.median([y for y, v in ys.items() for _ in range(v)])))
# newest listings: types of buildings listed since 2015 in England
recent = [r for r in rows if r["nation"] == "England" and (r["list_year"] or 0) >= 2015]
R["eng_recent"] = dict(n=len(recent), types={k: v for k, v in Counter(r["type"] for r in recent).most_common()})

# ------------------------------------------------ construction dates
CENT = [("le15", "Before 1500", lambda c: c <= 15), ("c16", "1500s (16th century)", lambda c: c == 16),
        ("c17", "1600s (17th century)", lambda c: c == 17), ("c18", "1700s (18th century)", lambda c: c == 18),
        ("c19", "1800s (19th century)", lambda c: c == 19), ("c20", "1900 and later", lambda c: c >= 20)]
R["cent_keys"] = [c[0] for c in CENT]
R["cent_labels"] = {c[0]: c[1] for c in CENT}
def cent_class(c):
    for k, _, f in CENT:
        if f(c):
            return k
def cent_dist(cs, ws=None):
    """Century shares. With weights (Scotland), shares are weighted and the interval uses Kish's effective n."""
    n = len(cs)
    if ws is None:
        cc = Counter(cent_class(c) for c in cs)
        return dict(n=n, **{k: dict(n=cc[k], pct=pct(cc[k], n), ci=wilson(cc[k], n)) for k in R["cent_keys"]})
    W_ = sum(ws); neff = W_ * W_ / sum(w * w for w in ws)
    cw = Counter(); cc = Counter()
    for c, w in zip(cs, ws):
        cw[cent_class(c)] += w; cc[cent_class(c)] += 1
    return dict(n=n, n_eff=round(neff), **{k: dict(n=cc[k], pct=pct(cw[k], W_), ci=wilson(round(cw[k] / W_ * neff), round(neff))) for k in R["cent_keys"]})

byid = {key(r): r for r in rows}
R["dates"] = {}
for n in ["England", "Scotland", "Wales"]:
    s = samples[n]
    ok = [x for x in s if x["ok"]]
    dd = [x for x in ok if x.get("year")]
    ws = [x["w"] for x in dd] if n == "Scotland" else None
    R["dates"][n] = dict(n_sampled=len(s), n_text=len(ok), n_dated=len(dd), dated_pct=pct(len(dd), len(ok)),
                         n_period_word=sum(1 for x in dd if x.get("kind") == "period word"),
                         n_year=sum(1 for x in dd if x.get("kind") == "year"),
                         dist=cent_dist([x["century"] for x in dd], ws),
                         dist_earliest=cent_dist([(x["earliest"] - 1) // 100 + 1 for x in dd], ws))
    if n != "Wales":
        R["dates"][n]["population"] = sum(1 for r in rows if r["nation"] == n)
nd = [r for r in rows if r["nation"] == "Northern Ireland"]
ndd = [r for r in nd if r.get("ni_year")]
R["dates"]["Northern Ireland"] = dict(n_sampled=len(nd), n_text=len(nd), n_dated=len(ndd), dated_pct=pct(len(ndd), len(nd)),
                                      dist=cent_dist([(r["ni_year"] - 1) // 100 + 1 for r in ndd]),
                                      bands={k: v for k, v in Counter(r["ni_date"].strip() for r in ndd).most_common()})
# England sample by region; Georgian (18th century) and Victorian (19th century) shares
he_ids = {"England:" + x["id"]: x for x in samples["England"] if x["ok"] and x.get("year")}
byreg = defaultdict(list)
for k, x in he_ids.items():
    r = byid.get(k)
    if r:
        byreg[r["region"]].append(x["century"])
R["dates"]["England"]["by_region"] = {g: cent_dist(cs) for g, cs in byreg.items()}
# by grade and by type (England sample)
byt = defaultdict(list)
for k, x in he_ids.items():
    r = byid.get(k)
    if r:
        byt[r["type"]].append(x["century"])
R["dates"]["England"]["by_type"] = {t: cent_dist(cs) for t, cs in byt.items() if len(cs) >= 60}
# Wales by council
wd_ids = {"Wales:" + x["id"]: x for x in samples["Wales"] if x["ok"] and x.get("year")}
byc = defaultdict(list)
for k, x in wd_ids.items():
    r = byid.get(k)
    if r and r.get("council"):
        byc[r["council"]].append(x["century"])
R["dates"]["Wales"]["by_council"] = {g: cent_dist(cs) for g, cs in byc.items()}
R["dates"]["Wales"]["coverage_pct"] = pct(len(samples["Wales"]), R["nations"]["Wales"]["n"])

# oldest dated: by nation, from the official texts (England and Scotland samples, all of Wales) and NI
def oldest_list(prefix, src, k=8):
    out = []
    for kk, x in src.items():
        r = byid.get(kk)
        if r:
            out.append(dict(name=r["name"], year=x["year"], match=x.get("match"), county=r["county"], nation=r["nation"], url=r["url"], id=r["id"]))
    out.sort(key=lambda o: o["year"])
    return out[:k]
R["oldest"] = {"England_sample": oldest_list("England", he_ids), "Wales": oldest_list("Wales", wd_ids, 12),
               "Scotland_sample": oldest_list("Scotland", {"Scotland:" + x["id"]: x for x in samples["Scotland"] if x["ok"] and x.get("year")})}

# Wikidata inception layer
R["wikidata"] = dict(n=len(wd), by_nation=dict(Counter(k.split(":")[0] for k in wd)),
                     pct_of_all=pct(len(wd), len(rows)),
                     dist=cent_dist([v["century"] for v in wd.values()]))
# Wikidata vs official text, where both exist (sample)
both = []
for kk, v in wd.items():
    x = he_ids.get(kk) or wd_ids.get(kk)
    if x:
        both.append((v["century"], x["century"]))
R["wikidata"]["n_both"] = len(both)
R["wikidata"]["same_century_pct"] = pct(sum(1 for a, b in both if a == b), len(both))
# Wikidata leans to the old and famous: compare its century mix with the England sample
R["wikidata"]["tier1_pct"] = pct(sum(1 for k in wd if byid.get(k) and byid[k]["tier"] == 1), len(wd))

# oldest per county: best dated source per building (official text first, then NI band, then Wikidata)
best = {}
for kk, v in wd.items():
    best[kk] = dict(year=v["year"], src="Wikidata", label=v.get("label"), qid=v["qid"])
for kk, v in dates.items():
    best[kk] = dict(year=v["year"], src=v["source"], match=v.get("match"))
for r in rows:
    b = best.get(key(r))
    if b:
        r["built_year"], r["built_src"] = b["year"], b["src"]
    else:
        r["built_year"] = r["built_src"] = None
oc = {}
for r in rows:
    if r["built_year"] and r["county"]:
        o = oc.get(r["county"])
        if o is None or r["built_year"] < o["year"]:
            oc[r["county"]] = dict(county=r["county"], nation=r["nation"], name=r["name"], year=r["built_year"], src=r["built_src"], url=r["url"])
R["oldest_by_county_n"] = len(oc)
R["n_built_dated"] = sum(1 for r in rows if r["built_year"])
R["built_dated_by_source"] = dict(Counter(r["built_src"] for r in rows if r["built_src"]))

# ------------------------------------------------ hand checks of the date rules (code/manual_dates.py)
import manual_dates as MD
R["date_check"] = {
    "England": dict(n=MD.N, unsure=len(MD.UNSURE), wrong=len(MD.ERRORS), right=MD.N - len(MD.UNSURE) - len(MD.ERRORS)),
    "Scotland": dict(n=MD.SCOTLAND_N, unsure=0, wrong=len(MD.SCOTLAND_ERRORS), right=MD.SCOTLAND_N - len(MD.SCOTLAND_ERRORS)),
    "Wales": dict(n=MD.WALES_N, unsure=len(MD.WALES_UNSURE), wrong=len(MD.WALES_ERRORS), right=MD.WALES_N - len(MD.WALES_UNSURE) - len(MD.WALES_ERRORS)),
}
tot = {k: sum(v[k] for v in R["date_check"].values()) for k in ("n", "unsure", "wrong", "right")}
tot["right_pct"] = pct(tot["right"], tot["right"] + tot["wrong"])
R["date_check"]["all"] = tot

# ------------------------------------------------ write tables
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
with open(os.path.join(ROOT, "data", "counties.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(counties[0].keys()))
    w.writeheader(); w.writerows(counties)
with open(os.path.join(ROOT, "data", "towns.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["code", "name", "nation", "pop", "n", "per_1000", "top_n"])
    w.writeheader(); w.writerows(sorted(towns, key=lambda t: -t["n"]))
pickle.dump(dict(rows=rows, counties=counties, towns=towns, oc=oc), gzip.open(os.path.join(ROOT, "work", "analysed.pkl.gz"), "wb"))
json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["n_total", "uk_per_1000", "top_church_pct", "type_check_wales", "county_top_per_head"]}, indent=0)[:3000])
for n in R["dates"]:
    print(n, {k: R["dates"][n][k] for k in ["n_sampled", "n_dated", "dated_pct"]}, {k: R["dates"][n]["dist"][k]["pct"] for k in R["cent_keys"]})
