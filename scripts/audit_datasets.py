#!/usr/bin/env python3
"""
SONIQ — dataset audit script.

Loads every CSV in data/raw/ and prints a reproducible structural + quality
report for each: schema, dtypes, shape, missing values, duplicates, numeric
summaries, categorical cardinality, target distribution and feature
correlations.

Run:
    .venv/bin/python scripts/audit_datasets.py
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
SEP = "=" * 78


def section(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


def audit(path: Path) -> dict:
    df = pd.read_csv(path, low_memory=False)
    # drop unnamed index columns that some Kaggle mirrors add
    junk = [c for c in df.columns if c.lower().startswith("unnamed")]
    if junk:
        df = df.drop(columns=junk)

    section(f"FILE: {path.name}")
    print(f"shape: {df.shape[0]:,} rows x {df.shape[1]} cols")
    print(f"memory: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    section(f"{path.name} :: SCHEMA")
    print(df.dtypes.to_string())

    section(f"{path.name} :: HEAD")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.head(3).to_string())

    section(f"{path.name} :: MISSING VALUES")
    miss = pd.DataFrame({"n_missing": df.isna().sum(), "pct": 100 * df.isna().mean()})
    miss = miss[miss.n_missing > 0].sort_values("n_missing", ascending=False)
    print(miss.to_string() if len(miss) else "no missing values")

    section(f"{path.name} :: DUPLICATES")
    print(f"exact duplicate rows: {df.duplicated().sum():,}")
    for key in ("track_id", "track_name", "id"):
        if key in df.columns:
            print(f"duplicate {key}: {df.duplicated(key).sum():,} "
                  f"({df[key].nunique():,} unique)")
    if "artists" in df.columns:
        print(f"unique artists: {df['artists'].nunique():,}")
    if "track_artist" in df.columns:
        print(f"unique track_artist: {df['track_artist'].nunique():,}")

    section(f"{path.name} :: NUMERIC SUMMARY")
    num = df.select_dtypes(include=np.number)
    with pd.option_context("display.width", 200):
        print(num.describe().T.to_string())

    section(f"{path.name} :: CATEGORICAL CARDINALITY")
    cat_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "str"]
    for c in cat_cols:
        nun = df[c].nunique()
        if nun <= 400:
            print(f"{c}: {nun} unique")
        else:
            print(f"{c}: {nun:,} unique (high)")

    for target in ("popularity", "track_popularity"):
        if target in df.columns:
            section(f"{path.name} :: TARGET '{target}' DISTRIBUTION")
            s = df[target]
            print(s.describe().to_string())
            print(f"skew: {s.skew():.3f}  kurtosis: {s.kurtosis():.3f}")
            print(f"zeros: {(s == 0).sum():,} ({(s == 0).mean() * 100:.1f}%)")
            print(f"value counts (top 15):")
            print(s.value_counts().head(15).sort_index().to_string())

    section(f"{path.name} :: CORRELATION WITH TARGET / TOP FEATURES")
    tgt = next((t for t in ("popularity", "track_popularity") if t in df.columns), None)
    if tgt:
        cols = [c for c in df.select_dtypes(include=np.number).columns if c != tgt]
        corr = df[cols + [tgt]].corr(numeric_only=True)[tgt].drop(tgt)
        print(corr.sort_values(key=abs, ascending=False).to_string())

    if "track_genre" in df.columns:
        section(f"{path.name} :: GENRE BALANCE")
        vc = df["track_genre"].value_counts()
        print(f"{vc.size} genres; per-genre: min={vc.min()} max={vc.max()} median={vc.median()}")
    if "playlist_genre" in df.columns:
        section(f"{path.name} :: playlist_genre BALANCE")
        print(df["playlist_genre"].value_counts().to_string())
    if "playlist_subgenre" in df.columns:
        print(f"\nsubgenres: {df['playlist_subgenre'].nunique()}")

    return {"file": path.name, "rows": df.shape[0], "cols": df.shape[1]}


def main() -> None:
    files = sorted(RAW.glob("*.csv"))
    if not files:
        raise SystemExit(f"No CSVs found in {RAW}")
    summary = [audit(f) for f in files]
    section("SUMMARY")
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
