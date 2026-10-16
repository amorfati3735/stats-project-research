
# ============================================================================
# VARSA — Visualization Suite
# Creates presentation-ready plots for the Review 1 demo.
#
# Run from the VARSA project root:
#   source("varsa_visuals.R")
#
# Input:
#   data/raw/rainfall_alt.csv
#
# Output:
#   figures/r/*.png
# ============================================================================

# 0. Setup -------------------------------------------------------------------

if (!requireNamespace("ggplot2", quietly = TRUE)) {
  install.packages("ggplot2")
}

library(ggplot2)

data_file <- "data/raw/rainfall_alt.csv"

if (!file.exists(data_file)) {
  stop(
    "Dataset not found: ", data_file,
    "\nOpen the VARSA project root and ensure data/raw/rainfall_alt.csv exists."
  )
}

dir.create("figures/r", recursive = TRUE, showWarnings = FALSE)

df <- read.csv(
  data_file,
  stringsAsFactors = FALSE,
  check.names = FALSE
)

required <- c(
  "DIVISION", "YEAR", "ANNUAL", "Jun-Sep",
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
)

missing <- setdiff(required, names(df))

if (length(missing) > 0) {
  stop("Missing columns: ", paste(missing, collapse = ", "))
}

numeric_cols <- setdiff(required, "DIVISION")

for (nm in numeric_cols) {
  df[[nm]] <- suppressWarnings(as.numeric(df[[nm]]))
}

df$DIVISION <- as.character(df$DIVISION)

# Consistent visual theme -----------------------------------------------------

theme_varsA <- function() {
  theme_minimal(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", size = 15),
      plot.subtitle = element_text(color = "grey35"),
      axis.title = element_text(face = "bold"),
      panel.grid.minor = element_blank(),
      legend.position = "bottom",
      plot.margin = margin(12, 16, 12, 12)
    )
}

save_plot <- function(plot, filename, width = 10, height = 6) {
  path <- file.path("figures", "r", filename)

  ggsave(
    filename = path,
    plot = plot,
    width = width,
    height = height,
    dpi = 300,
    bg = "white"
  )

  message("Saved: ", path)
}

cat("\nVARSA visualization suite\n")
cat("Regions:", length(unique(df$DIVISION)), "\n")
cat("Years:", min(df$YEAR, na.rm = TRUE), "-",
    max(df$YEAR, na.rm = TRUE), "\n\n")


# 1. Regional rainfall variability -------------------------------------------

# Split annual rainfall by region and retain each region's label.
# The previous version built an unnecessary data frame with a zero-length
# DIVISION column, which caused the differing-number-of-rows error.
groups <- split(df$ANNUAL, df$DIVISION)

cv_rows <- lapply(names(groups), function(region) {
  x <- groups[[region]]
  x <- x[is.finite(x)]

  data.frame(
    DIVISION = region,
    mean = if (length(x) > 0) mean(x) else NA_real_,
    sd = if (length(x) > 1) sd(x) else NA_real_
  )
})

cv <- if (length(cv_rows) > 0) do.call(rbind, cv_rows) else data.frame(
  DIVISION = character(), mean = numeric(), sd = numeric()
)

cv$CV <- 100 * cv$sd / abs(cv$mean)
cv <- cv[is.finite(cv$CV), ]
cv$DIVISION <- reorder(cv$DIVISION, cv$CV)

p1 <- ggplot(cv, aes(x = DIVISION, y = CV)) +
  geom_col(fill = "#2878B5", width = 0.75) +
  coord_flip() +
  labs(
    title = "Which regions have the most variable rainfall?",
    subtitle = "Coefficient of variation of annual rainfall",
    x = NULL,
    y = "CV (%)"
  ) +
  theme_varsA()

save_plot(p1, "01_regional_variability.png", 10, 9)


# 2. Annual rainfall trends ---------------------------------------------------

annual <- aggregate(
  ANNUAL ~ YEAR,
  data = df,
  FUN = mean,
  na.rm = TRUE
)

annual <- annual[is.finite(annual$ANNUAL), ]

p2 <- ggplot(annual, aes(YEAR, ANNUAL)) +
  geom_line(color = "#2878B5", linewidth = 0.7) +
  geom_smooth(
    method = "lm",
    formula = y ~ x,
    se = TRUE,
    color = "#D9534F",
    fill = "#D9534F",
    alpha = 0.15
  ) +
  labs(
    title = "Annual rainfall over time",
    subtitle = "Mean across available meteorological subdivisions",
    x = "Year",
    y = "Mean annual rainfall (mm)"
  ) +
  theme_varsA()

save_plot(p2, "02_annual_rainfall_trend.png")


# 3. All-India monsoon index --------------------------------------------------

ai <- aggregate(
  df[["Jun-Sep"]],
  by = list(YEAR = df$YEAR),
  FUN = mean,
  na.rm = TRUE
)

names(ai)[2] <- "JJS"
ai <- ai[is.finite(ai$JJS), ]
normal <- mean(ai$JJS)

ai$Status <- ifelse(
  ai$JJS < 0.9 * normal,
  "Below 90% of mean",
  "At least 90% of mean"
)

p3 <- ggplot(ai, aes(YEAR, JJS, fill = Status)) +
  geom_col(width = 1) +
  geom_hline(
    yintercept = normal,
    linetype = "solid",
    color = "black",
    linewidth = 0.7
  ) +
  geom_hline(
    yintercept = 0.9 * normal,
    linetype = "dashed",
    color = "#D9534F",
    linewidth = 0.7
  ) +
  scale_fill_manual(values = c(
    "Below 90% of mean" = "#D9534F",
    "At least 90% of mean" = "#2878B5"
  )) +
  labs(
    title = "Indian monsoon rainfall index",
    subtitle = "Dashed line marks 90% of the historical mean",
    x = "Year",
    y = "Mean Jun-Sep rainfall (mm)",
    fill = "Season"
  ) +
  theme_varsA()

save_plot(p3, "03_monsoon_index.png", 12, 6)


# 4. Monthly rainfall heatmap by region ---------------------------------------

months <- c(
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
)

monthly <- do.call(rbind, lapply(months, function(m) {
  data.frame(
    DIVISION = df$DIVISION,
    MONTH = m,
    RAINFALL = df[[m]]
  )
}))

monthly <- aggregate(
  RAINFALL ~ DIVISION + MONTH,
  data = monthly,
  FUN = mean,
  na.rm = TRUE
)

monthly$MONTH <- factor(monthly$MONTH, levels = months)

# Order regions by mean annual rainfall for a more readable heatmap.
region_order <- aggregate(
  ANNUAL ~ DIVISION,
  data = df,
  FUN = mean,
  na.rm = TRUE
)

region_order <- region_order[order(region_order$ANNUAL), "DIVISION"]

monthly$DIVISION <- factor(
  monthly$DIVISION,
  levels = region_order
)

p4 <- ggplot(monthly, aes(MONTH, DIVISION, fill = RAINFALL)) +
  geom_tile(color = "white", linewidth = 0.15) +
  scale_fill_gradient(
    low = "#F7FBFF",
    high = "#08519C",
    name = "Mean rainfall\n(mm)"
  ) +
  labs(
    title = "Seasonal rainfall patterns across regions",
    subtitle = "Average monthly rainfall over the available years",
    x = NULL,
    y = "Meteorological subdivision"
  ) +
  theme_varsA() +
  theme(
    axis.text.y = element_text(size = 7),
    axis.text.x = element_text(angle = 0)
  )

save_plot(p4, "04_monthly_rainfall_heatmap.png", 11, 10)


# 5. Regional monsoon rainfall distribution ----------------------------------

monsoon <- df[
  is.finite(df[["Jun-Sep"]]),
  c("DIVISION", "Jun-Sep")
]

names(monsoon)[2] <- "JJS"

p5 <- ggplot(monsoon, aes(DIVISION, JJS)) +
  geom_boxplot(
    fill = "#83B8D8",
    color = "#234E70",
    outlier.alpha = 0.35,
    outlier.size = 0.8
  ) +
  coord_flip() +
  labs(
    title = "How does monsoon rainfall vary between regions?",
    subtitle = "Distribution of Jun-Sep totals across years",
    x = NULL,
    y = "Jun-Sep rainfall (mm)"
  ) +
  theme_varsA() +
  theme(axis.text.y = element_text(size = 7))

save_plot(p5, "05_regional_monsoon_boxplots.png", 11, 10)


# 6. Distribution comparison --------------------------------------------------

x <- df[["Jun-Sep"]]
x <- x[is.finite(x)]

# Fit Gamma, Weibull and Lognormal to positive rainfall only.
xp <- x[x > 0]

if (length(xp) >= 10) {
  if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
    install.packages("fitdistrplus")
  }

  fits <- list(
    Gamma = fitdistrplus::fitdist(xp, "gamma"),
    Weibull = fitdistrplus::fitdist(xp, "weibull"),
    Lognormal = fitdistrplus::fitdist(xp, "lnorm")
  )

  # Overlay fitted distributions with an empirical density.
  density_data <- data.frame(x = xp)

  p6 <- ggplot(density_data, aes(x)) +
    geom_density(
      aes(y = after_stat(density)),
      fill = "#83B8D8",
      alpha = 0.4,
      color = "#2878B5"
    ) +
    stat_function(
      fun = dgamma,
      args = list(
        shape = fits$Gamma$estimate["shape"],
        rate = fits$Gamma$estimate["rate"]
      ),
      color = "#D9534F",
      linewidth = 1
    ) +
    stat_function(
      fun = dweibull,
      args = list(
        shape = fits$Weibull$estimate["shape"],
        scale = fits$Weibull$estimate["scale"]
      ),
      color = "#228B22",
      linewidth = 1
    ) +
    stat_function(
      fun = dlnorm,
      args = list(
        meanlog = fits$Lognormal$estimate["meanlog"],
        sdlog = fits$Lognormal$estimate["sdlog"]
      ),
      color = "#7B61A8",
      linewidth = 1
    ) +
    labs(
      title = "Probability distribution fitting",
      subtitle = "Positive Jun-Sep rainfall observations",
      x = "Monsoon rainfall (mm)",
      y = "Density",
      caption = paste(
        "Blue: empirical density | Red: Gamma",
        "| Green: Weibull | Purple: Lognormal"
      )
    ) +
    theme_varsA()

  save_plot(p6, "06_distribution_fits.png", 10, 6)

  # AIC comparison
  aic_table <- data.frame(
    Distribution = names(fits),
    AIC = sapply(fits, AIC)
  )

  aic_table <- aic_table[order(aic_table$AIC), ]

  p6b <- ggplot(
    aic_table,
    aes(x = reorder(Distribution, AIC), y = AIC)
  ) +
    geom_col(fill = "#2878B5", width = 0.65) +
    coord_flip() +
    labs(
      title = "Comparing fitted rainfall distributions",
      subtitle = "Lower AIC indicates a better relative fit",
      x = NULL,
      y = "AIC"
    ) +
    theme_varsA()

  save_plot(p6b, "07_distribution_aic.png", 8, 5)

  write.csv(
    aic_table,
    "figures/r/distribution_aic.csv",
    row.names = FALSE
  )
} else {
  warning("Not enough positive observations for distribution fitting.")
}


# 7. Drought threshold plot ---------------------------------------------------

# This section also needs fitdistrplus if section 6 skipped fitting.
if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
  install.packages("fitdistrplus")
}

groups <- split(df$ANNUAL, df$DIVISION)

rp_rows <- lapply(names(groups), function(region) {
  z <- groups[[region]]
  z <- z[is.finite(z)]

  if (length(z) < 80 || any(z <= 0)) {
    return(NULL)
  }

  fit <- tryCatch(
    fitdistrplus::fitdist(z, "gamma"),
    error = function(e) NULL
  )

  if (is.null(fit)) {
    return(NULL)
  }

  shape <- unname(fit$estimate["shape"])
  rate <- unname(fit$estimate["rate"])

  data.frame(
    DIVISION = region,
    Mean = mean(z),
    Q05 = qgamma(0.05, shape = shape, rate = rate),
    Q02 = qgamma(0.02, shape = shape, rate = rate)
  )
})

rp_rows <- Filter(Negate(is.null), rp_rows)

if (length(rp_rows) > 0) {
  rp <- do.call(rbind, rp_rows)

  rp_long <- rbind(
    data.frame(
      DIVISION = rp$DIVISION,
      Threshold = "1-in-20 lower-tail threshold",
      Rainfall = rp$Q05
    ),
    data.frame(
      DIVISION = rp$DIVISION,
      Threshold = "1-in-50 lower-tail threshold",
      Rainfall = rp$Q02
    )
  )

  p7 <- ggplot(
    rp_long,
    aes(
      x = reorder(DIVISION, Rainfall),
      y = Rainfall,
      fill = Threshold
    )
  ) +
    geom_col(position = "dodge") +
    coord_flip() +
    scale_fill_manual(values = c(
      "1-in-20 lower-tail threshold" = "#E5A823",
      "1-in-50 lower-tail threshold" = "#D9534F"
    )) +
    labs(
      title = "Modelled low-rainfall thresholds",
      subtitle = "Gamma-fitted annual rainfall distributions",
      x = NULL,
      y = "Annual rainfall threshold (mm)",
      fill = NULL
    ) +
    theme_varsA() +
    theme(axis.text.y = element_text(size = 7))

  save_plot(p7, "08_drought_thresholds.png", 11, 10)

  write.csv(
    rp,
    "figures/r/drought_thresholds.csv",
    row.names = FALSE
  )
}


# 8. Regional trends heatmap / slope ranking ---------------------------------

trend_groups <- split(
  df[, c("YEAR", "Jun-Sep")],
  df$DIVISION
)

trend <- do.call(rbind, lapply(names(trend_groups), function(region) {
  g <- trend_groups[[region]]
  names(g) <- c("YEAR", "JJS")

  g <- g[complete.cases(g), ]
  g <- g[is.finite(g$YEAR) & is.finite(g$JJS), ]

  if (nrow(g) < 40 || length(unique(g$YEAR)) < 2) {
    return(NULL)
  }

  model <- lm(JJS ~ YEAR, data = g)

  data.frame(
    DIVISION = region,
    Slope = unname(coef(model)["YEAR"]),
    p_value = summary(model)$coefficients["YEAR", "Pr(>|t|)"]
  )
}))

if (!is.null(trend) && nrow(trend) > 0) {
  trend$q_value <- p.adjust(trend$p_value, method = "BH")
  trend$Significance <- ifelse(
    trend$q_value < 0.05,
    "BH-adjusted p < 0.05",
    "Not significant after BH"
  )

  p8 <- ggplot(
    trend,
    aes(x = reorder(DIVISION, Slope), y = Slope, fill = Slope)
  ) +
    geom_col() +
    coord_flip() +
    scale_fill_gradient2(
      low = "#2166AC",
      mid = "white",
      high = "#B2182B",
      midpoint = 0,
      name = "Slope"
    ) +
    labs(
      title = "Regional monsoon rainfall trends",
      subtitle = "OLS slope in mm/year; positive and negative trends",
      x = NULL,
      y = "Trend slope (mm/year)"
    ) +
    theme_varsA() +
    theme(axis.text.y = element_text(size = 7))

  save_plot(p8, "09_regional_trend_slopes.png", 11, 10)

  write.csv(
    trend,
    "figures/r/regional_trends.csv",
    row.names = FALSE
  )
}


# 9. Finish -------------------------------------------------------------------

cat("\n============================================================\n")
cat("Visualization generation complete.\n")
cat("Find your charts in: figures/r/\n")
cat("============================================================\n")

# Uncomment to open the output folder in Windows:
# shell.exec(normalizePath("figures/r"))
