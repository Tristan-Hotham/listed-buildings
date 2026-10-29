"""Step 2: construction dates.

- Wales: every Cadw full report's History text (all list entries), parsed with rules.build_date.
- England: a seeded random sample of Historic England official list entry texts.
- Scotland: a seeded random sample of Historic Environment Scotland list descriptions.
- Northern Ireland: the record's own date band (Date_Const), for every building.
- Wikidata inception (P571) for items carrying a list ID, as a separate, labelled layer.

Writes work/dates.pkl.gz: {nation_id: {year, century, kind, match, basis, source}} and the
parsed samples (no listing text is published, only the date, the matched words and the rule).
"""
import gzip, json, os, re, sys, pickle
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from rules import build_date, find_dates

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.environ.get("RAW", "/home/claude/hist/_data18/listed-buildings")
D = pickle.load(gzip.open(os.path.join(ROOT, "work", "all.pkl.gz")))
rows = D["rows"]
key = lambda nation, i: nation + ":" + str(i)
known = {key(r["nation"], r["id"]) for r in rows}

dates = {}
samples = {}


def start_of_description(det):
    """Old-style entries start with a header (parish, grid reference, list numbers, list date, grade).
    The description proper starts after '2.' in the oldest format ('1. STREET ... 2. C17 house'),
    otherwise just after the grade token (GV II, II*, I)."""
    if re.match(r"^\D{0,80}?\b1\.\s", det):
        m2 = re.search(r"(?<![0-9.])2\.\s?(?=\(?[A-Z])", det[:500])
        if m2:
            return m2.end()
    m = re.search(r"G\.?V\.?\s*(II\s?\*|II|I)(?=\s*(?:[A-Z][a-z]|[Cc]\.?\s?[0-9]|[0-9]))", det[:450]) or \
        re.search(r"(?:\b|(?<=[a-z0-9)\-]))(II\s?\*|II|I)(?=\s*[A-Z][a-z])", det[:450])
    return m.end() if m else 0

# ---- England sample (Historic England official list entries)
he = json.load(gzip.open(os.path.join(RAW, "lb18_he_sample.json.gz")))
eng = []
for r in he["res"]:
    if r.get("st") != 200:
        eng.append(dict(id=str(r["id"]), ok=False))
        continue
    det = r.get("det") or ""
    # old-style entries start with a header (parish, grid reference, list numbers, list date, grade);
    # the description proper starts after the grade. Skip to just after the first grade token if found early.
    start = start_of_description(det)
    newstyle = re.match(r"\s*(?:MATERIALS|DESCRIPTION|PLAN|EXTERIOR)\b", det) is not None
    hb = build_date(r["hist"]) if (newstyle and r.get("hist")) else None
    if hb:
        hb["basis"] += " (history section)"
    bd = hb or build_date(det, skip_before=start) or build_date(det)
    if not bd and r.get("hist"):
        bd = build_date(r["hist"])
        if bd:
            bd["basis"] += " (history section)"
    eng.append(dict(id=str(r["id"]), ok=True, **(bd or {})))
    if bd:
        dates[key("England", r["id"])] = dict(bd, source="HE list entry text (sample)")
samples["England"] = eng

# ---- Scotland sample (HES portal descriptions)
hs = json.load(gzip.open(os.path.join(RAW, "lb18_hes_sample.json.gz")))
sco = []
for r in hs["res"]:
    if r.get("st") != 200 or not r.get("desc"):
        sco.append(dict(id=r["ref"], ok=False, w=1 / D["meta"]["scotland_entity_counts"].get(r["ref"], 1)))
        continue
    bd = build_date(r["desc"]) or (build_date(r.get("ssi")) if r.get("ssi") else None)
    # the sample was drawn from building points (entities); a designation with k entities was k times as
    # likely to be drawn, so each draw carries weight 1/k
    k_ent = D["meta"]["scotland_entity_counts"].get(r["ref"], 1)
    sco.append(dict(id=r["ref"], ok=True, w=1 / k_ent, **(bd or {})))
    if bd:
        dates[key("Scotland", r["ref"])] = dict(bd, source="HES list description (sample)")
samples["Scotland"] = sco

# ---- Wales: every Cadw report
cw = json.load(gzip.open(os.path.join(RAW, "lb18_cadw_text.json.gz")))
wal = []
for rid, (period, hist, reason) in cw["res"].items():
    period = "" if (period or "").startswith("History") else (period or "")
    bd = build_date(hist) if hist else None
    if not bd and period:
        bd = build_date(period)
        if bd:
            bd["basis"] = "Cadw period field"
    if not bd and reason:
        bd = build_date(reason)
        if bd:
            bd["basis"] += " (reason for designation)"
    wal.append(dict(id=str(rid), ok=bool(hist or reason), **(bd or {})))
    if bd:
        dates[key("Wales", rid)] = dict(bd, source="Cadw full report")
samples["Wales"] = wal

# ---- Northern Ireland: own date bands
for r in rows:
    if r["nation"] == "Northern Ireland" and r.get("ni_year"):
        dates[key("Northern Ireland", r["id"])] = dict(year=r["ni_year"], century=(r["ni_year"] - 1) // 100 + 1,
                                                        kind="band", match=r["ni_date"], basis="record date band",
                                                        source="NI Historic Buildings Record", earliest=r["ni_year"])

# ---- Wikidata inception
wd = {}
lines = D["wikidata_tsv"].strip().split("\n")[1:]
for ln in lines:
    p = ln.split("\t")
    if len(p) < 7:
        continue
    q = p[0].rsplit("/", 1)[-1].rstrip(">")
    ids = [x.strip('"') for x in p[1:5]]
    try:
        y = int(p[5])
    except ValueError:
        continue
    lab = re.sub(r'^"|"@en$', "", p[6])
    for nation, v in zip(["England", "Wales", "Scotland", "Northern Ireland"], ids):
        if not v:
            continue
        if nation == "Scotland" and not v.upper().startswith("LB"):
            v = "LB" + v if v.isdigit() else v
        k = key(nation, v)
        if k in known and 600 <= y <= 2026:
            if k not in wd or y < wd[k]["year"]:
                wd[k] = dict(year=y, century=(y - 1) // 100 + 1, qid=q, label=lab)

pickle.dump(dict(dates=dates, samples=samples, wikidata=wd, he_meta={k: he.get(k) for k in ("source", "retrieved", "seed", "n_population")},
                 hes_meta={k: hs.get(k) for k in ("source", "retrieved", "seed", "n_population")},
                 cadw_meta={k: cw.get(k) for k in ("source", "retrieved")}),
            gzip.open(os.path.join(ROOT, "work", "dates.pkl.gz"), "wb"))
for n, s in samples.items():
    ok = [x for x in s if x["ok"]]
    print(n, len(s), "ok", len(ok), "dated", sum(1 for x in ok if x.get("year")),
          Counter(x.get("century") for x in ok if x.get("year")).most_common(8),
          Counter(x.get("kind") for x in ok if x.get("year")))
print("wikidata matched", len(wd), Counter(k.split(":")[0] for k in wd))
print("dates total", len(dates), Counter(v["source"] for v in dates.values()))
