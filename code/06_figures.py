"""Step 6: static figures for the blog (release/blog/b_*.png, 1520 px wide) and the paper (release/paper/f_*.png)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *

BLOG = os.path.join(ROOT, "release", "blog"); PAPER = os.path.join(ROOT, "release", "paper")
os.makedirs(BLOG, exist_ok=True); os.makedirs(PAPER, exist_ok=True)
P = load_points()
X, Y = proj(P["lon"], P["lat"])
OUT = county_outlines()


def save(fig, name, paper=True, blog=True):
    if blog:
        fig.savefig(os.path.join(BLOG, "b_" + name + ".png"), dpi=200)
    if paper:
        fig.savefig(os.path.join(PAPER, "f_" + name + ".png"), dpi=110)
    plt.close(fig)


def outline(ax, lw=.25, col="#B9AE9A"):
    for props, polys in OUT:
        for p in polys:
            px, py = proj(p[:, 0], p[:, 1])
            ax.plot(px, py, color=col, lw=lw, zorder=1)


# 1. the map, by grade
fig = plt.figure(figsize=(7.6, 9.5)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
outline(ax)
for t, s, a in ((3, .3, .6), (2, .35, .8), (1, .8, 1)):
    m = P["tier"] == t
    ax.scatter(X[m], Y[m], s=s, c=TIER[t - 1], lw=0, alpha=a, zorder=2 + t, rasterized=True)
ax.set_xlim(-8.3 * np.cos(np.radians(54.5)), 1.9 * np.cos(np.radians(54.5))); ax.set_ylim(48.7, 59.0); ax.set_aspect("equal")
for i, (lab, c) in enumerate([("Grade I, category A", TIER[0]), ("Grade II*, category B (Scotland), B+ (NI)", TIER[1]), ("Grade II, category C, B1, B2, B", TIER[2])]):
    ax.scatter([.03], [.105 - i * .026], s=40, c=c, transform=ax.transAxes, clip_on=False); ax.text(.05, .105 - i * .026, lab, va="center", family=MONO, fontsize=9.5, color=INK, transform=ax.transAxes)
ax.text(.03, .105 - 3 * .026, f"{R['n_total']:,} list entries, one dot each", va="center", family=MONO, fontsize=9.5, color=MUTED, transform=ax.transAxes)
save(fig, "map")

# 2. Wales by century of build (every entry dated from Cadw's descriptions)
m = P["nation"] == 2
fig = plt.figure(figsize=(7.6, 8.2)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
outline(ax, .4)
k = cent_class(P["bu"][m])
ax.scatter(X[m][k < 0], Y[m][k < 0], s=1, c="#CFC6B6", lw=0, zorder=2, rasterized=True)
for i in range(6):
    q = k == i
    ax.scatter(X[m][q], Y[m][q], s=2.2 if i < 3 else 1.4, c=CCOL[i], lw=0, zorder=3 + (6 - i), rasterized=True)
ax.set_xlim(-6.9 * np.cos(np.radians(54.5)), -2.6 * np.cos(np.radians(54.5))); ax.set_ylim(51.3, 53.5); ax.set_aspect("equal")
for i, (lab, c) in enumerate([(R["cent_labels"][kk], CCOL[j]) for j, kk in enumerate(R["cent_keys"])] + [("no date found", "#CFC6B6")]):
    ax.scatter([.03], [.95 - i * .035], s=40, c=c, transform=ax.transAxes, clip_on=False); ax.text(.05, .95 - i * .035, lab, va="center", family=MONO, fontsize=9.5, transform=ax.transAxes)
save(fig, "wales_built")

# 3. per head, counties
def hbars(ax, labels, vals, cols, fmtf="{:.1f}"):
    yy = np.arange(len(vals))[::-1]
    ax.barh(yy, vals, color=cols, height=.7)
    ax.set_yticks(yy); ax.set_yticklabels(labels, family=MONO, fontsize=10.5)
    for y_, v in zip(yy, vals):
        if v == v:
            ax.text(v + max(vals) * .01, y_, fmtf.format(v), va="center", family=MONO, fontsize=10, color=MUTED)
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(v for v in vals if v == v) * 1.12)

top = R["county_top_per_head"]; bot = R["county_bottom_per_head"][::-1]
labs = [c["name"].replace("Herefordshire, County of", "Herefordshire") for c in top] + [""] + [c["name"] for c in bot]
vals = [c["per_1000"] for c in top] + [np.nan] + [c["per_1000"] for c in bot]
cols = [RED] * len(top) + [BG] + [SLATE] * len(bot)
fig, ax = plt.subplots(figsize=(7.6, 7.2)); hbars(ax, labs, vals, cols)
ax.set_xlabel("List entries per 1,000 residents", family=MONO, fontsize=10.5); fig.tight_layout(); save(fig, "counties")

# 4. towns per head
t = R["town_top_per_head"]
fig, ax = plt.subplots(figsize=(7.6, 6.0)); hbars(ax, [c["name"] for c in t], [c["per_1000"] for c in t], [OCHRE] * len(t))
ax.set_xlabel("List entries per 1,000 residents, built-up areas of 10,000+ people", family=MONO, fontsize=10.5); fig.tight_layout(); save(fig, "towns", blog=False)

# 5. types by nation
fig, ax = plt.subplots(figsize=(7.6, 5.6))
for j, n in enumerate(NATIONS):
    left = 0
    for tkey in TYPES:
        v = R["types"][n][tkey]["pct"]
        ax.barh(3 - j, v, left=left, color=TCOL[tkey], height=.62, edgecolor=BG, lw=.4)
        if v >= 6:
            ax.text(left + v / 2, 3 - j, f"{v:.0f}%", ha="center", va="center", fontsize=9, family=MONO, color="#fff" if tkey not in ("address", "other", "wall", "pub") else INK)
        left += v
ax.set_yticks(range(4)); ax.set_yticklabels(NATIONS[::-1], family=MONO, fontsize=10.5); ax.set_xlim(0, 100)
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0); ax.set_xlabel("Share of list entries (%)", family=MONO, fontsize=10)
hs = [plt.Rectangle((0, 0), 1, 1, color=TCOL[t_]) for t_ in TYPES]
fig.legend(hs, [TL[t_] for t_ in TYPES], loc="lower center", ncol=2, fontsize=8.6, frameon=False, prop={"family": MONO, "size": 8.6})
fig.subplots_adjust(left=.2, right=.97, top=.98, bottom=.42); save(fig, "types")

# 6. centuries by nation
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ncol = [RED, SLATE, OCHRE, "#5E7F3A"]
ks = R["cent_keys"]; w = .2
for j, n in enumerate(NATIONS):
    d = R["dates"][n]["dist"]
    xs = np.arange(len(ks)) + (j - 1.5) * w
    v = [d[k]["pct"] for k in ks]
    ax.bar(xs, v, width=w * .92, color=ncol[j], label=n + {"England": " (sample)", "Scotland": " (sample)", "Wales": " (every entry)", "Northern Ireland": " (record)"}[n])
    if n in ("England", "Scotland"):
        lo = [d[k]["ci"][0] for k in ks]; hi = [d[k]["ci"][1] for k in ks]
        ax.vlines(xs, lo, hi, color=INK, lw=1)
ax.set_xticks(range(len(ks))); ax.set_xticklabels([R["cent_labels"][k].replace(" (", "\n(") for k in ks], family=MONO, fontsize=8.6)
ax.set_ylabel("Share of dated entries (%)", family=MONO, fontsize=10); ax.legend(frameon=False, prop={"family": MONO, "size": 9}); fig.tight_layout(); save(fig, "centuries")

# 7. listing waves
fig, axs = plt.subplots(3, 1, figsize=(7.6, 6.6), sharex=True)
for ax, n, c in zip(axs, ["England", "Scotland", "Wales"], [RED, SLATE, OCHRE]):
    d = R["list_years"][n]["by_year"]
    ys = np.array([int(k) for k in d]); vs = np.array([d[k] for k in d])
    ax.bar(ys, vs, width=.85, color=c)
    ax.text(.01, .85, n, transform=ax.transAxes, family=MONO, fontsize=10.5, color=INK)
    ax.set_xlim(1945, 2027)
axs[-1].set_xlabel("Year first listed", family=MONO, fontsize=10)
fig.tight_layout(); save(fig, "waves")

# 8. England by region: 18th against 19th century
reg = R["dates"]["England"]["by_region"]
names = sorted(reg, key=lambda g: reg[g]["c18"]["pct"])
fig, ax = plt.subplots(figsize=(7.6, 5.0))
for i, g in enumerate(names):
    left = 0
    for j, k in enumerate(ks):
        v = reg[g][k]["pct"]; ax.barh(i, v, left=left, color=CCOL[j], height=.66, edgecolor=BG, lw=.4)
        if v >= 9:
            ax.text(left + v / 2, i, f"{v:.0f}", ha="center", va="center", fontsize=8.5, family=MONO, color="#fff")
        left += v
ax.set_yticks(range(len(names))); ax.set_yticklabels([f"{g} ({reg[g]['n']})" for g in names], family=MONO, fontsize=9.5)
ax.set_xlim(0, 100); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
ax.set_xlabel("Share of sampled, dated entries (%)", family=MONO, fontsize=10)
hs = [plt.Rectangle((0, 0), 1, 1, color=CCOL[j]) for j in range(len(ks))]
fig.legend(hs, [R["cent_labels"][k] for k in ks], loc="lower center", ncol=3, frameon=False, prop={"family": MONO, "size": 8.6})
fig.subplots_adjust(left=.33, right=.97, top=.98, bottom=.24); save(fig, "regions")
print("figures written")
