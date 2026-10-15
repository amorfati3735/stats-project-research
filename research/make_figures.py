#!/usr/bin/env python3
"""
SONIQ — Review 1 figures for the India monsoon direction.

Produces research/figures/*.png. Every figure is drawn from the audited
datasets in data/raw/; no synthetic data.

Run:
    .venv/bin/python research/make_figures.py
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
IND = ROOT / "data" / "raw"
OUT = ROOT / "research" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=140)
    plt.close(fig)
    print("wrote", OUT / name)


def main() -> None:
    d = pd.read_csv(IND / "rainfall_alt.csv")
    aqi = pd.read_csv(IND / "aqi_city_day.csv", parse_dates=["Date"])
    ele = pd.read_csv(IND / "corrected_daily_energy_met_MU.csv", parse_dates=["Date"])

    # 01 — the seasonal signature of Indian rainfall
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    lo = d.melt(id_vars=["DIVISION", "YEAR"], value_vars=MONTHS,
                var_name="month", value_name="mm").dropna()
    means = lo.groupby("month").mm.mean().reindex(MONTHS)
    ax[0].bar(MONTHS, means.values, color="#1f6f8b")
    ax[0].set_title("Mean monthly rainfall, 36 subdivisions, 1901-2015")
    ax[0].set_ylabel("mm")
    ax[0].axvspan(4.5, 8.5, color="#c9e4de", alpha=0.6, zorder=0)
    ax[0].text(6.5, means.max() * 0.92, "Jun-Sep\n75.2% of annual", ha="center", fontsize=9)
    share = 100 * d[[m for m in MONTHS]].sum() / d[[m for m in MONTHS]].sum().sum()
    ypos = np.arange(len(MONTHS))[::-1]
    ax[1].barh(ypos, share.values, color="#1f6f8b")
    ax[1].set_yticks(ypos, MONTHS)
    ax[1].set_xlabel("% of total rainfall")
    ax[1].set_title("Share of total rainfall by month")
    for y, v in zip(ypos, share.values):
        ax[1].text(v + 0.4, y, f"{v:.1f}%", va="center", fontsize=8)
    ax[1].set_xlim(0, 28)
    save(fig, "01_seasonality.png")

    # 02 — zero inflation by month
    fig, ax = plt.subplots(figsize=(8, 4))
    z = (d[MONTHS] == 0).mean().mul(100)
    ax.bar(MONTHS, z.values, color="#b23a48")
    ax.set_ylabel("% of division-years with exactly 0 mm")
    ax.set_title("Zero-inflation: a Bernoulli x Gamma mixture, not a single distribution")
    for i, v in enumerate(z.values):
        if v > 1:
            ax.text(i, v + 0.4, f"{v:.0f}", ha="center", fontsize=8)
    save(fig, "02_zero_inflation.png")

    # 03 — distribution fit on monsoon totals
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    x = d["Jun-Sep"].dropna().values
    ax[0].hist(x, bins=45, density=True, color="#cbdde8", edgecolor="white")
    xs = np.linspace(x.min(), 5000, 400)
    ax[0].plot(xs, stats.norm.pdf(xs, *stats.norm.fit(x)), "r-", lw=1.6,
               label=f"Normal (KS D={stats.kstest(x, stats.norm.cdf, args=stats.norm.fit(x)).statistic:.3f})")
    a, loc, sc = stats.gamma.fit(x)
    ax[0].plot(xs, stats.gamma.pdf(xs, a, loc, sc), "b-", lw=1.6,
               label=f"Gamma (KS D={stats.kstest(x, stats.gamma.cdf, args=(a, loc, sc)).statistic:.3f})")
    ax[0].set_xlabel("Jun-Sep total (mm)"); ax[0].set_ylabel("density")
    ax[0].set_title("Monsoon totals are right-skewed (skew=1.51)")
    ax[0].legend(fontsize=8)
    dm = d.groupby("DIVISION")["Jun-Sep"].apply(lambda s: stats.skew(s.dropna()))
    la = d.groupby("DIVISION")["ANNUAL"].apply(lambda s: stats.skew(s.dropna()))
    ax[1].scatter(dm, la, s=14, color="#1f6f8b")
    ax[1].plot([-0.5, 1.3], [-0.5, 1.3], "k--", lw=0.8)
    ax[1].set_xlabel("skew of Jun-Sep per division"); ax[1].set_ylabel("skew of annual per division")
    ax[1].set_title("Aggregation is mostly neutral, not a fix")
    save(fig, "03_distribution_fit.png")

    # 04 — spatial variability (CV ranking)
    fig, ax = plt.subplots(figsize=(9, 6))
    cv = d.groupby("DIVISION")["ANNUAL"].agg(["mean", "std"])
    cv["CV"] = 100 * cv["std"] / cv["mean"]
    cv = cv.dropna().sort_values("CV")
    cols = ["#b23a48" if v > 25 else "#1f6f8b" for v in cv.CV]
    ax.barh(cv.index, cv.CV, color=cols)
    ax.set_xlabel("Coefficient of variation of annual rainfall (%)")
    ax.set_title("Which subdivisions are unreliable? CV of annual rainfall, 1901-2015")
    ax.tick_params(axis="y", labelsize=6.5)
    for i, v in enumerate(cv.CV):
        ax.text(v + 0.3, i, f"{v:.0f}", va="center", fontsize=6)
    save(fig, "04_variability_cv.png")

    # 05 — trends with multiplicity correction
    fig, ax = plt.subplots(figsize=(9, 5))
    rows = []
    for div, g in d.dropna(subset=["Jun-Sep"]).groupby("DIVISION"):
        t = g.YEAR.values.astype(float); y = g["Jun-Sep"].values
        tau, p = stats.kendalltau(t, y)
        sen = np.median([(y[j] - y[i]) / (t[j] - t[i]) for i, j in combinations(range(len(t)), 2)])
        rows.append((div, sen, p))
    tr = pd.DataFrame(rows, columns=["division", "sen", "p"])
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.feasibility_checks import bh  # single source of truth
    tr["q"] = bh(tr.p)
    tr = tr.sort_values("sen")
    cols = ["#b23a48" if q < 0.05 else "#9aa5b1" for q in tr.q]
    ax.barh(tr.division, tr.sen, color=cols)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Sen's slope of Jun-Sep rainfall (mm per year)")
    ax.set_title("Monsoon trends: 16/36 significant uncorrected, 9/36 survive BH-FDR 5%")
    ax.tick_params(axis="y", labelsize=6.5)
    save(fig, "05_trends_multiple_testing.png")

    # 06 — return periods
    fig, ax = plt.subplots(figsize=(8, 5))
    divs = ["WEST RAJASTHAN", "SAURASHTRA & KUTCH", "PUNJAB", "TAMIL NADU", "KERALA"]
    for div in divs:
        x = d.loc[d.DIVISION == div, "ANNUAL"].dropna().values
        a, loc, sc = stats.gamma.fit(x, floc=0)
        p = np.linspace(0.001, 0.5, 200)
        ax.plot(p, stats.gamma.ppf(p, a, loc, sc), label=div.title())
    ax.set_xscale("log")
    ax.set_xlabel("exceedance probability (return period = 1/p years)")
    ax.set_ylabel("annual rainfall (mm)")
    ax.set_title("Drought risk from a fitted Gamma: 1-in-20-yr and 1-in-50-yr deficits")
    ax.axvline(0.05, color="k", ls=":", lw=1); ax.axvline(0.02, color="k", ls="--", lw=1)
    ax.text(0.05, ax.get_ylim()[1] * 0.97, " 1-in-20", fontsize=8, va="top")
    ax.text(0.02, ax.get_ylim()[1] * 0.90, " 1-in-50", fontsize=8, va="top")
    ax.legend(fontsize=8)
    save(fig, "06_return_periods.png")

    # 07 — the contrast: why the time series is not i.i.d.
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    t = ele[["Date", "Total"]].dropna()
    ax[0].plot(t.Date, t.Total, lw=0.5, color="#1f6f8b")
    ax[0].set_title(f"Daily all-India electricity demand ({t.Date.min():%Y} - {t.Date.max():%Y})")
    ax[0].set_ylabel("MU"); ax[0].tick_params(axis="x", labelsize=7)
    ax[0].text(0.02, 0.05, f"lag-1 autocorrelation = {t.Total.autocorr(1):.3f}",
               transform=ax[0].transAxes, fontsize=9, color="#b23a48")
    pm = aqi.dropna(subset=["PM2.5"])
    ax[1].hist(pm["PM2.5"], bins=60, color="#c9a227")
    ax[1].set_xlim(0, 400)
    ax[1].set_title(f"Daily city PM2.5 ({len(pm):,} obs, {aqi.City.nunique()} cities)")
    ax[1].set_xlabel("PM2.5 (ug/m3)")
    save(fig, "07_contrast_datasets.png")


if __name__ == "__main__":
    main()
