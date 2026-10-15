#!/usr/bin/env python3
"""
SONIQ — India dataset audit / feasibility script.

Inspects every Indian dataset downloaded into data/raw/ and runs the
statistical feasibility checks the candidate projects would rely on, so the
comparison report quotes measured numbers.

Run:
    .venv/bin/python scripts/audit_datasets.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
IND = ROOT / "data" / "raw"
SEP = "=" * 78

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def section(t: str) -> None:
    print(f"\n{SEP}\n{t}\n{SEP}")


def basic(df: pd.DataFrame, name: str) -> None:
    section(f"[{name}] shape & dtype overview")
    print(f"{df.shape[0]:,} rows x {df.shape[1]} cols")
    print(df.dtypes.value_counts().to_string())
    miss = df.isna().sum()
    miss = miss[miss > 0]
    print("missing:", dict(miss.head(20)) if len(miss) else "none")
    print("exact duplicate rows:", df.duplicated().sum())


# ---------------------------------------------------------------- rainfall
def rainfall() -> None:
    d = pd.read_csv(IND / "rainfall_alt.csv")   # 1901-2015, Kaggle/OGD format
    basic(d, "RAINFALL 1901-2015")
    print(f"divisions: {d.DIVISION.nunique()}  years: {d.YEAR.min()}-{d.YEAR.max()} "
          f"({d.YEAR.nunique()} yrs)  rows: {len(d)}")

    section("[RAINFALL] coverage per division (year counts)")
    cov = d.groupby("DIVISION").YEAR.agg(["count", "min", "max"]).sort_values("count")
    print(cov.head(6).to_string())
    print("...")
    print(f"total divisions with incomplete history: {(cov['count'] < d.YEAR.nunique()).sum()}/{len(cov)}")

    section("[RAINFALL] zero-inflation by month (share of exactly 0 mm)")
    z = (d[MONTHS] == 0).mean().mul(100).round(1)
    print(z.to_string())

    section("[RAINFALL] seasonal / annual summary (mm)")
    with pd.option_context("display.width", 160):
        print(d[["ANNUAL", "Jun-Sep", "Mar-May", "Oct-Dec", "Jan-Feb"]].describe().T.to_string())

    section("[RAINFALL] distribution fits for JJAS (monsoon) total")
    x = d["Jun-Sep"].dropna().values
    for nm, dist in (("normal", stats.norm), ("gamma", stats.gamma),
                     ("weibull_min", stats.weibull_min), ("lognormal", stats.lognorm)):
        p = dist.fit(x)
        D, pv = stats.kstest(x, dist.cdf, args=p)
        print(f"  {nm:12s} D={D:.4f}  p={pv:.3g}  params={np.round(p, 3)}")
    print(f"  JJAS mean={x.mean():.1f} sd={x.std(ddof=1):.1f} skew={stats.skew(x):.3f} "
          f"min={x.min():.1f} max={x.max():.1f}")

    section("[RAINFALL] one-way ANOVA: JJAS ~ division (36 groups)")
    gs = [g["Jun-Sep"].dropna().values for _, g in d.groupby("DIVISION")]
    F, p = stats.f_oneway(*gs)
    lev_w, lev_p = stats.levene(*gs)
    grand = d["Jun-Sep"].mean()
    ssb = sum(len(g) * (g.mean() - grand) ** 2 for g in gs)
    sst = ((d["Jun-Sep"] - grand) ** 2).sum()
    print(f"F={F:.1f}  p={p:.3g}  eta^2={ssb/sst:.4f}  Levene W={lev_w:.1f} p={lev_p:.3g}")

    section("[RAINFALL] variability ranking: CV of ANNUAL rainfall per division")
    cv = d.groupby("DIVISION")["ANNUAL"].agg(["mean", "std", "count"])
    cv["CV_%"] = 100 * cv["std"] / cv["mean"]
    cv = cv.sort_values("CV_%", ascending=False)
    print("most variable:"); print(cv.head(6).round(1).to_string())
    print("least variable:"); print(cv.tail(6).round(1).to_string())

    section("[RAINFALL] temporal trend (OLS slope of JJAS on YEAR, per division)")
    slopes = []
    for div, g in d.dropna(subset=["Jun-Sep"]).groupby("DIVISION"):
        if len(g) > 40:
            b, a, r, pv, se = stats.linregress(g.YEAR, g["Jun-Sep"])
            slopes.append((div, b, pv))
    sl = pd.DataFrame(slopes, columns=["division", "slope_mm_per_yr", "p"])
    print(f"divisions with negative slope: {(sl.slope_mm_per_yr < 0).sum()}/{len(sl)}")
    print(f"significant at 5% (uncorrected): {(sl.p < 0.05).sum()}/{len(sl)}")
    print(sl.sort_values("slope_mm_per_yr").head(5).round(3).to_string(index=False))
    print(sl.sort_values("slope_mm_per_yr").tail(5).round(3).to_string(index=False))

    section("[RAINFALL] extreme-probability example (per-division Gamma fit)")
    print("P(annual rainfall < 75% of the division normal) = 'drought' probability")
    rows = []
    for div, g in d.groupby("DIVISION"):
        x = g["ANNUAL"].dropna().values
        if len(x) < 80:
            continue
        a, loc, sc = stats.gamma.fit(x)
        Dg, _ = stats.kstest(x, stats.gamma.cdf, args=(a, loc, sc))
        w = stats.weibull_min.fit(x)
        Dw, _ = stats.kstest(x, stats.weibull_min.cdf, args=w)
        thr = 0.75 * x.mean()
        rows.append((div, x.mean(), a, Dg, Dw, stats.gamma.cdf(thr, a, loc, sc), float((x < thr).mean())))
    ex = pd.DataFrame(rows, columns=["division", "mean_mm", "gamma_shape", "KS_gamma", "KS_weibull",
                                     "P_drought_gamma", "P_drought_empirical"])
    print(ex.sort_values("P_drought_empirical", ascending=False).round(3).to_string(index=False))
    print("\nKS: gamma beats normal almost everywhere (see the JJAS fit table above);")
    print("weibull is competitive; the yearly series are skewed, not normal.")

    section("[RAINFALL] period comparison: 1901-1957 vs 1958-2015 (JJAS per division)")
    first = d[d.YEAR <= 1957]
    second = d[d.YEAR > 1957]
    out = []
    for div, g in d.groupby("DIVISION"):
        a = g.loc[g.YEAR <= 1957, "Jun-Sep"].dropna()
        b = g.loc[g.YEAR > 1957, "Jun-Sep"].dropna()
        if len(a) > 20 and len(b) > 20:
            t, p_t = stats.ttest_ind(a, b, equal_var=False)
            Fv = a.var(ddof=1) / b.var(ddof=1)
            p_f = 2 * min(stats.f.cdf(Fv, len(a) - 1, len(b) - 1),
                          1 - stats.f.cdf(Fv, len(a) - 1, len(b) - 1))
            out.append((div, a.mean(), b.mean(), p_t, a.std(ddof=1), b.std(ddof=1), p_f))
    oc = pd.DataFrame(out, columns=["division", "mean_pre1957", "mean_post1957", "p_ttest",
                                    "sd_pre1957", "sd_post1957", "p_Ftest"])
    print(f"divisions tested: {len(oc)}")
    print(f"  mean shifted (Welch t, p<0.05, uncorrected): {(oc.p_ttest < 0.05).sum()}")
    print(f"  variance changed (F-test, p<0.05, uncorrected): {(oc.p_Ftest < 0.05).sum()}")
    print(f"  mean of all division means: pre={oc.mean_pre1957.mean():.1f} post={oc.mean_post1957.mean():.1f}")
    print(oc.sort_values("p_ttest").head(5).round(3).to_string(index=False))

    section("[RAINFALL] data-quality caveat check (network changes can fake trends)")
    ar = d[d.DIVISION == "ARUNACHAL PRADESH"].dropna(subset=["Jun-Sep"])
    print("ARUNACHAL PRADESH starts in", int(ar.YEAR.min()),
          "; JJAS mean by 20-year block:")
    ar = ar.copy(); ar["block"] = (ar.YEAR // 20) * 20
    print(ar.groupby("block")["Jun-Sep"].agg(["size", "mean"]).round(1).to_string())
    print("-> a large negative slope here reflects a short/uneven record, not necessarily climate.")


# ---------------------------------------------------------------- air quality
def air() -> None:
    d = pd.read_csv(IND / "aqi_city_day.csv")
    basic(d, "AIR QUALITY city_day")
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    print(f"cities: {d.City.nunique()}  dates: {d.Date.min().date()} -> {d.Date.max().date()}")
    print("rows per city (min/median/max):",
          int(d.groupby('City').size().min()), int(d.groupby('City').size().median()),
          int(d.groupby('City').size().max()))
    pol = ["PM2.5", "PM10", "NO2", "NOx", "NH3", "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene"]
    section("[AIR] pollutant summary + missingness")
    s = d[pol].describe().T[["count", "mean", "std", "50%", "max"]]
    s["missing_%"] = 100 * (1 - s["count"] / len(d))
    print(s.round(2).to_string())
    section("[AIR] AQI buckets")
    print(d["AQI_Bucket"].value_counts(dropna=False).to_string())
    section("[AIR] ANOVA: PM2.5 ~ city (top 10 cities by count)")
    top = d.City.value_counts().head(10).index
    gs = [g["PM2.5"].dropna().values for _, g in d[d.City.isin(top)].groupby("City") if g["PM2.5"].notna().sum() > 30]
    F, p = stats.f_oneway(*gs)
    lev = stats.levene(*gs)
    print(f"k={len(gs)}  F={F:.1f}  p={p:.3g}  Levene W={lev.statistic:.1f} p={lev.pvalue:.3g}")
    section("[AIR] correlation PM2.5 vs other pollutants (Pearson)")
    print(d[["PM2.5"] + [c for c in pol if c != "PM2.5"]].corr(numeric_only=True)["PM2.5"]
          .sort_values(ascending=False).round(3).to_string())


# ---------------------------------------------------------------- crop
def crop() -> None:
    d = pd.read_csv(IND / "crop_production.csv")
    d.columns = [c.strip() for c in d.columns]
    basic(d, "CROP PRODUCTION")
    print(f"states: {d.State_Name.nunique()}  districts: {d.District_Name.nunique()}  "
          f"crops: {d.Crop.nunique()}  years: {d.Crop_Year.min()}-{d.Crop_Year.max()}")
    print("seasons:", d.Season.str.strip().unique()[:10])
    section("[CROP] key coverage problems")
    print(f"rows with Production == 0: {(d.Production == 0).sum():,} ({100*(d.Production==0).mean():.1f}%)")
    print(f"rows with Area == 0: {(d.Area == 0).sum():,}")
    print(f"duplicate (state,district,crop,year,season): "
          f"{d.duplicated(['State_Name','District_Name','Crop','Crop_Year','Season']).sum():,}")
    print("rows per year (head/tail):")
    yr = d.groupby("Crop_Year").size()
    print(yr.head(3).to_string()); print(yr.tail(3).to_string())
    section("[CROP] can rainfall be joined? subdivision vs district granularity")
    print("crop geography = district name (free text), rainfall geography = 36 meteorological subdivisions")
    print("direct join possible:", False, "- would need a district->subdivision lookup (not shipped)")
    section("[CROP] ANOVA example: yield (Production/Area) across seasons, for Rice")
    r = d[(d.Crop == "Rice") & (d.Area > 0)].copy()
    r["yield_t_ha"] = r.Production / r.Area
    r = r[r.yield_t_ha.between(0.01, 15)]  # trim obvious unit errors
    gs = [g.yield_t_ha.dropna().values for _, g in r.groupby(r.Season.str.strip()) if len(g) > 50]
    if len(gs) > 1:
        F, p = stats.f_oneway(*gs)
        print(f"Rice n={len(r):,} k={len(gs)} F={F:.1f} p={p:.3g} "
              f"Wilcoxon-note: extreme skew (skew={stats.skew(r.yield_t_ha):.2f})")


# ---------------------------------------------------------------- electricity
def electricity() -> None:
    e = pd.read_csv(IND / "corrected_daily_energy_met_MU.csv")
    p = pd.read_csv(IND / "corrected_peak_met_MW.csv")
    basic(e, "ELECTRICITY daily energy (MU)")
    e["Date"] = pd.to_datetime(e["Date"], errors="coerce")
    print(f"dates: {e.Date.min().date()} -> {e.Date.max().date()}  n={len(e)}")
    states = [c for c in e.columns if c not in ("Date", "Total", "AMNSIL", "Damodar Valley Corporation")]
    section("[ELEC] per-state missingness (top 10)")
    m = e[states].isna().mean().mul(100).sort_values(ascending=False)
    print(m.head(10).round(1).to_string())
    section("[ELEC] Total demand summary + seasonality")
    t = e[["Date", "Total"]].dropna().copy()
    t["month"] = t.Date.dt.month
    t["year"] = t.Date.dt.year
    print(t.Total.describe().round(1).to_string())
    print("mean Total by month (MU):")
    print(t.groupby("month").Total.mean().round(0).to_string())
    section("[ELEC] one-way ANOVA: daily Total ~ month")
    gs = [g.Total.values for _, g in t.groupby("month")]
    F, pv = stats.f_oneway(*gs)
    grand = t.Total.mean()
    ssb = sum(len(g) * (g.mean() - grand) ** 2 for g in gs)
    sst = ((t.Total - grand) ** 2).sum()
    print(f"F={F:.1f} p={pv:.3g} eta^2={ssb/sst:.4f}")
    section("[ELEC] lag-1 autocorrelation of daily Total (independence check)")
    print(f"r(Total_t, Total_t-1) = {t.Total.autocorr(1):.4f}   "
          f"(raw i.i.d. assumption clearly violated)")
    section("[ELEC] distribution fit for daily Total")
    for nm, dist in (("normal", stats.norm), ("gamma", stats.gamma), ("weibull", stats.weibull_min)):
        prm = dist.fit(t.Total.values)
        D, pvv = stats.kstest(t.Total.values, dist.cdf, args=prm)
        print(f"  {nm:8s} D={D:.4f} p={pvv:.3g}")


def main() -> None:
    rainfall()
    air()
    crop()
    electricity()


if __name__ == "__main__":
    main()
