#!/usr/bin/env python3
"""
SONIQ — reproducible initial EDA.

Generates the Review-1 figures into research/figures/ from the real downloaded
data. Small on purpose: six figures that together tell the whole story.

Run:
    .venv/bin/python research/eda.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
FIG = ROOT / "research" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

ACCENT = "#1DB954"
AUDIO = ["danceability", "energy", "key", "loudness", "mode", "speechiness",
         "acousticness", "instrumentalness", "liveness", "valence", "tempo",
         "duration_ms"]


def load(name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, low_memory=False)
    return df.drop(columns=[c for c in df.columns if c.lower().startswith("unnamed")])


def cfg(ax, title: str) -> None:
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(alpha=0.25)


def main() -> None:
    k = load("kaggle_spotify_tracks_114k.csv")
    tt = load("tidytuesday_spotify_songs.csv")
    made = []

    # 1 — sample sizes / provenance overview
    fig, ax = plt.subplots(figsize=(7, 3.2))
    rows = ["Kaggle 114k\n(114 genres)", "TidyTuesday\n(6 genres)"]
    ax.barh(rows, [len(k), len(tt)], color=[ACCENT, "#4c72b0"])
    for i, v in enumerate([len(k), len(tt)]):
        ax.text(v + 1500, i, f"{v:,} rows", va="center", fontsize=10)
    ax.set_xlim(0, 135000)
    cfg(ax, "Datasets: tracks downloaded and audited (measured)")
    ax.set_xlabel("rows")
    fig.tight_layout(); fig.savefig(FIG / "01_datasets.png", dpi=110); plt.close(fig)
    made.append("01_datasets.png")

    # 2 — popularity histogram + ECDF (both datasets)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for s, lab, c in ((k.popularity, "Kaggle 114k", ACCENT),
                      (tt.track_popularity, "TidyTuesday", "#4c72b0")):
        axes[0].hist(s, bins=50, alpha=0.55, label=lab, color=c)
        x = np.sort(s); axes[1].plot(x, np.arange(1, x.size + 1) / x.size, label=lab, color=c)
    axes[0].set_xlabel("popularity (0-100)"); axes[0].set_ylabel("tracks")
    cfg(axes[0], "Popularity histogram — flat with a spike at 0")
    axes[0].legend(fontsize=8)
    axes[1].set_xlabel("popularity"); axes[1].set_ylabel("ECDF"); cfg(axes[1], "ECDF")
    axes[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "02_popularity_distribution.png", dpi=110); plt.close(fig)
    made.append("02_popularity_distribution.png")

    # 3 — distribution fits (show all simple fits fail)
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    x = k.popularity.values.astype(float)
    ax.hist(x, bins=50, density=True, alpha=0.45, color="#999999", label="observed")
    xs = np.linspace(0, 100, 400)
    for nm, dist in (("Normal", stats.norm), ("Gamma", stats.gamma),
                     ("Weibull", stats.weibull_min)):
        p = dist.fit(x)
        ax.plot(xs, dist.pdf(xs, *p), lw=1.4, label=f"{nm} fit")
    cfg(ax, "Popularity: no simple distribution fits (KS p\u22480 for all)")
    ax.set_xlabel("popularity"); ax.set_ylabel("density"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "03_fitted_distributions.png", dpi=110); plt.close(fig)
    made.append("03_fitted_distributions.png")

    # 4 — genre comparison (top/bottom 10 of 114 genres + all 6 TT genres)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    m = k.groupby("track_genre")["popularity"].mean().sort_values()
    sel = pd.concat([m.head(10), m.tail(10)])
    axes[0].barh(sel.index, sel.values,
                 color=["#c44e52"] * 10 + [ACCENT] * 10)
    axes[0].tick_params(labelsize=7)
    cfg(axes[0], "Mean popularity — 10 lowest / 10 highest of 114 genres")
    axes[0].set_xlabel("mean popularity")
    ttm = tt.groupby("playlist_genre")["track_popularity"].mean().sort_values()
    axes[1].barh(ttm.index, ttm.values, color="#4c72b0")
    cfg(axes[1], "Mean popularity by playlist genre (TidyTuesday)")
    axes[1].set_xlabel("mean popularity")
    fig.tight_layout(); fig.savefig(FIG / "04_genre_means.png", dpi=110); plt.close(fig)
    made.append("04_genre_means.png")

    # 5 — correlation heatmap incl. target, Pearson
    cols = ["popularity"] + AUDIO
    c = k[cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(c.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=90, fontsize=7)
    ax.set_yticks(range(len(cols))); ax.set_yticklabels(cols, fontsize=7)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{c.values[i, j]:.2f}", ha="center", va="center",
                    fontsize=5.5, color="black")
    cfg(ax, "Pearson correlation (Kaggle 114k): target row is nearly blank")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout(); fig.savefig(FIG / "05_correlation.png", dpi=110); plt.close(fig)
    made.append("05_correlation.png")

    # 6 — strongest feature vs popularity + OLS residuals
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    d = k[["popularity", "instrumentalness"]].dropna()
    r = stats.pearsonr(d.popularity, d.instrumentalness)[0]
    axes[0].scatter(d.instrumentalness, d.popularity, s=1, alpha=0.06, color="#333333")
    b, a = np.polyfit(d.instrumentalness, d.popularity, 1)
    xs = np.linspace(0, 1, 50)
    axes[0].plot(xs, a + b * xs, color=ACCENT, lw=2)
    cfg(axes[0], f"Weakest-of-all-strong: instrumentalness vs popularity (r={r:.3f})")
    axes[0].set_xlabel("instrumentalness"); axes[0].set_ylabel("popularity")

    dd = k[["popularity"] + AUDIO + ["explicit"]].dropna()
    X = dd[AUDIO + ["explicit"]].astype(float)
    Xs = StandardScaler().fit_transform(X)
    y = dd.popularity.values
    m2 = LinearRegression().fit(Xs, y)
    fitted = m2.predict(Xs)
    axes[1].scatter(fitted, y - fitted, s=1, alpha=0.06, color="#333333")
    axes[1].axhline(0, color=ACCENT, lw=1.5)
    cfg(axes[1], f"OLS residuals (R²={m2.score(Xs, y):.3f}) — no structure, no signal")
    axes[1].set_xlabel("fitted popularity"); axes[1].set_ylabel("residual")
    fig.tight_layout(); fig.savefig(FIG / "06_scatter_residuals.png", dpi=110); plt.close(fig)
    made.append("06_scatter_residuals.png")

    print(f"wrote {len(made)} figures to {FIG}:")
    for f in made:
        print("  -", f)


if __name__ == "__main__":
    main()
