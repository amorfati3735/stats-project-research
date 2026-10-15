# India Dataset Audit — VARSA (monsoon) direction

Verified schema, coverage and data-quality findings for every dataset
downloaded for the VARSA monsoon project.

**Read this as measured evidence, not as a promise.** Everything below was produced
by running code against files on this machine. Anything that could not be verified is
marked `UNVERIFIED` or `DOCUMENTED ONLY`.

- Machine date: 2026-10-15
- Project root: `/mnt/windows/Users/DELL/Downloads/materialgram/soniq/`
- Data directory: `data/raw/` (git-ignored)
- Audit scripts: `scripts/audit_datasets.py` (schemas) and `scripts/feasibility_checks.py` (statistics)
- Raw output: `research/logs/audit_raw.txt`, `research/logs/stats_raw.txt`
- Figures: `research/figures/`
- Python: `.venv` (Python 3.12.12; pandas 3.0.6, numpy 2.5.4, scipy 1.18.1,
  statsmodels 0.15.0, scikit-learn 1.9.1, matplotlib)

## 0. Files in `data/raw/`

| File | Bytes | Rows | Cols | What it is |
|---|---|---|---|---|
| `rainfall_alt.csv` | 437,910 | 4,116 | 19 | **Primary rainfall candidate** (Kaggle `rajanand` format, Kaggle/OGD lineage): 36 subdivisions × 1901–2015 |
| `rainfall_1901_2015.csv` | 441,180 | 4,188 | 19 | Second rainfall mirror, extended to **2017**; minor name differences (`SUBDIVISION`) |
| `aqi_city_day.csv` | 2,574,056 | 29,531 | 16 | CPCB daily city air quality, 26 cities, 2015-01-01 → 2020-07-01 |
| `crop_production.csv` | 15,316,741 | 246,091 | 7 | State/district/season/crop Area & Production, 1997–2015 |
| `corrected_daily_energy_met_MU.csv` | 807,563 | 3,955 | 40 | Daily state electricity supplied (MU), 2013-01-01 → 2024-04-28 |
| `corrected_peak_met_MW.csv` | 1,039,164 | 3,955 | 40 | Daily state peak met demand (MW), same dates |
| `cpi_india.csv` | 20,232,662 | 300,518 | 8 | CPI by state × commodity group × sector, monthly 2014-01 → 2025-12 |
| `derived_trend_tests.csv` | small | 36 | 9 | Output of `scripts/feasibility_checks.py` §1 |

Total ≈ 41 MB. All files are plain CSV (no archives, no credentials). The AQI and crop
files exactly match the byte sizes published on their Kaggle pages (2.57 MB and
15.32 MB), which is evidence the mirrors are the original files and not edits.

---

## 1. Rainfall — 36 meteorological subdivisions, monthly, 1901–2015

### 1.1 Provenance

| | |
|---|---|
| Original | **"Rainfall in India"** by Rajanand Ilangovan on Kaggle — <https://www.kaggle.com/datasets/rajanand/rainfall-in-india> |
| Verified licence | **CC BY-SA 4.0** (stated on the Kaggle page) |
| Upstream | India Meteorological Department (IMD), Government of India; Kaggle page states IMD shared it under the *Government Open Data License – India* |
| Official platform | Open Government Data platform catalog "Area weighted monthly, seasonal and annual rainfall (in mm) for 36 meteorological subdivisions from 1901-2015" — <https://www.data.gov.in/resource/area-weighted-monthly-seasonal-and-annual-rainfall-mm-36-meteorological-subdivisions-1901> |
| File downloaded (`rainfall_alt.csv`) | <https://raw.githubusercontent.com/MainakRepositor/Datasets/master/rainfall%20in%20india%201901-2015.csv> |
| File downloaded (`rainfall_1901_2015.csv`) | <https://raw.githubusercontent.com/raghav0807/Rainfall-Data-Analysis-Visualization-/main/Dataset.csv> |
| Authentication | none (raw GitHub) |
| Format / size | CSV, 428 KB / 437,910 B |

**Why the OGD platform itself was not used for the download:** the platform's API returns
HTTP 400 without a free registered API key, and the resource pages build their download
link with JavaScript. `api.data.gov.in/resource/...` without a key → `400`. The mirror
files are byte-consistent with the published Kaggle artefacts and are used here as the
verified copy.

### 1.2 Schema (measured)

`DIVISION` (string), `YEAR` (int), `JAN … DEC` (float ×12), `ANNUAL` (float),
`Jan-Feb`, `Mar-May`, `Jun-Sep`, `Oct-Dec` (float). Units mm.

- 4,116 rows, 36 divisions, 115 years (1901–2015). 36 × 115 = 4,140; the 24 missing
  division-years are the genuine gaps listed below.
- Exact duplicate rows: **0**. Duplicate `(DIVISION, YEAR)`: **0**.
- Missing values: JAN 4, FEB 3, MAR 6, APR 4, MAY 3, JUN 5, JUL 7, AUG 4, SEP 6, OCT 7,
  NOV 11, DEC 10, ANNUAL 26, Jan-Feb 6, Mar-May 9, Jun-Sep 10, Oct-Dec 13.
- Incomplete histories: `ARUNACHAL PRADESH` 97 years (starts 1916),
  `ANDAMAN & NICOBAR ISLANDS` 110, `LAKSHADWEEP` 114. The other 33 divisions have all 115.
- Missingness is concentrated in early years and in the three short/remote divisions —
  plausible record gaps, not a parse failure.
- `ANNUAL` is not always exactly the sum of the 12 months for rows with a missing month;
  use seasonal columns or recompute, and document which you chose.

### 1.3 Distribution of values

| vector | n | mean | sd | min | median | max | skew |
|---|---|---|---|---|---|---|---|
| ANNUAL | 4,090 | 1411.0 | 903.8 | 62.3 | 1121.3 | 6331.1 | 1.32 (pooled) |
| Jun-Sep (monsoon) | 4,106 | 1064.7 | 707.7 | 57.4 | 881.1 | 4536.9 | **1.506** |
| Mar-May (pre-monsoon) | 4,107 | 155.9 | 201.3 | 0.0 | 74.8 | 1745.8 | — |
| Oct-Dec (post-monsoon) | 4,103 | 154.1 | 166.9 | 0.0 | 98.2 | 1252.5 | — |
| Jan-Feb (winter) | 4,110 | 40.7 | 59.3 | 0.0 | 19.2 | 699.5 | — |

- **Seasonality is extreme**: Jun-Sep carries **75.2 %** of all rainfall. Monthly means
  (mm) — JAN 19.0, FEB 21.8, MAR 27.4, APR 43.1, MAY 85.7, JUN 230.2, JUL 347.2,
  AUG 290.3, SEP 197.4, OCT 95.5, NOV 39.9, DEC 18.9. One-way ANOVA of monthly rainfall
  by month: **F = 3051.7, p ≈ 0, η² = 0.405** (n = 49,322). A two-way ANOVA
  (division × month) is the natural next step.
- **Drought years are common**: taking the all-India mean of the 36 subdivision Jun-Sep
  totals (normal 1064.7 mm, sd 97.2, n = 115), **23 years fall below 90 % of normal
  (20.0 %)**; the driest are **1972 (−22.8 %), 2002 (−21.3 %), 1905 (−17.4 %),
  2009 (−17.0 %), 1979 (−16.3 %), 1918 (−15.9 %)**. A single computed drought index
  therefore reproduces the historically documented drought seasons from the data itself.
  **No year falls below 75 % of normal at all-India level** — severe deficits are a
  *regional* phenomenon, which is exactly why the per-division return periods in §1.4
  matter and why the national average is the wrong statistic to lead with.
- **Zero-inflation is real and month-specific** (share of division-years with exactly
  0 mm): JAN 14.8 %, FEB 15.7 %, MAR 11.0 %, APR 5.3 %, MAY 2.0 %, **JUN–SEP 0.0 %**,
  OCT 2.1 %, NOV 15.8 %, **DEC 21.5 %**.

### 1.4 Statistical feasibility (measured — `scripts/feasibility_checks.py`)

**Regional differences — one-way ANOVA, Jun-Sep ~ division (36 groups):**
`F = 811.5`, `p ≈ 0`, **η² = 0.8747**; Levene `W = 53.4`, `p ≈ 0`
(equal-variance assumption violated → report Welch ANOVA / Games-Howell as the robust
version, which is itself the correct methodological answer).

**Regional variability ranking — CV of annual rainfall:**

| most variable | mean mm | CV % | | least variable | mean mm | CV % |
|---|---|---|---|---|---|---|
| SAURASHTRA & KUTCH | 495.2 | **40.8** | | ASSAM & MEGHALAYA | 2580.7 | 12.0 |
| WEST RAJASTHAN | 292.7 | 37.2 | | SUB HIMALAYAN WB & SIKKIM | 2752.2 | 12.3 |
| ARUNACHAL PRADESH | 3418.9 | 31.6 | | ORISSA | 1458.2 | 12.8 |
| GUJARAT REGION | 918.2 | 30.3 | | ANDAMAN & NICOBAR | 2927.4 | 14.0 |
| PUNJAB | 593.5 | 27.5 | | COASTAL KARNATAKA | 3408.4 | 14.2 |

**Temporal trends (per division, Jun-Sep, 40+ years):**
- OLS slope: 19/36 negative; **16/36 significant at p < 0.05 uncorrected**.
- Mann-Kendall (Kendall τ): 15/36 significant; sign agrees with OLS in **36/36**.
- Sen's slope: sign agrees with OLS in **36/36**.
- **Benjamini–Hochberg FDR 5 %: only 9/36 survive.** Divisions that are "significant"
  uncorrected but *not* after correction: BIHAR (0.0175 → 0.0526), EAST MADHYA PRADESH
  (0.0159 → 0.0519), KONKAN & GOA (0.0140 → 0.0504), CHHATTISGARH (0.0311 → 0.0800),
  KERALA (0.0437 → 0.1008), SAURASHTRA & KUTCH (0.0448 → 0.1008), UTTARAKHAND
  (0.0248 → 0.0686). This is the single most quotable methodological result in the
  dataset: a naive analysis would have reported 16 "significant" monsoon trends.
- Largest Sen slopes: ARUNACHAL PRADESH −17.4 mm/yr, NAGA MANI MIZO TRIPURA −3.2,
  KERALA −2.2; positive: COASTAL KARNATAKA +2.9, KONKAN & GOA +2.9.
- **Caveat, measured:** the Arunachal record starts in 1916 and its Jun-Sep mean falls
  monotonically by 20-year block (1900s 3260.7; 1920s 3094.3; 1940s 2647.5; 1960s 1878.6;
  1980s 1942.2; 2000s 1583.9). A step-like decline of this shape in a *short, changing
  station network* is not safely readable as climate change. Flag it, do not headline it.

**Period comparison (1901–1957 vs 1958–2015, Jun-Sep per division):**
mean shifted in 13/36 divisions (Welch t, uncorrected p < 0.05); variance changed in only
2/36 (F-test). Mean of the 36 division means: pre 1094.3 mm → post 1055.5 mm. Consistent
with "no large systematic shift in mean, some changes in the tails".

**Power:** with n ≈ 115 years and the observed within-division sd, the smallest slope
detectable at 80 % power / 5 % two-sided is a median of **1.42 mm/yr ≈ 0.16 % of the
division mean per year (≈ 18 % over the century)**. The century is long enough to detect
trends that matter — this is a defensible answer to "do we have enough data?".

**Distribution fitting (Jun-Sep, pooled across divisions):**

| model | KS D | p |
|---|---|---|
| Normal | 0.1352 | 6.1e-66 |
| Gamma | 0.0505 | 1.5e-9 |
| Weibull (min) | 0.0708 | 2.4e-18 |
| Lognormal | **0.0255** | 0.0092 |

Fitting per division on the **annual** totals, the winner varies by region — and that is
the interesting finding, not a problem:

| division | best by AIC | best KS D | Normal KS D |
|---|---|---|---|
| WEST RAJASTHAN | gamma | 0.067 | 0.091 |
| SAURASHTRA & KUTCH | weibull | 0.048 | 0.079 |
| KERALA | lognormal | 0.0436 | 0.0436 |
| TAMIL NADU | weibull | 0.089 | 0.089 |
| ASSAM & MEGHALAYA | **normal** | 0.0444 | 0.0444 |
| COASTAL ANDHRA PRADESH | lognormal | 0.056 | 0.072 |

`WEST RAJASTHAN` full table (mean 292.7, sd 108.8, skew 0.94): normal KS 0.091 (AIC 1408.0),
gamma KS 0.067 (AIC 1400.0), weibull KS 0.081 (AIC 1407.8), lognormal KS 0.091 (AIC 1405.4).
**Note:** above the seasonal/annual level the skewed families win for the dry divisions;
for the wettest divisions the annual total is already close to Normal. Shapiro-Wilk on
annual totals rejects normality in only **12/36** divisions; the per-division median skew
is +0.31 (the pooled skew is 1.32 because the divisions have very different means).

**Zero-inflation model:** December, the driest month, has `P(0 mm) = 0.215` (n = 4,106);
the positive part (n = 3,222) has mean 24.0, skew **4.73**, and a Gamma fit with
shape ≈ 0.05. July has `P(0) = 0.000`. So a Bernoulli × Gamma mixture is the honest model
for monthly rainfall, and the mixture weights themselves vary by month, division and
season — a genuinely rich probability-modelling exercise rather than a textbook exercise.

**Spatial dependence:** pairwise Pearson r of annual Jun-Sep across the 630 division
pairs: mean 0.196, median 0.196, **78.6 % of pairs positive**, max 0.812 (neighbours),
min −0.363. So there is a shared all-India monsoon component, but the average pair only
correlates at r ≈ 0.2. Divisions are neither independent nor interchangeable — both
multiplicity (36 tests) and dependence must be handled explicitly.

**Bootstrap vs textbook interval** (annual mean, 4,000 resamples):

| division | skew | t-CI 95 % | bootstrap-CI 95 % | width diff |
|---|---|---|---|---|
| WEST RAJASTHAN | +0.94 | (272.6, 312.8) | (273.0, 313.4) | +0.7 % |
| KERALA | +0.49 | (2847.5, 3003.5) | (2850.9, 3003.7) | −2.0 % |
| TAMIL NADU | −0.73 | (913.0, 974.4) | (912.5, 973.3) | −0.8 % |

The CLT already holds at n ≈ 110 in every division, so the t-interval is fine and the
bootstrap agrees. That is a *result* to report (with the caveat that the bootstrap earns
its keep on small subsamples and on the skewed monthly series, not on 115-year means).

**Drought probability / return periods** (Gamma fitted to annual totals with location 0):

| division | mean | observed min | 1-in-20-yr | 1-in-50-yr | q05 % of mean | q02 % of mean |
|---|---|---|---|---|---|---|
| WEST RAJASTHAN | 292.7 | 62.3 | 139.4 | 114.4 | 47.6 % | 39.1 % |
| SAURASHTRA & KUTCH | 495.2 | 92.7 | 207.3 | 163.8 | 41.9 % | 33.1 % |
| GUJARAT REGION | 918.2 | 392.6 | 505.1 | 431.6 | 55.0 % | 47.0 % |
| TAMIL NADU | 943.7 | 318.0 | 664.5 | 607.3 | 70.4 % | 64.3 % |
| PUNJAB | 593.5 | 274.7 | 359.7 | 315.7 | 60.6 % | 53.2 % |
| KERALA | 2925.5 | 2068.8 | 2275.6 | 2134.8 | 77.8 % | 73.0 % |

**Tested and rejected hypothesis (negative result, reported rather than dropped):**
skewness of annual rainfall is *not* explained by how wet a division is —
Pearson r = −0.026 (p = 0.881), Spearman ρ = −0.222 (p = 0.194).

### 1.5 Second mirror (`rainfall_1901_2015.csv`)

Same 36 subdivisions and the same 19 columns (column named `SUBDIVISION`), but
**1901–2017 (117 years), 4,188 rows**, with 26 rows containing at least one NaN.
Using it extends the series by two years at the cost of an unverified 2016–2017 tail.
Recommendation: **use `rainfall_alt.csv` (1901–2015) as the canonical series** for
anything statistical, and treat 2016–2017 only as a sensitivity check.

### 1.6 Granularity limits — be careful in the report

- **It is subdivision-level (36), not district-level and not gridded.** Do not write
  "district-wise rainfall analysis" with this file.
- **Monthly is the finest time step.** No daily data; no way to study extreme daily
  events (cloudbursts) from this file.
- It cannot be joined directly to district-level crop data (§3) without a
  district → subdivision crosswalk that is not shipped with either dataset.
- The IMD 0.25° daily gridded product (1901–2024, 135 × 129 grid points) is officially
  listed at <https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html> and would
  remove both limits. **`UNVERIFIED` for our purposes**: the page builds its download link
  with JavaScript, no direct file URL appears in the served HTML, and probing guessed
  paths returned no response. Budget this as a stretch goal only, and only with a
  working download confirmed before it is promised to anyone.

---

## 2. Air quality — CPCB daily city data

| | |
|---|---|
| Original | **"Air Quality Data in India (2015 - 2020)"** — <https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india> |
| Licence (verified on the page) | **CC0: Public Domain** |
| Upstream | Central Pollution Control Board (CPCB) — <https://cpcb.nic.in/> |
| Downloaded | <https://raw.githubusercontent.com/adityarc19/aqi-india/main/city_day.csv> |
| Format | CSV, 2,574,056 B — identical to the 2.57 MB `city_day.csv` on the Kaggle page |
| Auth | none |

**Measured schema:** 29,531 rows × 16 columns — `City`, `Date`, `PM2.5`, `PM10`, `NO`,
`NO2`, `NOx`, `NH3`, `CO`, `SO2`, `O3`, `Benzene`, `Toluene`, `Xylene`, `AQI`,
`AQI_Bucket`. 26 cities, 2015-01-01 → 2020-07-01. Rows per city: min 113, median 1113,
max 2009 — **very unbalanced panel**.

**Missingness is the headline problem:**

| column | missing % | | column | missing % |
|---|---|---|---|---|
| Xylene | **61.3** | | Benzene | 19.0 |
| PM10 | **37.7** | | PM2.5 | 15.6 |
| NH3 | 35.0 | | NOx | 14.2 |
| Toluene | 27.2 | | O3 | 13.6 |
| AQI / AQI_Bucket | 15.9 | | SO2 / NO2 / CO | 13.1 / 12.1 / 7.0 |

`AQI_Bucket` counts: Moderate 8,829; Satisfactory 8,224; missing 4,681; Poor 2,781;
Very Poor 2,337; Good 1,341; Severe 1,338.

**Feasibility results:** PM2.5 mean 67.45, median 48.57, max 949.99 (heavily skewed).
One-way ANOVA PM2.5 ~ city (10 largest): F = 558.5, p ≈ 0, Levene W = 349.1, p ≈ 0
→ same heteroscedasticity caveat as rainfall. Pearson r of PM2.5 with PM10 0.846,
NOx 0.437, NO2 0.351, NH3 0.275, O3 0.161, SO2 0.132, Toluene 0.117, Xylene 0.115,
CO 0.090, Benzene 0.024. So there is one strong association (PM2.5–PM10) and the rest
are weak — a workable correlation/regression story, but thinner than rainfall's.

**Verdict:** usable, but the panel is short (5.5 years), heavily unbalanced, and 1/3–2/3
missing for several pollutants. It supports missing-data methods and threshold
probabilities, not long-run trend analysis.

---

## 3. Crop production (state / district / season)

| | |
|---|---|
| Original | **"India Crop Production - State wise"** — <https://www.kaggle.com/datasets/aravindpcoder/india-crop-production-state-wise> (identical file also listed as `abhinand05/crop-production-in-india`) |
| Licence (verified) | **CC0: Public Domain** |
| Upstream | Ministry of Agriculture and Farmers Welfare, Government of India |
| Downloaded | <https://raw.githubusercontent.com/Vishnukurra101/crop-production-india/main/crop_production.csv> |
| Format | CSV, 15,316,741 B — matches the Kaggle page's 15.32 MB / 246,091 rows / 7 columns exactly |
| Auth | none |

**Measured schema:** 246,091 rows × 7 columns — `State_Name`, `District_Name`, `Crop_Year`,
`Season`, `Crop`, `Area`, `Production`. 33 states, **646 districts**, 124 crops,
1997–2015, 6 seasons (Kharif, Rabi, Whole Year, Autumn, Summer, Winter).
Note: names carry stray whitespace (`'Kharif     '`) — strip on load.

**Data-quality findings:**
- `Production` missing in 3,730 rows; `Production == 0` in 3,523 rows (1.4 %);
  `Area == 0` in 0 rows (so yield = Production/Area is computable, but guard the zeros).
- Duplicate `(State, District, Crop, Year, Season)`: 0.
- **2015 is a partial year** (562 rows vs 10,973 in 2014). Either drop 2015 or state the
  caveat — a trend analysis that includes it will be wrong.
- No `Yield` column; derive `Production / Area` and screen unit errors
  (the related Kaggle notebooks report sugarcane yields > 168 t/ha as errors).
- Rice-yield ANOVA across seasons: n = 15,068, F = 382.0, p ≈ 0, skew 0.72
  → strong seasonal effect, but on a right-skewed response (use log or a non-parametric
  test, or state the violation).

**The join question the brief explicitly asks about:**
crop geography is **district name in free text** (646 values); rainfall geography is the
**36 meteorological subdivisions**. **A direct join is not possible** with the shipped
files (`direct join possible: False`). A state-level join *is* feasible with a hand-built
36-subdivision → state crosswalk (the state names themselves are usable), so a
state-level rainfall-vs-yield analysis is possible at the cost of ~1 day of careful
mapping work — but do not promise a district-level rainfall-yield regression.

---

## 4. Electricity demand — daily, per state

| | |
|---|---|
| Original | **"Daily electricity demand data for Indian states (2014–2024)"** — Zenodo record <https://zenodo.org/records/14983362>, DOI **10.5281/zenodo.14983362** |
| Licence (verified via the Zenodo API) | **CC BY 4.0** |
| Creators | Hunt, Kieran; Bloomfield, Hannah (published 2025-03-06) |
| Upstream | Scraped from India's national grid (CEA / Grid-India daily reports) |
| Downloaded | `corrected_daily_energy_met_MU.csv` (807,563 B) and `corrected_peak_met_MW.csv` (1,039,164 B); record also publishes `peak_unmet_MW.csv`, uncorrected versions, and 36 per-state files with meteorological covariates (~3.6 MB each) |
| Auth | none |

**Measured schema:** 3,955 rows × 40 columns — `Date` + one column per state/UT + grid
entities (`AMNSIL`, `Damodar Valley Corporation`) + `Total`. Daily supplied energy in MU.
**Measured dates: 2013-01-01 → 2024-04-28** (the record title says 2014–2024 — the file
itself starts in 2013; state the measured range, not the title).

**Quality:**
- **43 exact duplicate rows** (must be de-duplicated; they will silently inflate n).
- Whole-column gaps: `Andaman and Nicobar Islands` and `Lakshadweep` are 100 % missing;
  `Dadra and Nagar Haveli` / `Daman and Diu` 17.6 %; `Telangana` 10.7 % (state created in
  2014); `AMNSIL` 92 rows. Effectively 33 usable states.
- `Total` mean 3464.7 MU, sd 569.8, min 2218.7, max 5224.3.

**Feasibility results:**
- Monthly means of `Total` (MU): Jan 3364, Feb 3498, Mar 3535, Apr 3542, May 3517,
  Jun 3585, Jul 3535, **Aug 3586**, Sep 3574, Oct 3387, **Nov 3202**, Dec 3264.
  One-way ANOVA `Total` ~ month: F = 17.9, p = 2.5e-35, **η² = 0.048** — a real but
  *small* seasonal effect, and the peak is in the humid months, not the hottest ones.
- **lag-1 autocorrelation of daily `Total` = 0.9874.** This is the decisive methodological
  fact: ordinary t-tests, ANOVA and OLS on these daily values are invalid as-is. The
  project would have to teach/test autocorrelation-aware methods (differences, HAC
  standard errors, ARIMA / seasonal decomposition, block bootstrap).
- Distribution fits on daily `Total`: normal KS D 0.0568 (p 1.6e-11), gamma 0.0230
  (p 0.030), weibull 0.0286 (p 0.003).

**Verdict:** excellent dataset (long, official, CC BY, plus a deficit column and weather
covariates). Its statistical centre of gravity is *time-series*, which is only partly in
the listed syllabus — high ceiling, higher methodological risk.

---

## 5. Consumer price index (CPI)

| | |
|---|---|
| Original | **"Consumer Price Index"** dataset on the India Data Portal (CKAN) — package `consumer-price-index-cpi` |
| Licence | Open Data Commons Attribution License (per CKAN metadata) |
| Upstream | Ministry of Statistics and Programme Implementation (MoSPI), CPI base 2012 = 100 |
| Downloaded | <https://ckandev.indiadataportal.com/dataset/b8836317-263c-4e11-a94c-32e5b295cd30/resource/487c360b-fbc1-4664-8b49-e11c73d105e5/download/consumer_price_index.csv> |
| Format | CSV, 20,232,662 B |
| Auth | none |

**Measured schema:** 300,518 rows × 8 columns — `id`, `date`, `state_name`, `state_code`,
`commodity_group`, `cpi`, `inflation_rate`. 37 states/UTs + `All India`; 28 commodity
groups (General Index, Cereals And Products, Vegetables, Fuel And Light, Housing,
Health, Transport And Communication, …); 3 sectors (Combined / Rural / Urban);
**monthly, 2014-01 → 2025-12 (143 months)**.

**Quality:** `cpi` and `inflation_rate` missing in 3,154 rows; **83 duplicate
`(date, state_name, commodity_group, sector)` rows** — de-duplicate before analysis.
All-India Combined headline inflation: mean 5.01 %, sd 5.78, min −27.57 %, max +60.50 %
(food groups drive the extremes: All-India Combined `Vegetables` CPI ranges 114.5 → 292.0).

**Feasibility results:** All-India `Cereals And Products` monthly inflation (n = 143,
mean 4.69, sd 3.93, skew 0.86): Shapiro/KS vs Normal D = 0.1017 (p = 0.097, not rejected),
vs Student-t D = 0.0686 (p = 0.49); **lag-1 autocorrelation 0.9599**. One-way ANOVA of
inflation across states (Cereals, Combined, k = 22): F = 2.0, p = 0.0036 — a *weak*
cross-sectional effect with strongly autocorrelated residuals.

**Blocked route, reported honestly:** the official MoSPI API
(`https://api.mospi.gov.in/api/cpi/getCPIData`) is unreachable from this machine —
`curl: (35) TLS connect error: … unsafe legacy renegotiation disabled` and
`--ciphers 'DEFAULT@SECLEVEL=1'` did not help (the server requires legacy TLS
renegotiation, which OpenSSL 3 refuses). The CKAN copy above is the practical route.

---

## 6. Candidates checked but not downloaded

| Candidate | Status |
|---|---|
| IMD 0.25° daily gridded rainfall 1901–2024, NetCDF | **`DOCUMENTED ONLY`** — officially listed at <https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html> (135 × 129 grid, 124 years). The download link is generated by JavaScript; no direct file URL in the served HTML; guessed paths returned no response. Not verified, not promised. |
| `data.gov.in` resources (rainfall catalog, district-wise crop production) | **`API-GATED`** — `api.data.gov.in` returns **HTTP 400** without a free registered API key. The catalog pages are readable, the files are not directly scriptable. Mirrors used instead. |
| `Vonter/india-cpcb-aqi` (15-minutely + hourly CPCB, ODbL) | **`NOT DOWNLOADED`** — real and well-documented (Parquet + `.csv.gz` releases, ODbL-1.0) and would be the better AQI source for a *station-level* study; skipped here because the daily city file already answers the feasibility question. |
| OpenCity CKAN (Delhi hourly AQI, Public Domain) | **`AVAILABLE`** — e.g. <https://data.opencity.in/dataset/delhi-hourly-air-quality-reports>; a valid single-city deep-dive source. |
| ICRISAT district-level crop data, 1978–2017, 80 columns (CC BY 4.0) | **`DOCUMENTED ONLY`** — a better long-horizon agriculture source than §3 (<https://www.kaggle.com/datasets/ankanhore545/district-wise-major-crops-production-in-india>), but not downloaded. |
| Kaggle-gated India datasets (e.g. `yamaerenay`, `pyatakov`) | **`BLOCKED`** — no Kaggle credentials on this machine (`~/.kaggle/kaggle.json` absent). |

---

## 7. Reproducing all of this

```bash
cd /mnt/windows/Users/DELL/Downloads/materialgram/soniq

# 1. schemas, missingness, coverage, first-pass tests
.venv/bin/python scripts/audit_datasets.py            > research/logs/audit_raw.txt

# 2. statistics that decide feasibility (trends + BH, power, distribution
#    selection, zero-inflation, spatial dependence, bootstrap CIs, return periods,
#    all-India drought frequency)
.venv/bin/python scripts/feasibility_checks.py     > research/logs/stats_raw.txt

# 3. figures for Review 1
.venv/bin/python research/make_figures.py         # -> research/figures/
```

Exact download commands are in `scripts/fetch_data.sh` (India section). No dataset in
this audit requires credentials, and no paid API was used.

## 8. One-paragraph bottom line

The rainfall file is small (428 KB, 4,116 rows) but it is the richest *statistical*
object of the five: it is skewed, seasonally extreme, zero-inflated at monthly
resolution, spatially dependent, mildly non-normal in a region-dependent way, and long
enough (115 years) to detect a trend of ≈ 18 % per century while still producing a
textbook multiple-comparison trap (16 "significant" → 9 after BH). The other four
datasets are genuinely usable but each has a handicap that shows up in the numbers:
air quality is a short, unbalanced panel with 1/3–2/3 of several columns missing; crop
data cannot be joined to rainfall at district level without a crosswalk; electricity is a
0.99-autocorrelated time series that punishes naive inference; CPI adds only 12 years and
is also strongly autocorrelated. Details and the scored comparison are in
`research/project_definition.md`.
