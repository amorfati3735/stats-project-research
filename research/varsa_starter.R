#!/usr/bin/env Rscript
# ============================================================================
# VARSA — RStudio starter script for Review 1 demo
# Indian monsoon rainfall: 36 meteorological subdivisions, 1901-2015
#
# Reproduces the headline numbers from the Python pipeline:
#   - CV ranking of regional variability
#   - One-way ANOVA of Jun-Sep rain ~ region (Welch, since Levene rejects)
#   - Distribution fitting: Normal vs Gamma vs Weibull vs Lognormal (KS + AIC)
#   - Trend per region + Benjamini-Hochberg correction
#   - Gamma return periods (1-in-20 / 1-in-50 year drought)
#
# Data: data/raw/rainfall_alt.csv  (download with scripts/fetch_data.sh)
#
# Run in RStudio: source("research/varsa_starter.R")
# ============================================================================

if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
  message("Installing fitdistrplus (one-time)...")
  install.packages("fitdistrplus")
}
library(fitdistrplus)

cat("===========================================================================\n")
cat("VARSA — Indian Monsoon Rainfall Review-1 Demo (R)\n")
cat("===========================================================================\n")

# ----------------------------------------------------------------------------
# 1. Load data
# ----------------------------------------------------------------------------
df <- read.csv("data/raw/rainfall_alt.csv", stringsAsFactors = FALSE)
cat(sprintf("\nData: %d rows x %d cols | %d regions | years %d-%d\n",
            nrow(df), ncol(df), length(unique(df$DIVISION)),
            min(df$YEAR), max(df$YEAR)))

# ----------------------------------------------------------------------------
# 2. CV ranking — which regions are least reliable?
# ----------------------------------------------------------------------------
cv <- aggregate(ANNUAL ~ DIVISION, data = df, FUN = function(x) {
  c(mean = mean(x, na.rm = TRUE), sd = sd(x, na.rm = TRUE), n = sum(!is.na(x)))
})
cv <- do.call(data.frame, cv)
names(cv) <- c("DIVISION", "mean", "sd", "n")
cv$CV <- 100 * cv$sd / cv$mean
cv <- cv[order(-cv$CV), ]

cat("\n--- CV of ANNUAL rainfall (most variable first) ---\n")
print(head(cv[, c("DIVISION", "mean", "CV")], 8), row.names = FALSE)
cat("... least variable:\n")
print(tail(cv[, c("DIVISION", "mean", "CV")], 4), row.names = FALSE)

# ----------------------------------------------------------------------------
# 3. One-way ANOVA: Jun-Sep rain ~ region
#    (Levene will reject equal variances -> report Welch)
# ----------------------------------------------------------------------------
jj <- na.omit(df[, c("DIVISION", "Jun-Sep")])
names(jj)[2] <- "JJS"
fit_aov <- aov(JJS ~ DIVISION, data = jj)
cat("\n--- One-way ANOVA: Jun-Sep rainfall ~ region ---\n")
print(summary(fit_aov))

# Eta-squared
ss <- summary(fit_aov)[[1]][, "Sum Sq"]
eta2 <- ss[1] / sum(ss)
cat(sprintf("Eta-squared = %.4f (%.1f%% of variation is between regions)\n",
            eta2, 100 * eta2))

# Welch ANOVA (the correct version when variances differ)
welch <- oneway.test(JJS ~ DIVISION, data = jj, var.equal = FALSE)
cat(sprintf("\nWelch ANOVA (var.equal = FALSE): F = %.1f, p = %.3g\n",
            welch$statistic, welch$p.value))

# ----------------------------------------------------------------------------
# 4. Distribution fitting on monsoon (Jun-Sep) totals
# ----------------------------------------------------------------------------
x <- na.omit(df[["Jun-Sep"]])
cat("\n--- Distribution fitting on Jun-Sep totals (n =", length(x), ") ---\n")

fits <- list(
  normal   = fitdist(x, "norm"),
  gamma    = fitdist(x, "gamma"),
  weibull  = fitdist(x, "weibull"),
  lnorm    = fitdist(x, "lnorm")
)

gof <- data.frame(
  model = names(fits),
  logLik = sapply(fits, function(f) f$loglik),
  stringsAsFactors = FALSE
)
gof$AIC <- -2 * gof$logLik + 2 * c(2, 3, 3, 3)
gof <- gof[order(gof$AIC), ]
print(gof, row.names = FALSE)

# KS test vs normal (the naive choice)
kn <- ks.test(x, "pnorm", mean = mean(x), sd = sd(x))
cat(sprintf("\nKS test vs Normal: D = %.4f, p = %.3g  (Normal rejected if p < 0.05)\n",
            kn$statistic, kn$p.value))

# ----------------------------------------------------------------------------
# 5. Zero-inflation by month (share of exactly 0 mm)
# ----------------------------------------------------------------------------
months <- c("JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC")
zero_share <- sapply(months, function(m) mean(df[[m]] == 0, na.rm = TRUE) * 100)
cat("\n--- Share of exactly 0 mm by month ---\n")
print(round(zero_share, 1))

# ----------------------------------------------------------------------------
# 6. Trend per region (Sen's slope) + Benjamini-Hochberg correction
# ----------------------------------------------------------------------------
sen_slope <- function(t, y) {
  n <- length(t)
  slopes <- sapply(2:n, function(i) (y[i] - y[1:(i-1)]) / (t[i] - t[1:(i-1)]))
  median(unlist(slopes), na.rm = TRUE)
}

jj2 <- na.omit(df[, c("DIVISION", "YEAR", "Jun-Sep")])
names(jj2)[3] <- "JJS"
trend_rows <- lapply(split(jj2, jj2$DIVISION), function(g) {
  if (sum(!is.na(g$JJS)) < 40) return(NULL)
  t <- g$YEAR; y <- g$JJS
  lm_fit <- lm(y ~ t)
  co <- summary(lm_fit)$coefficients
  mk <- cor.test(t, y, method = "kendall")
  list(
    division = unique(g$DIVISION),
    n = length(y),
    ols_slope = co[2, 1],
    ols_p = co[2, 4],
    tau = as.numeric(mk$estimate),
    mk_p = mk$p.value,
    sen = sen_slope(t, y)
  )
})
trend_rows <- trend_rows[!sapply(trend_rows, is.null)]
tr <- do.call(rbind, lapply(trend_rows, as.data.frame))
tr$q_ols <- p.adjust(tr$ols_p, method = "BH")

cat("\n--- Trends: OLS p<0.05 uncorrected vs BH-surviving ---\n")
cat(sprintf("Uncorrected significant: %d / %d\n",
            sum(tr$ols_p < 0.05), nrow(tr)))
cat(sprintf("Survive BH-FDR 5%%:      %d / %d\n",
            sum(tr$q_ols < 0.05), nrow(tr)))

cat("\nStrongest Sen slopes:\n")
print(head(tr[order(tr$sen), c("division", "sen", "mk_p", "q_ols")], 4), row.names = FALSE)
cat("...\n")
print(tail(tr[order(tr$sen), c("division", "sen", "mk_p", "q_ols")], 4), row.names = FALSE)

# ----------------------------------------------------------------------------
# 7. Return periods — Gamma fit to annual rainfall per region
#    1-in-20-year low (q05) and 1-in-50-year low (q02)
# ----------------------------------------------------------------------------
cat("\n--- 1-in-20 / 1-in-50 year drought (Gamma fit to ANNUAL) ---\n")
rp_rows <- lapply(split(df, df$DIVISION), function(g) {
  x <- na.omit(g[["ANNUAL"]])
  if (length(x) < 80) return(NULL)
  fd <- fitdist(x, "gamma")
  q20 <- qgamma(0.05, shape = fd$estimate["shape"], rate = fd$estimate["rate"])
  q50 <- qgamma(0.02, shape = fd$estimate["shape"], rate = fd$estimate["rate"])
  data.frame(
    division = unique(g$DIVISION),
    mean = mean(x),
    q20 = q20, q50 = q50,
    q20_pct = 100 * q20 / mean(x),
    q50_pct = 100 * q50 / mean(x),
    stringsAsFactors = FALSE
  )
})
rp_rows <- rp_rows[!sapply(rp_rows, is.null)]
rp <- do.call(rbind, rp_rows)
rp <- rp[order(rp$q20_pct), ]
print(head(rp[, c("division", "mean", "q20", "q50", "q20_pct")], 7), row.names = FALSE)

# ----------------------------------------------------------------------------
# 8. All-India monsoon index + drought frequency
# ----------------------------------------------------------------------------
ai <- aggregate(Jun-Sep ~ YEAR, data = df, FUN = mean)
names(ai)[2] <- "JJS"
norm <- mean(ai$JJS)
dry <- sum(ai$JJS < 0.9 * norm)
cat(sprintf("\n--- All-India Jun-Sep index ---\n"))
cat(sprintf("Normal = %.1f mm, n = %d years\n", norm, nrow(ai)))
cat(sprintf("Years below 90%% of normal: %d / %d (%.1f%%)\n",
            dry, nrow(ai), 100 * dry / nrow(ai)))
cat(sprintf("Driest seasons: %s\n",
            paste(ai$YEAR[order(ai$JJS)][1:6], collapse = ", ")))

cat("\n===========================================================================\n")
cat("END — all numbers reproducible from data/raw/rainfall_alt.csv\n")
cat("===========================================================================\n")
