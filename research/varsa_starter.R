
# ============================================================================
# VARSA — Indian Monsoon Rainfall Analysis
# Review 1 demo | 36 meteorological subdivisions | 1901-2015
#
# Analyses:
#   1. Data validation
#   2. Coefficient of Variation (CV) ranking
#   3. Standard ANOVA and Welch ANOVA
#   4. Distribution fitting: Normal, Gamma, Weibull, Lognormal
#   5. Monthly zero-rainfall frequency
#   6. Regional rainfall trends + Benjamini-Hochberg correction
#   7. Gamma-based drought return-period thresholds
#   8. All-India monsoon index
#
# Expected CSV: data/raw/rainfall_alt.csv
# Run from RStudio using Source, or:
# source("varsa_starter.R")
# ============================================================================


# ----------------------------------------------------------------------------
# 0. Package setup
# ----------------------------------------------------------------------------

if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
  install.packages("fitdistrplus")
}

library(fitdistrplus)

cat("\n")
cat("============================================================\n")
cat(" VARSA - Indian Monsoon Rainfall Analysis (R)\n")
cat("============================================================\n")


# ----------------------------------------------------------------------------
# 1. Load and validate data
# ----------------------------------------------------------------------------

data_file <- "data/raw/rainfall_alt.csv"

if (!file.exists(data_file)) {
  stop(
    "Dataset not found: ", data_file,
    "\nCurrent working directory: ", getwd(),
    "\nPlace rainfall_alt.csv inside data/raw/ or open the VARSA project root."
  )
}

# IMPORTANT: check.names = FALSE preserves the column name "Jun-Sep".
df <- read.csv(
  data_file,
  stringsAsFactors = FALSE,
  check.names = FALSE
)

if (!is.data.frame(df)) {
  stop("Data loading failed: df is not a data frame.")
}

required_cols <- c(
  "DIVISION", "YEAR", "ANNUAL", "Jun-Sep",
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
)

missing_cols <- setdiff(required_cols, names(df))

if (length(missing_cols) > 0) {
  stop(
    "Missing required CSV columns: ",
    paste(missing_cols, collapse = ", "),
    "\nAvailable columns: ",
    paste(names(df), collapse = ", ")
  )
}

# Convert analytical columns to numeric safely.
numeric_cols <- setdiff(required_cols, "DIVISION")

for (col in numeric_cols) {
  if (!is.numeric(df[[col]])) {
    original <- df[[col]]
    converted <- suppressWarnings(as.numeric(original))
    
    bad <- !is.na(original) & is.na(converted)
    
    if (any(bad)) {
      warning("Non-numeric values converted to NA in column: ", col)
    }
    
    df[[col]] <- converted
  }
}

df$DIVISION <- as.character(df$DIVISION)

if (nrow(df) == 0) {
  stop("The CSV contains no observations.")
}

if (all(is.na(df$YEAR)) || all(is.na(df$DIVISION))) {
  stop("YEAR or DIVISION contains no usable values.")
}

cat(sprintf(
  "\nDataset: %d rows x %d columns\n",
  nrow(df), ncol(df)
))

cat(sprintf(
  "Regions: %d | Years: %s-%s\n",
  length(unique(na.omit(df$DIVISION))),
  min(df$YEAR, na.rm = TRUE),
  max(df$YEAR, na.rm = TRUE)
))

cat("Missing values in Jun-Sep: ",
    sum(is.na(df[["Jun-Sep"]])), "\n", sep = "")


# ----------------------------------------------------------------------------
# 2. Coefficient of Variation (CV) ranking
# ----------------------------------------------------------------------------
# CV = (standard deviation / mean) * 100
# Higher CV indicates greater relative variability.

annual_groups <- split(
  df$ANNUAL,
  df$DIVISION
)

cv_rows <- lapply(names(annual_groups), function(region) {
  x <- annual_groups[[region]]
  x <- x[is.finite(x)]
  
  data.frame(
    DIVISION = region,
    mean = if (length(x)) mean(x) else NA_real_,
    sd = if (length(x) > 1) sd(x) else NA_real_,
    n = length(x)
  )
})

cv <- do.call(rbind, cv_rows)

cv$CV <- ifelse(
  is.finite(cv$mean) & cv$mean != 0,
  100 * cv$sd / abs(cv$mean),
  NA_real_
)

cv <- cv[order(cv$CV, decreasing = TRUE, na.last = TRUE), ]

cat("\n--- CV of annual rainfall: most variable regions ---\n")
print(
  head(cv[, c("DIVISION", "mean", "sd", "CV", "n")], 8),
  row.names = FALSE
)

cat("\n--- Least variable regions ---\n")
print(
  tail(cv[!is.na(cv$CV), c("DIVISION", "mean", "sd", "CV", "n")], 4),
  row.names = FALSE
)


# ----------------------------------------------------------------------------
# 3. ANOVA: monsoon rainfall versus region
# ----------------------------------------------------------------------------

jj <- df[, c("DIVISION", "Jun-Sep")]
names(jj)[2] <- "JJS"

jj <- jj[
  complete.cases(jj) & is.finite(jj$JJS),
]

jj$DIVISION <- droplevels(factor(jj$DIVISION))

if (nlevels(jj$DIVISION) < 2) {
  stop("ANOVA requires at least two regions with valid observations.")
}

fit_aov <- aov(JJS ~ DIVISION, data = jj)

cat("\n--- Standard one-way ANOVA ---\n")
print(summary(fit_aov))

# Eta-squared: proportion of observed variation associated with region.
ss <- summary(fit_aov)[[1]][, "Sum Sq"]
eta2 <- ss[1] / sum(ss)

cat(sprintf(
  "Eta-squared = %.4f (%.1f%% of observed variation)\n",
  eta2, 100 * eta2
))

# Welch ANOVA does not assume equal population variances.
welch <- oneway.test(
  JJS ~ DIVISION,
  data = jj,
  var.equal = FALSE
)

cat("\n--- Welch ANOVA (primary if variances differ) ---\n")
cat(sprintf(
  "F = %.4f | df1 = %.2f | df2 = %.2f | p = %.6g\n",
  unname(welch$statistic),
  unname(welch$parameter[1]),
  unname(welch$parameter[2]),
  welch$p.value
))

cat(
  "Interpretation: a small p-value suggests that not all regional\n",
  "mean monsoon rainfall values are equal.\n",
  sep = ""
)


# ----------------------------------------------------------------------------
# 4. Distribution fitting: Normal, Gamma, Weibull, Lognormal
# ----------------------------------------------------------------------------

x <- df[["Jun-Sep"]]
x <- x[is.finite(x)]

cat("\n--- Distribution fitting: Jun-Sep rainfall ---\n")
cat("Valid observations:", length(x), "\n")

if (length(x) < 10) {
  stop("Too few observations for reliable distribution fitting.")
}

# Gamma, Weibull and Lognormal require strictly positive values.
if (any(x <= 0)) {
  warning(
    "Non-positive Jun-Sep values found. ",
    "Distribution fitting below uses strictly positive observations."
  )
  x <- x[x > 0]
}

if (length(x) < 10) {
  stop("Too few positive observations for distribution fitting.")
}

fits <- list(
  Normal = fitdist(x, "norm"),
  Gamma = fitdist(x, "gamma"),
  Weibull = fitdist(x, "weibull"),
  Lognormal = fitdist(x, "lnorm")
)

# All four distributions estimate two parameters.
# AIC = -2 * log-likelihood + 2 * number of parameters.
gof <- data.frame(
  model = names(fits),
  logLik = sapply(fits, function(f) f$loglik),
  parameters = sapply(fits, function(f) length(f$estimate)),
  stringsAsFactors = FALSE
)

gof$AIC <- -2 * gof$logLik + 2 * gof$parameters
gof <- gof[order(gof$AIC), ]

cat("\n--- Model comparison (lower AIC is preferred) ---\n")
print(gof, row.names = FALSE)

cat("\nBest model by AIC:", gof$model[1], "\n")

# Descriptive KS statistic against a fitted Normal distribution.
# IMPORTANT: its ordinary p-value is not calibrated when parameters
# are estimated from the same data. Do not use it as a formal
# 5% rejection test without a suitable correction or bootstrap.
ks_normal <- suppressWarnings(
  ks.test(
    x,
    "pnorm",
    mean = mean(x),
    sd = sd(x)
  )
)

cat("\n--- KS comparison against fitted Normal ---\n")
cat(sprintf(
  "D = %.4f | nominal p-value = %.5g\n",
  unname(ks_normal$statistic),
  ks_normal$p.value
))
cat(
  "Caution: the nominal KS p-value is not a calibrated test here,\n",
  "because the Normal parameters were estimated from these observations.\n",
  sep = ""
)


# ----------------------------------------------------------------------------
# 5. Zero-rainfall frequency by month
# ----------------------------------------------------------------------------
# Percentage of valid observations with exactly 0 mm rainfall.

months <- c(
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
)

zero_share <- sapply(months, function(m) {
  values <- df[[m]]
  values <- values[is.finite(values)]
  
  if (length(values) == 0) {
    return(NA_real_)
  }
  
  mean(values == 0) * 100
})

cat("\n--- Percentage of exactly zero rainfall by month ---\n")
print(round(zero_share, 2))


# ----------------------------------------------------------------------------
# 6. Regional trends: OLS, Kendall correlation and Sen's slope
# ----------------------------------------------------------------------------
# Benjamini-Hochberg correction controls the false discovery rate
# across the regional OLS trend tests.

sen_slope <- function(t, y) {
  valid <- is.finite(t) & is.finite(y)
  t <- t[valid]
  y <- y[valid]
  
  if (length(t) < 2 || anyDuplicated(t)) {
    return(NA_real_)
  }
  
  pairs <- combn(seq_along(t), 2)
  
  slopes <- (
    y[pairs[2, ]] - y[pairs[1, ]]
  ) / (
    t[pairs[2, ]] - t[pairs[1, ]]
  )
  
  median(slopes, na.rm = TRUE)
}

trend_data <- df[, c("DIVISION", "YEAR", "Jun-Sep")]
names(trend_data)[3] <- "JJS"

trend_data <- trend_data[
  complete.cases(trend_data) &
    is.finite(trend_data$YEAR) &
    is.finite(trend_data$JJS),
]

trend_groups <- split(trend_data, trend_data$DIVISION)

trend_rows <- lapply(names(trend_groups), function(region) {
  g <- trend_groups[[region]]
  g <- g[order(g$YEAR), ]
  
  # At least 40 observations, as in the original analysis.
  if (nrow(g) < 40 || anyDuplicated(g$YEAR)) {
    return(NULL)
  }
  
  if (length(unique(g$JJS)) < 2) {
    return(NULL)
  }
  
  lm_fit <- lm(JJS ~ YEAR, data = g)
  co <- summary(lm_fit)$coefficients
  
  mk <- suppressWarnings(
    cor.test(
      g$YEAR,
      g$JJS,
      method = "kendall",
      exact = FALSE
    )
  )
  
  data.frame(
    division = region,
    n = nrow(g),
    ols_slope = unname(co["YEAR", "Estimate"]),
    ols_p = unname(co["YEAR", "Pr(>|t|)"]),
    tau = unname(mk$estimate),
    mk_p = mk$p.value,
    sen = sen_slope(g$YEAR, g$JJS)
  )
})

trend_rows <- Filter(Negate(is.null), trend_rows)

if (length(trend_rows) == 0) {
  stop("No regions had sufficient valid data for trend analysis.")
}

tr <- do.call(rbind, trend_rows)
rownames(tr) <- NULL

tr$q_ols <- p.adjust(tr$ols_p, method = "BH")
tr$q_kendall <- p.adjust(tr$mk_p, method = "BH")

cat("\n--- Regional rainfall trends ---\n")

cat(sprintf(
  "OLS significant before correction: %d / %d\n",
  sum(tr$ols_p < 0.05, na.rm = TRUE),
  nrow(tr)
))

cat(sprintf(
  "OLS significant after BH correction: %d / %d\n",
  sum(tr$q_ols < 0.05, na.rm = TRUE),
  nrow(tr)
))

cat(sprintf(
  "Kendall significant after BH correction: %d / %d\n",
  sum(tr$q_kendall < 0.05, na.rm = TRUE),
  nrow(tr)
))

cat("\n--- Strongest negative Sen slopes ---\n")
print(
  head(
    tr[order(tr$sen), c("division", "n", "sen", "mk_p", "q_kendall")],
    4
  ),
  row.names = FALSE
)

cat("\n--- Strongest positive Sen slopes ---\n")
print(
  tail(
    tr[order(tr$sen), c("division", "n", "sen", "mk_p", "q_kendall")],
    4
  ),
  row.names = FALSE
)

cat(
  "\nSlope units: rainfall millimetres per year.\n",
  "A negative slope indicates a downward trend; a positive slope\n",
  "indicates an upward trend. Statistical significance alone does\n",
  "not establish the cause of a trend.\n",
  sep = ""
)


# ----------------------------------------------------------------------------
# 7. Drought return-period thresholds
# ----------------------------------------------------------------------------
# Fit Gamma to annual rainfall within each region.
#
# 1-in-20-year lower-tail threshold: 5th percentile.
# 1-in-50-year lower-tail threshold: 2nd percentile.
#
# These are model-based estimates, not guaranteed recurrence intervals.

annual_groups <- split(df$ANNUAL, df$DIVISION)

rp_rows <- lapply(names(annual_groups), function(region) {
  values <- annual_groups[[region]]
  values <- values[is.finite(values)]
  
  if (length(values) < 80 || any(values <= 0)) {
    return(NULL)
  }
  
  fd <- tryCatch(
    fitdist(values, "gamma"),
    error = function(e) NULL
  )
  
  if (is.null(fd)) {
    warning("Gamma fit failed for region: ", region)
    return(NULL)
  }
  
  shape <- unname(fd$estimate["shape"])
  rate <- unname(fd$estimate["rate"])
  
  q20 <- qgamma(0.05, shape = shape, rate = rate)
  q50 <- qgamma(0.02, shape = shape, rate = rate)
  
  data.frame(
    division = region,
    n = length(values),
    mean = mean(values),
    q20 = q20,
    q50 = q50,
    q20_pct = 100 * q20 / mean(values),
    q50_pct = 100 * q50 / mean(values)
  )
})

rp_rows <- Filter(Negate(is.null), rp_rows)

if (length(rp_rows) > 0) {
  rp <- do.call(rbind, rp_rows)
  rownames(rp) <- NULL
  rp <- rp[order(rp$q20_pct), ]
  
  cat("\n--- Lowest modelled drought thresholds ---\n")
  print(
    head(
      rp[, c("division", "n", "mean", "q20", "q50", "q20_pct")],
      7
    ),
    row.names = FALSE
  )
  
  cat(
    "\nq20 = modelled 5th percentile of annual rainfall.\n",
    "q50 = modelled 2nd percentile of annual rainfall.\n",
    sep = ""
  )
} else {
  warning(
    "No regions met the criteria for annual Gamma return-period fitting."
  )
}


# ----------------------------------------------------------------------------
# 8. All-India monsoon index and dry-season frequency
# ----------------------------------------------------------------------------
# This is the unweighted average of available regional Jun-Sep totals
# for each year, not an area-weighted national rainfall estimate.

ai <- aggregate(
  df[["Jun-Sep"]],
  by = list(YEAR = df$YEAR),
  FUN = mean,
  na.rm = TRUE
)

names(ai)[2] <- "JJS"

ai <- ai[is.finite(ai$JJS) & is.finite(ai$YEAR), ]
ai <- ai[order(ai$YEAR), ]

if (nrow(ai) == 0) {
  stop("Could not calculate the all-India monsoon index.")
}

normal_mean <- mean(ai$JJS)
dry_years <- ai$JJS < 0.9 * normal_mean
dry_count <- sum(dry_years)

cat("\n--- All-India monsoon index ---\n")

cat(sprintf(
  "Mean regional monsoon index: %.2f mm\n",
  normal_mean
))

cat(sprintf(
  "Years available: %d\n",
  nrow(ai)
))

cat(sprintf(
  "Years below 90%% of the mean: %d / %d (%.2f%%)\n",
  dry_count,
  nrow(ai),
  100 * dry_count / nrow(ai)
))

cat(sprintf(
  "Six driest years: %s\n",
  paste(ai$YEAR[order(ai$JJS)][seq_len(min(6, nrow(ai)))],
        collapse = ", ")
))


# ----------------------------------------------------------------------------
# 9. Save results for further analysis
# ----------------------------------------------------------------------------
# Outputs are saved to the project working directory.

write.csv(cv, "varsA_cv_results.csv", row.names = FALSE)
write.csv(gof, "varsA_distribution_results.csv", row.names = FALSE)
write.csv(tr, "varsA_trend_results.csv", row.names = FALSE)
write.csv(ai, "varsA_all_india_index.csv", row.names = FALSE)

if (exists("rp") && is.data.frame(rp)) {
  write.csv(rp, "varsA_drought_thresholds.csv", row.names = FALSE)
}

cat("\n--- Output files saved ---\n")
cat("varsA_cv_results.csv\n")
cat("varsA_distribution_results.csv\n")
cat("varsA_trend_results.csv\n")
cat("varsA_all_india_index.csv\n")

if (exists("rp") && is.data.frame(rp)) {
  cat("varsA_drought_thresholds.csv\n")
}

cat("\n============================================================\n")
cat(" VARSA analysis completed.\n")
cat(" Review the statistical assumptions before presenting results.\n")
cat("============================================================\n")
