"""Shared rules: building type from a listing name, and a construction date from listing text.

Both sets of rules are deliberately simple and open, so anyone can check them.
"""
import re

# ---------------------------------------------------------------- types
# Order of the list is the order of the legend. Each type has keyword phrases.
TYPES = [
    ("church", "Churches and chapels", [
        "church", "churches", "chapel", "chapels", "cathedral", "abbey", "priory", "minster", "meeting house",
        "synagogue", "mosque", "kirk", "tabernacle", "oratory", "friary", "chantry", "baptistery", "nunnery",
        "convent", "parish church", "free church", "methodist chapel", "chapel of rest", "bell tower", "belfry"]),
    ("monument", "Tombs, crosses and monuments", [
        "tomb", "tombs", "headstone", "headstones", "gravestone", "gravestones", "grave", "graves", "monument",
        "monuments", "memorial", "memorials", "mausoleum", "obelisk", "chest tomb", "table tomb", "cross",
        "market cross", "churchyard cross", "burial enclosure", "burial ground", "vault", "ledger stone"]),
    ("war_memorial", "War memorials", ["war memorial", "war memorials", "cenotaph"]),
    ("house", "Houses and cottages", [
        "house", "houses", "cottage", "cottages", "farmhouse", "farm house", "hall", "manor", "manor house", "villa",
        "rectory", "vicarage", "parsonage", "manse", "lodge", "lodges", "terrace", "mansion", "grange", "dwelling",
        "dwellings", "flats", "tenement", "tenements", "bungalow", "homestead", "croft", "country house",
        "presbytery", "farm", "court house farm", "glebe house", "steward's house", "bothy", "almshouse", "almshouses"]),
    ("farm", "Barns and farm buildings", [
        "barn", "barns", "granary", "stable", "stables", "cowhouse", "cowhouses", "cowshed", "byre", "byres",
        "dovecote", "dovecot", "doocot", "cart shed", "cartshed", "shelter shed", "outbuilding", "outbuildings",
        "farm building", "farm buildings", "oast", "oast house", "hop kiln", "wheelhouse", "horse engine house",
        "steading", "threshing barn", "pigsty", "pigsties", "hayloft", "cart lodge", "coach house", "coachhouse",
        "stable block", "stable range", "shippon", "linhay", "hovel", "piggery", "dairy", "farmstead", "mains"]),
    ("pub", "Pubs, inns and hotels", ["public house", "inn", "hotel", "tavern", "pub", "bar", "arms", "alehouse"]),
    ("commercial", "Shops, banks and offices", [
        "shop", "shops", "shopfront", "bank", "office", "offices", "arcade", "chambers", "exchange", "store",
        "stores", "department store", "showroom"]),
    ("transport", "Bridges, roads, railways and canals", [
        "bridge", "bridges", "viaduct", "railway", "station", "milestone", "milestones", "milepost", "mileposts",
        "mile post", "mile stone", "signpost", "fingerpost", "finger post", "guide post", "guidepost", "lock",
        "locks", "canal", "aqueduct", "tunnel", "toll house", "tollhouse", "signal box", "footbridge", "culvert",
        "wharf", "harbour", "pier", "lighthouse", "quay", "slipway", "dock", "docks", "level crossing",
        "turnpike", "direction post", "lock keeper's cottage", "boundary stone", "boundary post", "boundary marker"]),
    ("wall", "Walls, gates and railings", [
        "wall", "walls", "gate", "gates", "gateway", "gateways", "gate piers", "gatepiers", "gatepier", "gate pier",
        "railings", "railing", "piers", "lych gate", "lychgate", "ha ha", "ha-ha", "screen wall", "steps",
        "boundary wall", "boundary walls", "garden wall", "garden walls", "entrance gates", "archway", "arch",
        "balustrade", "retaining wall", "kerb"]),
    ("street", "Kiosks, post boxes, pumps and lamps", [
        "telephone kiosk", "telephone kiosks", "kiosk", "kiosks", "post box", "pillar box", "letter box",
        "wall box", "lamp", "lamps", "lamp post", "lamp standard", "lamppost", "pump", "pumps", "drinking fountain",
        "trough", "horse trough", "cattle trough", "bollard", "bollards", "bench", "ventilation column",
        "ventilating pipe", "urinal", "shelter", "bus shelter", "clock", "clock tower", "conduit", "well", "well head",
        "wellhead", "stocks", "fire alarm", "sign", "street sign", "postbox", "telephone box"]),
    ("industrial", "Mills, works and industry", [
        "mill", "mills", "works", "kiln", "kilns", "factory", "brewery", "chimney", "mine", "engine house",
        "maltings", "malthouse", "malt house", "forge", "smithy", "foundry", "warehouse", "warehouses", "colliery",
        "tannery", "gasholder", "pumping station", "waterworks", "windmill", "watermill", "water mill", "limekiln",
        "limekilns", "lime kiln", "lime kilns", "furnace", "workshop", "workshops", "distillery", "pithead",
        "headframe", "winding house", "ropewalk", "boathouse", "icehouse works", "sawmill", "granary mill"]),
    ("civic", "Schools, halls and public buildings", [
        "school", "schools", "schoolhouse", "town hall", "library", "hospital", "sheriff court", "county court", "crown court", "courthouse", "church hall", "parish hall",
        "court house", "police station", "market hall", "museum", "theatre", "cinema", "institute", "college",
        "university", "workhouse", "prison", "gaol", "jail", "fire station", "post office", "baths", "town house",
        "guildhall", "guild hall", "assembly rooms", "drill hall", "infirmary", "dispensary", "village hall",
        "mechanics institute", "corn exchange", "tolbooth", "council offices", "lecture hall", "observatory"]),
    ("garden", "Garden and park structures", [
        "garden", "summerhouse", "summer house", "gazebo", "folly", "temple", "statue", "statues", "urn", "urns",
        "sundial", "ice house", "icehouse", "orangery", "fountain", "grotto", "pavilion", "conservatory",
        "greenhouse", "glasshouse", "glasshouses", "vase", "vases", "sculpture", "belvedere", "eyecatcher",
        "bandstand", "bath house", "boat house", "column", "pedestal", "plinth", "terrace walls"]),
    ("defence", "Castles and defences", [
        "castle", "tower house", "fort", "pillbox", "pill box", "barracks", "keep", "bastion", "battery",
        "defences", "city wall", "town wall", "fortifications", "martello tower", "blockhouse", "gun emplacement"]),
    ("other", "Other or not clear from the name", []),
]
TYPE_KEYS = [t[0] for t in TYPES]
TYPE_LABEL = {t[0]: t[1] for t in TYPES}

_kw = []
for key, _lab, words in TYPES:
    for w in words:
        _kw.append((w, key))
_kw.sort(key=lambda x: -len(x[0]))
_KW = {w: k for w, k in _kw}
_RX = re.compile(r"(?<![a-z])(" + "|".join(re.escape(w) for w, _ in _kw) + r")(?![a-z])")
_SPLIT = re.compile(r",|\(| at | to | of | in | near | approximately | approx\.? | about | immediately | on | adjoining | adjacent | opposite | attached to | within | south | north | east | west | including | with | formerly | behind | beside | outside | inside |;")
_ADDR = re.compile(r"^\s*(nos?\.?|numbers?|flats?)?\s*\d+[a-z]?\b|^\s*\d")


def _norm(s):
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[‘’`]", "'", s)
    s = re.sub(r"\s+", " ", s)
    return " " + s.strip() + " "


def building_type(name, extra=None):
    """Return (type key, rule) for a listing name.

    The rule: take the head of the name (before the first preposition or comma),
    split it on 'and', and in the first part that has a keyword take the LAST keyword
    (English noun phrases end in their head noun: 'Barn Close House' is a house).
    War memorials and churchyard monuments are checked first. Names that are only a
    street address become 'house' only if nothing else fires; they are flagged.
    """
    n = _norm(name)
    if re.search(r"war memorial|cenotaph", n):
        return "war_memorial", "war memorial"
    head = _SPLIT.split(n, maxsplit=1)[0]
    for part in re.split(r" and |/|\+", head):
        ms = list(_RX.finditer(part))
        if ms:
            k = _KW[ms[-1].group(1)]
            return k, "head:" + ms[-1].group(1)
    ms = list(_RX.finditer(n))
    if ms:
        k = _KW[ms[0].group(1)]
        return k, "first:" + ms[0].group(1)
    if extra:
        m = list(_RX.finditer(_norm(extra)))
        if m:
            return _KW[m[0].group(1)], "extra:" + m[0].group(1)
    if _ADDR.search(n.strip()) or re.search(r"\b(street|road|lane|place|square|row|terrace|crescent|parade|avenue|gardens|close|hill|green|walk|way)\b", n):
        return "address", "address only"
    return "other", "none"


# Cadw broad classes and NI uses, mapped to the same types for checking and for NI
NI_USE = [  # NI CurrentUse text keywords, first match wins
    (r"telephone|kiosk|post box|pillar|pump|lamp|fountain|trough", "street"),
    (r"war memorial", "war_memorial"),
    (r"memorial|monument|grave|tomb|mausoleum|cross", "monument"),
    (r"church|chapel|cathedral|abbey|meeting house|friary|synagogue|mosque|religious", "church"),
    (r"public house|hotel|inn|bar\b", "pub"),
    (r"shop|bank|office|commercial|store|showroom", "commercial"),
    (r"bridge|railway|station|canal|lock|milestone|harbour|pier|lighthouse|quay|viaduct|aqueduct", "transport"),
    (r"gate|lodge|wall|railing|screen", "wall"),
    (r"mill|factory|works|warehouse|brewery|distillery|kiln|forge|foundry|industrial|mine|gas", "industrial"),
    (r"school|college|universit|hall\b|court|library|hospital|museum|theatre|cinema|police|barrack|institute|orphan|workhouse|prison|gaol|market|civic|education|health|fire station|post office", "civic"),
    (r"barn|farm|outbuilding|stable|byre|dovecote|granary|store\b", "farm"),
    (r"garden|summer|gazebo|folly|temple|statue|urn|sundial|ice house|orangery|bandstand|park", "garden"),
    (r"castle|tower house|fort|bawn|defence|military", "defence"),
    (r"house|cottage|dwelling|rector|manse|vicarage|villa|glebe|terrace|residen|flat", "house"),
]


def ni_type(use, address):
    u = (use or "").lower()
    for rx, k in NI_USE:
        if re.search(rx, u):
            return k, "use:" + rx.split("|")[0]
    return building_type((address or "").split("\n")[0])


# ---------------------------------------------------------------- dates
_Q = r"(?P<q>early|earlier|mid|middle|late|later|end of the|end of|beginning of the|start of the|first half of the|second half of the|first quarter of the|last quarter of the|first half of|second half of|1st half of|2nd half of|C?[0-9]{2}th early)?"
RX_CENT_C = re.compile(r"(?i:" + _Q + r")" + r"[\s\-]*(?<![A-Za-z0-9])C\.?\s?(?P<c>1[0-9]|2[01]|[1-9])(?![0-9])(?:th)?")  # capital C only: a small c is circa
RX_CENT_W = re.compile(_Q + r"[\s\-]*(?P<c>1[0-9]|2[01]|[5-9]|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth)(?:st|nd|rd|th)?[\s\-]+centur", re.I)
RX_YEAR = re.compile(r"(?<![0-9/\-\.:])(?P<circa>c\.?\s?|circa\s|ca\.?\s)?(?P<y>1[0-9]{3}|20[0-2][0-9])(?:s)?(?![0-9]|/|\.[0-9]|:)", re.I)
WORDS = {"eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16,
         "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20}
STYLE = [  # period words used only when no number is given
    (r"\banglo-saxon\b|\bsaxon\b", 1000), (r"\bnorman\b", 1120), (r"\bmedieval\b|\bmediaeval\b", 1350),
    (r"\btudor\b", 1530), (r"\belizabethan\b", 1580), (r"\bjacobean\b", 1615), (r"\bgeorgian\b", 1770),
    (r"\bregency\b", 1820), (r"\bvictorian\b", 1870), (r"\bedwardian\b", 1905), (r"\binter-?war\b", 1930),
    (r"\bpost-?war\b", 1955)]
STYLE = [(rx + r"(?![\s\-]*(?:revival|style|gothic|manner|taste))", y) for rx, y in STYLE]
_GRID = re.compile(r"(?<![A-Za-z])[A-HJ-Z]{2}\s?[0-9]{2,5}(?:\s?-\s?[0-9]{2,5})?\s?[0-9]{0,5}\b")


def _qyear(c, q):
    base = (c - 1) * 100
    q = (q or "").lower()
    if q.startswith(("early", "earlier", "beginning", "start", "first quarter")):
        return base + 15
    if q.startswith(("mid", "middle")):
        return base + 50
    if q.startswith(("late", "later", "end", "last quarter")):
        return base + 85
    if q.startswith(("first half", "1st half")):
        return base + 25
    if q.startswith(("second half", "2nd half")):
        return base + 75
    return base + 50


def find_dates(text):
    """All date mentions in a text: list of (position, year estimate, century, kind, matched text)."""
    t = text or ""
    # drop boilerplate that follows the description on the publishers' pages
    # administrative notes that carry dates of their own
    t = re.sub(r"(?i)this (?:list )?entry was (?:subject to a minor amendment|removed from the list)[^.]*?(?:current standards\.?|\.)", " ", t)
    t = re.sub(r"(?i)the asset was previously listed[^.]*\.", " ", t)
    t = re.sub(r"(?i)\([^()]{0,40}(?:inspection|currently|at the time)[^()]{0,40}\)", " ", t)
    t = re.sub(r"(?i)\b(?:currently|at the time of (?:inspection|survey|listing)) \(?[0-9]{4}\)?", " ", t)
    for cut in ("Listing NGR", "Legacy The contents", "References Bibliography", "Statement of Special Interest", "Sources: ", "Re-categorised as", "Upgraded from", "In accordance with Section"):
        k = t.find(cut)
        if k > 0:
            t = t[:k]
    t = _GRID.sub(lambda m: " " * len(m.group(0)), t)  # blank out grid references
    t = re.sub(r"(?<=C)(?:1[lI]|[lI]{2})(?![0-9a-z])", "11", t)  # OCR: 'Cll' for C11
    t = re.sub(r"(?<=C)[lI](?=[0-9](?![0-9]))", "1", t)  # OCR: 'Cl7' for C17
    t = re.sub(r"(?<![A-Za-z0-9])l(?=[0-9](?:st|nd|rd|th))", "1", t)  # OCR: 'l8th' for 18th
    out = []
    for m in RX_CENT_C.finditer(t):
        c = int(m.group("c"))
        if 7 <= c <= 21:
            out.append((m.start("c"), _qyear(c, m.group("q")), c, "century", m.group(0).strip()))
    for m in RX_CENT_W.finditer(t):
        g = m.group("c").lower()
        c = WORDS.get(g) or int(g)
        if 5 <= c <= 21:
            out.append((m.start("c"), _qyear(c, m.group("q")), c, "century", m.group(0).strip()))
    for m in RX_YEAR.finditer(t):
        y = int(m.group("y"))
        if 600 <= y <= 2026:
            out.append((m.start("y"), y, (y - 1) // 100 + 1, "year", m.group(0).strip()))
    out.sort()
    # drop century mentions that are part of a year range already counted at the same place
    return out


def build_date(text, skip_before=0):
    """The date a listing text gives first (the build date in almost all list descriptions).

    Returns dict(year, century, kind, match, basis) or None. If no number is found,
    a period word (Georgian, Victorian...) is used and flagged.
    """
    ds = [d for d in find_dates(text) if d[0] >= skip_before]
    low = (text or "").lower()
    pw = None
    for rx, y in STYLE:
        m = re.search(rx, low[skip_before:])
        if m and (pw is None or m.start() < pw[0]):
            pw = (m.start() + skip_before, y, m.group(0))
    if pw and (not ds or pw[0] < ds[0][0]) and pw[0] - skip_before < 60:
        # a period word right at the start of the description ("Cross. Medieval.") beats a later number
        return {"year": pw[1], "century": (pw[1] - 1) // 100 + 1, "kind": "period word", "match": pw[2],
                "basis": "period word", "earliest": min([pw[1]] + [x[1] for x in ds])}
    if ds:
        d = ds[0]
        # a first date about the origins of the site (a saint's foundation, a Roman camp) rather than the
        # building: if its sentence talks of foundation or the site, and a later sentence has a date, use that
        t = text or ""
        st = t.rfind(".", 0, d[0]) + 1
        en = t.find(".", d[0]); en = len(t) if en < 0 else en
        sent = t[st:en].lower()
        if re.search(r"\b(founded|foundation|site|originated|established|said to have been|tradition|first church|earlier church|mentioned|recorded|granted|charter)\b", sent):
            later = [x for x in ds if x[0] > en]
            if later:
                d = later[0]
        return {"year": d[1], "century": d[2], "kind": d[3], "match": d[4], "basis": "first date in text",
                "earliest": min(x[1] for x in ds)}
    low = (text or "").lower()
    best = None
    for rx, y in STYLE:
        m = re.search(rx, low)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), y, m.group(0))
    if best:
        return {"year": best[1], "century": (best[1] - 1) // 100 + 1, "kind": "period word", "match": best[2],
                "basis": "period word", "earliest": best[1]}
    return None


def ni_date(s):
    """NI Historic Buildings Record 'Date_Const' bands, e.g. '1820 - 1839', 'Pre 1600'."""
    s = (s or "").strip()
    m = re.match(r"^(1[0-9]{3}|20[0-2][0-9])\s*-\s*(1[0-9]{3}|20[0-2][0-9])$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b >= a and b - a <= 120:
            return {"year": (a + b) // 2, "lo": a, "hi": b}
    if re.match(r"(?i)^pre\s*1600$", s):
        return {"year": 1550, "lo": None, "hi": 1599}
    return None
