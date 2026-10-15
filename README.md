# VARSA — Statistical Analysis of Indian Monsoon Rainfall Variability

**VARSA** ("rain" in Hindi/Sanskrit) — research/feasibility phase for a
Probability & Statistics course project (CSE undergraduate,
3-week cycle: Review 1 → Review 2 → Review 3).

**Central question:** *How variable is Indian monsoon rainfall across regions
and time, are the observed regional differences and long-run trends
statistically significant, and what is the probability of an extreme rainfall
deficit in each region?*

**Dataset:** India Meteorological Department (IMD), via the Open Government
Data platform — area-weighted monthly, seasonal and annual rainfall (mm) for 36
meteorological subdivisions, 1901–2015. One CSV, no credentials, 428 KB.

## Status: research phase only

No application has been built yet (deliberately). This directory contains the
verified dataset, the audit, the statistical feasibility evidence and the
three-week plan.

| file | what it is |
|---|---|
| `research/project_definition.md` | monsoon project definition — RQs, methods, rubric, plan, Review-1 answers |
| `research/dataset_audit.md` | measured schema, coverage and data-quality findings |
| `research/make_figures.py` | reproducible Review-1 figures → `research/figures/*.png` |
| `research/figures/` | seven real Review-1 figures (real data, generated locally) |
| `research/logs/audit_raw.txt`, `research/logs/stats_raw.txt` | raw script output |
| `scripts/audit_datasets.py` | schema / missingness / duplicate / summary report |
| `scripts/feasibility_checks.py` | distribution fits, power, multiple testing, trends, return periods |
| `scripts/fetch_data.sh` | re-download the data (no credentials needed) |

## Reproduce everything

```bash
python -m venv .venv && . .venv/bin/activate   # or: uv venv .venv
pip install -r requirements.txt
bash scripts/fetch_data.sh                       # downloads to data/raw/
python scripts/audit_datasets.py   | tee research/logs/audit_raw.txt
python scripts/feasibility_checks.py | tee research/logs/stats_raw.txt
python research/make_figures.py
```

## Data

Downloaded and audited (see `research/dataset_audit.md`):

- **IMD subdivision rainfall 1901–2015** — 4,116 rows × 19 columns, 36 meteorological
  subdivisions × 115 years, monthly + seasonal + annual totals, mm
  SHA-256: `fdc0b7fd8fccea2aab3910014ca7cacdd2f9faee511adda22b43cf30b680b4ec`

Optional secondary datasets (not needed for the core project) are in
`scripts/fetch_data.sh`.

Large data files are git-ignored; re-fetch them with `scripts/fetch_data.sh`.

## Headline measured findings (all reproducible)

| Question | Answer |
|---|---|
| How seasonal is Indian rainfall? | **75.2%** falls in Jun–Sep; monthly mean 19 mm (Jan) → 347 mm (Jul) |
| Do regions differ? | Yes — one-way ANOVA **F = 811.5, η² = 0.875**, Levene p ≈ 0 |
| Which regions are least reliable? | **Saurashtra & Kutch CV 40.8%**, West Rajasthan 37.2 %, Arunachal 31.6 %; least variable Assam & Meghalaya 12.0 % |
| Has monsoon changed? | 16/36 subdivision trends look significant — **only 9/36 survive** Benjamini–Hochberg at 5 % FDR |
| Is a single distribution enough? | No — December has **21.5% exact-zero** months with positive-part skew 4.73 |
| Extreme deficit | 1-in-20-year annual deficit = **47.6%** of normal in West Rajasthan vs **77.8%** in Kerala |
| Centennial trend detectability | median detectable slope ≈ **18% over the century** at 80 % power |

**What this means for the assignment:** the same syllabus (t-tests, F-tests,
ANOVA, distribution fitting, Pearson/Spearman, CIs, diagnostics) produces
*strong* effect sizes on rainfall — not the near-zero signal of a music-popularity
regression. Every figure above is generated locally from the downloaded CSV;
none are scraped or borrowed.

## Where the Spotify work went

This repo previously held a Spotify music-popularity baseline ("SONIQ").
It has been archived on the `soniq-spotify-archive` branch so `main` is
monsoon-only. If you ever need it:

```bash
git switch soniq-spotify-archive
git switch main
```
