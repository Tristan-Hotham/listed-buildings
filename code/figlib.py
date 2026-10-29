"""Shared drawing helpers for the header, the blog and paper figures and the Reddit collage (matplotlib).
Fonts: FONT_DIR holding Fraunces, Source Serif 4 and IBM Plex Mono (github.com/google/fonts); otherwise
matplotlib's defaults are used.
"""
import json, os, gzip, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from palette import *

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
DISP = None
if os.path.isdir(FD):
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
        if os.path.exists(os.path.join(FD, f)):
            fm.fontManager.addfont(os.path.join(FD, f))
    DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": SER, "font.size": 12, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "savefig.facecolor": BG,
                     "figure.facecolor": BG, "axes.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
TYPES = R["type_order"]; TL = R["type_labels"]
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]


def load_points():
    """Columns from data/points.bin.gz (same layout as the page reads)."""
    meta = json.load(open(os.path.join(ROOT, "work", "points_meta.json")))
    b = gzip.open(os.path.join(ROOT, "data", "points.bin.gz")).read()
    n, nc = meta["n"], meta["nx"] * meta["ny"] + 1
    o = nc * 4
    x = np.frombuffer(b, "<u2", n, o); o += 2 * n
    y = np.frombuffer(b, "<u2", n, o); o += 2 * n
    cols = {}
    for k in ("nt", "ty", "ly", "bu", "co", "sr"):
        cols[k] = np.frombuffer(b, "u1", n, o); o += n
    W, S, E, N = meta["bbox"]
    lon = W + x / 65535 * (E - W); lat = S + y / 65535 * (N - S)
    return dict(lon=lon, lat=lat, nation=cols["nt"] >> 2, tier=cols["nt"] & 3, **cols)


def proj(lon, lat):
    """Simple equal-ish projection for Britain and Ireland: x scaled by cos(54.5)."""
    return lon * np.cos(np.radians(54.5)), lat


def county_outlines():
    gj = json.load(open(os.path.join(ROOT, "data", "counties.geojson")))
    out = []
    for f in gj["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        out.append((f["properties"], [np.array(p[0]) for p in polys]))
    return out


def cent_class(bu):
    y = bu.astype(int) * 10 + 500
    k = np.full(len(bu), -1)
    for i, hi in enumerate([1500, 1600, 1700, 1800, 1900, 99999]):
        k[(k < 0) & (bu > 0) & (y <= hi)] = i
    return k
