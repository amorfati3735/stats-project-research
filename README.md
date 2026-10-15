# SONIQ — Statistical Analysis of Music Popularity and Audio Characteristics

Research/feasibility phase for a Probability & Statistics course project (CSE
undergraduate, 3-week cycle: Review 1 → Review 2 → Review 3).

**Research question:** *Can statistical analysis of music audio characteristics
reveal significant relationships with track popularity?*

The measured answer is nuanced: **statistically yes, practically barely** —
which is exactly the interesting part.

## Status: research phase only

No application has been built yet (deliberately). This directory contains the
verified data, the audit, the statistical feasibility evidence and the plan.

## Direction reassessment (2026-10-15)

The Spotify direction was reassessed against five India-focused alternatives at
the user's request. **Recommended direction: Indian monsoon/rainfall analysis**
(proposed name **VARSA**), with the Spotify work kept as a fallback — nothing
Spotify was deleted or modified.

| file | what it is |
|---|---|
| `research/project_direction_comparison.md` | the reassessment report (dataset table, feasibility per candidate, scored rubric, 3-week plan, final answers) |
| `research/india_dataset_audit.md` | measured schema/quality + statistics for all six Indian datasets |
| `research/india_figures.py` → `research/figures_india/` | seven real Review-1 figures for the monsoon direction |
| `scripts/india_audit.py`, `scripts/india_stats_checks.py` | India audit + the statistics that decide feasibility |
| `data/india/` | downloaded Indian datasets (git-ignored; see `scripts/fetch_data.sh --india`) |

Headline: monsoon region explains η² = 0.875 of Jun-Sep rainfall variance
(vs η² = 0.254 for Spotify genre), 16/36 subdivision trends shrink to 9/36 after
Benjamini–Hochberg correction, and the 1-in-20-year deficit ranges from 47.6 %
of normal (West Rajasthan) to 77.8 % (Kerala).

## Start here

| file | what it is |
|---|---|
| `research/feasibility_report.md` | the main report (datasets, RQs, methods, plan, recommendation) |
| `research/dataset_audit.md` | measured schema/quality findings for every downloaded dataset |
| `research/eda.py` | reproducible initial EDA → `research/figures/*.png` |
| `research/figures/` | the six Review-1 figures (real plots, real data) |
| `research/_audit_raw.txt`, `research/_feasibility_raw.txt` | raw script output |
| `scripts/audit_datasets.py` | schema / missingness / duplicate / summary report |
| `scripts/feasibility_checks.py` | distribution fits, t-tests, ANOVA, χ², regression |
| `scripts/fetch_data.sh` | re-download the data (no credentials needed; `--india` for the monsoon sets) |
| `research/project_direction_comparison.md` | direction reassessment vs five India-focused alternatives |

## Reproduce everything

```bash
python -m venv .venv && . .venv/bin/activate   # or: uv venv .venv
pip install -r requirements.txt
bash scripts/fetch_data.sh                     # add --with-fma for the optional FMA set
python scripts/audit_datasets.py   | tee research/_audit_raw.txt
python scripts/feasibility_checks.py | tee research/_feasibility_raw.txt
python research/eda.py
```

## Data

Downloaded and audited (see `research/dataset_audit.md`):

- **Kaggle Spotify Tracks Dataset** — 114,000 tracks × 20 columns, 114 genres
  (1,000 each), target `popularity` (0–100, 14.1 % zeros).
- **TidyTuesday Spotify Songs (2020-01-21)** — 32,833 tracks × 23 columns,
  6 genres / 24 subgenres, target `track_popularity`, plus release dates.
- *(optional)* **FMA metadata** — 106,574 tracks with count-based play counts.

Large data files are git-ignored; re-fetch them with `scripts/fetch_data.sh`.

## Headline measured findings

- No audio feature correlates with popularity above |r| = 0.10 (114k) / 0.15 (TidyTuesday).
- Multiple regression on audio features: held-out R² = 0.022 (114k), 0.071 (TidyTuesday).
- Genre is the strongest real signal: one-way ANOVA F = 343.5, η² = 0.254 (114 genres).
- Explicit vs clean: +3.5 popularity points, Cohen's d = 0.158 (significant but small).
- 21.3 % (114k) / 13.6 % (TidyTuesday) of rows are duplicate tracks — independence is violated.
