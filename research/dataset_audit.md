# SONIQ — Dataset Audit (measured, not assumed)

This file records **what was actually downloaded and inspected** on this machine.
Every number below comes from running the scripts in `scripts/` against the real
CSVs in `data/raw/`. Anything that could not be verified is marked
`UNVERIFIED` or `DOCUMENTED ONLY`.

- Audit script: `scripts/audit_datasets.py` (structure, missingness, duplicates, summaries)
- Statistics script: `scripts/feasibility_checks.py` (distribution fits, tests, regression)
- Raw output: `research/_audit_raw.txt`, `research/_feasibility_raw.txt`
- Environment: Python 3.12.12 venv (`.venv`) with pandas 3.0.6, numpy 2.5.4,
  scipy 1.18.1, statsmodels 0.15.0, scikit-learn 1.9.1, plotly 7.1.0

---

## 1. Files on disk

| file | bytes | rows × cols | source | licence (as seen) |
|---|---|---|---|---|
| `data/raw/kaggle_spotify_tracks_114k.csv` | 20,118,244 | 114,000 × 21 (20 usable) | Kaggle "Spotify Tracks Dataset" (maharshipandya), pulled through the Hugging Face mirror | Kaggle page: *"Database: Open Database, Contents: © Original Authors"*; HF mirror metadata says `bsd` |
| `data/raw/tidytuesday_spotify_songs.csv` | 7,971,379 | 32,833 × 23 | TidyTuesday 2020-01-21 (`rfordatascience/tidytuesday`) | repo `LICENSE` = **CC0-1.0** |
| `data/raw/fma_metadata.zip` | 358,412,441 (download in progress at time of writing) | — | FMA (Defferrard et al., ISMIR 2017) | metadata **CC BY 4.0**, code MIT |

---

## 2. Kaggle Spotify Tracks Dataset (114,000 rows)

Source of record: <https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset>
Auth-free mirror used: <https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv>

### Schema
`track_id, artists, album_name, track_name, popularity, duration_ms, explicit,
danceability, energy, key, loudness, mode, speechiness, acousticness,
instrumentalness, liveness, valence, tempo, time_signature, track_genre`
(plus an unnamed row-index column, dropped).

dtypes: `popularity/key/mode/time_signature/duration_ms` int; `explicit` bool;
the eight `0–1` audio-features + `loudness` + `tempo` float; rest string.

### Quality findings (measured)
| check | result |
|---|---|
| missing values | 3 columns × 1 row (`artists`, `album_name`, `track_name`) — a single record |
| exact duplicate rows | **450** |
| duplicate `track_id` | **24,259** rows are repeats of an already-seen `track_id` (89,741 unique ids) |
| rows inside duplicate-id groups | **40,900 (35.9 %)** |
| `track_id`s appearing in >1 genre | **16,299** (max 9 genres for one id) |
| duplicate ids with **non-constant** popularity | **720** (same track, different popularity → inconsistent snapshot) |
| duplicate `(track_name, artists)` pairs | 32,656 |
| distinct genres (`track_genre`) | **114**, exactly **1,000 rows each** (fully balanced by construction) |
| distinct artists | 31,437 |
| tracks per artist | mean 3.63, max 279 |

The dataset description claims *"125 different genres"*; the file contains
**114**. The claim is wrong for this file — use 114.

### Target: `popularity`
n = 114,000, mean **33.24**, sd **22.31**, min 0, max 100, median 35, IQR 17–50.
Skew **0.046**, kurtosis **−0.928** (flat / almost rectangular).
**14.1 % of rows are exactly 0** (16,020 rows). 1 % and 5 % quantiles are both 0.

Fitted distributions (Kolmogorov–Smirnov against the fitted CDF):

| distribution | fitted parameters | KS D | KS p |
|---|---|---|---|
| Normal | μ=33.24, σ=22.31 | 0.0877 | ~0 |
| Gamma | shape≈1432, loc≈−811, scale≈0.589 | 0.0889 | ~0 |
| Weibull (min) | k≈2.07, loc≈−10.8, scale≈49.7 | 0.1097 | ~0 |
| Beta (x/100) | fit fails — the 0-valued rows violate `0 < x < 1` | — | — |

**Conclusion:** with n = 114,000 *no* simple continuous distribution fits; the
target is a bounded, near-uniform, zero-inflated discrete score. This is a
feature, not a bug, for a P&S project — but it must be stated honestly instead
of forcing "popularity ~ Normal".

### Feature–target association (all measured, n = 114,000)
| feature | Pearson r | p | Spearman ρ | p |
|---|---|---|---|---|
| instrumentalness | −0.0951 | 2e−227 | −0.0785 | 4e−155 |
| loudness | +0.0504 | 4e−65 | +0.0352 | 1e−32 |
| speechiness | −0.0449 | 5e−52 | −0.0679 | 2e−116 |
| valence | −0.0405 | 1e−42 | −0.0419 | 2e−45 |
| danceability | +0.0354 | 5e−33 | +0.0266 | 2e−19 |
| acousticness | −0.0255 | 8e−18 | +0.0084 | 0.0046 |
| mode | −0.0139 | 3e−06 | −0.0145 | 1e−06 |
| tempo | +0.0132 | 8e−06 | +0.0171 | 8e−09 |
| duration_ms | −0.0071 | 0.0165 | +0.0282 | 2e−21 |
| liveness | −0.0054 | 0.069 | −0.0082 | 0.0057 |
| key | −0.0039 | 0.193 | −0.0026 | 0.382 |
| energy | +0.0011 | 0.721 | −0.0235 | 2e−15 |

**No |r| exceeds 0.10.** Several are "highly significant" only because n is
enormous. Sign flips between Pearson and Spearman (e.g. `duration_ms`,
`acousticness`) confirm the relationships are non-linear/rank-driven at best.

### Group comparisons
- One-way ANOVA, `popularity ~ track_genre` (k = 114, n = 1,000 each):
  **F = 343.46, p ≈ 0, η² = 0.254**; Levene **W = 256.8, p ≈ 0** (variances
  clearly unequal: within-genre sd ranges 3.9 → 34.7, an 8.8× ratio).
  Highest genre means: pop-film 59.3, k-pop 56.9, chill 53.7, sad 52.4.
  Lowest: iranian 2.2, romance 3.2, latin 8.3, detroit-techno 11.2.
- Welch t-test, popularity by `explicit`: n=9,747 vs 104,253,
  mean 36.45 vs 32.94, **diff 3.52, 95 % CI [3.02, 4.02], t = 13.76,
  p = 1e−42, Cohen's d = 0.158** (small effect, statistically overwhelming).
- χ² independence, `explicit` × `track_genre`: χ² = 18,460.2, df = 113,
  p ≈ 0, **Cramér's V = 0.402**, min expected count 85.5.

### Regression (predictors standardised; see the conditioning note below)
| model | predictors | test R² | OLS R² | adj R² |
|---|---|---|---|---|
| audio features only | 13 | 0.0223 | 0.0246 | 0.0244 |
| audio + 113 genre dummies | 126 | 0.2587 | 0.2597 | 0.2588 |

Train/test gap ≤ 0.003 → no overfitting at this n.

**Interpretation:** audio characteristics explain ~2 % of popularity variance.
Genre dummies lift it to ~26 %, but genre here is the *sampling stratum* of the
scrape (1,000 tracks deliberately drawn per genre), so this is closer to an
artefact of how the data was collected than a musical finding.

### Duplicate sensitivity (measured)
| quantity | all rows | de-duplicated on `track_id` |
|---|---|---|
| rows | 114,000 | 89,741 (−21.3 %) |
| r(instrumentalness, popularity) | −0.0951 | −0.1275 |
| r(duration_ms, popularity) | −0.0071 | −0.0231 |
| r(energy, popularity) | +0.0011 | +0.0137 |

De-duplication does not change the story, but it does change the numbers →
the analysis must fix and document one rule.

### Temporal information
**None.** The 114k file has no release date, year, or chart-position column.

### Other data-quality oddities
- `duration_ms` min = 0 (impossible), max = 5,237,295 ms (~87 min).
- `loudness` max = +4.53 dB (unusually hot) and min = −49.53 dB.
- `tempo` min = 0 BPM (impossible → missing-coded as 0).

---

## 3. TidyTuesday Spotify Songs (32,833 rows)

Source of record: <https://github.com/rfordatascience/tidytuesday/blob/main/data/2020/2020-01-21/readme.md>
Download: <https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-01-21/spotify_songs.csv>
Collected from the Spotify Web API via the R package `spotifyr`.

### Schema
`track_id, track_name, track_artist, track_popularity, track_album_id,
track_album_name, track_album_release_date, playlist_name, playlist_id,
playlist_genre, playlist_subgenre, danceability, energy, key, loudness, mode,
speechiness, acousticness, instrumentalness, liveness, valence, tempo,
duration_ms`

### Quality findings (measured)
| check | result |
|---|---|
| missing | 3 columns × 5 rows (`track_name`, `track_artist`, `track_album_name`) |
| exact duplicate rows | 0 |
| duplicate `track_id` | 4,477 (28,356 unique) → **13.6 % redundant** |
| duplicate ids with non-constant popularity | **0** (internally consistent) |
| `playlist_genre` | **6** categories: edm 6,043 · rap 5,746 · pop 5,507 · r&b 5,431 · latin 5,155 · rock 4,951 |
| `playlist_subgenre` | 24 categories, 949–1,809 rows each |
| nesting check | every subgenre maps to exactly **one** genre → **subgenre is nested in genre** |
| distinct artists | 10,692 (mean 3.07 tracks/artist, max 161) |
| release years | 1957–2020 (3 rows in the 1950s; 23,214 rows in the 2010s) |

### Target: `track_popularity`
n = 32,833, mean **42.48**, sd **24.98**, min 0, max 100, median 45, IQR 24–62.
Skew **−0.233**, kurtosis **−0.933**; **8.2 %** are exactly 0.
Fits: Normal D = 0.0700, Gamma D = 0.0713, Weibull D = 0.0700 — all rejected
(p ≈ 0). Same story as the 114k set: bounded, flat, zero-inflated.

### Feature–target association (measured, n = 32,833)
| feature | Pearson r | Spearman ρ |
|---|---|---|
| instrumentalness | **−0.1499** | **−0.1932** |
| duration_ms | **−0.1437** | −0.1207 |
| energy | **−0.1091** | −0.1185 |
| acousticness | +0.0852 | +0.1288 |
| danceability | +0.0648 | +0.0653 |
| loudness | +0.0577 | +0.0654 |
| liveness | −0.0546 | −0.0299 |
| valence | +0.0332 | +0.0372 |
| tempo | −0.0054 (p=0.33) | −0.0223 |
| speechiness | +0.0068 (p=0.22) | +0.0067 |
| key | −0.0007 (p=0.91) | −0.0014 |
| mode | +0.0106 (p=0.054) | +0.0126 |

Associations are ~1.5× stronger than in the 114k set but still **|r| < 0.20**.

### Group comparisons
- One-way ANOVA, `track_popularity ~ playlist_genre` (k = 6):
  **F = 207.2, p = 2.7e−218, η² = 0.0306**; Levene W = 44.5, p ≈ 0
  (again heteroscedastic). Means: pop 47.7, latin 47.0, rap 43.2, rock 41.7,
  r&b 41.2, edm 34.8.
- χ², `playlist_genre` × `playlist_subgenre`: χ² = 164,165, df = 115,
  p ≈ 0, **Cramér's V = 1.000** — a perfect association, because the two
  variables are nested. This test is *meaningless here* (good teaching example
  of a violated assumption).

### Regression (predictors standardised)
| model | predictors | test R² | OLS R² |
|---|---|---|---|
| audio only | 12 | 0.0707 | 0.0722 |
| audio + genre dummies | 17 | 0.0877 | 0.0906 |

### Temporal information (present)
- corr(release year, popularity) r = **+0.061**, p = 3e−28 (tiny effect).
- Mean popularity by decade (n ≥ 30): 1960s 49.3 · 1970s 46.7 · 1980s 44.6 ·
  1990s 40.0 · 2000s 33.6 · 2010s 43.8 · 2020s 46.5 — a **U-shape**, which is
  a nice non-monotonic result for a regression/ANOVA discussion.
- Caveat: the sample is 71 % 2010s, so pre-2000 decades rest on few hundred
  rows each and reflect playlist curation, not the historical chart.

### Duplicate sensitivity (measured)
| quantity | all rows | dedup on `track_id` |
|---|---|---|
| rows | 32,833 | 28,356 (−13.6 %) |
| r(instrumentalness, popularity) | −0.1499 | −0.1244 |
| r(duration_ms, popularity) | −0.1437 | −0.1397 |
| r(energy, popularity) | −0.1091 | −0.1036 |

---

## 4. FMA metadata (Free Music Archive)

**DOCUMENTED ONLY — download incomplete at time of writing.**
The file (`fma_metadata.zip`, 358,412,441 bytes) is being fetched from
<https://os.unil.cloud.switch.ch/fma/fma_metadata.zip> and takes ~30–45 min on
this connection. Nothing below has been read from the archive yet.

Documented contents (FMA README + paper, Defferrard et al., ISMIR 2017):
- `tracks.csv` — 106,574 tracks × 518 columns (hierarchical MultiIndex
  `('track','album','artist','set')`); includes `('track','genre_top')`,
  `('track','listens')`, `('track','favorite')`, `('track','interest')`,
  `('track','duration')`, tags, album/artist metadata.
- `genres.csv` — 163 genres with parent ids (hierarchy).
- `echonest.csv` — 249 Echo Nest features for a **subset of 13,129 tracks**:
  `audio_features` (acousticness, danceability, energy, instrumentalness,
  liveness, speechiness, tempo, valence, …), `social_features`
  (`song_hotttnesss`, `artist_familiarity`, `artist_hotttnesss`), `ranks`,
  `temporal_features`.
- `features.csv` — librosa features (mfcc, chroma, spectral) for all tracks.
- 16,341 artists, 14,854 albums, 161–163 genres.
- Licence: metadata **CC BY 4.0**; dataset "meant for research purposes".

Why it is interesting *if* verified: `listens` is a **count** variable
(different from Spotify's bounded 0–100 score), which makes Poisson / negative
binomial / Gamma / Weibull fitting, and variance-stabilising transforms,
genuinely appropriate rather than forced.

---

## 5. Environment gotcha found while auditing (worth knowing)

On the **unscaled** design matrix, `sklearn.linear_model.LinearRegression`
silently returned **wrong** coefficients for the 114k regression — R² = 0.025
instead of the correct 0.2597 (condition number of the design ≈ 3e7, driven by
`duration_ms` ~ 2e5 vs O(1) features). `numpy.linalg.lstsq` and `statsmodels`
agreed with each other; sklearn only matched once predictors were standardised.

Consequence for the project:
- always **standardise/scale predictors** before fitting (and report
  standardised coefficients, which are also easier to interpret),
- cross-check any regression against two implementations,
- keep `duration` in minutes (or z-scores), never raw milliseconds.
