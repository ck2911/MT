#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readxl)
  library(jsonlite)
})

root <- normalizePath(getwd(), mustWork = TRUE)
raw_dir <- file.path(root, "data", "raw", "eu_de")
processed_dir <- file.path(root, "data", "processed", "eu_de")
config_dir <- file.path(root, "config")

dir.create(processed_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(config_dir, recursive = TRUE, showWarnings = FALSE)

stop_if_missing <- function(path) {
  if (!file.exists(path)) stop("Missing required raw file: ", path, call. = FALSE)
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

last_by_quarter <- function(df, value_cols) {
  work <- df[, c("date", value_cols), drop = FALSE]
  work$qdate <- quarter_end(work$date)
  out <- do.call(rbind, lapply(split(work, work$qdate), function(z) {
    z <- z[order(z$date), , drop = FALSE]
    row <- z[nrow(z), c("qdate", value_cols), drop = FALSE]
    names(row)[1] <- "date"
    row
  }))
  rownames(out) <- NULL
  out
}

mean_by_quarter <- function(df, value_cols) {
  work <- df[, c("date", value_cols), drop = FALSE]
  work$date <- quarter_end(work$date)
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

raw_files <- list(
  wx = stop_if_missing(file.path(raw_dir, "1. Wu-Xia Euro Area Shadow Rate.xls")),
  ecb_assets = stop_if_missing(file.path(raw_dir, "ecb_central_bank_assets_weekly.csv")),
  dfr = stop_if_missing(file.path(raw_dir, "ecb_deposit_facility_rate_daily.csv")),
  hh_loans = stop_if_missing(file.path(raw_dir, "4. loans to euro area households granted by MFIs .xlsx")),
  nfc_loans = stop_if_missing(file.path(raw_dir, "5. Adjusted loans to euro area NFCs granted by MFIs.xlsx")),
  enterprise_standards = stop_if_missing(file.path(raw_dir, "6. Credit standards-Overall-Enterprise, Euro area, Quarterly.xlsx")),
  household_standards = stop_if_missing(file.path(raw_dir, "6.1 Credit standards-Household, Euro area, Quarterly.xlsx")),
  house_prices = stop_if_missing(file.path(raw_dir, "germany_residential_prices_quarterly.csv")),
  dax = stop_if_missing(file.path(raw_dir, "8. DAX 40.csv")),
  compensation = stop_if_missing(file.path(raw_dir, "9. Compensation per employee.xlsx")),
  retail = stop_if_missing(file.path(raw_dir, "10 volume of sales in wholesale and retail trade .xlsx")),
  hicp = stop_if_missing(file.path(raw_dir, "hicp_selected_cp00_de_ea20_ea.tsv"))
)

# Wu-Xia keeps the shadow-rate stance visible before the return to positive rates.
wx <- read_excel(raw_files$wx, sheet = 1, col_names = FALSE, .name_repair = "minimal")
names(wx) <- c("yyyymm", "wx_shadow_rate")
wx$yyyymm <- as.integer(wx$yyyymm)
wx$date <- month_end(as.Date(sprintf("%04d-%02d-01", wx$yyyymm %/% 100, wx$yyyymm %% 100)))
wx <- wx[, c("date", "wx_shadow_rate")]
wx_q <- mean_by_quarter(wx, "wx_shadow_rate")

# ECB assets proxy the balance-sheet/liquidity channel.
assets <- read.csv(raw_files$ecb_assets, stringsAsFactors = FALSE)
assets <- data.frame(date = as.Date(assets$observation_date), ecb_assets_ea_stock = as.numeric(assets$ecb_assets_ea_stock))
assets_q_last <- last_by_quarter(assets, "ecb_assets_ea_stock")
assets_q_mean <- mean_by_quarter(assets, "ecb_assets_ea_stock")
names(assets_q_mean)[2] <- "ecb_assets_ea_qavg"
assets_q <- merge(assets_q_last, assets_q_mean, by = "date", all = TRUE)
assets_q$ecb_assets_ea_trillions <- assets_q$ecb_assets_ea_stock / 1000000

# DFR is the conventional policy-rate benchmark.
dfr <- read.csv(raw_files$dfr, stringsAsFactors = FALSE)
dfr <- data.frame(date = as.Date(dfr$observation_date), dfr = as.numeric(dfr$dfr))
dfr_q_last <- last_by_quarter(dfr, "dfr")
names(dfr_q_last)[2] <- "dfr_eop"
dfr_q_mean <- mean_by_quarter(dfr, "dfr")
names(dfr_q_mean)[2] <- "dfr_qavg"
dfr_q <- merge(dfr_q_last, dfr_q_mean, by = "date", all = TRUE)

# Household and NFC stocks separate housing-adjacent credit from productive credit.
hh <- read_ecb_portal(raw_files$hh_loans, "hh_loans_ea_stock")
nfc <- read_ecb_portal(raw_files$nfc_loans, "nfc_loans_ea_stock")
loans_q <- merge(last_by_quarter(hh, "hh_loans_ea_stock"), last_by_quarter(nfc, "nfc_loans_ea_stock"), by = "date", all = TRUE)

# BLS standards add credit-supply pressure at their observed quarterly frequency.
enterprise <- read_ecb_portal(raw_files$enterprise_standards, "credit_standards_enterprise")
enterprise$date <- quarter_end(enterprise$date)
household <- read_ecb_portal(raw_files$household_standards, "credit_standards_household")
household$date <- quarter_end(household$date)

# German residential prices anchor the housing-side quarterly series.
hpi <- read.csv(raw_files$house_prices, stringsAsFactors = FALSE)
hpi <- data.frame(date = quarter_end(as.Date(hpi$observation_date)), house_price_de = as_num(hpi$house_price_de))

# DAX gives a market-price channel for comparison with housing and wages.
dax <- read.csv(raw_files$dax, stringsAsFactors = FALSE)
dax <- data.frame(date = as.Date(dax$Date), dax_close = as.numeric(dax$Close), dax_volume = as.numeric(dax$Volume))
dax_q <- last_by_quarter(dax, c("dax_close", "dax_volume"))

# Compensation per employee is kept quarterly rather than filled into monthly data.
comp <- read_ecb_portal(raw_files$compensation, "compensation_ea20_nominal")
comp$date <- quarter_end(comp$date)

# Retail volume is a demand-side check, not a main thesis outcome.
ret <- read_excel(raw_files$retail, sheet = "Sheet 1", col_names = FALSE, .name_repair = "minimal")
month_cells <- as.character(unlist(ret[10, ]))
month_cols <- which(grepl("^[0-9]{4}-[0-9]{2}$", month_cells))
de_row <- which(as.character(ret[[1]]) == "Germany" &
                  as.character(ret[[2]]) == "Retail trade, except of motor vehicles and motorcycles")[1]
retail_mom <- as_num(unlist(ret[de_row, month_cols]))
retail_dates <- month_end(as.Date(paste0(month_cells[month_cols], "-01")))
retail <- data.frame(date = retail_dates, retail_de_mom_pct = retail_mom)
retail$retail_de_chained_index <- 100 * cumprod(1 + retail$retail_de_mom_pct / 100)
retail_q <- mean_by_quarter(retail, c("retail_de_mom_pct", "retail_de_chained_index"))
names(retail_q)[2] <- "retail_de_mom_pct_qavg"
names(retail_q)[3] <- "retail_de_chained_index_qavg"

# HICP deflators put asset and income series in real terms.
hicp <- read_hicp_rows(raw_files$hicp)
hicp_q <- mean_by_quarter(hicp, c("hicp_de", "hicp_ea20", "hicp_ea"))

quarterly <- merge_series(list(
  wx_q, dfr_q, assets_q, loans_q, enterprise, household, hpi, comp, dax_q, retail_q, hicp_q
))
quarterly <- quarterly[order(quarterly$date), ]

canonical_dates <- data.frame(date = quarter_end(seq(as.Date("2005-01-01"), as.Date("2025-10-01"), by = "3 months")))
quarterly <- merge(canonical_dates, quarterly, by = "date", all.x = TRUE)
quarterly <- quarterly[order(quarterly$date), ]

quarterly$house_price_de_real <- with(quarterly, house_price_de / hicp_de * 100)
quarterly$compensation_ea20_real <- with(quarterly, compensation_ea20_nominal / hicp_ea20 * 100)
quarterly$dax_real_de <- with(quarterly, dax_close / hicp_de * 100)

log_vars <- c(
  "hh_loans_ea_stock",
  "nfc_loans_ea_stock",
  "ecb_assets_ea_stock",
  "house_price_de",
  "house_price_de_real",
  "compensation_ea20_nominal",
  "compensation_ea20_real",
  "dax_close",
  "dax_real_de",
  "hicp_de",
  "hicp_ea20"
)
for (var in log_vars) {
  quarterly[[paste0("ln_", var)]] <- ifelse(quarterly[[var]] > 0, log(quarterly[[var]]), NA_real_)
}

quarterly$quarter <- paste0(format(quarterly$date, "%Y"), "Q", ((as.integer(format(quarterly$date, "%m")) - 1) %/% 3 + 1))
quarterly$baseline_sample <- quarterly$date >= as.Date("2005-03-31") & quarterly$date <= as.Date("2022-06-30")
quarterly$robustness_sample <- quarterly$date >= as.Date("2005-03-31") & quarterly$date <= as.Date("2025-12-31")

quarterly$dummy_gfc_2008q4 <- as.integer(quarterly$date == as.Date("2008-12-31"))
quarterly$dummy_euro_crisis_2012q3 <- as.integer(quarterly$date == as.Date("2012-09-30"))
quarterly$dummy_qe_launch_2015q1 <- as.integer(quarterly$date == as.Date("2015-03-31"))
quarterly$dummy_covid_2020q2 <- as.integer(quarterly$date == as.Date("2020-06-30"))
quarterly$dummy_2022_tightening_q3 <- as.integer(quarterly$date == as.Date("2022-09-30"))
quarterly$regime_qe_2015_2022q2 <- as.integer(quarterly$date >= as.Date("2015-03-31") & quarterly$date <= as.Date("2022-06-30"))
quarterly$regime_post_covid <- as.integer(quarterly$date >= as.Date("2020-06-30"))
quarterly$regime_post_2022_tightening <- as.integer(quarterly$date >= as.Date("2022-09-30"))

column_order <- c(
  "date", "quarter", "baseline_sample", "robustness_sample",
  "wx_shadow_rate", "dfr_eop", "dfr_qavg",
  "ecb_assets_ea_stock", "ecb_assets_ea_qavg", "ecb_assets_ea_trillions", "ln_ecb_assets_ea_stock",
  "hh_loans_ea_stock", "ln_hh_loans_ea_stock",
  "nfc_loans_ea_stock", "ln_nfc_loans_ea_stock",
  "house_price_de", "house_price_de_real", "ln_house_price_de", "ln_house_price_de_real",
  "compensation_ea20_nominal", "compensation_ea20_real",
  "ln_compensation_ea20_nominal", "ln_compensation_ea20_real",
  "dax_close", "dax_real_de", "ln_dax_close", "ln_dax_real_de",
  "hicp_de", "hicp_ea20", "hicp_ea", "ln_hicp_de", "ln_hicp_ea20",
  "credit_standards_enterprise", "credit_standards_household",
  "retail_de_mom_pct_qavg", "retail_de_chained_index_qavg",
  "dummy_gfc_2008q4", "dummy_euro_crisis_2012q3", "dummy_qe_launch_2015q1",
  "dummy_covid_2020q2", "dummy_2022_tightening_q3",
  "regime_qe_2015_2022q2", "regime_post_covid", "regime_post_2022_tightening"
)
quarterly <- quarterly[, column_order]

write.csv(quarterly, file.path(processed_dir, "final_quarterly_model_dataset.csv"), row.names = FALSE)

dictionary <- data.frame(
  variable = column_order,
  role = c(
    "date_index", "date_label", "sample_flag", "sample_flag",
    "policy_baseline", "policy_robustness", "policy_robustness",
    "liquidity_core", "liquidity_robustness", "liquidity_scaled", "liquidity_core_log",
    "credit_household", "credit_household_log",
    "credit_productive", "credit_productive_log",
    "asset_housing_nominal", "asset_housing_real", "asset_housing_nominal_log", "asset_housing_real_log",
    "income_nominal", "income_real", "income_nominal_log", "income_real_log",
    "asset_equity_nominal", "asset_equity_real", "asset_equity_nominal_log", "asset_equity_real_log",
    "deflator_germany", "deflator_ea20", "deflator_ea", "deflator_germany_log", "deflator_ea20_log",
    "auxiliary_credit_supply", "auxiliary_credit_supply",
    "auxiliary_demand_growth", "diagnostic_constructed_index",
    "break_dummy", "break_dummy", "break_dummy", "break_dummy", "break_dummy",
    "regime_dummy", "regime_dummy", "regime_dummy"
  ),
  source = c(
    "constructed", "constructed", "constructed", "constructed",
    "Wu-Xia", "ECB policy-rate mirror", "ECB policy-rate mirror",
    "ECB balance-sheet mirror", "ECB balance-sheet mirror", "constructed", "constructed",
    "ECB Data Portal BSI", "constructed",
    "ECB Data Portal BSI", "constructed",
    "BIS residential-property-price mirror", "constructed", "constructed", "constructed",
    "ECB Data Portal MNA", "constructed", "constructed", "constructed",
    "CSV market data", "constructed", "constructed", "constructed",
    "Eurostat HICP", "Eurostat HICP", "Eurostat HICP", "constructed", "constructed",
    "ECB Bank Lending Survey", "ECB Bank Lending Survey",
    "Eurostat STS", "constructed",
    "constructed", "constructed", "constructed", "constructed", "constructed",
    "constructed", "constructed", "constructed"
  ),
  transformation = c(
    "quarter-end date", "YYYYQ label", "2005Q1-2022Q2", "2005Q1-2025Q4",
    "quarterly average of monthly level", "end-of-quarter daily level", "quarterly average daily level",
    "end-of-quarter weekly stock", "quarterly average weekly stock", "stock divided by 1,000,000", "natural log",
    "end-of-quarter monthly stock", "natural log",
    "end-of-quarter monthly stock", "natural log",
    "quarterly index level", "nominal HPI / German HICP * 100", "natural log", "natural log",
    "quarterly nominal index", "nominal compensation / EA20 HICP * 100", "natural log", "natural log",
    "quarter-end monthly close", "DAX close / German HICP * 100", "natural log", "natural log",
    "quarterly average monthly index", "quarterly average monthly index", "quarterly average monthly index", "natural log", "natural log",
    "quarterly net-tightening survey balance", "quarterly net-tightening survey balance",
    "quarterly average monthly percent change", "chain index from monthly percent changes",
    "1 in 2008Q4", "1 in 2012Q3", "1 in 2015Q1", "1 in 2020Q2", "1 in 2022Q3",
    "1 from 2015Q1 through 2022Q2", "1 from 2020Q2 onward", "1 from 2022Q3 onward"
  ),
  final_status = c(
    rep("metadata", 4),
    "baseline policy/shock variable", "robustness policy variable", "robustness policy variable",
    "core liquidity/QE variable", "robustness liquidity variable", "scaled descriptive variable", "core liquidity/QE variable",
    "core endogenous candidate", "core endogenous candidate",
    "core endogenous candidate", "core endogenous candidate",
    "diagnostic nominal variable", "core endogenous candidate", "diagnostic nominal variable", "core endogenous candidate",
    "diagnostic nominal variable", "core endogenous candidate", "diagnostic nominal variable", "core endogenous candidate",
    "expanded endogenous candidate", "expanded endogenous candidate", "expanded endogenous candidate", "expanded endogenous candidate",
    "deflator", "deflator", "deflator", "deflator", "deflator",
    "exogenous/auxiliary", "exogenous/auxiliary",
    "stationary robustness variable", "diagnostic only",
    rep("deterministic control", 8)
  ),
  stringsAsFactors = FALSE
)
write.csv(dictionary, file.path(processed_dir, "variable_dictionary.csv"), row.names = FALSE)

sample_windows <- list(
  baseline = list(start = "2005Q1", start_date = "2005-03-31", end = "2022Q2", end_date = "2022-06-30", policy_variable = "wx_shadow_rate"),
  robustness = list(start = "2005Q1", start_date = "2005-03-31", end = "2025Q4", end_date = "2025-12-31", policy_variable = "dfr_eop")
)
write_json(sample_windows, file.path(config_dir, "sample_windows.json"), pretty = TRUE, auto_unbox = TRUE)

breaks <- data.frame(
  break_id = c("gfc_2008q4", "euro_crisis_2012q3", "qe_launch_2015q1", "covid_2020q2", "tightening_2022q3"),
  date = c("2008-12-31", "2012-09-30", "2015-03-31", "2020-06-30", "2022-09-30"),
  dummy_variable = c("dummy_gfc_2008q4", "dummy_euro_crisis_2012q3", "dummy_qe_launch_2015q1", "dummy_covid_2020q2", "dummy_2022_tightening_q3"),
  motivation = c(
    "global financial crisis and ECB liquidity response",
    "euro-area sovereign crisis and OMT-era break risk",
    "public-sector purchase programme / QE launch regime marker",
    "COVID shock and PEPP liquidity expansion",
    "inflation shock and ECB tightening regime"
  ),
  use_in_baseline = c(TRUE, TRUE, TRUE, TRUE, FALSE),
  use_in_robustness = c(TRUE, TRUE, TRUE, TRUE, TRUE),
  stringsAsFactors = FALSE
)
write.csv(breaks, file.path(config_dir, "structural_breaks.csv"), row.names = FALSE)

model_blocks <- list(
  endogenous_core = c("ln_ecb_assets_ea_stock", "ln_hh_loans_ea_stock", "ln_nfc_loans_ea_stock", "ln_house_price_de_real", "ln_compensation_ea20_real"),
  endogenous_expanded = c("ln_ecb_assets_ea_stock", "ln_hh_loans_ea_stock", "ln_nfc_loans_ea_stock", "ln_house_price_de_real", "ln_compensation_ea20_real", "ln_dax_real_de"),
  exogenous_baseline = c("wx_shadow_rate", "credit_standards_enterprise", "credit_standards_household", "dummy_gfc_2008q4", "dummy_euro_crisis_2012q3", "dummy_qe_launch_2015q1", "dummy_covid_2020q2"),
  exogenous_robustness = c("dfr_eop", "credit_standards_enterprise", "credit_standards_household", "dummy_gfc_2008q4", "dummy_euro_crisis_2012q3", "dummy_qe_launch_2015q1", "dummy_covid_2020q2", "dummy_2022_tightening_q3"),
  external_instrument_placeholder = c("ecb_monetary_surprise")
)
write_json(model_blocks, file.path(config_dir, "model_blocks.json"), pretty = TRUE, auto_unbox = TRUE)

coverage <- data.frame(
  variable = names(quarterly),
  observations = vapply(quarterly, function(x) sum(!is.na(x)), integer(1)),
  missing = vapply(quarterly, function(x) sum(is.na(x)), integer(1)),
  start = vapply(quarterly, function(x) {
    idx <- which(!is.na(x))
    if (!length(idx)) return(NA_character_)
    as.character(quarterly$date[min(idx)])
  }, character(1)),
  end = vapply(quarterly, function(x) {
    idx <- which(!is.na(x))
    if (!length(idx)) return(NA_character_)
    as.character(quarterly$date[max(idx)])
  }, character(1)),
  stringsAsFactors = FALSE
)
write.csv(coverage, file.path(processed_dir, "final_dataset_coverage.csv"), row.names = FALSE)

cat("Wrote quarterly dataset to ", file.path(processed_dir, "final_quarterly_model_dataset.csv"), "\n", sep = "")
cat("Rows: ", nrow(quarterly), " Columns: ", ncol(quarterly), "\n", sep = "")
