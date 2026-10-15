#!/usr/bin/env python3
"""
SONIQ — statistical feasibility checks.

Runs the candidate analyses the course project would rely on, on the *real*
downloaded datasets, so the feasibility report quotes verified numbers rather
than assumptions.

Analyses
  1. Popularity distribution + fitted distributions (Normal/Gamma/Weibull/Beta)
  2. One-way ANOVA of popularity across genre (+ Levene, eta-squared)
  3. Welch two-sample t-test: explicit vs non-explicit (+ Cohen's d, 95% CI)
  4. Chi-square test of independence: explicit x genre
  5. Pearson vs Spearman correlation of each audio feature with popularity
  6. Multiple linear regression, train/test R-squared
  7. Duplicate-track sensitivity (dedup and repeat)
  8. Temporal analysis for the dataset that has release dates

Run:
    .venv/bin/python scripts/feasibility_checks.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
SEP = "=" * 78

AUDIO = [
    "danceability", "energy", "key", "loudness", "mode", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
    "duration_ms",
]


def section(t: str) -> None:
    print(f"\n{SEP}\n{t}\n{SEP}")


def load(name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, low_memory=False)
    df = df.drop(columns=[c for c in df.columns if c.lower().startswith("unnamed")])
    return df


# ---------------------------------------------------------------- 1. distribution
def distribution(pop: pd.Series, label: str) -> None:
    section(f"[1] POPULARITY DISTRIBUTION — {label}")
    x = pop.dropna().astype(float)
    print(f"n={x.size:,} mean={x.mean():.3f} sd={x.std(ddof=1):.3f} "
          f"min={x.min():.0f} max={x.max():.0f}")
    print(f"skew={x.skew():.3f} kurtosis={x.kurtosis():.3f} "
          f"zeros={(x==0).mean()*100:.1f}%")
    q = x.quantile([.01, .05, .25, .5, .75, .95, .99])
    print("quantiles:", " ".join(f"{k:g}={v:.1f}" for k, v in q.items()))
    print("\nfitted distributions (KS test vs fit; smaller D = better fit):")
    fits = {
        "normal": stats.norm,
        "gamma": stats.gamma,
        "weibull_min": stats.weibull_min,
        "beta(scaled)": None,   # needs scaling to [0,1]
    }
    for nm, dist in fits.items():
        try:
            if nm == "beta(scaled)":
                data = x / 100.0
                a, b, loc, sc = stats.beta.fit(data, floc=0, fscale=1)
                D, p = stats.kstest(data, "beta", args=(a, b, 0, 1))
                print(f"  {nm:14s} a={a:.3f} b={b:.3f}  D={D:.4f} p={p:.3g}")
            else:
                params = dist.fit(x)
                D, p = stats.kstest(x, dist.cdf, args=params)
                ps = " ".join(f"{v:.3f}" for v in params)
                print(f"  {nm:14s} params=[{ps}]  D={D:.4f} p={p:.3g}")
        except Exception as e:  # noqa: BLE001
            print(f"  {nm}: fit failed ({e})")


# ---------------------------------------------------------------- 2. ANOVA
def anova(df: pd.DataFrame, pop: str, group: str, label: str) -> None:
    section(f"[2] ONE-WAY ANOVA: {pop} ~ {group} — {label}")
    d = df[[pop, group]].dropna()
    groups = [g[pop].values for _, g in d.groupby(group) if len(g) > 1]
    labels = [k for k, g in d.groupby(group) if len(g) > 1]
    sizes = d.groupby(group)[pop].size()
    print(f"k={len(groups)} groups; n per group: min={sizes.min()} "
          f"max={sizes.max()} median={int(sizes.median())}")
    F, p = stats.f_oneway(*groups)
    lev_w, lev_p = stats.levene(*groups)
    grand = d[pop].mean()
    ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    ss_total = ((d[pop] - grand) ** 2).sum()
    eta2 = ss_between / ss_total
    print(f"F={F:.2f}  p={p:.3g}  eta^2={eta2:.4f}  (Levene W={lev_w:.1f} p={lev_p:.3g})")
    means = d.groupby(group)[pop].mean().sort_values(ascending=False)
    print("highest-mean groups:", ", ".join(f"{k}={v:.1f}" for k, v in means.head(5).items()))
    print("lowest-mean groups:", ", ".join(f"{k}={v:.1f}" for k, v in means.tail(5).items()))


# ---------------------------------------------------------------- 3. t-test
def ttest(df: pd.DataFrame, pop: str, flag: str, label: str) -> None:
    section(f"[3] WELCH t-TEST: {pop} by {flag} — {label}")
    d = df[[pop, flag]].dropna()
    a = d.loc[d[flag] == True, pop].astype(float)   # noqa: E712
    b = d.loc[d[flag] == False, pop].astype(float)  # noqa: E712
    t, p = stats.ttest_ind(a, b, equal_var=False)
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    pooled = np.sqrt(((a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)) / (a.size + b.size - 2))
    ci = stats.t.interval(0.95, a.size + b.size - 2, loc=diff, scale=se)
    print(f"n(explicit)={a.size:,} mean={a.mean():.2f} | n(clean)={b.size:,} mean={b.mean():.2f}")
    print(f"diff={diff:.3f}  95% CI=[{ci[0]:.3f}, {ci[1]:.3f}]  t={t:.2f}  p={p:.3g}  Cohen's d={diff/pooled:.3f}")


# ---------------------------------------------------------------- 4. chi-square
def chisq(df: pd.DataFrame, f1: str, f2: str, label: str) -> None:
    section(f"[4] CHI-SQUARE INDEPENDENCE: {f1} x {f2} — {label}")
    d = df[[f1, f2]].dropna()
    ct = pd.crosstab(d[f1], d[f2])
    chi2, p, dof, exp = stats.chi2_contingency(ct)
    n = ct.values.sum()
    cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    print(f"table {ct.shape}  chi2={chi2:.1f}  dof={dof}  p={p:.3g}  n={n:,}  Cramer's V={cramers_v:.3f}")
    print(f"min expected count={exp.min():.2f}")


# ---------------------------------------------------------------- 5. correlations
def correlations(df: pd.DataFrame, pop: str, feats: list[str], label: str) -> pd.DataFrame:
    section(f"[5] PEARSON vs SPEARMAN vs POPULARITY — {label}")
    d = df[[pop] + [c for c in feats if c in df.columns]].dropna()
    out = []
    for c in [c for c in feats if c in df.columns]:
        r, pr = stats.pearsonr(d[pop], d[c])
        rho, ps = stats.spearmanr(d[pop], d[c])
        out.append((c, r, pr, rho, ps))
    res = pd.DataFrame(out, columns=["feature", "pearson_r", "p_pearson", "spearman_rho", "p_spearman"])
    with pd.option_context("display.width", 200):
        print(res.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    return res


# ---------------------------------------------------------------- 6. regression
def regression(df: pd.DataFrame, pop: str, feats: list[str], label: str,
               dummies: str | None = None) -> None:
    """OLS with standardised predictors.

    NOTE: scaling matters. `duration_ms` is ~2e5 while dummy/audio columns are
    O(1); on the *unscaled* design sklearn's LinearRegression silently returns
    badly wrong coefficients (R2 0.025 vs the true 0.2597 from lstsq). We
    standardise, then cross-check sklearn against statsmodels.
    """
    section(f"[6] MULTIPLE REGRESSION — {label}")
    cols = [c for c in feats if c in df.columns] + ([dummies] if dummies else [])
    d = df[[pop] + cols].dropna()
    X = pd.get_dummies(d[cols], columns=[dummies], drop_first=True) if dummies else d[cols]
    X = X.astype(float)
    y = d[pop].astype(float)
    cond_raw = np.linalg.cond(np.column_stack([np.ones(len(X)), X.values]))
    Xs = (X - X.mean()) / X.std(ddof=0)
    Xtr, Xte, ytr, yte = train_test_split(Xs, y, test_size=0.2, random_state=42)
    m = LinearRegression().fit(Xtr, ytr)
    r2_tr = m.score(Xtr, ytr)
    r2_te = m.score(Xte, yte)
    ols = sm.OLS(y, sm.add_constant(Xs)).fit()
    print(f"predictors={X.shape[1]}  n={len(d):,}  cond(design)={cond_raw:.3g}")
    print(f"train R2={r2_tr:.4f}   test R2={r2_te:.4f}   (gap={r2_tr-r2_te:.4f})   "
          f"OLS full R2={ols.rsquared:.4f} adj={ols.rsquared_adj:.4f}")
    # standardised coefficients = effect per 1 SD, directly comparable
    top = ols.params.drop("const").abs().sort_values(ascending=False).head(6)
    print("largest |std. coef|:", ", ".join(f"{k}={ols.params[k]:+.3f}" for k in top.index))


def main() -> None:
    k = load("kaggle_spotify_tracks_114k.csv")
    tt = load("tidytuesday_spotify_songs.csv")

    distribution(k["popularity"], "Kaggle 114k")
    distribution(tt["track_popularity"], "TidyTuesday")

    anova(k, "popularity", "track_genre", "Kaggle 114k (114 genres)")
    anova(tt, "track_popularity", "playlist_genre", "TidyTuesday (6 genres)")

    ttest(k, "popularity", "explicit", "Kaggle 114k")

    chisq(k, "explicit", "track_genre", "Kaggle 114k")
    chisq(tt, "playlist_genre", "playlist_subgenre", "TidyTuesday")

    correlations(k, "popularity", AUDIO, "Kaggle 114k")
    correlations(tt, "track_popularity", AUDIO, "TidyTuesday")

    regression(k, "popularity", AUDIO + ["explicit"], "Kaggle 114k, audio features only")
    regression(k, "popularity", AUDIO + ["explicit"], "Kaggle 114k, audio + genre dummies", dummies="track_genre")
    regression(tt, "track_popularity", AUDIO, "TidyTuesday, audio features only")
    regression(tt, "track_popularity", AUDIO, "TidyTuesday, audio + genre dummies", dummies="playlist_genre")

    # 7. duplicate sensitivity
    section("[7] DUPLICATE-TRACK SENSITIVITY")
    for name, df, pop in (("Kaggle 114k", k, "popularity"),
                          ("TidyTuesday", tt, "track_popularity")):
        dd = df.drop_duplicates("track_id")
        print(f"{name}: {len(df):,} rows -> {len(dd):,} unique track_id "
              f"({100*(1-len(dd)/len(df)):.1f}% removed)")
        for c in ("instrumentalness", "duration_ms", "energy"):
            if c in dd:
                r_all = stats.pearsonr(df[pop], df[c])[0]
                r_dd = stats.pearsonr(dd[pop], dd[c])[0]
                print(f"   r({c}, {pop}): all={r_all:+.4f}  dedup={r_dd:+.4f}")
        # artist-level non-independence
        art = df.get("track_artist", df.get("artists"))
        print(f"   tracks/artist: mean={len(df)/art.nunique():.2f} max={df.groupby(art).size().max()}")

    # 8. temporal
    section("[8] TEMPORAL INFORMATION")
    tt2 = tt.dropna(subset=["track_album_release_date"]).copy()
    tt2["year"] = pd.to_numeric(tt2["track_album_release_date"].str[:4], errors="coerce")
    tt2 = tt2.dropna(subset=["year"])
    print(f"TidyTuesday release years: {int(tt2.year.min())}–{int(tt2.year.max())}; n={len(tt2):,}")
    print("tracks per decade:")
    print((tt2["year"] // 10 * 10).value_counts().sort_index().to_string())
    tt2["decade"] = (tt2["year"] // 10 * 10).astype(int)
    dec = tt2.groupby("decade")["track_popularity"].agg(["size", "mean"]).query("size >= 30")
    print(dec.to_string())
    r, p = stats.pearsonr(tt2["year"], tt2["track_popularity"])
    print(f"corr(release year, popularity) r={r:.3f} p={p:.3g}")
    print(f"Kaggle 114k temporal columns: none (no release date / year field)")


if __name__ == "__main__":
    main()
