"""Step 7: header.png, the 1200 by 630 social card."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *

P = load_points(); X, Y = proj(P["lon"], P["lat"])
fig = plt.figure(figsize=(6, 3.15), dpi=200)
ax = fig.add_axes([.55, .0, .45, 1]); ax.set_axis_off()
for t, s, a in ((3, .05, .5), (2, .1, .8), (1, .3, 1)):
    m = P["tier"] == t
    ax.scatter(X[m], Y[m], s=s, c=TIER[t - 1], lw=0, alpha=a, rasterized=True)
ax.set_xlim(-8.3 * np.cos(np.radians(54.5)), 1.9 * np.cos(np.radians(54.5))); ax.set_ylim(49.85, 59.0); ax.set_aspect("equal")
fig.text(.05, .89, "DATA STUDY  ·  BUILDINGS  ·  UNITED KINGDOM 2026", family=MONO, fontsize=6.2, color=MUTED)
fig.text(.045, .82, "The Listed", fontproperties=DISP, fontsize=34, color=INK, va="top")
fig.text(.045, .62, "Kingdom", fontproperties=DISP, fontsize=34, color=RED, va="top")
fig.text(.05, .38, f"Every listed building in the UK: {R['n_total']:,} entries\nfrom the four national lists, by grade, type,\nwhen they were listed and when they were built.",
         family=SER, fontsize=7.6, color=INK, va="top", linespacing=1.2)
fig.text(.05, .05, "Dr Tristan Hotham · Independent researcher", family=MONO, fontsize=6, color=MUTED)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=200)
print("header.png written")
