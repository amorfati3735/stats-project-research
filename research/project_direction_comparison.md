# Project Direction Comparison — Spotify (SONIQ) vs India-focused Statistics Projects

Research and feasibility reassessment. **Nothing here is implemented**; this document
exists to choose a direction with evidence.

- Prepared: 2026-10-15
- Project root: `/mnt/windows/Users/DELL/Downloads/materialgram/soniq/`
- Existing Spotify artefacts: **read and preserved, not modified**
- Companion document for measured schema/quality details: `research/india_dataset_audit.md`
- Every number below was produced by running code against downloaded files
  (`scripts/india_audit.py`, `scripts/india_stats_checks.py`, `research/india_figures.py`;
  raw output in `research/_india_audit_raw.txt`, `research/_india_stats_raw.txt`).
  Nothing here is quoted from a blog, a dataset description or an expectation.

---

## 1. Executive summary

**The Spotify project is the safest choice and, statistically, the shallowest. The Indian
monsoon project is the strongest choice, with risks that are visible and manageable.**

What the existing Spotify work actually established (measured earlier in this repo):
the maximum absolute correlation between any audio feature and `popularity` is **|r| =
0.095** on 114,000 tracks (0.150 on the TidyTuesday set); a held-out OLS predicting
popularity from audio alone reaches **R² = 0.022**, rising to 0.259 only once 114 genre
dummies are added; no simple distribution fits popularity (KS p ≈ 0); 21.3 % of rows are
redundant duplicates. In short: **the data is large, clean and easy, and the signal is
almost absent.** The interesting statistics are the *methodological traps* (unscaled
`LinearRegression` silently returning R² = 0.025 instead of 0.2597 because
`duration_ms ≈ 2e5` makes the design matrix ill-conditioned), not the phenomenon.

What the India work establishes (measured today): a 428 KB, 4,116-row, 36-subdivision ×
115-year rainfall series on which the same syllabus produces **strong, quotable results** —
Jun-Sep rainfall differs across subdivisions with **η² = 0.8747** (F = 811.5), annual
rainfall variability ranges from **CV 12.0 % (Assam & Meghalaya) to 40.8 % (Saurashtra &
Kutch)**, **16 of 36** subdivision trends look significant until Benjamini–Hochberg
correction cuts them to **9**, the 1-in-20-year deficit is **47.6 % of normal in West
Rajasthan** but 77.8 % in Kerala, and 75.2 % of all rainfall falls in four months with up
to 21.5 % of dry-season months at *exactly* zero millimetres.

Scores (1–5, nine criteria, unweighted mean): **Monsoon 4.56 > Air quality 3.78 >
Electricity 3.67 > Spotify 3.33 = Agriculture 3.33 > CPI 3.22.**

**Recommendation: switch the primary project to Indian monsoon rainfall analysis, and keep
the finished Spotify audit as a zero-cost fallback.** The switch costs almost nothing:
the data is already downloaded and audited, six of the seven Review-1 figures already
exist, and the Spotify work is not overwritten.

---

## 2. What the existing Spotify work already measures — and what is incomplete

*(Required by the brief §1: separate measured findings from outstanding work. The files
were inspected; nothing was changed.)*

### 2.1 Measured (these numbers are trustworthy and reusable)

| Finding | Value |
|---|---|
| Datasets verified | Kaggle Spotify Tracks 114k (114,000 × 20, 114 genres × 1,000 rows) and TidyTuesday Spotify Songs (32,833 × 23, 6 genres / 24 subgenres) |
| Strongest association with popularity | max abs Pearson \|r\| = **0.095** (114k) / 0.150 (TidyTuesday) |
| Predictive ceiling | held-out OLS R² **0.022** (audio only) → **0.259** (audio + 114 genre dummies) on 114k; TidyTuesday 0.071 → 0.088 |
| Genre effect | one-way ANOVA F = 343.46, **η² = 0.254** (114 genres), Levene p ≈ 0 |
| Explicit vs clean tracks | difference 3.52 popularity points, 95 % CI [3.02, 4.02], Cohen's d = 0.158 |
| Explicit × genre independence | χ² Cramér's V = 0.402 |
| Popularity zeros | 14.1 % (114k) / 8.2 % (TidyTuesday) |
| Distribution fit | no simple distribution fits popularity (KS p ≈ 0) |
| Duplicates | 21.3 % redundant rows (114k) / 13.6 % (TidyTuesday) |
| Temporal dimension | TidyTuesday only, release dates 1957–2020 (71 % in the 2010s); 114k has **no** date column |
| Documented trap | unscaled sklearn `LinearRegression` returned R² = 0.025 vs the true 0.2597 (condition number ≈ 3 × 10⁷, driven by `duration_ms ≈ 2e5`); `np.linalg.lstsq` and statsmodels agreed |
| Metadata discrepancy | Kaggle description says "125 genres"; the file contains **114** |

### 2.2 Incomplete or blocked in the Spotify work

- **FMA metadata (planned third dataset) is `DOCUMENTED ONLY`.** The download from
  `os.unil.cloud.switch.ch` repeatedly truncated (`curl: (18) end of response with N bytes
  missing`, then a timeout); the partial archive was deleted rather than half-analysed.
  FMA-based analyses (listens distribution, audio-feature ↔ listens correlations) were
  never run.
- **Kaggle-gated duplicates** of the 114k set (the 160k/600k variants) could not be
  obtained — no `~/.kaggle/kaggle.json` on this machine, HuggingFace mirrors return 401.
  So there is no second, larger sample to validate the weak-correlation result against.
- **No interaction, no diagnostics depth, no resampling.** The work stops at: groups,
  correlations, one OLS with dummies, one t-test, one χ². Missed opportunities the brief
  would otherwise expect: interaction terms (genre × explicit), residual diagnostics
  beyond a scatter, cross-validation of the genre-dummy model, multiple-comparison
  correction across the 9 features, and any time trend (impossible on the 114k file).
- **No application exists.** `research/eda.py` produces six static PNGs; there is no
  Streamlit/dashboard prototype, which is an explicit Review 1 item.
- **The weak-signal problem is structural, not fixable.** More features will not rescue a
  phenomenon whose best univariate correlation is 0.095.

---

## 3. Dataset comparison table (verified sources only)

All Indian files below were **actually downloaded and inspected** on 2026-10-15. Sizes
are measured bytes. "Licence" is what the publishing page/metadata states.

| # | Dataset | Upstream source | Downloaded from | Auth | Licence | Format / size | Shape | Coverage |
|---|---|---|---|---|---|---|---|---|
| A1 | **Rainfall, 36 meteorological subdivisions, monthly** (1901–2015) | IMD via Open Government Data platform — <https://www.data.gov.in/resource/area-weighted-monthly-seasonal-and-annual-rainfall-mm-36-meteorological-subdivisions-1901>; Kaggle original <https://www.kaggle.com/datasets/rajanand/rainfall-in-india> | <https://raw.githubusercontent.com/MainakRepositor/Datasets/master/rainfall%20in%20india%201901-2015.csv> | none | **CC BY-SA 4.0** (Kaggle page); IMD under Govt Open Data Licence – India | CSV, 437,910 B | **4,116 × 19** | 36 subdivisions × 115 years, monthly + seasonal + annual |
| A2 | Rainfall, same source, extended to 2017 | same as A1 (later revision) | <https://raw.githubusercontent.com/raghav0807/Rainfall-Data-Analysis-Visualization-/main/Dataset.csv> | none | as A1 (mirror) | CSV, 441,180 B | 4,188 × 19 | 36 subdivisions × 1901–2017, 26 rows with NaN |
| B1 | **Air quality, daily by city** (2015–2020) | CPCB — <https://cpcb.nic.in/>; Kaggle <https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india> | <https://raw.githubusercontent.com/adityarc19/aqi-india/main/city_day.csv> | none | **CC0: Public Domain** | CSV, 2,574,056 B (identical to the published 2.57 MB) | **29,531 × 16** | 26 cities, 2015-01-01 → 2020-07-01, daily |
| B2 | Air quality, station-level 15-min/hourly (variant) | CPCB Data & AQI repositories | <https://github.com/Vonter/india-cpcb-aqi> (release assets) | none | **ODbL-1.0** | Parquet / `.csv.gz` | *not downloaded* | station-level, longer window |
| C1 | **Crop area & production**, state/district/season | Ministry of Agriculture & Farmers Welfare via Kaggle <https://www.kaggle.com/datasets/aravindpcoder/india-crop-production-state-wise> | <https://raw.githubusercontent.com/Vishnukurra101/crop-production-india/main/crop_production.csv> | none | **CC0: Public Domain** | CSV, 15,316,741 B (matches published 15.32 MB / 246,091 rows) | **246,091 × 7** | 33 states, 646 districts, 124 crops, 1997–2015 |
| C2 | Crop production, ICRISAT district-level 1978–2017, 80 cols (variant) | ICRISAT via Kaggle <https://www.kaggle.com/datasets/ankanhore545/district-wise-major-crops-production-in-india> | — | none (Kaggle account for download) | **CC BY 4.0** | CSV | *not downloaded* | 40 years, per-crop area/production/yield |
| D1 | **Daily electricity demand per state** (2014–2024) | CEA / Grid-India grid reports; Zenodo DOI **10.5281/zenodo.14983362** | <https://zenodo.org/records/14983362> (`corrected_daily_energy_met_MU.csv`) | none | **CC BY 4.0** | CSV, 807,563 B | **3,955 × 40** | 33 usable states + grid entities, 2013-01-01 → 2024-04-28, daily |
| D2 | Daily peak met demand / unmet deficit | as D1 | same record | none | CC BY 4.0 | CSV, 1,039,164 B / 677,255 B | 3,955 × 40 | same dates |
| E1 | **CPI by state × commodity group × sector**, monthly | MoSPI CPI (base 2012 = 100) via India Data Portal (CKAN) | <https://ckandev.indiadataportal.com/dataset/b8836317-263c-4e11-a94c-32e5b295cd30/resource/487c360b-fbc1-4664-8b49-e11c73d105e5/download/consumer_price_index.csv> | none | **Open Data Commons Attribution (ODC-By)** | CSV, 20,232,662 B | **300,518 × 8** | 37 states/UTs + All-India, 28 groups, 3 sectors, 2014-01 → 2025-12 |
| S1 | Spotify Tracks 114k (existing) | Kaggle | already in `data/raw/` | none | page: "Database: Open Database, Contents: © Original Authors" | CSV, 20,118,244 B | 114,000 × 20 | 114 genres × 1,000 |
| S2 | TidyTuesday Spotify Songs (existing) | TidyTuesday GitHub | already in `data/raw/` | none | CC0-1.0 (repo) | CSV, 7,971,379 B | 32,833 × 23 | 6 genres / 24 subgenres, 1957–2020 |

**Blocked / gated, reported honestly:** `api.data.gov.in` requires a free registered API
key (returns **HTTP 400** without one). The MoSPI official CPI API
(`api.mospi.gov.in`) is unreachable from this machine —
`curl: (35) TLS connect error: … unsafe legacy renegotiation disabled` (OpenSSL 3 refuses
the legacy renegotiation the server requires; `--ciphers 'DEFAULT@SECLEVEL=1'` did not
help). IMD's official **0.25° daily gridded rainfall (1901–2024)** is listed at
<https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html> but is
**`UNVERIFIED`**: the download link is built by JavaScript and no direct file URL appears
in the served HTML. No paid API was used and no credentials exist on this machine.

---

## 4. Feasibility findings for each candidate (measured)

### A. Indian monsoon / rainfall — **strongest statistical object**

- **Shape:** 36 subdivisions × 1901–2015 (115 years), monthly + 3 seasonal aggregates +
  annual. 0 duplicate rows. 26 rows with a missing `ANNUAL`, 3–11 per month.
- **Coverage gaps:** Arunachal Pradesh starts 1916 (97 yrs), Andaman & Nicobar 110,
  Lakshadweep 114; the other 33 divisions are complete.
- **Seasonality:** Jun-Sep = **75.2 %** of annual rainfall. Monthly means run 19 mm (Jan)
  → 347 mm (Jul) → 19 mm (Dec). One-way ANOVA month: F = 3051.7, η² = 0.405.
- **Regional signal is much stronger than Spotify's:** ANOVA Jun-Sep ~ division gives
  **F = 811.5, η² = 0.8747** (vs η² = 0.254 for Spotify genre). Levene W = 53.4, p ≈ 0 →
  violates equal variances, so the *correct* answer is Welch ANOVA / Games-Howell, and
  reporting both is exactly the kind of judgement a statistics panel looks for.
- **Variability ranking is a real, quotable deliverable:** CV of annual rainfall ranges
  **12.0 % (Assam & Meghalaya) → 40.8 % (Saurashtra & Kutch)**, with West Rajasthan 37.2 %,
  Gujarat 30.3 %, Punjab 27.5 % at the unreliable end.
- **Trend analysis is a genuine methodological set-piece:** 16/36 divisions show a
  p < 0.05 linear trend (Jun-Sep vs year), Mann-Kendall agrees on the sign in 36/36 cases,
  but **Benjamini–Hochberg at FDR 5 % leaves only 9/36** — e.g. Kerala p = 0.0437 → q =
  0.1008, Konkan & Goa p = 0.0140 → q = 0.0504. A naive project would have claimed 16
  trends. This is the single best teaching result in either dataset.
- **Power is adequate:** the median slope detectable at 80 % power over 115 years is
  1.42 mm/yr ≈ 0.16 % of the mean per year (≈ 18 % per century).
- **Distribution modelling actually works — and the answer differs by region.** Pooled
  Jun-Sep: Normal KS D = 0.1352 (p = 6e-66) vs Gamma 0.0505, Weibull 0.0708, Lognormal
  **0.0255**. Per division on annual totals the AIC winner is Gamma (West Rajasthan),
  Weibull (Saurashtra & Kutch, Tamil Nadu), Lognormal (Kerala, Coastal Andhra) and
  **Normal (Assam & Meghalaya)**. Shapiro rejects normality of annual totals in 12/36
  divisions; median per-division skew = +0.31 (pooled 1.32).
- **Zero-inflation is real:** December has P(0 mm) = 0.215 and its positive part has skew
  4.73; July has P(0) = 0.000. Monthly rainfall is a **Bernoulli × Gamma mixture**, not a
  single distribution.
- **Extremes are quantifiable and map nicely:** 1-in-20-year annual deficit = 47.6 % of
  normal (West Rajasthan), 41.9 % (Saurashtra & Kutch), 55.0 % (Gujarat), 60.6 % (Punjab),
  70.4 % (Tamil Nadu), 77.8 % (Kerala).
- **Honest negative result available:** skewness of annual rainfall is *not* predicted by
  how wet the division is — Pearson r = −0.026 (p = 0.881), Spearman ρ = −0.222 (p = 0.194).
  Reporting a well-designed rejection is a strength, not a gap.
- **Dependence is a real trap and a real exercise:** pairwise correlation of annual Jun-Sep
  across 630 division pairs: mean 0.196, **78.6 % positive**, max 0.812. Divisions are
  neither independent nor interchangeable.
- **Limits to state in the report:** subdivision-level only (36), monthly only (no daily
  extremes), and **not joinable to district-level crop data** without a crosswalk.
- **Cost:** 428 KB, loads instantly, no auth, no cleaning beyond strip/dropna.

### B. Indian air quality

- 29,531 daily city rows, 16 columns, 26 cities, 2015-01-01 → 2020-07-01, no duplicates.
- **Unbalanced panel:** rows per city range 113 → 2,009 (median 1,113).
- **Heavy missingness:** Xylene 61.3 %, PM10 37.7 %, NH3 35.0 %, Toluene 27.2 %,
  Benzene 19.0 %, PM2.5 15.6 %, AQI 15.9 %.
- Strong ANOVA across cities (F = 558.5, p ≈ 0) with Levene p ≈ 0; exactly one strong
  correlation (PM2.5–PM10 r = 0.846), then NOx 0.437, NO2 0.351, NH3 0.275, and the rest
  ≤ 0.16.
- **Verdict:** workable and relevant, but a 5.5-year unbalanced panel with 1/3–2/3 missing
  in several pollutants supports *missing-data methods and threshold probabilities*, not
  long-run trend analysis. The station-level ODbL variant (B2) would fix the resolution
  problem but adds its own data-engineering load.

### C. Indian agriculture

- 246,091 rows × 7 columns; 33 states, 646 districts, 124 crops, 6 seasons, 1997–2015.
- 3,730 missing `Production`; 3,523 rows with `Production == 0` (1.4 %); 0 duplicate keys;
  **2015 is incomplete (562 rows vs 10,973 in 2014)**; season labels carry stray
  whitespace; no `Yield` column (derive `Production / Area`, and screen unit errors — the
  published notebooks flag sugarcane yields > 168 t/ha as errors).
- Rice yield differs across seasons (n = 15,068, F = 382.0, p ≈ 0) but the response is
  right-skewed (skew 0.72).
- **The brief's explicit test fails here:** rainfall is subdivision-level (36), crop data
  is district-level free text (646) — **a direct join is not possible**
  (`direct join possible: False`). A *state-level* join is feasible with a hand-built
  36-subdivision → state crosswalk (~1 day), so a state-level rainfall-yield analysis is
  possible but a district-level one must not be promised.

### D. Indian electricity

- 3,955 daily rows × 40 columns, 2013-01-01 → 2024-04-28 (title says 2014–2024; the file
  itself starts 2013).
- **43 exact duplicate rows**; two states 100 % missing (Andaman & Nicobar, Lakshadweep),
  Dadra & Nagar Haveli / Daman & Diu 17.6 %, Telangana 10.7 % → ~33 usable states.
- `Total` mean 3464.7 MU, sd 569.8, min 2218.7, max 5224.3. Monthly means peak in
  **Aug (3586) and Jun (3585)** and bottom in **Nov (3202)** — a real but *small* seasonal
  effect: one-way ANOVA ~ month F = 17.9, p = 2.5e-35, **η² = 0.048**.
- **lag-1 autocorrelation = 0.9874.** Naive t-tests/ANOVA/OLS on daily values are invalid;
  the project must use differencing, HAC errors, ARIMA/seasonal decomposition or a block
  bootstrap. High ceiling, higher statistical risk, and the centre of gravity is
  time-series rather than the core probability syllabus.
- Extra value not yet used: `peak_unmet_MW.csv` (deficits) and 36 per-state files with
  daily weather covariates (~3.6 MB each) for demand-vs-weather modelling.

### E. Indian CPI / inflation

- 300,518 rows × 8 columns; 37 states/UTs + All-India; 28 commodity groups; 3 sectors;
  monthly 2014-01 → 2025-12 (143 months).
- `cpi`/`inflation_rate` missing in 3,154 rows; **83 duplicate keys**.
- All-India Combined inflation: mean 5.01 %, sd 5.78, min −27.57 %, max +60.50 %
  (food groups drive extremes; All-India Combined Vegetables CPI spans 114.5 → 292.0).
- All-India Cereals inflation (n = 143): skew 0.86, Normal not rejected (KS D = 0.1017,
  p = 0.097; Student-t D = 0.0686, p = 0.49) but **lag-1 autocorrelation 0.9599**.
- Cross-state differences are *weak*: ANOVA of Cereals inflation across states
  (k = 22) F = 2.0, p = 0.0036 with autocorrelated residuals.
- **Verdict:** real data, real questions, but 12 years, smooth autocorrelated series and
  weak cross-sectional effects — the least rewarding of the five, and it cannot be joined
  to the rainfall series (rainfall ends 2015; only 2014–2015 overlap).

### Deliberately tested and rejected cross-dataset ideas

- **Rainfall × crop yield at district level** — blocked: incompatible geographies.
- **Rainfall deficit × food inflation (lagged)** — blocked: rainfall ends 2015, CPI starts
  2014 → a 2-year overlap. Not viable.
- **Rainfall × electricity demand** — overlap only 2013–2015 → too short for seasonality
  and extremes. Not viable.
- These are recorded so no one re-proposes them in week 2.

---

## 5. Statistical methods available, per topic (mapped to the syllabus)

Syllabus items: descriptive/EDA · probability distributions & fitting · expectation,
variance, covariance, correlation · confidence intervals · hypothesis testing (t, F) ·
chi-square · Pearson & Spearman · simple/multiple regression · one-way/two-way ANOVA ·
model diagnostics & validation.

| Syllabus item | A Monsoon | B Air quality | C Agriculture | D Electricity | E CPI | S Spotify (existing) |
|---|---|---|---|---|---|---|
| Descriptive / EDA | ✅ 36 × 115 heatmaps, CV ranking | ✅ city × month | ✅ state × year × crop | ✅ long time series | ✅ | ✅ done |
| Distributions & fitting | ✅✅ Gamma/Weibull/Lognormal; **Bernoulli × Gamma mixture**; AIC/KS | ✅ log-normal-ish concentrations | ⚠️ skewed yields, few clean laws | ✅ daily demand (Gamma) | ✅ t vs Normal | ❌ nothing fits (measured) |
| Expectation / variance / covariance / correlation | ✅ CV, spatial covariance matrix | ✅ pollutant correlation matrix | ✅ yield variance decomposition | ✅ | ✅ | ✅ done (weak) |
| Confidence intervals | ✅ t-CI **and** bootstrap, compared | ✅ | ✅ | ⚠️ needs block bootstrap | ✅ | ✅ done (1) |
| t-tests / F-tests | ✅ Welch period test; **F-test for variance change**; Levene | ✅ pre/post-2020 lockdown is a natural experiment | ✅ | ⚠️ autocorrelated | ✅ | ✅ done (1) |
| Chi-square | ✅ GoF on binned fitted distribution; independence of drought class × region/decade | ⚠️ AQI bucket × city/season | ⚠️ crop × season | ⚠️ | ⚠️ category × state | ✅ done (1) |
| Pearson & Spearman | ✅ rainfall vs year; division pairs; JJAS vs annual | ✅ PM2.5 vs pollutants | ✅ area vs production | ✅ | ✅ | ✅ done |
| Simple / multiple regression | ✅ trend per division (+ **multiple-comparison correction**) | ✅ AQI ~ pollutants | ✅ yield ~ area/season | ✅ demand ~ weather (state files) | ✅ inflation ~ time/category | ✅ done |
| One-way / two-way ANOVA | ✅✅ division; month; **division × month**; Welch version | ✅ city; city × season | ✅ season; crop; state | ✅ state; month | ✅ state; category | ✅ done (1) |
| Diagnostics & validation | ✅ residual checks, KS/AD, bootstrap, sensitivity to BH, network-change caveat | ✅ missing-data sensitivity | ✅ unit-error screening | ✅ stationarity/ACF | ✅ | ✅ done |

**Legend:** ✅✅ = the dataset is unusually well suited · ✅ = well supported · ⚠️ = possible
only with explicit assumptions or extra work · ❌ = measured as not supported.

**Methods that are *not* justified and should be avoided or restated:**

- **Ordinary one-way ANOVA with equal-variance assumptions** on rainfall or PM2.5 —
  Levene rejects in both (p ≈ 0). Use Welch ANOVA / Games-Howell and say why.
- **Ordinary t-tests and ANOVA on daily electricity demand or monthly CPI** —
  lag-1 autocorrelation is 0.987 and 0.960 respectively. Use differences, HAC/Newey-West
  standard errors, ARIMA, or a block bootstrap; report the effective sample size.
- **Reading 36 uncorrected trend p-values as 36 findings** — apply BH (or Bonferroni) and
  report both. This is a *feature* of the monsoon project.
- **Any district-level rainfall-yield regression** — the geographies do not match.
- **Any causal claim** (e.g. "rainfall caused the yield change"). All five datasets are
  observational.
- **Forcing every syllabus item in.** Monsoon naturally covers all eleven; that is a
  reason to prefer it, not a reason to pad the others.

---

## 6. Preliminary findings from the actual downloaded data

### 6.1 Rainfall (the case for the direction)

Seven figures already exist in `research/figures_india/`
(`01_seasonality.png` … `07_contrast_datasets.png`), generated by
`research/india_figures.py`. They show: the Jun-Sep concentration; the month-by-month
zero-inflation; the Normal-vs-Gamma fit on monsoon totals; the 36-division CV ranking; the
Sen slopes coloured by BH significance; the Gamma return-period curves; and a contrast
panel (electricity's autocorrelated series and the PM2.5 histogram).

Headline numbers (all measured, all reproducible):

| Question | Answer |
|---|---|
| How seasonal is Indian rainfall? | **75.2 %** of it falls in Jun-Sep; monthly mean 19 mm (Jan) → 347 mm (Jul) |
| How often is a year dry? | **23 of 115** years (20.0 %) below 90 % of the all-India normal (1064.7 mm); driest 1972 (−22.8 %), 2002 (−21.3 %), 1905 (−17.4 %), 2009 (−17.0 %). **No year falls below 75 % nationally** — severe deficits are regional, which is why the per-division return periods carry the argument |
| Do regions differ? | Yes, overwhelmingly: ANOVA **F = 811.5, η² = 0.8747**, Levene p ≈ 0 |
| Which regions are least reliable? | **Saurashtra & Kutch CV 40.8 %**, West Rajasthan 37.2 %, Arunachal 31.6 %; least variable Assam & Meghalaya 12.0 % |
| Has it changed? | 16/36 significant before correction, **9/36 after BH**; 1901–57 mean 1094.3 mm vs 1958–2015 1055.5 mm; variance changed in only 2/36 (F-test) |
| Do extremes matter? | 1-in-20-yr deficit = **47.6 %** of normal in West Rajasthan vs **77.8 %** in Kerala |
| Which distribution? | Lognormal/Gamma beat Normal on monsoon totals (KS D 0.0255 / 0.0505 vs 0.1352); on annual totals the winner is region-dependent |
| Is a single distribution enough? | No — December is **21.5 % zeros** with positive-part skew 4.73: a Bernoulli × Gamma mixture |
| Can we detect a century-scale change? | Yes: median detectable slope 1.42 mm/yr ≈ 18 % per century at 80 % power |
| Are the divisions independent? | No — 78.6 % of the 630 pairs correlate positively (mean r = 0.196, max 0.812) |

### 6.2 The other candidates (why they are not first)

- **Air quality:** one strong association (PM2.5–PM10, r = 0.846), everything else ≤ 0.44;
  Xylene 61 % and PM10 38 % missing; 5.5 years.
- **Agriculture:** season affects rice yield (F = 382.0) but the natural rainfall-yield
  question is blocked by geography; 2015 is a partial year; unit errors present.
- **Electricity:** month explains only **η² = 4.8 %** of daily demand variation, and
  lag-1 autocorrelation is 0.987 — statistically interesting *because* it is hard.
- **CPI:** cross-state differences are weak (F = 2.0) with autocorrelation 0.96.
- **Spotify:** best \|r\| = 0.095; R² = 0.022 without genre dummies.

---

## 7. Comparison rubric with scores and justification

**Scoring.** Each criterion is scored 1 (poor) – 5 (excellent). I deliberately report the
**unweighted mean** so the ranking does not hide behind weights, then discuss the two
criteria that deserve the most weight in a *Probability & Statistics* course —
*statistical depth* and *ability to produce meaningful findings* — plus *three-week
feasibility*. "Risk of methodological problems" is scored so that **5 = low risk**.

| Criterion | Spotify | **Monsoon** | Air quality | Agriculture | Electricity | CPI |
|---|---|---|---|---|---|---|
| Dataset accessibility & reliability | 4 | **4** | 4 | 4 | **5** | 4 |
| Statistical depth | 3 | **5** | 4 | 3 | 4 | 3 |
| Real-world relevance | 3 | **5** | 5 | 5 | 5 | 4 |
| Interestingness of the research question | 2 | **5** | 4 | 3 | 4 | 3 |
| Visualization / presentation potential | 3 | **5** | 4 | 3 | 4 | 3 |
| Ability to produce meaningful findings | 2 | **5** | 3 | 3 | 3 | 2 |
| Feasibility within three weeks | **5** | 4 | 4 | 3 | 3 | 4 |
| Risk of methodological problems (5 = low) | 4 | 3 | 3 | 3 | 2 | 3 |
| Ability to demonstrate results at Review 1 | 4 | **5** | 3 | 3 | 3 | 3 |
| **Unweighted mean** | **3.33** | **4.56** | 3.78 | 3.33 | 3.67 | 3.22 |

Justifications, in the order they matter:

1. **Statistical depth — Monsoon 5.** It is the only candidate that exercises the *whole*
   syllabus natively: a probability distribution question (fit and select among
   Gamma/Weibull/Lognormal), a mixture/zero-inflation question, CI estimation with a
   bootstrap cross-check, three different hypothesis-test families (t, F, χ²), ANOVA with
   a real variance violation to handle, Pearson **and** Spearman with a negative result,
   regression with a multiple-comparison correction, and diagnostics. Spotify scores 3
   because its syllabus content is broad but shallow — the tests run, but on noise.
2. **Meaningful findings — Monsoon 5, Spotify 2.** Measured effect sizes decide this:
   η² = 0.8747 (monsoon region) vs η² = 0.254 (Spotify genre); best univariate r = 0.196
   *for spatial structure* vs 0.095 for popularity. A monsoon report can say "these
   regions are reliably different and these nine trends survive correction"; a Spotify
   report can only say "audio features barely predict popularity".
3. **Feasibility — Spotify 5, Monsoon 4.** Spotify's data is already audited and its
   scripts already exist; that is real, banked work. Monsoon is 428 KB with no auth and
   no cleaning, but it needs one mapping task (subdivision → state) only if the
   agriculture/electricity extensions are attempted — the core project needs nothing.
4. **Risk — Spotify 4, Monsoon 3, Electricity 2.** Monsoon's risks (heteroscedasticity,
   spatial dependence, multiplicity, changing station networks) are *identified and
   addressable* and are the reason the project is interesting. Electricity's 0.987
   autocorrelation makes incorrect inference the default outcome for students who have not
   met time series, which is the highest methodological risk in the table.
5. **Accessibility — Electricity 5.** Zenodo with a DOI, CC BY 4.0, no auth, plus a
   documented data-quality story (43 duplicates, two 100 %-missing states). Monsoon gets 4
   because the canonical copy here is a mirror, not the OGD download, and OGD needs an API
   key.
6. **Review 1 — Monsoon 5, Spotify 4.** Both can show real figures today; Spotify already
   has six, monsoon already has seven. Air quality, agriculture, electricity and CPI have
   none yet.

**Trade-off in one sentence.** Spotify is a low-risk, low-payoff project whose statistical
content is mostly about avoiding traps; the monsoon is a medium-risk, high-payoff project
whose statistical content *is* the phenomenon.

**Alternatives discovered (not in the original five).** (i) The **station-level CPCB**
dataset (`Vonter/india-cpcb-aqi`, ODbL-1.0) fixes air quality's resolution problem and
would score better on depth and findings than B1 — but it was not downloaded, so it cannot
be scored as a verified candidate and is not recommended as the primary. (ii) **ICRISAT
district-level crop data 1978–2017 (CC BY 4.0, 80 columns)** is a better long-horizon
agriculture source than C1 — also not downloaded, also not displacing the monsoon.
(iii) A **monsoon × ENSO/IOD teleconnection** extension is *conceptually* attractive
(NOAA publishes free indices) but the external index files are **`UNVERIFIED`** and must
not be promised before a working download is confirmed.

---

## 8. Recommended direction, research question and project title

### 8.1 Recommended direction

**Take the Indian monsoon/rainfall project as the primary deliverable. Keep the Spotify
artefacts as the fallback.** Concretely: do not delete or rewrite anything Spotify;
build the new project alongside it in the same repo (`data/india/`, `scripts/india_*.py`,
`research/figures_india/`, `research/project_direction_comparison.md`,
`research/india_dataset_audit.md`, `research/india_figures.py`).

Why this is the right call, in one line each: (1) the statistical effect sizes are
1.5–5× larger; (2) the probability content is genuinely present (distribution selection,
mixtures, extremes) rather than nominal; (3) it covers all eleven syllabus items without
padding; (4) drought-risk findings are immediately meaningful; (5) the data is 428 KB,
requires no credentials and no cleaning; (6) a reviewer will remember it, whereas another
Spotify audio-feature analysis is indistinguishable from thousands of others; (7) switching
costs almost nothing because the audit and six of seven Review-1 figures are already built.

### 8.2 Suggested name

**VARSA** ("rain" in Hindi/Sanskrit) — short, unambiguous, and avoids any Spotify branding
or implied affiliation. (Retire the name SONIQ, which was tied to the Spotify notion.)

### 8.3 Title

> **"How Unreliable Is the Indian Monsoon? Statistical Analysis of Rainfall Variability,
> Trends and Drought Risk Across 36 Meteorological Subdivisions (1901–2015)"**

### 8.4 Central research question

> **How variable is Indian monsoon rainfall across regions and time, are the observed
> regional differences and long-run trends statistically significant, and what is the
> probability of an extreme rainfall deficit in each region?**

Sub-questions (each mapped to a named method, each answerable from the one dataset):

| # | Sub-question | Method | Data columns |
|---|---|---|---|
| RQ1 | Do mean Jun-Sep totals differ across the 36 subdivisions, and how large is the effect? | One-way ANOVA + η², **Welch ANOVA** and Games-Howell (Levene says variances differ), Tukey HSD for contrast | `DIVISION`, `Jun-Sep` |
| RQ2 | Which subdivisions are least *reliable* (not just wettest/driest)? | CV ranking + bootstrap CI on CV; Levene / F-test to compare variances across periods | `ANNUAL`, `Jun-Sep` |
| RQ3 | Has the level or the variability of monsoon rainfall changed? | OLS regression per division, **Mann-Kendall/Sen's slope**, Welch two-sample t-test on 1901–57 vs 1958–2015, F-test on variances — **all with Benjamini–Hochberg correction** | `YEAR`, `Jun-Sep` |
| RQ4 | What is the probability of a serious deficit, and does it vary by region? | Gamma/Weibull/Lognormal fitting (KS + AIC/BIC), quantiles → 1-in-20 / 1-in-50-year deficits, χ² goodness-of-fit on binned data | `ANNUAL` |
| RQ5 | Can monthly rainfall be modelled probabilistically at all? | **Bernoulli × Gamma (zero-inflated) mixture**, P(0) by month, Gamma on the positive part; compare against a single Normal | `JAN…DEC` |
| RQ6 | Do regional monsoons move together, and what does that do to inference? | Pearson/Spearman correlation matrix across 630 division pairs; effective-sample-size note; Spearman shown as the robust companion | `Jun-Sep` by `YEAR` × `DIVISION` |
| RQ7 | Is there a real seasonal × regional interaction? | **Two-way ANOVA** (division × month) with residual diagnostics | `DIVISION` × month |

A tested-and-rejected hypothesis is included on purpose (annual-rainfall skew is not
explained by mean rainfall: r = −0.026, p = 0.881) so the report shows the team can
report a null result.

---

## 9. Recommended dataset and exact download instructions

**Primary dataset — one file is enough for the entire core project:**

| | |
|---|---|
| Title | Rainfall in India — area-weighted monthly, seasonal and annual rainfall for 36 meteorological subdivisions, 1901–2015 |
| Provenance | India Meteorological Department, via the Open Government Data platform; Kaggle copy by Rajanand Ilangovan |
| Licence | CC BY-SA 4.0 (state it, and keep attribution to IMD/OGD) |
| Size | 437,910 bytes, CSV, 4,116 rows × 19 columns |
| SHA-256 | `fdc0b7fd8fccea2aab3910014ca7cacdd2f9faee511adda22b43cf30b680b4ec` |

```bash
cd /mnt/windows/Users/DELL/Downloads/materialgram/soniq
mkdir -p data/india && cd data/india

# primary: 36 subdivisions, monthly, 1901-2015 (CC BY-SA 4.0)
curl -sSL -o rainfall_1901_2015_kaggle.csv \
  'https://raw.githubusercontent.com/MainakRepositor/Datasets/master/rainfall%20in%20india%201901-2015.csv'

# integrity check - must print the hash above
sha256sum rainfall_1901_2015_kaggle.csv

# optional sensitivity check: the same series extended to 2017 (unverified tail)
curl -sSL -o rainfall_1901_2017_mirror.csv \
  'https://raw.githubusercontent.com/raghav0807/Rainfall-Data-Analysis-Visualization-/main/Dataset.csv'
```

Notes: the file already present locally is `data/india/rainfall_alt.csv`, which is the
same file (same hash). If the OGD copy is wanted instead, register for a free API key at
<https://www.data.gov.in/> and use the catalog page
<https://www.data.gov.in/resource/area-weighted-monthly-seasonal-and-annual-rainfall-mm-36-meteorological-subdivisions-1901>;
without a key the API returns HTTP 400, which is why the mirror was used.

**Optional secondary datasets, only if the core is finished.** Downloads already verified
locally, commands in `scripts/fetch_data.sh`:

```bash
# air quality, daily by city, 2015-2020, CC0
curl -sSL -o aqi_city_day.csv \
  'https://raw.githubusercontent.com/adityarc19/aqi-india/main/city_day.csv'

# crop area & production, district/season, 1997-2015, CC0
curl -sSL -o crop_production.csv \
  'https://raw.githubusercontent.com/Vishnukurra101/crop-production-india/main/crop_production.csv'

# daily electricity demand per state, CC BY 4.0 (Zenodo DOI 10.5281/zenodo.14983362)
curl -sSL -o corrected_daily_energy_met_MU.csv \
  'https://zenodo.org/records/14983362/files/corrected_daily_energy_met_MU.csv?download=1'
```

**Do not** plan around the IMD 0.25° gridded NetCDF or the MoSPI/OGD APIs until a working
download has actually been demonstrated — both are currently unverified/blocked
(`research/india_dataset_audit.md` §6).

---

## 10. Proposed application (dashboard) — strongest three candidates

### 10.1 Monsoon dashboard (recommended) — VARSA

*Core, realistically buildable in the three weeks* (Streamlit + Plotly, reading only the
one CSV):

1. **Regional variability ranking** — horizontal CV bars for the 36 subdivisions, sortable,
   with HDI-style colouring. *(figure 04 already exists)*
2. **Seasonal heatmap** — division × month mean rainfall on a shared colour scale, showing
   the Jun-Sep wall. *(figure 01)*
3. **Year × division heatmap** — the full 1901–2015 matrix, so the deficit years appear
   as vertical stripes. The driest seasons in this record, as departures from the
   all-India normal of 1064.7 mm, are **1972 (−22.8 %), 2002 (−21.3 %), 1905 (−17.4 %),
   2009 (−17.0 %), 1918 (−15.9 %), 1965 (−15.7 %)**; 23 of the 115 years sit below 90 % of
   normal.
4. **Distribution explorer** — histogram + fitted Gamma/Weibull/Lognormal/Normal overlay
   with live KS D and AIC, and a division selector. *(figure 03)*
5. **Drought probability calculator** — pick a division and a rainfall threshold, get
   P(deficit), the required return period, and the Gamma-vs-empirical comparison.
   *(figure 06)*
6. **Trend panel** — Sen's slope per division with p-values shown **before and after
   Benjamini–Hochberg**, with a toggle. This is the app's signature feature. *(figure 05)*
7. **Interpretation panel** — every gauge carries one plain-English sentence and one
   explicit assumption/caveat (e.g. "Welch ANOVA used because Levene's test rejects equal
   variances").

*Optional / stretch:* an India choropleth of the 36 subdivisions **only if** a matching
meteorological-subdivision boundary file is found — **`UNVERIFIED`**; no such file has been
located or verified, and the figures above deliberately do not depend on a map. A
state-level choropleth from a public India-states boundary file is the fallback, and the
heatmaps and bar rankings alone tell the whole story.

### 10.2 Air-quality dashboard (runner-up)

City × month pollutant heatmaps, city ranking with bootstrap CIs, PM2.5–PM10 scatter with
a fitted line and diagnostics, threshold-exceedance probability per city, and an explicit
missing-data panel (Xylene 61 %, PM10 38 %) — the honesty about missingness is what would
make it stand out.

### 10.3 Electricity dashboard (third)

Daily demand time series with a 7-day rolling mean, state × month heatmap, month-of-year
boxplots with an ANOVA table attached, an ACF/PACF panel that makes the 0.987
autocorrelation visible, and a peak-demand exceedance calculator. Attractive, but it
requires the team to implement autocorrelation-aware inference correctly.

*(Spotify's dashboard would be genre rankings, a correlation heatmap and regression
diagnostics — visually fine, but it would present a 0.095 correlation as the finding.)*

---

## 11. Three-week execution plan

The exact Review 1 date is still an open question (§13). The plan is therefore expressed
as **Day 1 … Day 21** from the confirmed start; if Review 1 falls on Day 7, the Review 1
box below is the hard commitment and everything after it is Review 2.

### Review 1 (30 % of marks) — Days 1–7: *"this is feasible and here is the evidence"*

Day-to-day:

| Day | Work | Output |
|---|---|---|
| 1 | Re-download the rainfall CSV, verify the SHA-256, write the data-quality section | `research/india_dataset_audit.md` §1 signed off |
| 2 | Descriptive statistics + the division/month/year structure; heatmaps | figures 01–02 |
| 3 | Distribution fitting (Gamma/Weibull/Lognormal/Normal, KS + AIC) on 6 divisions | figure 03 + a fit/selection table |
| 4 | CV ranking + Levene/F-test checks | figure 04 |
| 5 | Trend tests (OLS/Sen/Mann-Kendall) + BH correction | figure 05 + the 16 → 9 result |
| 6 | Return-period curves + drought probabilities | figure 06 |
| 7 | **Review 1:** problem statement, motivation, verified dataset, objectives/RQs, methodology table, initial audit, 6–7 real graphs, bare Streamlit shell | slides + `research/feasibility_report`-style writeup |

Review 1 needs **no** modelling, no dashboard polish and no literature review beyond IMD/
drought-risk background. Everything listed is already produced or one day away.

### Review 2 (70 % of marks) — Days 8–17

- Formal hypothesis tests **with the correct variants**: Welch ANOVA + Games-Howell
  (Levene rejects), Welch t-test for the 1901–57 vs 1958–2015 comparison, **F-test for the
  variance change**, χ² goodness-of-fit on the binned fitted distribution.
- Distribution analysis completed: per-division model selection, zero-inflated
  Bernoulli × Gamma for monthly data, KS/AIC tables.
- Correlation: Pearson **and** Spearman on the division correlation matrix, with the
  dependence caveat and an effective-sample-size note.
- Two-way ANOVA (division × month) + residual diagnostics; log-transform comparison.
- Regression: per-division trend with BH-adjusted inference; sensitivity to the 2016–2017
  extension and to the three incomplete divisions.
- Bootstrap CIs alongside t-CIs, and a short honest note on where they agree.
- Interactive dashboard built (items 1–7 of §10.1).
- Interpretation write-up: findings, effect sizes, uncertainty, and **limitations stated
  as limitations**.

### Review 3 (final report, 10 %) — Days 18–21

- Final report: title, abstract, background, data & quality, methods, results with
  figures, discussion, limitations, conclusion.
- References (IMD, OGD, Kaggle originals, scipy/statsmodels documentation for the exact
  tests used).
- Reproducible scripts cleaned up: `scripts/india_audit.py`,
  `scripts/india_stats_checks.py`, `research/india_figures.py`, plus a `Makefile`-style
  three-line reproduction block.
- Final application + presentation; rehearsal with the caveat sentences spoken out loud.

### Must be done before Review 1 vs. can wait

**Before:** verified dataset + hash, data-quality audit, the RQ list, the method table,
6–7 real graphs, a bare dashboard shell that loads the CSV.
**Can wait:** every test statistic, the mixture model, the two-way ANOVA, regression
diagnostics, the interactive maps, the literature review.

---

## 12. Review 1 checklist (recommended project)

- [ ] Problem statement and motivation — monsoon dependence, drought exposure, why
      variability (not just totals) is the statistical question.
- [ ] **Verified, downloadable dataset** — hash-verified CSV, source URL, licence
      (CC BY-SA 4.0), attribution to IMD/OGD, size, shape; note that the OGD API needs a
      key and a mirror was used.
- [ ] Data-quality audit — missingness per column, the three incomplete divisions, the
      `ANNUAL` ≠ sum-of-months caveat, zero-inflation counts.
- [ ] Objectives and 7 research questions (RQ1–RQ7).
- [ ] Literature/background — IMD subdivision climatology, the standard "rainfall
      variability and drought" framing, previous multiple-comparison pitfalls in trend
      studies.
- [ ] Methodology table — question → test → assumption → what happens if the assumption
      fails (Welch/Games-Howell/block bootstrap).
- [ ] Four to six real exploratory graphs — seven already generated in
      `research/figures_india/`.
- [ ] Basic dashboard prototype — Streamlit shell loading the CSV with the CV ranking and
      the seasonal heatmap.
- [ ] Explicit statement of what is *not* claimed (no causality, no district-level
      rainfall-yield link, no daily extremes).

---

## 13. Risks, assumptions and unresolved questions

### 13.1 Risks (with mitigations)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Applying equal-variance ANOVA to rainfall | high if unmanaged | wrong conclusions | Levene up front; report Welch + Games-Howell |
| Reporting 16 uncorrected trends as findings | high | weakens the whole report | BH correction in the default pipeline (already implemented) |
| Mistaking station-network changes for climate change | medium | a wrong headline | the Arunachal check already in `india_stats_checks.py`; phrase trends as "in this record" |
| Treating divisions as independent | medium | over-stated significance | spatial-correlation section + effective sample size note |
| Sourcing an India meteorological-subdivision boundary file | medium | dashboard map blocked | the analysis and 7 figures do **not** need a map; state-level fallback or none |
| Over-scoping into agriculture/electricity joins | medium | deadline slip | those are explicitly optional; the district join is known-impossible |
| 2015 partial year in the crop file / partial 2015 rows in rainfall | low | small bias | exclude or flag; already documented |
| Reproducibility drift (different mirror later) | low | audit mismatch | SHA-256 recorded; hash check in the fetch script |

### 13.2 Assumptions

- The mirror files are faithful copies of the published Kaggle/OGD artefacts. Evidence:
  byte-identical sizes for the AQI and crop files, and the rainfall column structure
  matching the Kaggle schema exactly. This is strong but not cryptographic provenance.
- 1901–2015 subdivision series are comparable across the whole window. They are *not*
  fully comparable (network changes), which is why the trend section carries the caveat.
- The team is comfortable with SciPy/statsmodels or willing to learn the specific calls
  used in `scripts/india_stats_checks.py`.

### 13.3 Unresolved questions for the user

1. **Exact Review 1 date** — the whole schedule keys off this.
2. **Format of Review 1** — slides only, live demo, or a written submission?
3. **Weekly time budget per team member** — determines whether the dashboard is core or stretch.
4. **Is a working Streamlit app required at Review 1, or is a prototype enough?**
5. **Team size and division of labour** — the monsoon project splits cleanly into
   data/EDA, inference, distributions/extremes, and app.
6. **Retire the SONIQ name?** (Recommended: yes, adopt VARSA.)
7. **Where should the project ultimately live** — keep the mixed repo, or split
   `soniq/` into `spotify/` and `varsa/` before Review 2? (Do it *before* Review 2 if at
   all; moving files mid-analysis is the classic own-goal.)

---

## 14. Source references

**Rainfall**
- IMD / OGD catalog: <https://www.data.gov.in/resource/area-weighted-monthly-seasonal-and-annual-rainfall-mm-36-meteorological-subdivisions-1901>
- Kaggle original: <https://www.kaggle.com/datasets/rajanand/rainfall-in-india> (CC BY-SA 4.0)
- Downloaded mirrors: <https://raw.githubusercontent.com/MainakRepositor/Datasets/master/rainfall%20in%20india%201901-2015.csv> (1901–2015) and <https://raw.githubusercontent.com/raghav0807/Rainfall-Data-Analysis-Visualization-/main/Dataset.csv> (1901–2017)
- IMD gridded 0.25° daily rainfall, 1901–2024 (**listed, download `UNVERIFIED`**): <https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html>

**Air quality**
- CPCB: <https://cpcb.nic.in/>
- Kaggle original: <https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india> (CC0)
- Downloaded mirror: <https://raw.githubusercontent.com/adityarc19/aqi-india/main/city_day.csv>
- Station-level variant (not downloaded, ODbL-1.0): <https://github.com/Vonter/india-cpcb-aqi>
- OpenCity CKAN (Delhi hourly, Public Domain): <https://data.opencity.in/dataset/delhi-hourly-air-quality-reports>

**Agriculture**
- Kaggle originals: <https://www.kaggle.com/datasets/aravindpcoder/india-crop-production-state-wise> (CC0) and <https://www.kaggle.com/datasets/abhinand05/crop-production-in-india>
- Downloaded mirror: <https://raw.githubusercontent.com/Vishnukurra101/crop-production-india/main/crop_production.csv>
- ICRISAT district-level variant (not downloaded, CC BY 4.0): <https://www.kaggle.com/datasets/ankanhore545/district-wise-major-crops-production-in-india>

**Electricity**
- Zenodo, DOI 10.5281/zenodo.14983362 — Hunt & Bloomfield, "Daily electricity demand data for Indian states (2014–2024)" (CC BY 4.0): <https://zenodo.org/records/14983362>

**CPI**
- India Data Portal (CKAN) package `consumer-price-index-cpi` (ODC-By), MoSPI CPI base 2012 = 100: <https://ckandev.indiadataportal.com/api/3/action/package_show?id=consumer-price-index-cpi>
- MoSPI CPI portal: <https://cpi.mospi.gov.in/> (API `api.mospi.gov.in` blocked by legacy-TLS from this machine)

**Spotify (existing project, preserved)**
- Kaggle Spotify Tracks 114k — file already in `data/raw/kaggle_spotify_tracks_114k.csv`
- TidyTuesday Spotify Songs (CC0-1.0) — file already in `data/raw/tidytuesday_spotify_songs.csv`
- Internal measured findings reused above are from `research/feasibility_report.md`,
  `research/dataset_audit.md`, `scripts/feasibility_checks.py`, `scripts/audit_datasets.py`.

**Software used for every number in this report:** Python 3.12.12 with pandas 3.0.6,
numpy 2.5.4, scipy 1.18.1, statsmodels 0.15.0, scikit-learn 1.9.1, matplotlib, plotly.

---

## 15. Final decision — direct answers

**1. Is Indian monsoon/rainfall more feasible than Spotify for this assignment?**
*Feasible?* Comparable — and slightly *less* work than completing Spotify, because the
data is smaller, needs no cleaning and needs no joins. *Better?* Yes, decisively, on the
axis that matters: the monsoon has real effects to find (η² = 0.8747 across regions, CV
12.0 % → 40.8 %, 47.6 % → 77.8 % drought severity, 9/36 trends surviving correction),
where Spotify's largest univariate correlation with popularity is 0.095 and its model R²
without genre dummies is 0.022. So: yes, more feasible to produce *defensible, meaningful*
statistics, from a smaller and cleaner file.

**2. Which candidate gives the strongest combination of depth, meaningful questions,
visual appeal and three-week feasibility?**
**Indian monsoon rainfall** (mean score 4.56/5 vs Air quality 3.78, Electricity 3.67,
Spotify 3.33, Agriculture 3.33, CPI 3.22). Air quality is the best runner-up; electricity
is the highest-ceiling, highest-risk option; Spotify remains the safest fallback.

**3. Which exact dataset should we use?**
The **36-meteorological-subdivision monthly rainfall series, 1901–2015** — Kaggle
`rajanand/rainfall-in-india` (CC BY-SA 4.0), IMD/OGD lineage, 4,116 × 19, 437,910 bytes,
SHA-256 `fdc0b7fd8fccea2aab3910014ca7cacdd2f9faee511adda22b43cf30b680b4ec`. One file
supports the entire core project; the 1901–2017 mirror is a sensitivity check only.

**4. What is the most compelling research question?**
*How variable is Indian monsoon rainfall across regions and time, are the observed
regional differences and long-run trends statistically significant, and what is the
probability of an extreme rainfall deficit in each region?* Its strongest single result is
the multiplicity trap: **16 of 36 subdivision trends look significant, and only 9 survive
Benjamini–Hochberg correction** — a finding that is simultaneously quantitative,
methodologically serious and easy to present.

**5. What can we realistically demonstrate at Review 1?**
Everything the brief asks for, and more than any other candidate. Data and audit are done;
**seven real figures already exist** (`research/figures_india/01…07`); the RQ and method
tables exist; and the headline results — CV ranking, η² = 0.8747, the 16 → 9 correction,
the drought return-period curves — are already computed. A bare Streamlit shell that loads
the CSV and renders the CV ranking plus the seasonal heatmap is roughly a day of work.

**6. What are the main risks?**
(a) Heteroscedasticity — Levene rejects in rainfall (p ≈ 0) and in PM2.5 (p ≈ 0), so the
default equal-variance ANOVA is wrong and must be replaced by Welch/Games-Howell;
(b) multiplicity — 36 tests will produce ~2 false positives by chance alone, fixed by BH;
(c) spatial dependence — 78.6 % of division pairs correlate positively, so effective
sample size is below 36; (d) reading a changing station network as climate change (the
Arunachal record is the concrete case); (e) over-scoping into agriculture/electricity
joins that the geographies and date ranges do not actually support; (f) sourcing an India
meteorological-subdivision boundary file for the map (unverified — the analysis does not
depend on it). All six are visible, bounded and already documented in code.

**7. Smallest credible version, and how to extend it into a polished application.**
*Smallest credible version (fits Review 1–2 with slack):* one CSV; CV ranking of the 36
subdivisions; Welch ANOVA + η² for the regional difference; Gamma/Weibull/Lognormal model
selection on six representative divisions; Sen's slope per division with BH correction;
Gamma-based 1-in-20 / 1-in-50-year deficit per division; and five figures. No joins, no
maps, no external data, no time-series modelling.
*Extending it into a polished application:* add a year × division heatmap, a live
threshold-exceedance calculator ("give me a division and a rainfall value"), a trend panel
with a before/after-BH toggle, a distribution-explorer with live KS/AIC readouts, and an
interpretation strip that prints one plain-English sentence plus one honest caveat per
result. Then, if time remains, add the *optional* extensions in priority order:
state-level rainfall vs electricity demand (2013–2015 overlap only — verify before
promising), state-level rainfall vs crop yield via a hand-built subdivision → state
crosswalk, and only last an India choropleth once a verified boundary file exists.
