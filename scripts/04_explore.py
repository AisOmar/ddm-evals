"""Exploratory look (plan v2, phase 3). Tables + conditional plots. Nothing here is a hypothesis test.

usage: python scripts/04_explore.py [--data results/pilot.csv] [--figdir results/figures]

Difficulty (3.2) is estimated from EVEN repeats only (p_correct_even -> tertiles hard/medium/easy);
the by-difficulty plot uses ODD repeats, so the strata are never read off the runs they describe.
"""
import argparse, math, pathlib
import numpy as np, pandas as pd, yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="results/pilot.csv")
ap.add_argument("--figdir", default="results/figures")
a = ap.parse_args()
cfg = yaml.safe_load(open("config.yaml"))
COND = list(cfg["conditions"])                       # fixed order from config: the 2x2 reads row-wise
df = pd.read_csv(a.data)
ans = df[df.outcome == "answered"].copy()            # positive-length, answered runs: what the DDM is fit to
ans["correct"] = ans.correct.astype(bool)
ans["log_tok"] = np.log10(ans.reasoning_tokens.clip(lower=1))

# ---------------------------------------------------------------- tables
pd.set_option("display.width", 160)
print("3.1 outcome rates by condition")
print(pd.crosstab(df.condition, df.outcome).reindex(COND).assign(n=lambda t: t.sum(axis=1)).to_string())
print("\n3.1 answered runs: accuracy and reasoning-token quantiles (rt_source:", ", ".join(df.rt_source.dropna().unique()), ")")
print(ans.groupby("condition").agg(n=("correct", "size"), acc=("correct", "mean"),
      tok_p10=("reasoning_tokens", lambda x: x.quantile(.1)), tok_med=("reasoning_tokens", "median"),
      tok_p90=("reasoning_tokens", lambda x: x.quantile(.9))).reindex(COND).round(2).to_string())
print("\n3.1 zero-token share of all runs (bare-letter replies), by condition")
print(df.groupby("condition").outcome.apply(lambda s: (s == "zero_tokens").mean()).reindex(COND).round(3).to_string())
print("\n3.2 token quantiles by correctness within condition")
print(ans.groupby(["condition", "correct"]).reasoning_tokens.describe()[["count", "25%", "50%", "75%"]].reindex(COND, level=0).round(0).to_string())
print("\n3.2 position: accuracy when correct option is A vs B")
print(ans.groupby("correct_is_A").correct.mean().round(3).to_string())

even = ans[ans.rep % 2 == 0].groupby("qid").correct.mean().rename("p_even")
strata = pd.qcut(even.rank(method="first"), 3, labels=["hard", "medium", "easy"]).rename("difficulty")
odd = ans[ans.rep % 2 == 1].join(strata, on="qid")
print("\n3.2 difficulty strata from even reps (n questions, mean p_correct_even):")
print(pd.concat([even, strata], axis=1).groupby("difficulty", observed=True).p_even.agg(["size", "mean"]).round(2).to_string())
print("\n3.2 odd reps: accuracy and median tokens by stratum x condition")
print(odd.groupby(["difficulty", "condition"], observed=True).agg(acc=("correct", "mean"), med_tok=("reasoning_tokens", "median")).unstack().reindex(columns=COND, level=1).round(2).to_string())
print("\n3.3 error counts per condition (answered runs)")
print(ans.groupby("condition").correct.apply(lambda c: int((~c).sum())).reindex(COND).to_string())
print("\n3.4 length clustering: most common exact token counts (share of answered runs)")
vc = ans.reasoning_tokens.value_counts()
print((vc.head(5) / len(ans)).round(4).to_string(), f"\n  distinct values: {ans.reasoning_tokens.nunique()} of {len(ans)} runs")
print("\n3.4 bimodality check: median tokens and accuracy by has_code (question-level covariate) x condition")
print(ans.groupby(["has_code", "condition"]).agg(n=("correct", "size"), acc=("correct", "mean"), med_tok=("reasoning_tokens", "median")).unstack().reindex(columns=COND, level=1).round(2).to_string())

# 3.4b Within-question length variability vs what a DDM can produce. A diffusion process at accuracy p has a
# timing CV that falls with drift*boundary; near-constant lengths at 70-80% accuracy are outside its range.
ans["lrt"] = np.log(ans.reasoning_tokens.clip(lower=1))
cell = ans.groupby(["qid", "condition"]).agg(n=("lrt", "size"), sd_log=("lrt", "std"), acc=("correct", "mean"), med=("reasoning_tokens", "median")).dropna()
cell = cell[cell.n >= 5]
print(f"\n3.4b within-question length variability ({len(cell)} question x condition cells with >=5 answered runs)")
print(f"  sd of log(reasoning tokens) within cell: median {cell.sd_log.median():.2f}, IQR [{cell.sd_log.quantile(.25):.2f}, {cell.sd_log.quantile(.75):.2f}]")
print("  by cell accuracy band:", {f"[{lo:.2f},{hi:.2f})": round(float(cell[(cell.acc >= lo) & (cell.acc < hi)].sd_log.median()), 2) for lo, hi in [(0, .7), (.7, .95), (.95, 1.01)]})
sim_path = pathlib.Path("results/recovery/model_gen_ddm_truth.csv")
sim_cell = None
if sim_path.exists():
    sim = pd.read_csv(sim_path); sim = sim[sim.outcome == "answered"].copy(); sim["lrt"] = np.log(sim.rt)
    sim_cell = sim.groupby(["qid", "condition"]).agg(n=("lrt", "size"), sd_log=("lrt", "std"), acc=("correct", "mean")).dropna(); sim_cell = sim_cell[sim_cell.n >= 5]
    print(f"  reference, pilot-calibrated DDM simulation: median {sim_cell.sd_log.median():.2f}, IQR [{sim_cell.sd_log.quantile(.25):.2f}, {sim_cell.sd_log.quantile(.75):.2f}]")
# 3.4c Pooled version that works at any number of repeats >= 2 (the R1 rerun has 2 per cell): the residual sd of
# log length after removing question x condition cell means, df-weighted. Two lower bounds on the true spread:
# answered runs only (truncation removes the long tail), and answered + censored with censored runs scored at the
# cap (their true length is >= the cap, so pair differences are understated).
def pooled_sd(frame):
    g = frame.groupby(["qid", "condition"]).lrt
    n, sd = g.size(), g.std()
    ok = n >= 2
    return float(np.sqrt(((n[ok] - 1) * sd[ok] ** 2).sum() / (n[ok] - 1).sum())), int(ok.sum())
ps, nc = pooled_sd(ans)
print(f"\n3.4c pooled within-cell sd of log(reasoning tokens), answered runs: {ps:.2f} over {nc} cells with >=2 runs")
cen = df[df.outcome == "censored"].copy()
if len(cen):
    cen["lrt"] = np.log(cfg["model"]["max_tokens"]); cen["correct"] = False
    ps2, nc2 = pooled_sd(pd.concat([ans, cen]))
    mixed = pd.concat([ans.assign(c=0), cen.assign(c=1)]).groupby(["qid", "condition"]).c.agg(["min", "max", "size"])
    mixed = mixed[(mixed["size"] >= 2) & (mixed["min"] == 0) & (mixed["max"] == 1)]
    print(f"  answered + censored (censored scored at the {cfg['model']['max_tokens']}-token cap, a lower bound): {ps2:.2f} over {nc2} cells")
    print(f"  cells with both an answered and a censored repeat: {len(mixed)} of {nc2}")
# DDM reference for the pooled number: sd of log decision time for a Wiener process at a given accuracy, t0 = 0
# (t0 > 0 only lowers it). Euler simulation, independent of the pilot calibration.
rng = np.random.default_rng(0)
def ddm_sdlog(p, n=20000, dt=0.005, a=1.0):
    v = np.log(p / (1 - p)) / (2 * a)          # P(upper) = 1/(1+exp(-2va)) with boundaries +-a, start 0
    x = np.zeros(n); t = np.zeros(n); alive = np.ones(n, bool)
    for _ in range(int(400 / dt)):
        if not alive.any(): break
        x[alive] += v * dt + np.sqrt(dt) * rng.standard_normal(alive.sum()); t[alive] += dt
        alive &= np.abs(x) < a
    return float(np.log(t[~alive]).std())
print("  DDM reference, sd of log decision time by accuracy (t0 = 0):", {p: round(ddm_sdlog(p), 2) for p in (0.75, 0.9, 0.96, 0.99)})
both = ans.groupby(["qid", "condition"]).filter(lambda x: x.correct.nunique() == 2)
dlt = both.groupby(["qid", "condition"]).apply(lambda x: x[~x.correct].lrt.mean() - x[x.correct].lrt.mean(), include_groups=False)
print(f"  within-cell log-length(incorrect) - log-length(correct): mean {dlt.mean():+.2f} over {len(dlt)} mixed cells ({(dlt > 0).mean():.0%} positive); slow errors in the pooled data are between questions, not within")

# ---------------------------------------------------------------- figures
# Reference palette (dataviz skill, references/palette.md), light mode. Correct/incorrect means pass/fail,
# so it wears the fixed status pair (good / critical), both >= 3:1 on the light surface; single-series
# panels wear categorical slot 1. Text wears ink tokens, never series color.
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
C_OK, C_ERR, C_ONE = "#0ca30c", "#d03b3b", "#2a78d6"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-", "axes.axisbelow": True,
    "xtick.major.size": 0, "ytick.major.size": 0, "font.size": 9, "axes.titlesize": 10, "legend.frameon": False})
LABEL = {c: c.replace("plain_", "plain · ").replace("sbs_", "step-by-step · ") for c in COND}
figdir = pathlib.Path(a.figdir); figdir.mkdir(parents=True, exist_ok=True)
MODEL = df.model.iloc[0]

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d

def grid2x2(title):
    fig, axs = plt.subplots(2, 2, figsize=(8, 5.6), sharex=True, sharey=True)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="semibold")
    return fig, axs.ravel()

def save(fig, name, note):
    fig.text(0.01, 0.005, note, color=MUTED, fontsize=7.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95)); fig.savefig(figdir / name, dpi=170); plt.close(fig)
    print("wrote", figdir / name)

# Fig 1 (3.1): accuracy with 95% Wilson CI, and median tokens with IQR, per condition. Two measures -> two panels.
g = ans.groupby("condition").agg(n=("correct", "size"), k=("correct", "sum"), med=("reasoning_tokens", "median"),
                                 q1=("reasoning_tokens", lambda x: x.quantile(.25)), q3=("reasoning_tokens", lambda x: x.quantile(.75))).reindex(COND)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.4))
fig.suptitle("3.1  Accuracy and reasoning length by condition (answered runs)", x=0.01, ha="left", fontsize=11, fontweight="semibold")
y = np.arange(len(COND))[::-1]
for ax in (ax1, ax2):
    ax.grid(axis="x"); ax.grid(False, axis="y"); ax.set_yticks(y); ax.set_yticklabels([LABEL[c] for c in COND]); ax.spines["left"].set_visible(False)
for yi, (c, r) in zip(y, g.iterrows()):
    lo, hi = wilson(r.k, r.n); ax1.plot([lo, hi], [yi, yi], color=C_ONE, lw=2, solid_capstyle="round")
    ax1.plot(r.k / r.n, yi, "o", ms=7, color=C_ONE, mec=SURF, mew=1.5); ax1.text(hi + 0.01, yi, f"{r.k / r.n:.2f}", va="center", color=INK2, fontsize=8)
    ax2.plot([r.q1, r.q3], [yi, yi], color=C_ONE, lw=2, solid_capstyle="round")
    ax2.plot(r.med, yi, "o", ms=7, color=C_ONE, mec=SURF, mew=1.5); ax2.text(r.q3 + 15, yi, f"{int(r.med)}", va="center", color=INK2, fontsize=8)
ax1.axvline(0.5, color=AXIS, lw=0.8); ax1.set_xlim(0.45, 1.0); ax1.set_xlabel("accuracy (dot) and 95% Wilson interval")
ax2.set_xlim(0, None); ax2.set_xlabel("reasoning tokens: median (dot) and IQR")
save(fig, "fig1_accuracy_tokens_by_condition.png", f"{MODEL} · answered runs per condition: " + ", ".join(f"{int(g.loc[c, 'n'])}" for c in COND) + " (in panel order) · vertical rule at 0.5 = chance for two options")

# Fig 2 (3.2): token distributions for correct vs incorrect within condition (ECDF on log scale).
fig, axs = grid2x2("3.2  Reasoning-token distribution by correctness, within condition (ECDF)")
for ax, c in zip(axs, COND):
    sub = ans[ans.condition == c]
    for ok, col, lab in [(True, C_OK, "correct"), (False, C_ERR, "incorrect")]:
        x = np.sort(sub[sub.correct == ok].reasoning_tokens.values); ax.plot(x, np.arange(1, len(x) + 1) / len(x), color=col, lw=2, label=lab, solid_joinstyle="round")
    ax.set_xscale("log"); ax.set_title(LABEL[c], loc="left")
    ax.text(0.02, 0.93, f"correct n={int(sub.correct.sum())}   incorrect n={int((~sub.correct).sum())}", transform=ax.transAxes, ha="left", va="top", color=MUTED, fontsize=7.5)
for ax in axs[2:]: ax.set_xlabel("reasoning tokens (log scale)")
for ax in axs[::2]: ax.set_ylabel("cumulative share of runs")
axs[0].legend(loc="lower right", fontsize=8)
save(fig, "fig2_tokens_by_correctness.png", f"{MODEL} · answered runs only; zero-token traces are a separate outcome and excluded here")

# Fig 3 (3.2): tokens by difficulty stratum (from even reps) x correctness, plotted on odd reps.
fig, axs = grid2x2("3.2  Reasoning tokens by difficulty stratum and correctness (odd repeats; strata from even repeats)")
order = ["hard", "medium", "easy"]
for ax, c in zip(axs, COND):
    sub = odd[odd.condition == c]
    for ok, col, lab, dx in [(True, C_OK, "correct", -0.08), (False, C_ERR, "incorrect", 0.08)]:
        s = sub[sub.correct == ok].groupby("difficulty", observed=True).reasoning_tokens
        q = pd.DataFrame({"med": s.median(), "q1": s.quantile(.25), "q3": s.quantile(.75), "n": s.size()}).reindex(order)
        xs = np.arange(3) + dx
        for xi, (_, r) in zip(xs, q.iterrows()):
            if r.n >= 3: ax.plot([xi, xi], [r.q1, r.q3], color=col, lw=2, solid_capstyle="round")
        ax.plot(xs, q.med.where(q.n >= 3), "o", ms=7, color=col, mec=SURF, mew=1.5, label=lab, ls="none")
    ax.set_xticks(range(3)); ax.set_xticklabels(order); ax.set_title(LABEL[c], loc="left"); ax.set_yscale("log")
for ax in axs[2:]: ax.set_xlabel("difficulty stratum (tertiles of p_correct on even repeats)")
for ax in axs[::2]: ax.set_ylabel("reasoning tokens: median, IQR")
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="upper right", bbox_to_anchor=(0.99, 0.965), ncol=2, fontsize=8)
save(fig, "fig3_tokens_by_difficulty.png", f"{MODEL} · cells with fewer than 3 runs are not drawn")

# Fig 4 (3.4): raw token-count histograms per condition to show (absence of) length clustering.
fig, axs = grid2x2("3.4  Reasoning-token histogram per condition (length clustering check)")
bins = np.linspace(0, ans.reasoning_tokens.quantile(.99), 50)
for ax, c in zip(axs, COND):
    sub = df[df.condition == c]; ax.hist(sub[sub.outcome == "answered"].reasoning_tokens, bins=bins, color=C_ONE, edgecolor=SURF, linewidth=0.6)
    z = (sub.outcome == "zero_tokens").mean(); ax.set_title(LABEL[c], loc="left")
    ax.text(0.98, 0.9, f"zero-token share {z:.0%}\ncensored {int((sub.outcome == 'censored').sum())}, refusal {int((sub.outcome == 'refusal').sum())}", transform=ax.transAxes, ha="right", va="top", color=MUTED, fontsize=7.5)
for ax in axs[2:]: ax.set_xlabel("reasoning tokens")
for ax in axs[::2]: ax.set_ylabel("runs")
save(fig, "fig4_token_histograms.png", f"{MODEL} · bins to the 99th percentile; zero-token traces excluded from the bars and reported as a share")

# Fig 5 (3.4b): within-question length variability against cell accuracy; the DDM reference is the band it can reach.
fig, ax = plt.subplots(figsize=(7.2, 4.2))
fig.suptitle("3.4b  Within-question spread of reasoning length vs. accuracy of that question", x=0.01, ha="left", fontsize=11, fontweight="semibold")
if sim_cell is not None:
    ax.plot(sim_cell.acc + np.random.default_rng(0).uniform(-0.012, 0.012, len(sim_cell)), sim_cell.sd_log, "o", ms=5, color=GRID, mec=SURF, mew=0.8, label="DDM simulated at pilot-calibrated parameters")
# Two-repeat runs (R1 rerun) have no >=5 cells: fall back to every cell with >=2 answered runs, where the cell sd is
# |difference|/sqrt(2) and accuracy can only be 0, 0.5 or 1, and draw the pooled value as a line.
pcell = cell if len(cell) else ans.groupby(["qid", "condition"]).agg(n=("lrt", "size"), sd_log=("lrt", "std"), acc=("correct", "mean")).dropna()
plab = f"{MODEL}, pilot" if len(cell) else f"{MODEL}, pilot (2 repeats per cell; pooled sd {ps:.2f}, line)"
ax.plot(pcell.acc + np.random.default_rng(1).uniform(-0.012, 0.012, len(pcell)), pcell.sd_log, "o", ms=6, color=C_ONE, mec=SURF, mew=1.2, label=plab)
if not len(cell):
    ax.axhline(ps, color=C_ONE, lw=2)
ax.set_xlabel("accuracy of the question in that condition (answered runs, 5-10 repeats)"); ax.set_ylabel("sd of log(reasoning tokens) across repeats")
ax.set_xlim(0.45, 1.03); ax.set_ylim(0, None); ax.legend(loc="upper left", fontsize=8)
save(fig, "fig5_within_question_length_spread.png", "each dot is one question x condition cell; a diffusion model's timing variance rises as accuracy falls toward chance")
