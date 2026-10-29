"""Step 5: build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json. Facts the
template states in words are checked against the data first (check()).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from palette import TCOL, CCOL
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
META = json.load(open(os.path.join(ROOT, "work", "points_meta.json")))


def get(path):
    v = R
    for k in re.split(r"\.(?![^\[]*\])", path):
        m = re.fullmatch(r'(\w+)\["(.+)"\]', k)
        if m:
            v = v[m.group(1)][m.group(2)]; continue
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "f1": return f"{v:,.1f}"
    if f == "f2": return f"{v:,.2f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


def check():
    """Facts stated in words on the page, paper, blog and collage."""
    N = R["nations"]
    order = sorted(["England", "Scotland", "Wales", "Northern Ireland"], key=lambda n: -N[n]["per_1000"])
    assert order == ["Wales", "Scotland", "England", "Northern Ireland"], order
    D = R["dates"]
    assert D["England"]["dist"]["c19"]["pct"] > D["England"]["dist"]["c18"]["pct"] > D["England"]["dist"]["le15"]["pct"]
    assert D["Northern Ireland"]["dist"]["c19"]["pct"] > max(D[n]["dist"]["c19"]["pct"] for n in ("England", "Scotland", "Wales"))
    assert D["Scotland"]["dist"]["c19"]["pct"] > D["Wales"]["dist"]["c19"]["pct"] > D["England"]["dist"]["c19"]["pct"], [D[n]["dist"]["c19"]["pct"] for n in D]
    names = [c["name"] for c in R["county_top_per_head"]]
    assert names[:6] == ["Isles of Scilly", "City of London", "Powys", "Gwynedd", "Rutland", "Herefordshire, County of"], names
    reg = D["England"]["by_region"]
    assert max(reg, key=lambda g: reg[g]["le15"]["pct"]) == "East of England"
    assert sorted(reg, key=lambda g: -reg[g]["c19"]["pct"])[:2] == ["London", "North West"]
    assert R["oldest"]["England_sample"][0]["name"] == "CHURCH OF ST MARY" and R["oldest"]["England_sample"][0]["county"] == "Oxfordshire"
    T = R["types"]
    assert max(T["Scotland"], key=lambda k: T["Scotland"][k]["top_pct"]) == "house"
    assert R["eng_recent"]["types"]["war_memorial"] * 2 > R["eng_recent"]["n"]
    assert max(T["Wales"], key=lambda k: T["Wales"][k]["top_pct"] if k != "church" else 0) == "defence"
    assert D["England"]["dist"]["le15"]["pct"] < D["Wales"]["dist"]["le15"]["pct"] + 1
    assert T["Scotland"]["church"]["top_pct"] < T["England"]["church"]["top_pct"]
    for k in ("house", "farm", "wall", "church"):
        assert T["UK"][k]["n"] > 0


if __name__ == "__main__":
    if not os.environ.get("SKIPCHECK"): check()
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    keep = ("nations", "types", "type_labels", "cent_keys", "cent_labels", "dates", "list_years", "county_top_per_head",
            "county_bottom_per_head", "town_top_per_head", "town50_top_per_head", "pop_year")
    slim = {k: R[k] for k in keep}
    slim["dates"] = {n: {k: v for k, v in d.items() if k in ("dist", "by_region", "n_dated")} for n, d in R["dates"].items()}
    slim["list_years"] = {n: {"by_year": d["by_year"]} for n, d in R["list_years"].items()}
    slim["types"] = {n: {t: {"n": v["n"], "pct": v["pct"]} for t, v in d.items()} for n, d in R["types"].items()}
    html = html.replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*META*/", json.dumps(META, separators=(",", ":")))
    html = html.replace("/*TCOL*/", json.dumps(TCOL)).replace("/*CCOL*/", json.dumps(CCOL))
    assert "{{" not in html and "/*RESULTS" not in html
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html))
