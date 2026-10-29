# The Listed Kingdom

Every listed building in the United Kingdom on one map: 465,740 entries on the four national lists (England, Scotland, Wales and Northern Ireland), by grade, by type (read from the names), by the year first listed and, where the official description or record says, by when they were built.

**Interactive version:** https://maps.tristanhotham.com/listed-buildings/

This repository holds the interactive page, the harmonised data and the analysis code for the data study *The Listed Kingdom: every listed building in the United Kingdom by grade, type, date of listing and date of building* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Blog: https://blog.tristanhotham.com/2026/10/29/listed-buildings/ . Paper: https://doi.org/10.5281/zenodo.23761429

## Headline results

- 465,740 list entries in all (379,683 England, 46,749 Scotland, 30,110 Wales, 9,198 Northern Ireland), about 6.7 per 1,000 people. Wales has the most per head (9.5), then Scotland (8.4), England (6.5) and Northern Ireland (4.8).
- By county and unitary authority, the Isles of Scilly (56.5 per 1,000) and the City of London (43.5) lead, then Powys, Gwynedd, Rutland and Herefordshire; Barking and Dagenham has the fewest (0.18). Among towns of 10,000+ in England and Wales, Ludlow leads (40.7).
- Read from their names, 31.4% of entries are houses and cottages, 6.8% barns and farm buildings and 6.7% churches and chapels; but 53.5% of England's Grade I entries are churches and chapels. The top grade is 2.9% of all entries.
- From the first date in the official descriptions: in a random sample of England's entries 30.8% of dated entries were built in the 1700s and 32.6% in the 1800s. The 1800s share is 56.4% in Wales (every entry), 65.2% in Scotland (sample) and 73.5% in Northern Ireland (record bands).
- In England the East of England has the oldest listed stock (10.1% before 1500) and London the youngest (56.2% from the 1800s).
- 46.9% of England's entries were first listed in the 1980s (peak year 1987). Of 5,682 English entries listed since 2015, 2,889 are war memorials.

## Files

- `index.html`: the interactive page (every entry as a dot, coloured by grade, type, date of building or year listed; per head by county; place and postcode search; Map layers panel; charts).
- `header.png`: social card.
- `data/listed_england_part1.csv.gz` (North East, North West, Yorkshire and The Humber, East and West Midlands), `data/listed_england_part2.csv.gz` (the rest of England), `data/listed_scotland.csv.gz`, `data/listed_wales.csv.gz`, `data/listed_northern_ireland.csv.gz`: one row per list entry: list id, name, grade, tier (1 top, 2 middle, 3 other), year first listed, type (read from the name), coordinates (WGS84), county or unitary authority code, built-up area code (2022), built year estimate and its source (`text` = official description, `ni_band` = NI record date band, `wikidata` = Wikidata inception), and Northern Ireland's date band.
- `data/build_dates_parsed.csv.gz`: every parsed description (England and Scotland samples, all of Wales): year estimate, century, kind (year, century or period word), the words matched, the rule, the earliest date in the text and the Scottish sampling weight. The description texts themselves are not republished.
- `data/counties.csv`, `data/counties.geojson`: counts, population, entries per 1,000 and counts by type for the 218 counties and unitary authorities (outlines: ONS, simplified).
- `data/towns.csv`: counts and per head figures for built-up areas (population for England and Wales only).
- `data/results.json`: every number used on the page, in the paper, the blog and the collage.
- `data/points.bin.gz`, `data/names/*.json.gz`, `data/places.json`: compact files the page reads (packed columns and names; place names from OS Open Names and GeoNames).
- `code/`: the analysis (see below), `code/rules.py` (type and date rules), `code/manual_dates.py` (the hand check), templates for the page, paper and blog.
- `release/`: the paper (PDF and LaTeX), blog figures and post, Zenodo files.
- `reddit/`: the collage and its post text.

## Method in brief

Types: keyword rules read the head of each name (before "at", "to", "of" or a comma) and take its last keyword ("Barn Close House" is a house). Checked against Cadw's own broad classes in Wales: consistent in 70.9% of 18,631 entries.

Dates: the first date in each official description (a year or a century such as "Late C17"), skipping the header of old English entries, administrative notes and dates about the origins of a site when a later date follows; centuries placed at their middle, "early" and "late" moved 35 years. A hand check of 120 descriptions found the rules right in 97.4% of the cases that could be judged. Scotland's sample was drawn from building points, so draws are weighted by one over the number of points in their designation.

## Caveats

- Counts are of list entries, not buildings; grades are not comparable across nations.
- Types are read from names; about a quarter of names do not say.
- Build dates are the first date in each description: they lean young for buildings with long histories, and for some old churches (especially in Wales) they are a foundation date rather than standing fabric. Do not use them to name an "oldest building".
- England and Scotland dates are random samples (5,000 and 2,000 entries). Wikidata dates on the map are sparse and lean to famous buildings.
- Listing dates are of survivors on today's lists. Northern Ireland's open data has no listing date.

## How to rerun

Raw bundles (gzipped JSON fetched in a browser from the publishers' services; see `code/01_prepare.py` and `code/02_dates.py` for their structure) are read from `RAW` (default `/home/claude/hist/_data18/listed-buildings`). County outlines and populations are read from the takeaways project's files (`COUNTIES`, `COUNTY_CSV`), ONS lookups and Census 2021 from `ONSGEO`, `LSOA_BUA`, `TS001`.

```
python3 code/01_prepare.py     # harmonise the four lists, county and built-up area
python3 code/02_dates.py       # parse dates from descriptions; NI bands; Wikidata
python3 code/03_analyse.py     # every number -> data/results.json, tables
python3 code/04_page_data.py   # page files and published tables
python3 code/05_build_site.py  # index.html (checks the facts stated in words)
python3 code/06_figures.py     # blog and paper figures
python3 code/07_header.py      # header.png
python3 code/08_paper.py       # paper PDF (xelatex)
python3 code/09_release.py     # blog post, Zenodo files, README
python3 reddit/collage.py      # collage
```

## Sources and licences

- Historic England, National Heritage List for England, listed building points (ArcGIS feature service) and official list entry text (sample, read for dates only). Contains Historic England data © Historic England 2026. Open Government Licence v3.0.
- Historic Environment Scotland, Listed Buildings (inspire.hes.scot map service) and portal descriptions (sample, read for dates only). Open Government Licence v3.0.
- Cadw, Listed Buildings (DataMapWales WFS) and Cadw full reports (read for dates only). Open Government Licence v3.0.
- Department for Communities, Historic Environment Division, Historic Buildings Record (ArcGIS feature service, OpenDataNI). Open Government Licence v3.0.
- Office for National Statistics: Counties and Unitary Authorities (December 2023) boundaries, Built-up Areas (2022), Census 2021 (TS001) and lookups, mid-year population estimates; NRS and NISRA estimates. Contains OS data © Crown copyright and database right 2023. Open Government Licence v3.0.
- Wikidata (CC0), via QLever.
- Place names: OS Open Names (OGL v3.0) and GeoNames (CC BY 4.0). Map tiles on the page: Esri. Map library: Leaflet.

## Licence

Data files: Open Government Licence v3.0 (derived from the sources above; Wikidata-derived fields CC0). Text and figures: CC BY 4.0. Code: MIT. See LICENSE.

## Citation

Hotham, T. (2026) The Listed Kingdom: every listed building in the United Kingdom by grade, type, date of listing and date of building. Zenodo. https://doi.org/10.5281/zenodo.23761429

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
