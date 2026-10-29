"""Step 9: README.md, LICENSE, the blog post and meta, and the Zenodo files."""
import json, os, re, shutil, zipfile, glob

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))


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


fill = lambda t: re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), t)

# README and LICENSE
open(os.path.join(ROOT, "README.md"), "w").write(fill(open(os.path.join(HERE, "readme_template.md")).read()))
open(os.path.join(ROOT, "LICENSE"), "w").write("""MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This licence covers the code in code/, reddit/collage.py and the page scripts.
The data files in data/ are derived from Historic England, Historic Environment
Scotland, Cadw, the Department for Communities (Northern Ireland) and the Office
for National Statistics, and are released under the Open Government Licence v3.0
(https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/);
fields from Wikidata are CC0. The text and figures are released under the
Creative Commons Attribution 4.0 International licence (CC BY 4.0):
https://creativecommons.org/licenses/by/4.0/ . See README.md for all sources.
""")

# blog
B = os.path.join(ROOT, "release", "blog")
post = fill(open(os.path.join(HERE, "blog_template.html")).read())
open(os.path.join(B, "post.html"), "w").write(post)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", post):
    assert os.path.exists(os.path.join(B, m)), m
json.dump({"title": "The Listed Kingdom: every listed building in the UK",
           "slug": "listed-buildings",
           "excerpt": fill("I put all {{n_total|int}} entries on the UK's four lists of listed buildings on one map, read their names to see what they are and their descriptions to see when they were built. Mostly Georgian and Victorian houses, with a great many churches at the top."),
           "seo_description": "Every listed building in the UK mapped: where they are thickest, what they are, when they were built and when they were listed.",
           "tags": ["listed buildings", "heritage", "architecture", "history", "maps", "open data", "UK", "data"],
           "header_alt": fill("Title card reading 'The Listed Kingdom' in black and red on pale stone, beside a map of the UK made of small dots, one for each listed building, coloured by grade. Text: every listed building in the UK, {{n_total|int}} entries from the four national lists, by grade, type, when they were listed and when they were built.")},
          open(os.path.join(B, "meta.json"), "w"), indent=1, ensure_ascii=False)

# Zenodo
Z = os.path.join(ROOT, "release", "zenodo")
shutil.rmtree(Z, ignore_errors=True); os.makedirs(Z)
shutil.copy(os.path.join(ROOT, "release", "Hotham_Listed_Kingdom.pdf"), Z)
for f in glob.glob(os.path.join(ROOT, "data", "listed_*.csv.gz")) + [os.path.join(ROOT, "data", x) for x in ("build_dates_parsed.csv.gz", "counties.csv", "towns.csv", "results.json")]:
    shutil.copy(f, Z)
with zipfile.ZipFile(os.path.join(Z, "listed-buildings_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(glob.glob(os.path.join(ROOT, "code", "*"))):
        if os.path.isfile(f) and not f.endswith(".pyc"):
            zf.write(f, os.path.relpath(f, ROOT))
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
        if os.path.isfile(f) and not os.path.basename(f).startswith("listed_") and os.path.basename(f) not in ("points.bin.gz", "places.json"):
            zf.write(f, os.path.relpath(f, ROOT))
    zf.write(os.path.join(ROOT, "README.md"), "README.md"); zf.write(os.path.join(ROOT, "LICENSE"), "LICENSE")
    zf.write(os.path.join(ROOT, "reddit", "collage.py"), "reddit/collage.py")
abstract = open(os.path.join(ROOT, "release", "paper", "Hotham_Listed_Kingdom.tex")).read()
abstract = abstract.split("\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
abstract = abstract.replace("\\%", "%").replace("\\&", "&").replace("``", '"').replace("''", '"')
json.dump({"title": "The Listed Kingdom: Every Listed Building in the United Kingdom by Grade, Type, Date of Listing and Date of Building",
           "description_html": "<p>" + abstract + "</p><p>Interactive version: https://maps.tristanhotham.com/listed-buildings/. Data and code: https://github.com/Tristan-Hotham/listed-buildings. Blog post: to follow.</p>",
           "keywords": ["listed buildings", "built heritage", "National Heritage List for England", "Cadw", "Historic Environment Scotland",
                        "Northern Ireland Historic Buildings Record", "open data", "text mining", "architectural history", "United Kingdom"],
           "licence": "cc-by-4.0",
           "related": [
               {"identifier": "https://github.com/Tristan-Hotham/listed-buildings", "relation": "issupplementedby", "resource_type": "software"},
               {"identifier": "https://maps.tristanhotham.com/listed-buildings/", "relation": "issupplementedby", "resource_type": "other"},
               {"identifier": "https://historicengland.org.uk/listing/the-list/", "relation": "isderivedfrom", "resource_type": "dataset"},
               {"identifier": "https://portal.historicenvironment.scot/", "relation": "isderivedfrom", "resource_type": "dataset"},
               {"identifier": "https://datamap.gov.wales/", "relation": "isderivedfrom", "resource_type": "dataset"},
               {"identifier": "https://www.opendatani.gov.uk/", "relation": "isderivedfrom", "resource_type": "dataset"},
               {"identifier": "https://geoportal.statistics.gov.uk/", "relation": "isderivedfrom", "resource_type": "dataset"},
               {"identifier": "https://www.wikidata.org/", "relation": "isderivedfrom", "resource_type": "dataset"}]},
          open(os.path.join(Z, "meta.json"), "w"), indent=1, ensure_ascii=False)
print("release written", sorted(os.listdir(Z)))
