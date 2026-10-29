"""Reddit collage for The Listed Kingdom. Run from the project root: python3 reddit/collage.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figlib import *

P = load_points(); X, Y = proj(P["lon"], P["lat"])
BGC = "#F2EDE3"; FG = INK; MUT = MUTED
XL = (-8.25 * np.cos(np.radians(54.5)), 1.85 * np.cos(np.radians(54.5))); YL = (49.85, 58.75)
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BGC)
fig.text(.04, .968, "The Listed Kingdom", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .912, f"Every listed building in the United Kingdom, one dot each: {R['n_total']:,} entries on the four national\n"
         f"lists, coloured by grade. Grade I and its equals are {R['uk_top_pct']:.1f}% of them.", family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.35)

# hero map by grade
ax = fig.add_axes([0.0, 0.29, 0.6, 0.575]); ax.set_axis_off(); ax.set_facecolor(BGC)
for t, sz, al in ((3, .6, .8), (2, .5, .85), (1, .75, 1)):
    m = P["tier"] == t
    ax.scatter(X[m], Y[m], s=sz, c=TIER[t - 1], lw=0, alpha=al, rasterized=True)
ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_aspect("equal")
lx = .6; ly = .84
fig.text(lx, ly + .012, "GRADE", family=MONO, fontsize=11, color=MUT)
for i, (lab, c, n) in enumerate([("Grade I, category A", TIER[0], sum(R["nations"][k]["top_n"] for k in NATIONS)),
                                 ("Grade II*, category B (Scot.), B+ (NI)", TIER[1], sum(R["nations"][k]["mid_n"] for k in NATIONS)),
                                 ("Grade II, category C, B1, B2, B", TIER[2], R["n_total"] - sum(R["nations"][k]["top_n"] + R["nations"][k]["mid_n"] for k in NATIONS))]):
    yy = ly - .022 - i * .022
    fig.patches.append(plt.Circle((lx + .008, yy + .005), .0055, transform=fig.transFigure, color=c, figure=fig))
    fig.text(lx + .02, yy, lab + (f"  {n:,}" if n else ""), family=MONO, fontsize=11, color=FG, va="bottom")
fig.text(lx, ly - .095, f"Grades differ between nations: Scotland puts\n{R['nations']['Scotland']['mid_pct']:.0f}% of its list in category B, so it looks amber.", family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.35)

# big numbers
D = R["dates"]; LY = R["list_years"]["England"]; ER = R["eng_recent"]
notes = [
    (f"{R['top_church_pct']['England']:.0f}%", "of England's Grade I entries are churches\nand chapels."),
    (f"{D['England']['dist']['c18']['pct'] + D['England']['dist']['c19']['pct']:.0f}%", f"of a random sample of {D['England']['n_dated']:,} English entries\nwere built in the 1700s or 1800s (from the\nfirst date in each official description)."),
    (f"{LY['in_1980s_pct']:.0f}%", f"of England's entries were first listed in the\n1980s. The busiest year was {LY['peak_year']}."),
    (f"{100 * ER['types']['war_memorial'] / ER['n']:.0f}%", f"of England's listings since 2015 are war\nmemorials ({ER['types']['war_memorial']:,} of {ER['n']:,})."),
]
for i, (big, small) in enumerate(notes):
    y0 = .70 - i * .104
    fig.text(.6, y0, big, fontproperties=DISP, fontsize=30, color=RED, va="top")
    fig.text(.6, y0 - .036, small, family=SER, fontsize=12, color=FG, va="top", linespacing=1.25)

# small multiples: six kinds
SM = [("church", "Churches"), ("farm", "Barns, farm bldgs"), ("street", "Kiosks, pumps"),
      ("industrial", "Mills, industry"), ("war_memorial", "War memorials"), ("defence", "Castles, defences")]
fig.text(.04, .283, "SIX KINDS OF LISTED BUILDING, READ FROM THEIR NAMES", family=MONO, fontsize=11, color=MUT)
for i, (t, lab) in enumerate(SM):
    a = fig.add_axes([0.02 + i * .163, 0.075, 0.16, 0.18]); a.set_axis_off()
    a.scatter(X[::4], Y[::4], s=.05, c="#D3C9B7", lw=0, rasterized=True)
    m = P["ty"] == TYPES.index(t)
    a.scatter(X[m], Y[m], s=min(3.0, 7000 / m.sum()), c=TCOL[t], lw=0, alpha=.85, rasterized=True)
    a.set_xlim(*XL); a.set_ylim(*YL); a.set_aspect("equal")
    a.set_title(f"{lab}\n{int(m.sum()):,}", family=MONO, fontsize=10.5, color=FG, pad=2)

fig.text(.04, .018, "Data: Historic England, National Heritage List for England; Historic Environment Scotland; Cadw; Department for Communities NI, Historic Buildings\n"
         "Record (all Open Government Licence v3.0), retrieved 2026. Types read from entry names with keyword rules. Build dates from the official list\n"
         "descriptions (random samples in England and Scotland, every entry in Wales). Analysis and chart: Tristan Hotham, with Python and matplotlib.", family=MONO, fontsize=9, color=MUT, linespacing=1.4)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "listed_kingdom.png"), facecolor=BGC, dpi=200)
print("ok")
