# SONIQ — Feasibility Report

**Project:** SONIQ — Statistical Analysis of Music Popularity and Audio Characteristics
**Course:** Probability & Statistics (CSE undergraduate), 3-week cycle, Reviews 1/2/3
**Phase:** Research & feasibility (no application built yet)
**Date of investigation:** 2026-10-15
**Where the evidence lives:** `data/raw/` (real downloads), `scripts/audit_datasets.py`,
`scripts/feasibility_checks.py`, `research/dataset_audit.md`, `research/_*_raw.txt`

> Everything quantitative in this report was **measured on downloaded files**.
> Statements taken from documentation only (licences, FMA contents) are labelled
> as such. Nothing here is fabricated.

---

## 1. Executive summary

1. **Datasets are not the bottleneck.** Two datasets were downloaded and fully
   audited in minutes, with no account, payment, or API key:
   - **Kaggle "Spotify Tracks Dataset"** — 114,000 tracks × 20 usable columns,
     114 genres × exactly 1,000 tracks each.
   - **TidyTuesday "Spotify Songs" (2020-01-21)** — 32,833 tracks × 23 columns,
     6 genres + 24 subgenres, plus a release date.
   A third (FMA metadata, 106,574 tracks with count-based play counts) is
   documented and downloadable.

2. **The headline statistical result is already known and must be designed
   around: audio features barely explain popularity.** Measured Pearson |r| with
   popularity never exceeds **0.10** in the 114k set (max: instrumentalness
   −0.0951) and **0.15** in TidyTuesday (max: instrumentalness −0.1499). A
   12–13 predictor OLS explains **R² ≈ 0.02 (114k)** / **≈ 0.07 (TidyTuesday)**
   of popularity variance on held-out data.

3. **That is a *good* P&S project, not a bad one** — provided it is framed as
   *"how strong is the relationship, and is statistical significance the same
   as practical importance?"* The dataset is large enough that **p-values are
   essentially meaningless**: e.g. `danceability` has r = 0.0354 with
   p = 5×10⁻³³. Teaching that gap *is* the project.

4. **Genre is the dominant, real signal** (one-way ANOVA on 114 genres:
   F = 343.5, η² = 0.254), but genre is also the **sampling stratum** of the
   scrape (exactly 1,000 tracks/genre), so part of it is an artefact. This is
   the single most interesting methodological discussion available.

5. **Duplicate tracks are real and large:** 35.9 % of the 114k rows sit in
   duplicate-`track_id` groups (21.3 % redundant rows); TidyTuesday has 13.6 %.
   Independence is violated; this must be handled once, consistently.

6. **Recommended direction: a hybrid of (B) and (C)** — statistically compare
   audio characteristics *across genres* **and** quantify the (weak)
   relationship between audio characteristics and popularity *with uncertainty
   and effect sizes*. Pure "predict popularity" (direction A) is the weakest
   choice: R² ≈ 0.02 means the headline number is "we failed to predict".

7. **Recommended stack:** Python + pandas/NumPy/SciPy/statsmodels/scikit-learn
   for analysis, **Streamlit + Plotly** for the app. Nothing heavier is needed.
   No ML beyond OLS/regularised OLS, no deep learning.

8. **Review 1 is very achievable:** the dataset is downloaded, audited, and
   already has real EDA plots and real test results. The remaining Review 1
   work is writing, not discovery.

---

## 2. Candidate dataset comparison

| # | Dataset | Rows × cols | Genres | Temporal | Popularity type | Licence | Access | Verdict |
|---|---|---|---|---|---|---|---|---|
| D1 | **Kaggle Spotify Tracks Dataset** (maharshipandya) — *audited* | 114,000 × 20 | 114 (1,000 each) | none | Spotify `popularity` 0–100, current snapshot | Kaggle: "Open Database, Contents © Original Authors"; HF mirror: BSD | direct CSV (HF mirror, no auth) | **PRIMARY** |
| D2 | **TidyTuesday Spotify Songs 2020-01-21** — *audited* | 32,833 × 23 | 6 + 24 subgenres | release date 1957–2020 | Spotify `track_popularity` 0–100 | repo CC0-1.0 | direct CSV (no auth) | **SECONDARY** |
| D3 | **FMA metadata** (Defferrard et al. 2017) | 106,574 × 518 (tracks.csv) | 161–163 (hierarchy) | none (2017 dump) | `listens` count + `favorite` | metadata CC BY 4.0 | 342 MB zip, no auth | **OPTIONAL** (count models) |
| D4 | Kaggle "Spotify Dataset 1921–2020, 160k+ tracks" (yamaerenay) | ~160,000 × ~20 | data_by_genres.csv (2,974 genres) | year 1921–2020 | Spotify `popularity` | Kaggle terms | **requires Kaggle login** (HF mirror 401) | good but gated → skip |
| D5 | Kaggle "Spotify 1.2M / Spotify Million Song" | ~1M+ | — | — | none / lyrics | Kaggle terms | login; mostly lyrics | reject (no target) |
| D6 | "Top Hits Spotify 2000–2019" (paradisejoy) | 2,000 × 15 | — | year 2000–2019 | Spotify `popularity` | Kaggle terms | login | reject (n too small for inference) |
| D7 | MTG-Jamendo (metadata) | ~55,000 × tags | 195 tags (multi-label) | none | none | CC BY-NC-SA | GitHub | reject (no popularity) |
| D8 | AcousticBrainz / MusicBrainz dumps | millions | partial | partial | none | various | heavy infra (DB dump) | reject (3-week scope) |

Notes:
- **D4/D5/D6 were not downloaded**: they require a Kaggle account. Kaggle was
  reachable (HTTP 200) but this machine has no `~/.kaggle/kaggle.json`, and the
  Hugging Face mirrors of the yamaerenay sets return **401 (gated)**. They are
  listed as *unverified candidates*.
- **D3 was being downloaded** (358,412,441-byte `fma_metadata.zip`) at the time
  of writing; its contents come from the official FMA README, not from
  inspection. `dataset_audit.md` §4 will be updated with measured numbers once
  the archive is extracted.

---

## 3. Verified sources and download links

| dataset | official source | exact file actually used | size |
|---|---|---|---|
| D1 | <https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset> | <https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv> | 20,118,244 B |
| D2 | <https://github.com/rfordatascience/tidytuesday/tree/main/data/2020/2020-01-21> | <https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-01-21/spotify_songs.csv> | 7,971,379 B |
| D3 | <https://github.com/mdeff/fma> | <https://os.unil.cloud.switch.ch/fma/fma_metadata.zip> | 358,412,441 B |
| Spotify field definitions | <https://developer.spotify.com/documentation/web-api/reference/get-audio-features> | (documentation) | — |

Reproduce D1/D2 with plain `curl` (no credentials), e.g.:
```bash
curl -sSL -o data/raw/kaggle_spotify_tracks_114k.csv \
  https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv
curl -sSL -o data/raw/tidytuesday_spotify_songs.csv \
  https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-01-21/spotify_songs.csv
```

Licences (as observed): D2 is **CC0-1.0** (repo `LICENSE`). D1 is ambiguous —
the Kaggle page shows *"Database: Open Database, Contents: © Original Authors"*
while the Hugging Face mirror metadata says `bsd`. Either way it is fine for a
course project **with attribution to Kaggle/Spotify**; the ambiguity is recorded
here rather than hidden. D3 metadata is **CC BY 4.0**.

---

## 4. Dataset schemas and quality findings

Full measured detail is in **`research/dataset_audit.md`**. Condensed:

**D1 (114k)** — 114,000 × 20; 1 fully empty-ish record (1 missing row in 3 text
columns); 450 exact duplicate rows; 24,259 duplicate `track_id` rows (35.9 % of
rows in duplicate groups); 720 duplicate ids have *inconsistent* popularity;
114 genres × 1,000 rows; popularity mean 33.24, sd 22.31, **14.1 % zeros**,
skew 0.05, kurtosis −0.93 (no distribution fits: KS D ≈ 0.088); `duration_ms`
min 0 ms, max ~87 min; `tempo` min 0 BPM (missing-coded).

**D2 (TidyTuesday)** — 32,833 × 23; 5 missing rows; 0 exact duplicates; 4,477
duplicate `track_id` rows (13.6 %); 6 genres × ~5,000 rows and 24 subgenres
**nested inside genre** (Cramér's V between them = 1.000); popularity mean 42.48,
sd 24.98, **8.2 % zeros**; release dates 1957–2020 but 71 % in the 2010s.

**D3 (FMA)** — documented, not yet inspected (see §2 note).

**Leakage / identifiers to drop before modelling:** `track_id`, `track_name`,
`artists`/`track_artist`, `album_name`/`track_album_id`, `playlist_id`,
`playlist_name`, `track_album_release_date` (keep as a *separate* temporal
variable, not as a raw string). There is **no classic leakage** (no feature is
derived from popularity), but two subtler traps exist:

1. **Genre is a sampling stratum** in D1 (1,000/genre). Genre dummies therefore
   capture the *collector's* choice as much as music.
2. **`explicit`** is a Spotify editorial flag, not an audio measurement; treat it
   as a categorical covariate, and do not interpret it causally.

---

## 5. Statistical feasibility assessment

### 5.1 What the data supports well

| Technique (syllabus) | Verdict | Evidence |
|---|---|---|
| Descriptive statistics & EDA | **Strong** | large n, 12 continuous features, 6–114 categories |
| Pearson & Spearman correlation | **Strong** | computed; the Pearson≠Spearman signs are a built-in lesson |
| Simple & multiple linear regression | **Strong** (as *association*, not prediction) | R² 0.02–0.26; train/test gap < 0.004 |
| Regression diagnostics | **Strong** | heteroscedasticity, near-collinearity, non-normality all present in real data |
| Confidence intervals | **Strong** | CI for mean popularity, for the explicit/clean difference, for regression coefficients |
| Two-sample tests (Welch t / Mann–Whitney) | **Strong** | explicit vs clean: d = 0.158; variances unequal |
| One-way ANOVA + post-hoc | **Strong** | genre F = 343.5, η² = 0.254, Levene p ≈ 0 |
| Chi-square / independence of attributes | **Strong**, with a trap | explicit × genre V = 0.402 (meaningful); genre × subgenre V = 1.000 |
| Sampling distributions & CLT | **Strong** | simulate sampling distribution of the mean from the skewed-ish target; show convergence |
| Distribution fitting (Bernoulli→Weibull, Gamma) | **Good with care** | bounded/zero-inflated target defeats simple fits — teach *why* (KS tests all reject) |
| Binomial / Poisson / Geometric / Negative binomial | **Weak on popularity, good on D3** | popularity is not a count; FMA `listens` **is** |
| Two-way ANOVA / RBD / LSD | **Possible** | e.g. genre × explicit, or genre × decade (D2), with unequal cells |
| Bootstrap / permutation tests | **Good (optional)** | cheap at this n, gives a modern CI alternative for skewed features |

### 5.2 What the data does **not** support

- **Causal claims** of any kind (promotion, artist fame, release timing absent).
- **Accurate popularity prediction.** R² ≈ 0.02 on audio features is the honest
  ceiling in D1; anything claiming higher should be treated as leakage or
  overfitting.
- **"Popularity is Normally distributed."** Measured autocorrelation-free but
  flat (kurtosis −0.93) with an atom at 0; the Normal fit fails decisively.
- **Temporal analysis on D1** — there is no time column at all.
- **Streaming counts / chart ranks** — no such column in any downloaded file.

### 5.3 Known methodological traps in these exact datasets (all measured)

| Trap | Measured value | Mitigation (cheap, appropriate) |
|---|---|---|
| Tiny p-values for negligible effects | r = 0.0354 → p = 5×10⁻³³ | report **effect size + CI** alongside every p; state n explicitly |
| Non-independence (same artist/album) | 3.63 tracks/artist (max 279) | de-duplicate on `track_id`; optionally average per artist/album as a **sensitivity analysis** |
| Duplicate tracks | 21.3 % (D1) / 13.6 % (D2) redundant rows | fix one rule: keep first row per `track_id`, document it, re-run key results both ways |
| Genre = sampling stratum | exactly 1,000 rows/genre | interpret genre effects as *labelled-genre* differences, not population effects |
| Bounded / zero-inflated target | 14.1 % exact zeros | avoid assuming Normality of the *outcome*; OLS inference survives by CLT at this n, verify with residual diagnostics + bootstrap |
| Heteroscedasticity across groups | Levene p ≈ 0 (D1, D2); within-genre sd 3.9–34.7 | **Welch** ANOVA / **Games–Howell** post-hoc; report Levene result |
| Multiple testing across many genres | 114 genres → 6,441 pairs | only compare a *pre-registered* shortlist (5–6 genres), or apply Benjamini–Hochberg |
| Nested categories tested for "independence" | genre × subgenre V = 1.000 | do not run that χ²; use it to show a violated assumption |
| Significance ≠ importance | explicit vs clean d = 0.16 | interpret in *popularity points* (3.5 points on a 0–100 scale) |
| Predictor scaling breaks solvers | sklearn R² 0.025 vs true 0.2597 | standardise predictors; cross-check two libraries (§5 audit note) |
| Non-reproducible target | Spotify `popularity` is a rolling recent-plays score | record the download date; state that results are a **snapshot**, not a fundamental property |

---

## 6. Proposed research questions and hypotheses

Each question is answerable with the downloaded data. `H0`/`H1` are given where a
formal test exists. Variables are named exactly as in the files.

**RQ1 — What is the distribution of Spotify track popularity?**
- Type: descriptive + goodness of fit. Variables: `popularity`.
- H0: `popularity` follows a Normal(μ, σ²) distribution.
- H1: it does not. Method: EDA, ECDF, moment check, χ²/KS goodness of fit.
- Assumptions/diagnostics: independence of tracks (violated → dedup), discreteness.
- Interpretation: a bounded, near-uniform, zero-inflated score → mean/median are
  weak summaries; motivates non-parametric and rank methods later.
- Confounders: the 0 atom is a *censoring* artefact (un-played tracks), not "bad music".
- Credibility: **High** (n = 114,000 and 32,833, both agree).

**RQ2 — Do high-energy and low-energy tracks differ in mean popularity?**
- H0: μ(high-energy) = μ(low-energy); H1: ≠.
- Variables: `energy` (split at median or at 0.5), `popularity`.
- Method: Welch two-sample t-test + 95 % CI for the difference + Cohen's d;
  Mann–Whitney U as robustness. Diagnostics: normality of *means* (CLT covers),
  equal variances (Welch), outliers (boxplot).
- Interpretation: measured effect in D1 is tiny (r = 0.001) → expect a
  statistically significant but practically zero difference; that **is** the result.
- Credibility: **High**; the honest answer is "no meaningful difference".

**RQ3 — Does average popularity differ across genres?**
- H0: μ₁ = μ₂ = … = μ_k; H1: at least one differs.
- Variables: `track_genre` (D1) / `playlist_genre`+`playlist_subgenre` (D2), `popularity`.
- Method: one-way ANOVA (Welch-corrected given Levene p ≈ 0) + η²; Games–Howell
  or BH-adjusted pairwise tests on a **pre-selected** shortlist; Kruskal–Wallis
  as a robustness check. Diagnostics: Levene, QQ of residuals, boxplots.
- Measured: F = 343.46, η² = 0.254 (D1: 114 genres); F = 207.21, η² = 0.031
  (D2: 6 genres).
- Interpretation: genre is the strongest real signal, but in D1 genre is the scrape
  stratum → discuss artefact vs music. Confounders: artist fame, era, playlist curation.
- Credibility: **Medium-high** (the effect is real *for these labelled sets*).

**RQ4 — Are `explicit` and `track_genre` independent?**
- H0: independent; H1: associated. Method: χ² test of independence + Cramér's V.
- Measured: χ² = 18,460, df = 113, p ≈ 0, V = 0.402 (min expected count 85.5 → valid).
- Interpretation: explicit content is highly genre-dependent → a good illustration
  of "independence of attributes"; also motivates *not* treating `explicit` as
  random across genres in later models.
- Trap to include: the **nested** `playlist_genre` × `playlist_subgenre` test
  returns V = 1.000 and demonstrates a violated assumption.

**RQ5 — Which audio features are associated with popularity, and how strong is
that association?**
- Method: full Pearson **and** Spearman matrices with popularity; significance +
  CI via Fisher z; explicit discussion of n-driven p-values; partial correlations
  controlling for genre.
- Measured: max |r| = 0.0951 (D1, instrumentalness), 0.1499 (D2); several sign
  flips between Pearson and Spearman.
- Interpretation: weak, mostly monotone-but-trivial relationships; the "most
  associated" feature changes between datasets → unstable.

**RQ6 — Can multiple audio features predict popularity, and how much variance is
explained?**
- Model: OLS `popularity ~ z-scored(audio features) + explicit` (+ genre dummies
  as a second model). Evaluate on a held-out 20 % split; report R², adjusted R²,
  RMSE; compare audio-only vs audio+genre.
- Measured: test R² = 0.0223 (audio only) → 0.2587 (+genre) in D1;
  0.0707 → 0.0877 in D2.
- Diagnostics: residual vs fitted (funnel = heteroscedasticity), QQ plot, VIF
  (energy/loudness collinear), influence (Cook's D), scaling (see §5 audit note).
- Interpretation: audio characteristics are **not** a useful popularity model;
  genre dummies add variance but are structural. Frame as a
  "statistically significant, practically limited" result.
- Credibility: **High** for the *negative* conclusion.

**RQ7 — Does the relationship hold within genres, and does it survive
de-duplication?**
- Method: repeat RQ5/RQ6 on 5–6 pre-selected genres; repeat the headline numbers
  after de-duplicating on `track_id` (21.3 % of rows removed).
- Measured (dedup): r(instrumentalness) −0.0951 → −0.1275; r(duration) −0.0071 →
  −0.0231; the story is unchanged.
- Interpretation: robustness / sensitivity analysis — essential for the viva.

**RQ8 (optional, D2 only) — Does popularity vary with release decade?**
- Method: one-way ANOVA across decades (post-1990 cells only, or pooled 5-year
  bins), plus a quadratic term in a simple regression; note the U-shape.
- Measured: mean popularity by decade dips in the 2000s (33.6) and rises again in
  the 2010s (43.8); corr(year, popularity) = +0.061.
- Confounders (explicit): the sample is playlist-curated and 71 % 2010s.
- Credibility: **Medium** — present as exploratory.

**RQ9 (optional, D3 only) — How are play counts (`listens`) distributed?**
- Method: fit Binomial/Poisson/negative-binomial, then log-transform and fit
  Gamma/Weibull; compare with AIC and a dispersion test.
- Only after FMA is verified. If it does not verify, drop this question rather
  than fake it.

---

## 7. Recommended statistical techniques (the strongest subset)

Ranked by (course coverage × data support × time cost):

1. **Descriptive statistics & EDA** — mandatory, cheap, sets up everything.
2. **Pearson + Spearman correlation** with CIs and effect-size framing.
3. **Confidence intervals** (mean popularity; difference of means; regression
   coefficients via bootstrap).
4. **Welch two-sample test** (explicit vs clean; median-split energy) with Cohen's d.
5. **One-way ANOVA** (genre / subgenre) + Levene + post-hoc Games–Howell + η²;
   Kruskal–Wallis robustness.
6. **Multiple linear regression** (standardised audio features; audio vs +genre),
   train/test evaluation, and a full **diagnostics** section.
7. **Chi-square test of independence** (explicit × genre) + Cramér's V, *and* the
   deliberately-broken nested case as a caution.

Secondary / if time allows: **goodness-of-fit** for `popularity` (show all simple
fits fail), **sampling distribution / CLT demonstration**, **bootstrap or
permutation CI**, **two-way ANOVA** (genre × explicit).

Deliberately **de-emphasised**: Poisson/geometric/NB (no count target in D1/D2 —
reintroduce only with verified FMA), heavy ML, and any tool whose output the team
cannot explain in the viva.

---

## 8. Risks, assumptions and limitations

**Assumptions made**
1. `popularity` is the intended target (documented, measured 0–100).
2. Downloaded snapshots are treated as *fixed* data; their collection date is
   recorded in the report.
3. Tracks are treated as the sampling unit unless stated otherwise.

**Risks**
| risk | likelihood | impact | mitigation |
|---|---|---|---|
| "Everything is insignificant-looking/weak" disappoints graders | medium | high | reframe as *significance vs effect size*; genre ANOVA and distribution fitting carry the "positive" results |
| Reviewers expect prediction accuracy | high | medium | explicitly scope out prediction; show the honest R² ceiling as a *finding* |
| Duplicate/non-independence criticised in viva | high | medium | pre-empt with the dedup sensitivity table |
| FMA download fails or is slow | medium | low | D1+D2 are sufficient; D3 is optional |
| Kaggle-gated datasets mis-described | low | medium | marked as unverified; no numbers quoted |
| Multiple-testing criticism (114 genres) | high | medium | pre-registered shortlist + BH correction |
| Tooling surprise (scaling bug, library drift) | medium | medium | pinned venv, two-library cross-checks, scripted pipelines |
| Target staleness (Spotify popularity drifts) | certain | low | stated as a limitation; no claim of reproducibility over time |

**Limitations to state in the final report**
- Observational data → **no causal inference**.
- The 114k set has **no temporal dimension**; genre labels are scrape strata.
- Audio features are Spotify's proprietary models (Echo Nest lineage), not raw
  acoustics; `energy`, `valence`, `instrumentalness` etc. are **estimates**.
- `popularity` = recent-play intensity, not lifetime streams; **stale by design**.
- Playlist-curated samples (D2) are not representative of "all music".
- Effect sizes are small: SS_R2 ≈ 0.02–0.10 for audio-only models.

---

## 9. Comparison of project directions

Scored 1 (poor) – 5 (excellent).

| criterion | **A. Popularity prediction** | **B. Genre comparison** | **C. Associations + uncertainty** |
|---|---|---|---|
| Statistical depth | 3 (regression/ML focus, thin inference) | 4 (ANOVA, post-hoc, χ²) | **5** (correlation, CI, tests, regression, diagnostics) |
| Dataset suitability | 2 (target is near-independent of features) | **5** (balanced, 114 genres, high n) | 4 (weak but well-powered) |
| Implementation difficulty | 4 (needs ML plumbing) | 4 | 4 |
| Visualisation opportunities | 4 | **5** (genre boxplots/violins, heatmaps) | **5** (scatter/corr matrices, CI plots, residuals) |
| Originality of RQs | 3 (heavily done on Kaggle) | 3 (also common) | **4** (the "weak but significant" framing is underused) |
| Course-concept coverage | 2 (mostly regression) | 4 | **5** |
| Risk of uninteresting/misleading results | **5 (high — R² ≈ 0.02)** | 2 | 2 |
| Feasibility in 3 weeks | 4 | **5** | 4 |
| Ease of defending in viva | 2 ("why is R² so low?") | **5** | 4 |

**Verdict:** Direction **C**, with **B's genre ANOVA** as the complementary
"strong signal" story, is the best fit. Direction **A alone** is the trap: it
converts a genuine, well-powered *negative* finding into a failed prediction
task.

---

## 10. Recommended direction and justification

**Recommended: "Statistical Analysis of Music Popularity and Audio
Characteristics" — direction C, supported by B.**

The title and the tentative research question already match this framing
(*"Can statistical analysis of music audio characteristics reveal significant
relationships with track popularity?"*). The measured answer is a nuanced
**"yes, statistically; barely, practically"** — which is a far stronger academic
result than a mediocre regression.

Concretely the narrative is:

1. **Popularity is a peculiar variable** (bounded, near-uniform, 14 % zeros, no
   simple fit) → distribution analysis.
2. **Audio features are weakly associated with it** (|r| ≤ 0.10–0.15; R² ≈
   0.02–0.09) but *significantly* so at n = 114,000 → significance vs effect size.
3. **Genre differences are large and real** (η² = 0.254 / F = 343) but genre is
   partly a sampling artefact → careful interpretation.
4. **Robustness**: everything survives (or not) de-duplication and stays weak
   within genres → limitations and honest conclusion.

Justification against the alternatives:
- Beats **A** because R² ≈ 0.02 makes "prediction" the wrong frame.
- Complementing **B** supplies the one strong, easily-visualised effect, so the
  project is not a wall of nulls.
- All of it maps directly onto Parts C/D/E of the syllabus and needs **no** new
  data collection, API keys, or expensive compute.

---

## 11. Proposed application architecture

**Stack:** Python 3.12 · pandas · NumPy · SciPy · statsmodels · scikit-learn ·
Streamlit · Plotly. Everything is already installed in `.venv`.

```
soniq/
  data/
    raw/          # downloaded CSVs (git-ignored, large)
    processed/    # cleaned parquet/csv produced by scripts/clean.py
  scripts/
    fetch_data.sh        # reproducible download (curl, no credentials)
    audit_datasets.py    # schema + quality report  (exists)
    feasibility_checks.py# stats feasibility checks (exists)
    clean.py             # dedup, dtypes, derived columns -> data/processed/
  research/       # this report + audit + raw logs
  app/
    app.py               # Streamlit entry point
    pages/               # 1_Overview, 2_Explorer, 3_Distributions, ...
    lib/                 # plotting + stats helpers (cached)
  tests/          # pytest: known-answer tests for each statistic
  requirements.txt / pyproject.toml
  README.md
```
Is this the most efficient stack? **Yes for this project.** Streamlit + Plotly
gives a polished interactive app with almost no front-end work; pandas/SciPy/
statsmodels give citable printed tests. A "simpler" static notebook would lose the
interactivity and a JS front-end would cost days for no statistical gain.
Nothing beyond these libraries is needed — no Dash, no databases, no deep learning.

**Design intent (explicitly not implemented yet):** dark, Spotify-*inspired*
theme (dark background, a bright green accent), **no Spotify logo or wordmark**,
a disclaimer "not affiliated with Spotify", metric cards, sidebar filters
(genre, popularity range, explicit), and every chart paired with a plain-English
statistical interpretation.

**MVP vs postponed**
| Feature | MVP (before/at Review 2) | Postpone |
|---|---|---|
| Overview dashboard (n, mean, sd, counts, source) | ✅ | |
| Dataset explorer (filterable table, download filtered CSV) | ✅ | |
| Distribution analysis (histogram, ECDF, QQ, fitted overlays, KS p) | ✅ | |
| Correlation analysis (Pearson/Spearman toggle, heatmap, CI) | ✅ | |
| Hypothesis-testing lab (choose test, see H0/H1, test stat, p, effect size, plot) | ✅ | |
| Regression lab (OLS with checkboxes, train/test R², coefficient table) | ✅ | |
| ANOVA / group comparison (box-violin, η², Levene, post-hoc) | ✅ | |
| Model diagnostics (residuals, QQ, VIF, Cook's D) | | ⏳ (after Review 1) |
| Interpretation & limitations page | ✅ | |
| Probability-distribution playground (simulate, CLT demo) | | ⏳ |
| Bootstrap/permutation CI explorer | | ⏳ |
| Multi-dataset comparison (D1 vs D2 side-by-side) | | ⏳ |
| Export report / PDF | | ⏳ |

---

## 12. Three-week implementation plan

Assumed shape of the cycle: ~1 week to Review 1, ~1.5 weeks of build, Review 2 at
the end of analysis, then the final report (Review 3). Adjust if the dates differ.

### Review 1 — feasibility and early progress (30 %)
**Must be finished before Review 1**
- [x] Problem statement and objectives (already drafted in the brief).
- [x] Dataset **verified and downloaded** (D1, D2) with links and licences.
- [x] Real schema + quality audit (`research/dataset_audit.md`).
- [x] Research questions RQ1–RQ7 with H0/H1, methods, diagnostics.
- [x] Statistical feasibility evidence (`research/_feasibility_raw.txt`).
- [ ] 6–8 **actual EDA plots** exported as PNG/PDF (histogram, ECDF, boxplots by
      genre, correlation heatmap, scatter with regression line, QQ plot).
- [ ] Initial literature/background notes (Spotify audio-feature docs; Echo Nest
      → Spotify lineage; 2–3 papers on music-popularity analysis).
- [ ] Streamlit prototype: one page, dark theme, live histogram + correlation
      heatmap from the real CSV (proof the app works, not the full app).
- [ ] Slide deck: problem → data → RQ → method → 2 early plots → plan.

**Can wait until after Review 1**
- FMA (D3) verification; two-way ANOVA; bootstrap; model diagnostics page;
  interpretation page polish; multi-dataset comparison.

### Review 2 — completed analysis (70 %)
- Cleaned dataset (`scripts/clean.py`) with a fixed dedup rule, saved to
  `data/processed/`; documented preprocessing.
- Full analysis: distribution fits + KS, Pearson/Spearman with CIs, Welch t-test
  + Cohen's d + CI, one-way ANOVA + Levene + Games–Howell + η², χ² + Cramér's V,
  OLS (audio-only vs +genre) with train/test R², full diagnostics.
- Sensitivity analysis: all headline numbers re-run on the deduplicated data.
- Working interactive dashboard covering the MVP features above.
- Interpretation write-up: significance vs effect size, limitations, confounders.

### Review 3 — final report and application (10 %)
- Final report: methodology, results, figures, limitations, reproducibility
  (`scripts/fetch_data.sh` + pinned `requirements.txt`), references.
- Final app + demo, and presentation.

---

## 13. Review 1 deliverables checklist

| # | Deliverable | Status |
|---|---|---|
| 1 | Problem statement + objectives | draft in brief |
| 2 | Dataset chosen, downloaded, **verified** (links, sizes, licences) | ✅ done |
| 3 | Dataset audit (rows, cols, missing, duplicates, target stats) | ✅ `research/dataset_audit.md` |
| 4 | Research questions with H0/H1, variables, methods, diagnostics | ✅ §6 |
| 5 | Statistical methodology / technique selection | ✅ §7 |
| 6 | Real EDA plots (not mock-ups) | ⬜ to generate |
| 7 | Background/literature notes | ⬜ to write |
| 8 | Preliminary app prototype (1 page, real data) | ⬜ to build |
| 9 | Feasibility evidence that the questions are answerable | ✅ §5 |
| 10 | Risk/limitation statement | ✅ §8 |
| 11 | Plan for Reviews 2–3 | ✅ §12 |

---

## 14. References and source links

1. Spotify Web API — audio features reference (field definitions):
   <https://developer.spotify.com/documentation/web-api/reference/get-audio-features>
2. Maharshi Pandya, *Spotify Tracks Dataset*, Kaggle (114k tracks, 114 genres):
   <https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset>
   — mirror used: <https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset>
3. TidyTuesday, *Spotify Songs*, 2020-01-21 (CC0-1.0 repo):
   <https://github.com/rfordatascience/tidytuesday/tree/main/data/2020/2020-01-21>
   — collected via the `spotifyr` R package (<https://www.rcharlie.com/spotifyr/>).
4. M. Defferrard, K. Benzi, P. Vandergheynst, X. Bresson, *FMA: A Dataset for
   Music Analysis*, ISMIR 2017: <https://arxiv.org/abs/1612.01840> ·
   <https://github.com/mdeff/fma> (metadata CC BY 4.0).
5. K. Pavlik, *Classifying songs with audio features* (origin of the TidyTuesday
   sample design): <https://www.kaylinpavlik.com/classifying-songs-genres/>
6. Library documentation used: pandas, NumPy, SciPy (`scipy.stats`), statsmodels,
   scikit-learn, Plotly, Streamlit.

---

## 15. Unresolved questions requiring human decisions

1. **Exact Review 1 date** — determines how much can be finished; the plan is
   written for "≈1 week to R1".
2. **Format of Review 1** (slides only? live demo? written submission?) — decides
   whether work goes into the deck or the app.
3. **Deadline/time budget per week** — is 4–6 h/week realistic, or more?
4. **Is a working Streamlit app required at Review 1**, or is a prototype enough?
5. **Report format/template** (college template, IEEE, plain Markdown) and page limit.
6. **Team size and division of labour** (solo vs group).
7. **Is FMA (D3) wanted?** It adds genuine count-distribution analysis but costs
   extra time; D1+D2 already satisfy the syllabus.
8. **Any instructor preference/ban** on tooling (e.g. "must be R", "must be Jupyter").
9. **Do we need to show ML?** The data argues "no"; confirm that omitting
   classifier/regressor benchmarking will not cost marks.
10. **Where should the project ultimately live** — the current folder
    (`~/Downloads/materialgram/soniq/`) or a dedicated repo/location?

---

## 16. Final recommendation (answers to the brief's 11 questions)

1. **Which dataset?** The **Kaggle Spotify Tracks Dataset (114k)** as primary —
   it is large, balanced (114 genres × 1,000), has a real measured target, and is
   downloadable without credentials. Add the **TidyTuesday Spotify Songs (32,833)**
   as a secondary set for temporal and subgenre analysis.
2. **Which exact file?** `data/raw/kaggle_spotify_tracks_114k.csv`, i.e.
   `https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv`
   (20,118,244 bytes); plus `data/raw/tidytuesday_spotify_songs.csv`
   (`https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-01-21/spotify_songs.csv`).
3. **Which target variable?** `popularity` (D1) / `track_popularity` (D2) — the
   0–100 Spotify popularity score, with the 0-inflation acknowledged.
4. **Which 5–7 analyses?** (i) descriptive EDA; (ii) Pearson **and** Spearman
   correlation with CIs; (iii) confidence intervals + Welch t-test with Cohen's d;
   (iv) one-way ANOVA + Levene + post-hoc + η²; (v) χ² independence + Cramér's V;
   (vi) multiple linear regression (audio vs +genre) with train/test and
   diagnostics; (vii) duplicate/non-independence sensitivity analysis.
5. **Three strongest research questions?**
   - RQ5: How strongly are audio features associated with popularity
     (and how much of the "significance" is just n)?
   - RQ3: Do genres differ in mean popularity, and how much of that is a
     sampling artefact?
   - RQ6: How much popularity variance can audio features actually explain on
     held-out data (the honest R² ceiling)?
6. **Main methodological risks?** Non-independent/duplicate tracks; genre as a
   sampling stratum; heteroscedasticity across genres; multiple testing; a
   bounded/zero-inflated target that defeats Normal assumptions; and the trap of
   reporting p-values without effect sizes. All have cheap mitigations (§5.3).
7. **What can realistically be shown at Review 1?** Verified datasets with
   provenance, the full audit, RQ list with hypotheses, real EDA plots, real test
   results (ANOVA F = 343.5 / η² = 0.254; explicit diff = 3.5 pts, d = 0.16;
   max |r| = 0.095), and a one-page working Streamlit prototype.
8. **What should the dashboard look like?** Dark, green-accented, Spotify-*inspired*
   but unaffiliated: sidebar filters → metric cards → tabs for Overview, Explorer,
   Distributions, Correlation, Hypothesis tests, Regression, ANOVA, Diagnostics,
   Limitations; every chart carries a one-line statistical interpretation.
9. **Minimum viable implementation?** `scripts/clean.py` producing one cleaned
   dataset + a single Streamlit app with Overview, Explorer, Distributions,
   Correlation and one hypothesis test, all reading `data/processed/`.
10. **Highest visual impact for least work?** (a) popularity histogram + ECDF with
    fitted curves; (b) correlation heatmap (Pearson/Spearman toggle); (c) genre
    box-violin plots sorted by mean; (d) the explicit-vs-clean CI dot plot;
    (e) the residual-vs-fitted diagnostic. These five charts tell the whole story.
11. **What to do immediately after approving the plan?** (1) fix the R1 date and
    format; (2) write `scripts/clean.py` and freeze the dedup rule; (3) generate
    the six EDA figures; (4) build the one-page Streamlit prototype; (5) write the
    literature notes; (6) assemble the R1 deck. Optionally (7) finish extracting
    FMA metadata if count-distribution analysis is wanted.
