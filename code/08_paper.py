"""Step 8: fill code/paper_template.tex from data/results.json, compile with xelatex (figures from step 6).
Writes release/paper/Hotham_Listed_Kingdom.tex and release/Hotham_Listed_Kingdom.pdf."""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Listed_Kingdom"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "f1": return f"{v:,.1f}"
    if f == "f2": return f"{v:.2f}"
    return tex(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


N = R["nations"]
rows = ""
for n in ["England", "Scotland", "Wales", "Northern Ireland"]:
    d = N[n]
    rows += f"{n} & {d['n']:,} & {d['pop']:,} & {d['per_1000']:.1f} & {d['top_grade']} & {d['top_pct']:.1f} & {d['mid_grade']} & {d['mid_pct']:.1f}\\\\\n"
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{The four lists. Population: mid-" + R["pop_year"] + " estimates. Top and middle grade: "
      "share of each nation's entries.}\\label{tab:nations}\\begin{tabular}{lrrrcrcr}\\toprule Nation & Entries & People & Per 1,000 & Top & \\% & Middle & \\%\\\\\\midrule\n"
      + rows + f"United Kingdom & {R['n_total']:,} & {R['uk_pop']:,} & {R['uk_per_1000']:.1f} & & {R['uk_top_pct']:.1f} & & \\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
ks = R["cent_keys"]
rows = ""
for n in ["England", "Scotland", "Wales", "Northern Ireland"]:
    d = R["dates"][n]["dist"]
    src = {"England": "sample", "Scotland": "sample (weighted)", "Wales": "all entries", "Northern Ireland": "record bands"}[n]
    rows += f"{n} ({src}) & {d['n']:,} & " + " & ".join(f"{d[k]['pct']:.1f}" for k in ks) + "\\\\\n"
    if n in ("England", "Scotland"):
        rows += " \\quad 95\\% interval & & " + " & ".join(f"{d[k]['ci'][0]:.1f} to {d[k]['ci'][1]:.1f}" for k in ks) + "\\\\\n"
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{3.5pt}\\caption{Century of building: share (\\%) of dated entries, by the first date in the "
      "official description (Northern Ireland: the record's date band).}\\label{tab:cent}\\begin{tabular}{lrrrrrrr}\\toprule & Dated & Before 1500 & 1500s & 1600s & 1700s & 1800s & 1900+\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_NATIONS}}", TN).replace("{{TABLE_CENT}}", TC)
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, stdout=subprocess.DEVNULL)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
for ext in (".aux", ".log", ".out", ".pdf"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
print("paper written")
