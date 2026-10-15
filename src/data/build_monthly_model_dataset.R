#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readxl)
})

root <- normalizePath(getwd(), mustWork = TRUE)
raw_dir <- file.path(root, "data", "raw", "eu_de")
proxy_dir <- file.path(raw_dir, "monthly_proxy_candidates")
banking_dir <- file.path(raw_dir, "banking_proxy_candidates")
processed_dir <- file.path(root, "data", "processed", "eu_de")

dir.create(processed_dir, recursive = TRUE, showWarnings = FALSE)

stop_if_missing <- function(path) {
  if (!file.exists(path)) stop("Missing required file: ", path, call. = FALSE)
  path
}

as_num <- function(x) suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", as.character(x))))

month_end <- function(d) {
  d <- as.Date(d)
  as.Date(vapply(d, function(one_date) {
    if (is.na(one_date)) return(NA_character_)
    first <- as.Date(format(one_date, "%Y-%m-01"))
    as.character(seq(first, by = "1 month", length.out = 2)[2] - 1)
  }, character(1)))
}

quarter_end <- function(d) {
  d <- as.Date(d)
  as.Date(vapply(d, function(one_date) {
    if (is.na(one_date)) return(NA_character_)
    y <- as.integer(format(one_date, "%Y"))
    m <- as.integer(format(one_date, "%m"))
    qm <- ((m - 1) %/% 3 + 1) * 3
    first <- as.Date(sprintf("%04d-%02d-01", y, qm))
    as.character(seq(first, by = "1 month", length.out = 2)[2] - 1)
  }, character(1)))
}

merge_series <- function(series_list) {
  Reduce(function(x, y) merge(x, y, by = "date", all = TRUE), series_list)
}

last_by_month <- function(df, value_cols) {
  work <- df[, c("date", value_cols), drop = FALSE]
  work$mdate <- month_end(work$date)
  out <- do.call(rbind, lapply(split(work, work$mdate), function(z) {
    z <- z[order(z$date), , drop = FALSE]
    row <- z[nrow(z), c("mdate", value_cols), drop = FALSE]
    names(row)[1] <- "date"
    row
  }))
  rownames(out) <- NULL
  out
}

mean_by_month <- function(df, value_cols) {
  work <- df[, c("date", value_cols), drop = FALSE]
  work$date <- month_end(work$date)
  aggregate(work[, value_cols, drop = FALSE], by = list(date = work$date), FUN = mean, na.rm = TRUE)
}

read_ecb_portal <- function(path, name) {
  x <- read_excel(path, sheet = "DATA", col_names = FALSE, .name_repair = "minimal")
  data <- x[16:nrow(x), c(1, 3)]
  names(data) <- c("date", name)
  data$date <- as.Date(data$date)
  data[[name]] <- as_num(data[[name]])
  data[!is.na(data$date), ]
}

read_hicp_rows <- function(path) {
  hicp_raw <- read.delim(path, sep = "\t", check.names = FALSE, stringsAsFactors = FALSE)
  key_col <- names(hicp_raw)[1]
  read_key <- function(key, var_name) {
    row <- hicp_raw[hicp_raw[[key_col]] == key, , drop = FALSE]
    if (!nrow(row)) stop("Missing HICP key: ", key, call. = FALSE)
    dates <- trimws(names(row)[-1])
    vals <- as_num(unlist(row[1, -1]))
    data.frame(date = month_end(as.Date(paste0(dates, "-01"))), value = vals, variable = var_name)
  }
  long <- rbind(
    read_key("M,I05,CP00,DE", "hicp_de"),
    read_key("M,I05,CP00,EA20", "hicp_ea20"),
    read_key("M,I05,CP00,EA", "hicp_ea")
  )
  wide <- reshape(long, idvar = "date", timevar = "variable", direction = "wide")
  names(wide) <- sub("^value\\.", "", names(wide))
  wide[order(wide$date), ]
}

read_ecb_proxy_csv <- function(path, name) {
  if (!file.exists(path)) {
    return(data.frame(date = as.Date(character()), value = numeric(), stringsAsFactors = FALSE))
  }
  x <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  if (!all(c("TIME_PERIOD", "OBS_VALUE") %in% names(x))) {
    stop("ECB proxy candidate is missing TIME_PERIOD/OBS_VALUE columns: ", path, call. = FALSE)
  }
  out <- data.frame(
    date = month_end(as.Date(paste0(x$TIME_PERIOD, "-01"))),
    value = as_num(x$OBS_VALUE),
    stringsAsFactors = FALSE
  )
  names(out)[2] <- name
  out[!is.na(out$date), ]
}

read_monthly_proxy_csv <- function(path, name) {
  if (!file.exists(path)) {
    return(data.frame(date = as.Date(character()), value = numeric(), stringsAsFactors = FALSE))
  }
  x <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  if (!all(c("TIME_PERIOD", "OBS_VALUE") %in% names(x))) {
    stop("Monthly proxy candidate is missing TIME_PERIOD/OBS_VALUE columns: ", path, call. = FALSE)
  }
  out <- data.frame(
    date = month_end(as.Date(paste0(x$TIME_PERIOD, "-01"))),
    value = as_num(x$OBS_VALUE),
    stringsAsFactors = FALSE
  )
  names(out)[2] <- name
  out[!is.na(out$date), ]
}

read_quarterly_proxy_csv <- function(path, name) {
  if (!file.exists(path)) {
    return(data.frame(date = as.Date(character()), value = numeric(), stringsAsFactors = FALSE))
  }
  x <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  if (!all(c("TIME_PERIOD", "OBS_VALUE") %in% names(x))) {
    stop("Quarterly proxy candidate is missing TIME_PERIOD/OBS_VALUE columns: ", path, call. = FALSE)
  }
  period_start <- as.Date(paste0(substr(x$TIME_PERIOD, 1, 4), "-", (as.integer(substr(x$TIME_PERIOD, 7, 7)) - 1) * 3 + 1, "-01"))
  out <- data.frame(
    date = quarter_end(period_start),
    value = as_num(x$OBS_VALUE),
    stringsAsFactors = FALSE
  )
  names(out)[2] <- name
  out[!is.na(out$date), ]
}

add_log <- function(data, var) {
  data[[paste0("ln_", var)]] <- ifelse(data[[var]] > 0, log(data[[var]]), NA_real_)
  data
}

add_diff <- function(data, var) {
  data[[paste0("d_", var)]] <- c(NA_real_, diff(data[[var]]))
  data
}

lag_n <- function(x, n) {
  if (length(x) <= n) return(rep(NA_real_, length(x)))
  c(rep(NA_real_, n), x[seq_len(length(x) - n)])
}

rolling_mean_n <- function(x, n) {
  if (length(x) < n) return(rep(NA_real_, length(x)))
  out <- rep(NA_real_, length(x))
  for (i in seq_along(x)) {
    if (i >= n) {
      window <- x[(i - n + 1):i]
      out[i] <- if (all(is.na(window))) NA_real_ else mean(window, na.rm = TRUE)
    }
  }
  out
}

raw_files <- list(
  wx = stop_if_missing(file.path(raw_dir, "1. Wu-Xia Euro Area Shadow Rate.xls")),
  ecb_assets = stop_if_missing(file.path(raw_dir, "ecb_central_bank_assets_weekly.csv")),
  dfr = stop_if_missing(file.path(raw_dir, "ecb_deposit_facility_rate_daily.csv")),
  hh_loans = stop_if_missing(file.path(raw_dir, "4. loans to euro area households granted by MFIs .xlsx")),
  nfc_loans = stop_if_missing(file.path(raw_dir, "5. Adjusted loans to euro area NFCs granted by MFIs.xlsx")),
  house_prices = stop_if_missing(file.path(raw_dir, "germany_residential_prices_quarterly.csv")),
  dax = stop_if_missing(file.path(raw_dir, "8. DAX 40.csv")),
  compensation = stop_if_missing(file.path(raw_dir, "9. Compensation per employee.xlsx")),
  retail = stop_if_missing(file.path(raw_dir, "10 volume of sales in wholesale and retail trade .xlsx")),
  hicp = stop_if_missing(file.path(raw_dir, "hicp_selected_cp00_de_ea20_ea.tsv")),
  surprises = stop_if_missing(file.path(processed_dir, "ecb_surprise_monthly.csv"))
)

proxy_files <- list(
  house_purchase_growth = file.path(proxy_dir, "ecb_bsi_house_purchase_annual_growth.csv"),
  house_purchase_pure_new_loans = file.path(proxy_dir, "ecb_mir_house_purchase_pure_new_loans.csv"),
  wage_tracker_headline = file.path(proxy_dir, "ecb_wage_tracker_headline.csv"),
  wage_tracker_ex_oneoffs = file.path(proxy_dir, "ecb_wage_tracker_ex_oneoffs.csv"),
  wage_tracker_unsmoothed_oneoffs = file.path(proxy_dir, "ecb_wage_tracker_unsmoothed_oneoffs.csv"),
  wage_tracker_coverage = file.path(proxy_dir, "ecb_wage_tracker_coverage.csv"),
  unemployment_ea21 = file.path(proxy_dir, "eurostat_unemployment_ea21_sa.csv"),
  employment_expectations_ea20 = file.path(proxy_dir, "eurostat_ecfin_employment_expectations_ea20.csv"),
  services_employment_expectations_ea20 = file.path(proxy_dir, "eurostat_ecfin_services_employment_expectations_ea20.csv"),
  ces_income_expectations = file.path(proxy_dir, "ecb_ces_income_expectations_12m_median.csv"),
  ces_unemployment_expectations = file.path(proxy_dir, "ecb_ces_unemployment_expectations_12m_median.csv"),
  sts_industry_wage_bill_de = file.path(proxy_dir, "eurostat_sts_industry_wage_bill_de.csv")
)

banking_files <- list(
  bls_credit_standards_mortgage = file.path(banking_dir, "ecb_bls_credit_standards_mortgage.csv"),
  bls_credit_standards_nfc = file.path(banking_dir, "ecb_bls_credit_standards_nfc.csv"),
  bls_credit_standards_consumer = file.path(banking_dir, "ecb_bls_credit_standards_consumer.csv"),
  bls_loan_demand_mortgage = file.path(banking_dir, "ecb_bls_loan_demand_mortgage.csv"),
  bls_loan_demand_nfc = file.path(banking_dir, "ecb_bls_loan_demand_nfc.csv"),
  bls_loan_demand_consumer = file.path(banking_dir, "ecb_bls_loan_demand_consumer.csv"),
  mir_mortgage_lending_rate = file.path(banking_dir, "ecb_mir_mortgage_lending_rate.csv"),
  mir_nfc_lending_rate = file.path(banking_dir, "ecb_mir_nfc_lending_rate.csv")
)

surprises <- read.csv(raw_files$surprises, stringsAsFactors = FALSE)
surprises$date <- as.Date(surprises$date)
surprises$event_count <- ifelse(is.na(surprises$event_count), 0L, as.integer(surprises$event_count))

shock_sum_cols <- grep("(_factor|weighted_composite)_monthly_sum$", names(surprises), value = TRUE)
for (column in shock_sum_cols) {
  zero_col <- paste0(column, "_zero")
  easing_col <- sub("_monthly_sum$", "_monthly_easing", column)
  surprises[[zero_col]] <- ifelse(surprises$event_count == 0L, 0, surprises[[column]])
  if (column == "qe_factor_monthly_sum") {
    surprises[[zero_col]] <- ifelse(surprises$date < as.Date("2014-01-01"), NA_real_, surprises[[zero_col]])
  }
  surprises[[easing_col]] <- -surprises[[zero_col]]
}

start_date <- as.Date("2005-01-01")
end_date <- max(surprises$date, na.rm = TRUE)
canonical_dates <- data.frame(
  date = month_end(seq(as.Date(format(start_date, "%Y-%m-01")), as.Date(format(end_date, "%Y-%m-01")), by = "1 month"))
)

# Wu-Xia keeps the shadow-rate stance visible before lift-off.
wx <- read_excel(raw_files$wx, sheet = 1, col_names = FALSE, .name_repair = "minimal")
names(wx) <- c("yyyymm", "wx_shadow_rate")
wx$yyyymm <- as.integer(wx$yyyymm)
wx$date <- month_end(as.Date(sprintf("%04d-%02d-01", wx$yyyymm %/% 100, wx$yyyymm %% 100)))
wx <- wx[, c("date", "wx_shadow_rate")]

# DFR controls for the conventional policy-rate path.
dfr <- read.csv(raw_files$dfr, stringsAsFactors = FALSE)
dfr <- data.frame(date = as.Date(dfr$observation_date), dfr = as.numeric(dfr$dfr))
dfr_m_last <- last_by_month(dfr, "dfr")
names(dfr_m_last)[2] <- "dfr_eop"
dfr_m_mean <- mean_by_month(dfr, "dfr")
names(dfr_m_mean)[2] <- "dfr_mavg"
dfr_m <- merge(dfr_m_last, dfr_m_mean, by = "date", all = TRUE)

# ECB assets capture balance-sheet liquidity at monthly frequency.
assets <- read.csv(raw_files$ecb_assets, stringsAsFactors = FALSE)
assets <- data.frame(date = as.Date(assets$observation_date), ecb_assets_ea_stock = as.numeric(assets$ecb_assets_ea_stock))
assets_m_last <- last_by_month(assets, "ecb_assets_ea_stock")
assets_m_mean <- mean_by_month(assets, "ecb_assets_ea_stock")
names(assets_m_mean)[2] <- "ecb_assets_ea_mavg"
assets_m <- merge(assets_m_last, assets_m_mean, by = "date", all = TRUE)
assets_m$ecb_assets_ea_trillions <- assets_m$ecb_assets_ea_stock / 1000000

# Household and NFC stocks keep household credit separate from productive credit.
hh <- read_ecb_portal(raw_files$hh_loans, "hh_loans_ea_stock")
nfc <- read_ecb_portal(raw_files$nfc_loans, "nfc_loans_ea_stock")

# Market and activity series give asset-price and demand context.
dax <- read.csv(raw_files$dax, stringsAsFactors = FALSE)
dax <- data.frame(date = month_end(as.Date(dax$Date)), dax_close = as.numeric(dax$Close), dax_volume = as.numeric(dax$Volume))

ret <- read_excel(raw_files$retail, sheet = "Sheet 1", col_names = FALSE, .name_repair = "minimal")
month_cells <- as.character(unlist(ret[10, ]))
month_cols <- which(grepl("^[0-9]{4}-[0-9]{2}$", month_cells))
de_row <- which(as.character(ret[[1]]) == "Germany" &
                  as.character(ret[[2]]) == "Retail trade, except of motor vehicles and motorcycles")[1]
retail_mom <- as_num(unlist(ret[de_row, month_cols]))
retail_dates <- month_end(as.Date(paste0(month_cells[month_cols], "-01")))
retail <- data.frame(date = retail_dates, retail_de_mom_pct = retail_mom)
retail$retail_de_chained_index <- 100 * cumprod(1 + retail$retail_de_mom_pct / 100)

hicp <- read_hicp_rows(raw_files$hicp)

# Monthly housing and wage proxies keep the comparison at observed frequency.
house_purchase_growth <- read_ecb_proxy_csv(proxy_files$house_purchase_growth, "ecb_house_purchase_growth_yoy")
house_purchase_pure_new <- read_ecb_proxy_csv(proxy_files$house_purchase_pure_new_loans, "ecb_house_purchase_pure_new_loans")
wage_tracker_headline <- read_ecb_proxy_csv(proxy_files$wage_tracker_headline, "ecb_wage_tracker_headline_yoy")
wage_tracker_ex_oneoffs <- read_ecb_proxy_csv(proxy_files$wage_tracker_ex_oneoffs, "ecb_wage_tracker_ex_oneoffs_yoy")
wage_tracker_unsmoothed <- read_ecb_proxy_csv(proxy_files$wage_tracker_unsmoothed_oneoffs, "ecb_wage_tracker_unsmoothed_oneoffs_yoy")
wage_tracker_coverage <- read_ecb_proxy_csv(proxy_files$wage_tracker_coverage, "ecb_wage_tracker_coverage_pct")
unemployment_ea21 <- read_monthly_proxy_csv(proxy_files$unemployment_ea21, "eurostat_unemployment_rate_ea21_sa")
employment_expectations_ea20 <- read_monthly_proxy_csv(proxy_files$employment_expectations_ea20, "eurostat_ecfin_eei_ea20")
services_employment_expectations_ea20 <- read_monthly_proxy_csv(proxy_files$services_employment_expectations_ea20, "eurostat_ecfin_services_employment_expectations_ea20")
ces_income_expectations <- read_ecb_proxy_csv(proxy_files$ces_income_expectations, "ecb_ces_income_expectations_12m_median")
ces_unemployment_expectations <- read_ecb_proxy_csv(proxy_files$ces_unemployment_expectations, "ecb_ces_unemployment_expectations_12m_median")
sts_industry_wage_bill_de <- read_monthly_proxy_csv(proxy_files$sts_industry_wage_bill_de, "eurostat_sts_industry_wage_bill_de")

# BLS observations stay sparse; filling them would blur the timing evidence.
bls_credit_standards_mortgage <- read_quarterly_proxy_csv(banking_files$bls_credit_standards_mortgage, "bls_credit_standards_mortgage_q_observed")
bls_credit_standards_nfc <- read_quarterly_proxy_csv(banking_files$bls_credit_standards_nfc, "bls_credit_standards_nfc_q_observed")
bls_credit_standards_consumer <- read_quarterly_proxy_csv(banking_files$bls_credit_standards_consumer, "bls_credit_standards_consumer_q_observed")
bls_loan_demand_mortgage <- read_quarterly_proxy_csv(banking_files$bls_loan_demand_mortgage, "bls_loan_demand_mortgage_q_observed")
bls_loan_demand_nfc <- read_quarterly_proxy_csv(banking_files$bls_loan_demand_nfc, "bls_loan_demand_nfc_q_observed")
bls_loan_demand_consumer <- read_quarterly_proxy_csv(banking_files$bls_loan_demand_consumer, "bls_loan_demand_consumer_q_observed")
mir_mortgage_lending_rate <- read_ecb_proxy_csv(banking_files$mir_mortgage_lending_rate, "ecb_mir_mortgage_lending_rate")
mir_nfc_lending_rate <- read_ecb_proxy_csv(banking_files$mir_nfc_lending_rate, "ecb_mir_nfc_lending_rate")

# Direct house-price and compensation series stay where they are observed.
hpi <- read.csv(raw_files$house_prices, stringsAsFactors = FALSE)
hpi <- data.frame(date = quarter_end(as.Date(hpi$observation_date)), house_price_de_q_observed = as_num(hpi$house_price_de))

comp <- read_ecb_portal(raw_files$compensation, "compensation_ea20_nominal_q_observed")
comp$date <- quarter_end(comp$date)

monthly <- merge_series(list(
  canonical_dates, surprises, wx, dfr_m, assets_m, hh, nfc, dax, retail, hicp,
  house_purchase_growth, house_purchase_pure_new,
  wage_tracker_headline, wage_tracker_ex_oneoffs, wage_tracker_unsmoothed,
  wage_tracker_coverage, unemployment_ea21, employment_expectations_ea20,
  services_employment_expectations_ea20, ces_income_expectations, ces_unemployment_expectations,
  sts_industry_wage_bill_de, bls_credit_standards_mortgage, bls_credit_standards_nfc,
  bls_credit_standards_consumer, bls_loan_demand_mortgage, bls_loan_demand_nfc,
  bls_loan_demand_consumer, mir_mortgage_lending_rate, mir_nfc_lending_rate,
  hpi, comp
))
monthly <- monthly[monthly$date %in% canonical_dates$date, ]
monthly <- monthly[order(monthly$date), ]

monthly$month <- format(monthly$date, "%Y-%m")
monthly$quarter <- paste0(format(monthly$date, "%Y"), "Q", ((as.integer(format(monthly$date, "%m")) - 1) %/% 3 + 1))
monthly$is_quarter_end_month <- as.integer(format(monthly$date, "%m") %in% c("03", "06", "09", "12"))
monthly$monthly_identification_sample <- monthly$date >= as.Date("2005-01-31") & monthly$date <= end_date
monthly$baseline_sample_monthly <- monthly$date >= as.Date("2005-01-31") & monthly$date <= as.Date("2022-06-30")
monthly$full_sample_monthly <- monthly$monthly_identification_sample

monthly$lp_monthly_regime <- ifelse(monthly$date <= as.Date("2014-01-31"), "pre_qe",
  ifelse(monthly$date <= as.Date("2019-12-31"), "qe",
    ifelse(monthly$date <= as.Date("2021-12-31"), "covid", "tightening")))

monthly$dax_real_de <- with(monthly, dax_close / hicp_de * 100)
monthly$hh_loans_ea_real <- with(monthly, hh_loans_ea_stock / hicp_ea20 * 100)
monthly$nfc_loans_ea_real <- with(monthly, nfc_loans_ea_stock / hicp_ea20 * 100)
monthly$house_price_de_real_q_observed <- with(monthly, house_price_de_q_observed / hicp_de * 100)
monthly$compensation_ea20_real_q_observed <- with(monthly, compensation_ea20_nominal_q_observed / hicp_ea20 * 100)

log_vars <- c(
  "ecb_assets_ea_stock", "ecb_assets_ea_mavg",
  "hh_loans_ea_stock", "hh_loans_ea_real",
  "nfc_loans_ea_stock", "nfc_loans_ea_real",
  "dax_close", "dax_real_de",
  "retail_de_chained_index",
  "ecb_house_purchase_pure_new_loans",
  "eurostat_sts_industry_wage_bill_de",
  "hicp_de", "hicp_ea20",
  "house_price_de_q_observed", "house_price_de_real_q_observed",
  "compensation_ea20_nominal_q_observed", "compensation_ea20_real_q_observed"
)
for (var in log_vars) {
  monthly <- add_log(monthly, var)
}

monthly$inflation_ea20_yoy_pct <- 100 * (monthly$ln_hicp_ea20 - lag_n(monthly$ln_hicp_ea20, 12))
monthly$inflation_de_yoy_pct <- 100 * (monthly$ln_hicp_de - lag_n(monthly$ln_hicp_de, 12))
monthly$ecb_wage_tracker_headline_real_yoy <- monthly$ecb_wage_tracker_headline_yoy - monthly$inflation_ea20_yoy_pct
monthly$ecb_wage_tracker_ex_oneoffs_real_yoy <- monthly$ecb_wage_tracker_ex_oneoffs_yoy - monthly$inflation_ea20_yoy_pct
monthly$ecb_wage_tracker_unsmoothed_oneoffs_real_yoy <- monthly$ecb_wage_tracker_unsmoothed_oneoffs_yoy - monthly$inflation_ea20_yoy_pct
monthly$ecb_wage_tracker_ex_oneoffs_real_yoy_ma3 <- rolling_mean_n(monthly$ecb_wage_tracker_ex_oneoffs_real_yoy, 3)
monthly$ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m <- monthly$ecb_wage_tracker_ex_oneoffs_real_yoy - lag_n(monthly$ecb_wage_tracker_ex_oneoffs_real_yoy, 3)
monthly$eurostat_labor_tightness_unemployment_inv <- -monthly$eurostat_unemployment_rate_ea21_sa
monthly$ecb_ces_real_income_expectations_12m_median <- monthly$ecb_ces_income_expectations_12m_median - monthly$inflation_ea20_yoy_pct
monthly$eurostat_sts_industry_wage_bill_de_yoy <- 100 * (log(monthly$eurostat_sts_industry_wage_bill_de) - lag_n(log(monthly$eurostat_sts_industry_wage_bill_de), 12))
monthly$eurostat_sts_industry_wage_bill_de_real_yoy <- monthly$eurostat_sts_industry_wage_bill_de_yoy - monthly$inflation_de_yoy_pct
monthly$ecb_mir_mortgage_lending_spread_dfr <- monthly$ecb_mir_mortgage_lending_rate - monthly$dfr_mavg
monthly$ecb_mir_nfc_lending_spread_dfr <- monthly$ecb_mir_nfc_lending_rate - monthly$dfr_mavg

diff_vars <- c(
  "wx_shadow_rate", "dfr_eop", "dfr_mavg",
  "ecb_assets_ea_stock", "ecb_assets_ea_mavg",
  "ecb_house_purchase_growth_yoy",
  "ecb_wage_tracker_headline_yoy",
  "ecb_wage_tracker_ex_oneoffs_yoy",
  "ecb_wage_tracker_unsmoothed_oneoffs_yoy",
  "inflation_ea20_yoy_pct",
  "inflation_de_yoy_pct",
  "ecb_wage_tracker_headline_real_yoy",
  "ecb_wage_tracker_ex_oneoffs_real_yoy",
  "ecb_wage_tracker_unsmoothed_oneoffs_real_yoy",
  "ecb_wage_tracker_ex_oneoffs_real_yoy_ma3",
  "ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m",
  "eurostat_unemployment_rate_ea21_sa",
  "eurostat_labor_tightness_unemployment_inv",
  "eurostat_ecfin_eei_ea20",
  "eurostat_ecfin_services_employment_expectations_ea20",
  "ecb_ces_income_expectations_12m_median",
  "ecb_ces_real_income_expectations_12m_median",
  "ecb_ces_unemployment_expectations_12m_median",
  "eurostat_sts_industry_wage_bill_de_yoy",
  "eurostat_sts_industry_wage_bill_de_real_yoy",
  "ecb_mir_mortgage_lending_rate",
  "ecb_mir_nfc_lending_rate",
  "ecb_mir_mortgage_lending_spread_dfr",
  "ecb_mir_nfc_lending_spread_dfr",
  "bls_credit_standards_mortgage_q_observed",
  "bls_credit_standards_nfc_q_observed",
  "bls_credit_standards_consumer_q_observed",
  "bls_loan_demand_mortgage_q_observed",
  "bls_loan_demand_nfc_q_observed",
  "bls_loan_demand_consumer_q_observed",
  paste0("ln_", c(
    "ecb_assets_ea_stock", "ecb_assets_ea_mavg",
    "hh_loans_ea_stock", "hh_loans_ea_real",
    "nfc_loans_ea_stock", "nfc_loans_ea_real",
    "dax_close", "dax_real_de",
    "retail_de_chained_index",
    "ecb_house_purchase_pure_new_loans",
    "hicp_de", "hicp_ea20",
    "house_price_de_real_q_observed",
    "compensation_ea20_real_q_observed"
  ))
)
for (var in diff_vars) {
  if (var %in% names(monthly)) monthly <- add_diff(monthly, var)
}

monthly$inflation_de_mom <- monthly$d_ln_hicp_de
monthly$inflation_ea20_mom <- monthly$d_ln_hicp_ea20
monthly$monthly_housing_available <- !is.na(monthly$house_price_de_real_q_observed)
monthly$monthly_compensation_available <- !is.na(monthly$compensation_ea20_real_q_observed)

priority_cols <- c(
  "date", "month", "quarter", "lp_monthly_regime", "monthly_identification_sample",
  "baseline_sample_monthly", "full_sample_monthly", "is_quarter_end_month",
  "event_count", "missing_month_flag",
  "timing_factor_monthly_sum_zero", "target_factor_monthly_sum_zero",
  "fg_factor_monthly_sum_zero", "qe_factor_monthly_sum_zero",
  "weighted_composite_monthly_sum_zero",
  "timing_factor_monthly_easing", "target_factor_monthly_easing",
  "fg_factor_monthly_easing", "qe_factor_monthly_easing",
  "weighted_composite_monthly_easing",
  "wx_shadow_rate", "d_wx_shadow_rate", "dfr_eop", "d_dfr_eop", "dfr_mavg", "d_dfr_mavg",
  "ecb_assets_ea_stock", "ecb_assets_ea_mavg", "ln_ecb_assets_ea_stock",
  "ln_ecb_assets_ea_mavg", "d_ecb_assets_ea_stock", "d_ecb_assets_ea_mavg",
  "d_ln_ecb_assets_ea_stock", "d_ln_ecb_assets_ea_mavg",
  "hh_loans_ea_stock", "ln_hh_loans_ea_stock", "hh_loans_ea_real",
  "ln_hh_loans_ea_real", "d_ln_hh_loans_ea_stock", "d_ln_hh_loans_ea_real",
  "nfc_loans_ea_stock", "ln_nfc_loans_ea_stock", "nfc_loans_ea_real",
  "ln_nfc_loans_ea_real", "d_ln_nfc_loans_ea_stock", "d_ln_nfc_loans_ea_real",
  "dax_close", "ln_dax_close", "dax_real_de", "ln_dax_real_de", "d_ln_dax_real_de",
  "retail_de_mom_pct", "retail_de_chained_index", "ln_retail_de_chained_index",
  "d_ln_retail_de_chained_index",
  "ecb_house_purchase_growth_yoy", "d_ecb_house_purchase_growth_yoy",
  "ecb_house_purchase_pure_new_loans", "ln_ecb_house_purchase_pure_new_loans",
  "d_ln_ecb_house_purchase_pure_new_loans",
  "ecb_wage_tracker_headline_yoy", "d_ecb_wage_tracker_headline_yoy",
  "ecb_wage_tracker_ex_oneoffs_yoy", "d_ecb_wage_tracker_ex_oneoffs_yoy",
  "ecb_wage_tracker_unsmoothed_oneoffs_yoy", "d_ecb_wage_tracker_unsmoothed_oneoffs_yoy",
  "inflation_ea20_yoy_pct", "d_inflation_ea20_yoy_pct",
  "ecb_wage_tracker_headline_real_yoy", "d_ecb_wage_tracker_headline_real_yoy",
  "ecb_wage_tracker_ex_oneoffs_real_yoy", "d_ecb_wage_tracker_ex_oneoffs_real_yoy",
  "ecb_wage_tracker_unsmoothed_oneoffs_real_yoy", "d_ecb_wage_tracker_unsmoothed_oneoffs_real_yoy",
  "ecb_wage_tracker_ex_oneoffs_real_yoy_ma3", "d_ecb_wage_tracker_ex_oneoffs_real_yoy_ma3",
  "ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m", "d_ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m",
  "ecb_wage_tracker_coverage_pct",
  "eurostat_unemployment_rate_ea21_sa", "eurostat_labor_tightness_unemployment_inv",
  "d_eurostat_unemployment_rate_ea21_sa", "d_eurostat_labor_tightness_unemployment_inv",
  "eurostat_ecfin_eei_ea20", "d_eurostat_ecfin_eei_ea20",
  "eurostat_ecfin_services_employment_expectations_ea20",
  "d_eurostat_ecfin_services_employment_expectations_ea20",
  "ecb_ces_income_expectations_12m_median", "d_ecb_ces_income_expectations_12m_median",
  "ecb_ces_real_income_expectations_12m_median", "d_ecb_ces_real_income_expectations_12m_median",
  "ecb_ces_unemployment_expectations_12m_median", "d_ecb_ces_unemployment_expectations_12m_median",
  "eurostat_sts_industry_wage_bill_de", "ln_eurostat_sts_industry_wage_bill_de",
  "eurostat_sts_industry_wage_bill_de_yoy", "eurostat_sts_industry_wage_bill_de_real_yoy",
  "d_eurostat_sts_industry_wage_bill_de_yoy", "d_eurostat_sts_industry_wage_bill_de_real_yoy",
  "ecb_mir_mortgage_lending_rate", "ecb_mir_nfc_lending_rate",
  "ecb_mir_mortgage_lending_spread_dfr", "ecb_mir_nfc_lending_spread_dfr",
  "d_ecb_mir_mortgage_lending_rate", "d_ecb_mir_nfc_lending_rate",
  "d_ecb_mir_mortgage_lending_spread_dfr", "d_ecb_mir_nfc_lending_spread_dfr",
  "bls_credit_standards_mortgage_q_observed", "bls_credit_standards_nfc_q_observed",
  "bls_credit_standards_consumer_q_observed", "bls_loan_demand_mortgage_q_observed",
  "bls_loan_demand_nfc_q_observed", "bls_loan_demand_consumer_q_observed",
  "hicp_de", "hicp_ea20", "hicp_ea", "inflation_de_mom", "inflation_ea20_mom",
  "inflation_de_yoy_pct", "d_inflation_de_yoy_pct",
  "house_price_de_q_observed", "house_price_de_real_q_observed",
  "ln_house_price_de_real_q_observed", "d_ln_house_price_de_real_q_observed",
  "compensation_ea20_nominal_q_observed", "compensation_ea20_real_q_observed",
  "ln_compensation_ea20_real_q_observed", "d_ln_compensation_ea20_real_q_observed",
  "monthly_housing_available", "monthly_compensation_available"
)
priority_cols <- priority_cols[priority_cols %in% names(monthly)]
remaining_cols <- setdiff(names(monthly), priority_cols)
monthly <- monthly[, c(priority_cols, remaining_cols)]

write.csv(monthly, file.path(processed_dir, "final_monthly_model_dataset.csv"), row.names = FALSE)

coverage <- data.frame(
  variable = names(monthly),
  observations = vapply(monthly, function(x) sum(!is.na(x)), integer(1)),
  missing = vapply(monthly, function(x) sum(is.na(x)), integer(1)),
  start = vapply(monthly, function(x) {
    idx <- which(!is.na(x))
    if (!length(idx)) return(NA_character_)
    as.character(monthly$date[min(idx)])
  }, character(1)),
  end = vapply(monthly, function(x) {
    idx <- which(!is.na(x))
    if (!length(idx)) return(NA_character_)
    as.character(monthly$date[max(idx)])
  }, character(1)),
  stringsAsFactors = FALSE
)
write.csv(coverage, file.path(processed_dir, "final_monthly_dataset_coverage.csv"), row.names = FALSE)

dictionary <- data.frame(
  variable = names(monthly),
  monthly_status = ifelse(grepl("_q_observed|monthly_housing_available|monthly_compensation_available", names(monthly)),
                          "quarterly_observed_only_no_interpolation",
                          "monthly_or_event_monthly"),
  identification_role = ifelse(grepl("factor_monthly|weighted_composite", names(monthly)),
                               "external_policy_surprise_candidate",
                               ifelse(grepl("^d_|^ln_|_rate|assets|loans|dax|retail|hicp|house_purchase|wage_tracker|unemployment|employment_expectations|eei|ces_|sts_industry_wage|mir_|bls_", names(monthly)),
                                      "monthly_model_candidate",
                                      "metadata")),
  notes = ifelse(grepl("_sum_zero$", names(monthly)),
                 "No-event months set to zero within source coverage; post-source months are excluded from the model date range.",
	                 ifelse(grepl("_q_observed", names(monthly)),
	                        "Observed only on quarter-end months; missing months are not interpolated.",
	                        ifelse(grepl("house_purchase|wage_tracker|unemployment|employment_expectations|eei|ces_|sts_industry_wage|mir_", names(monthly)),
	                               "Official monthly proxy candidate added without interpolation.",
	                               ""))),
  stringsAsFactors = FALSE
)
write.csv(dictionary, file.path(processed_dir, "monthly_variable_dictionary.csv"), row.names = FALSE)

cat("Wrote monthly dataset to ", file.path(processed_dir, "final_monthly_model_dataset.csv"), "\n", sep = "")
cat("Rows: ", nrow(monthly), " Columns: ", ncol(monthly), "\n", sep = "")
cat("Surprise source ends: ", as.character(end_date), "\n", sep = "")
