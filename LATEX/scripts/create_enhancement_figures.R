#!/usr/bin/env Rscript

# Enhancement figures for the thesis.
#
# Presentation only. Nothing here reads, computes, or alters an estimate: every
# value plotted is taken verbatim from the canonical CSV artifacts under
# results/final/.
#
# The visual language is a direct port of the matplotlib design system in
# src/viz/style.py, so the R figures and the Python figures read as one family:
# same serif face, same restrained navy/steel/brick/olive palette, same hairline
# horizontal-only grid, no in-figure titles (the LaTeX caption carries the
# title), frameless legend below the panel.
#
# Each figure keeps its existing canvas size in inches, because the audit script
# and the notebook figure registry depend on the file paths and the LaTeX
# include widths are fixed. Type and line weights are therefore expressed at
# print scale and multiplied by the ratio between the canvas width and the width
# the figure is actually printed at, so that a 8.5 pt tick label in style.py
# lands as a 8.5 pt tick label on the printed page.

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(tidyr)
  library(grid)
})

args <- commandArgs(trailingOnly = FALSE)
file_arg <- args[grepl("^--file=", args)]
if (length(file_arg) > 0) {
  script_dir <- dirname(normalizePath(sub("^--file=", "", file_arg[[1]])))
  repo_root <- normalizePath(file.path(script_dir, "..", ".."))
} else {
  repo_root <- normalizePath(getwd())
}

fig_dir <- file.path(repo_root, "results", "final", "figures", "enhancement")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

read_artifact <- function(...) {
  read.csv(file.path(repo_root, ...), stringsAsFactors = FALSE, check.names = FALSE)
}

# ----------------------------------------------------------------- palette
# Mirrors src/viz/style.py. Navy carries the estimate, steel carries
# uncertainty, brick is the single contrast accent, greys carry structure.
NAVY <- "#1F3B57"
NAVY_LIGHT <- "#41627F"
STEEL <- "#AFC2D1"
STEEL_FILL <- "#DCE5EC"
BRICK <- "#9C4722"
BRICK_LIGHT <- "#C08163"
OLIVE <- "#5F6B4A"
INK <- "#22282C"
GREY <- "#6E7B85"
GREY_LIGHT <- "#AAB4BB"
RULE <- "#3F484E"
GRID <- "#E7EBEE"

# Sequential ramp for matrices, light to deep navy. No rainbow.
SEQUENTIAL <- c("#F4F7F9", "#DCE5EC", "#B9CBD9", "#8EA9BF", "#5F82A0", "#3A5F7F", "#1F3B57")
# Diverging ramp, brick through neutral to navy, for signed matrices.
DIVERGING <- c("#9C4722", "#C08163", "#E3C8B8", "#F2F2F0", "#C3D2DD", "#7E9CB4", "#1F3B57")

# ------------------------------------------------------------------- sizes
TEXT_WIDTH_IN <- 6.30   # 16 cm text block
INCLUDE_FRACTION <- 0.80  # the single \thesisfigure include width
PRINTED_WIDTH_IN <- TEXT_WIDTH_IN * INCLUDE_FRACTION  # 5.04 in

FS_LABEL <- 9.5
FS_TICK <- 8.5
FS_LEGEND <- 8.5
FS_ANNOT <- 8.0
FS_SMALL <- 7.5

LW_MAIN <- 1.5
LW_THIN <- 0.7
LW_HAIR <- 0.55
MS_MAIN <- 3.6

DPI_PRINT <- 400        # raster resolution measured at printed size

serif_family <- function() {
  preferred <- c("Times New Roman", "STIX Two Text", "Nimbus Roman",
                 "TeX Gyre Termes", "Charter", "DejaVu Serif")
  available <- character(0)
  if (requireNamespace("systemfonts", quietly = TRUE)) {
    available <- unique(systemfonts::system_fonts()$family)
  }
  hit <- preferred[preferred %in% available]
  if (length(hit) > 0) hit[[1]] else "serif"
}
SERIF <- serif_family()

# Unit bridges. ggplot expresses line weights and glyph sizes in millimetre-ish
# units, so convert from the point sizes the design system is written in.
lw <- function(pt) pt / 2.134      # points -> linewidth

# matplotlib renders negative numbers with a typographic minus (U+2212).
# ggplot defaults to an ASCII hyphen, which reads visibly shorter.
minus_fmt <- function(x) sub('-', '\u2212', format(x, trim = TRUE), fixed = TRUE)
ts <- function(pt) pt / 2.845      # points -> geom_text / geom_point size
sw <- function(pt) pt / 1.4175     # points -> shape 21 stroke

# ------------------------------------------------------------------- theme
theme_thesis <- function(scale = 1) {
  theme_minimal(base_size = FS_TICK * scale, base_family = SERIF) +
    theme(
      text = element_text(family = SERIF, colour = INK),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank(),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA),
      panel.border = element_blank(),
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      panel.grid.major.y = element_line(colour = GRID, linewidth = lw(0.5 * scale)),
      panel.spacing = unit(10 * scale, "pt"),
      axis.title = element_text(size = FS_LABEL * scale, colour = INK, face = "plain"),
      axis.title.x = element_text(margin = margin(t = 5 * scale)),
      axis.title.y = element_text(margin = margin(r = 5 * scale)),
      axis.text = element_text(size = FS_TICK * scale, colour = INK),
      axis.text.x = element_text(margin = margin(t = 2.5 * scale)),
      axis.text.y = element_text(margin = margin(r = 2.5 * scale)),
      axis.line = element_line(colour = RULE, linewidth = lw(LW_HAIR * scale),
                               lineend = "square"),
      axis.ticks = element_line(colour = RULE, linewidth = lw(LW_HAIR * scale)),
      axis.ticks.length = unit(2.8 * scale, "pt"),
      strip.background = element_blank(),
      strip.text = element_text(size = FS_TICK * scale, colour = INK, face = "plain",
                                margin = margin(b = 4 * scale)),
      legend.position = "bottom",
      legend.title = element_blank(),
      legend.background = element_blank(),
      legend.key = element_blank(),
      legend.text = element_text(size = FS_LEGEND * scale, colour = INK),
      legend.key.height = unit(8 * scale, "pt"),
      legend.key.width = unit(13 * scale, "pt"),
      legend.margin = margin(t = 2 * scale),
      legend.box.spacing = unit(6 * scale, "pt"),
      plot.margin = margin(rep(5 * scale, 4))
    )
}

# Matrices carry no grid and no frame, the cells are the structure.
theme_thesis_matrix <- function(scale = 1) {
  theme_thesis(scale) +
    theme(
      panel.grid = element_blank(),
      axis.line = element_blank(),
      axis.ticks = element_blank(),
      axis.ticks.length = unit(2 * scale, "pt")
    )
}

# ------------------------------------------------------------------- output
# Vector device for the PDF twin. quartz embeds the requested system face
# directly, which keeps the PDF and the PNG on the same glyphs. cairo_pdf is the
# portable second choice. The base PostScript device is the last resort and only
# understands the built-in "Times" family, which is metrically the same face.
pdf_device <- function() {
  if (isTRUE(capabilities("aqua"))) {
    return(function(filename, width, height, bg = "white", ...) {
      grDevices::quartz(file = filename, type = "pdf", width = width, height = height,
                        family = SERIF, bg = bg)
    })
  }
  probe <- tempfile(fileext = ".pdf")
  cairo_ok <- isTRUE(capabilities("cairo")) &&
    !inherits(suppressWarnings(try(grDevices::cairo_pdf(probe), silent = TRUE)), "try-error")
  if (cairo_ok) {
    grDevices::dev.off()
    unlink(probe)
  }
  if (cairo_ok) {
    return(function(filename, width, height, bg = "white", ...) {
      grDevices::cairo_pdf(filename = filename, width = width, height = height,
                           family = SERIF, bg = bg)
    })
  }
  function(filename, width, height, bg = "white", ...) {
    grDevices::pdf(file = filename, width = width, height = height,
                   family = "Times", bg = bg, useDingbats = FALSE)
  }
}
PDF_DEVICE <- pdf_device()

# Writes the PNG the pipeline contract expects at the existing filename plus a
# vector PDF twin of identical physical size for LaTeX to include.
write_plot <- function(plot, filename, width, height, printed_width) {
  png_path <- file.path(fig_dir, filename)
  pdf_path <- sub("\\.png$", ".pdf", png_path)
  ggsave(
    filename = png_path, plot = plot,
    width = width, height = height,
    dpi = DPI_PRINT * printed_width / width,
    bg = "white"
  )
  ggsave(
    filename = pdf_path, plot = plot,
    width = width, height = height,
    device = PDF_DEVICE,
    bg = "white"
  )
  invisible(c(png_path, pdf_path))
}

selected <- c(
  "ecb_house_purchase_growth_yoy",
  "ln_ecb_house_purchase_pure_new_loans",
  "ecb_mir_mortgage_lending_spread_dfr",
  "ecb_mir_nfc_lending_spread_dfr",
  "ln_dax_real_de",
  "ln_ecb_assets_ea_stock",
  "ecb_wage_tracker_ex_oneoffs_real_yoy",
  "eurostat_ecfin_eei_ea20",
  "eurostat_sts_industry_wage_bill_de_real_yoy"
)

response_order <- c(
  "house-purchase lending growth",
  "pure new house-purchase loans",
  "mortgage lending spread",
  "NFC lending spread",
  "real DAX",
  "ECB assets",
  "real wage tracker excl. one-offs",
  "employment expectations",
  "German industry real wage bill growth"
)

block_for <- function(response) {
  case_when(
    response %in% c("ecb_house_purchase_growth_yoy", "ln_ecb_house_purchase_pure_new_loans") ~ "Housing finance",
    response %in% c("ecb_mir_mortgage_lending_spread_dfr", "ecb_mir_nfc_lending_spread_dfr") ~ "Lending conditions",
    response %in% c("ln_dax_real_de", "ln_ecb_assets_ea_stock") ~ "Market and liquidity",
    TRUE ~ "Compensation and labor"
  )
}

block_palette <- c(
  "Housing finance" = NAVY,
  "Lending conditions" = BRICK,
  "Market and liquidity" = OLIVE,
  "Compensation and labor" = GREY
)

# ------------------------------------------------ comparative IRF panel
irf <- read_artifact("results", "final", "tables", "normalized_irf_outputs.csv") %>%
  filter(shock == "target_factor_monthly_easing", response %in% selected) %>%
  mutate(
    block = block_for(response),
    response_label = factor(response_label, levels = response_order),
    horizon_months = as.numeric(horizon_months)
  )

irf_w <- PRINTED_WIDTH_IN
irf_h <- 3.6
irf_print <- PRINTED_WIDTH_IN
s <- irf_w / irf_print

comparative_irf <- ggplot(irf, aes(x = horizon_months, y = coefficient)) +
  geom_hline(yintercept = 0, colour = RULE, linewidth = lw(0.75 * s)) +
  geom_ribbon(aes(ymin = ci_90_low, ymax = ci_90_high, fill = block),
              alpha = 0.16, colour = NA) +
  geom_line(aes(colour = block), linewidth = lw(LW_MAIN * s)) +
  geom_point(aes(colour = block), shape = 21, fill = "white",
             size = ts(MS_MAIN * s), stroke = sw(1.1 * s)) +
  facet_wrap(~response_label, scales = "free_y", ncol = 3,
             labeller = label_wrap_gen(width = 26)) +
  scale_colour_manual(values = block_palette) +
  scale_fill_manual(values = block_palette) +
  # Ticks sit only at the estimated horizons and keep true linear spacing. In a
  # three-column panel h0 and h1 are too close to label both at print size, so
  # the label thinning is left to the guide while every tick mark stays.
  scale_x_continuous(breaks = c(0, 1, 3, 6, 12, 24),
                     guide = guide_axis(cap = "both", check.overlap = TRUE)) +
  scale_y_continuous(guide = guide_axis(cap = "both")) +
  guides(colour = guide_legend(nrow = 1), fill = guide_legend(nrow = 1)) +
  labs(x = "Horizon in months", y = "Normalized response") +
  theme_thesis(s)
write_plot(comparative_irf, "comparative_irf_panel.png", irf_w, irf_h, irf_print)

# -------------------------------------------------- sign persistence map
sign_score <- function(value) {
  case_when(
    value == "not_estimated" ~ "not estimated",
    grepl("^positive_p05", value) ~ "positive, p<0.05",
    grepl("^positive_p10", value) ~ "positive, p<0.10",
    grepl("^positive", value) ~ "positive, n.s.",
    grepl("^negative_p05", value) ~ "negative, p<0.05",
    grepl("^negative_p10", value) ~ "negative, p<0.10",
    grepl("^negative", value) ~ "negative, n.s.",
    TRUE ~ "not estimated"
  )
}

sign_label <- function(value) {
  case_when(
    value == "positive, p<0.05" ~ "++",
    value == "positive, p<0.10" ~ "+",
    value == "positive, n.s." ~ "+",
    value == "negative, p<0.05" ~ "--",
    value == "negative, p<0.10" ~ "-",
    value == "negative, n.s." ~ "-",
    TRUE ~ ""
  )
}

sign_heat <- read_artifact("results", "final", "uncertainty", "significance_heatmap.csv") %>%
  filter(response %in% selected) %>%
  pivot_longer(cols = starts_with("h"), names_to = "horizon", values_to = "classification") %>%
  mutate(
    response_label = factor(response_label, levels = rev(response_order)),
    horizon = factor(gsub("^h", "", horizon), levels = c("0", "1", "3", "6", "12", "24")),
    class = factor(
      sign_score(classification),
      levels = c(
        "negative, p<0.05", "negative, p<0.10", "negative, n.s.",
        "not estimated",
        "positive, n.s.", "positive, p<0.10", "positive, p<0.05"
      )
    ),
    label = sign_label(as.character(class)),
    label_colour = ifelse(as.character(class) %in% c("negative, p<0.05", "positive, p<0.05"),
                          "white", INK)
  )

sign_w <- PRINTED_WIDTH_IN
sign_h <- 2.98
sign_print <- PRINTED_WIDTH_IN
s <- sign_w / sign_print

sign_persistence <- ggplot(sign_heat, aes(x = horizon, y = response_label, fill = class)) +
  geom_tile(colour = "white", linewidth = lw(1.0 * s)) +
  geom_text(aes(label = label, colour = label_colour),
            size = ts(FS_ANNOT * s), family = SERIF) +
  scale_fill_manual(values = c(
    "negative, p<0.05" = DIVERGING[1],
    "negative, p<0.10" = DIVERGING[2],
    "negative, n.s." = DIVERGING[3],
    "not estimated" = DIVERGING[4],
    "positive, n.s." = DIVERGING[5],
    "positive, p<0.10" = DIVERGING[6],
    "positive, p<0.05" = DIVERGING[7]
  )) +
  scale_colour_identity() +
  scale_x_discrete(expand = c(0, 0)) +
  scale_y_discrete(expand = c(0, 0)) +
  guides(fill = guide_legend(nrow = 2, byrow = TRUE)) +
  labs(x = "Horizon in months", y = NULL) +
  theme_thesis_matrix(s)
write_plot(sign_persistence, "sign_persistence_map.png", sign_w, sign_h, sign_print)

# ---------------------------------------------- horizon durability matrix
persistence <- read_artifact("results", "final", "uncertainty", "persistence_confidence_matrix.csv") %>%
  filter(response %in% selected) %>%
  pivot_longer(cols = starts_with("h"), names_to = "horizon", values_to = "cum90") %>%
  mutate(
    response_label = factor(response_label, levels = rev(response_order)),
    horizon = factor(gsub("^h|_cum90$", "", horizon), levels = c("0", "1", "3", "6", "12", "24")),
    durability = ifelse(cum90 %in% c(TRUE, "True", "TRUE"), "90 percent interval excludes zero", "includes zero"),
    label = ifelse(durability == "90 percent interval excludes zero", "yes", "")
  )

dur_w <- PRINTED_WIDTH_IN
dur_h <- 2.88
dur_print <- PRINTED_WIDTH_IN
s <- dur_w / dur_print

durability_plot <- ggplot(persistence, aes(x = horizon, y = response_label, fill = durability)) +
  geom_tile(colour = "white", linewidth = lw(1.0 * s)) +
  geom_text(aes(label = label), colour = "white",
            size = ts(FS_ANNOT * s), family = SERIF) +
  scale_fill_manual(values = c(
    "90 percent interval excludes zero" = NAVY,
    "includes zero" = STEEL_FILL
  )) +
  scale_x_discrete(expand = c(0, 0)) +
  scale_y_discrete(expand = c(0, 0)) +
  guides(fill = guide_legend(nrow = 1)) +
  labs(x = "Horizon in months", y = NULL) +
  theme_thesis_matrix(s)
write_plot(durability_plot, "horizon_durability_matrix.png", dur_w, dur_h, dur_print)

# ------------------------------------------ robustness consistency matrix
stab <- read_artifact("results", "final", "stability", "monthly_cumulative_stability_long.csv") %>%
  filter(response %in% selected, horizon_months %in% c(6, 12, 24)) %>%
  mutate(
    response_label = factor(response_label, levels = rev(response_order)),
    filter = factor(
      sample_name,
      levels = c("full", "clean_events_only", "contaminated_events_only",
                 "exclude_covid", "exclude_crisis_windows",
                 "exclude_extreme_shock_outliers", "exclude_qe_launch"),
      labels = c("full", "clean", "contaminated", "ex-COVID",
                 "ex-crisis", "ex-outliers", "ex-QE launch")
    ),
    horizon_months = factor(paste0("h", horizon_months), levels = c("h6", "h12", "h24")),
    direction = case_when(
      cumulative_response > 0 ~ "positive",
      cumulative_response < 0 ~ "negative",
      TRUE ~ "mixed"
    )
  )

rob_w <- PRINTED_WIDTH_IN
rob_h <- 2.79
rob_print <- PRINTED_WIDTH_IN
s <- rob_w / rob_print

robustness_matrix <- ggplot(stab, aes(x = filter, y = response_label, fill = direction)) +
  geom_tile(colour = "white", linewidth = lw(0.9 * s)) +
  facet_wrap(~horizon_months, nrow = 1) +
  scale_fill_manual(values = c("positive" = NAVY, "negative" = BRICK, "mixed" = GREY_LIGHT)) +
  scale_x_discrete(expand = c(0, 0)) +
  scale_y_discrete(expand = c(0, 0)) +
  guides(fill = guide_legend(nrow = 1)) +
  labs(x = NULL, y = NULL) +
  theme_thesis_matrix(s) +
  theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5))
write_plot(robustness_matrix, "robustness_consistency_matrix.png", rob_w, rob_h, rob_print)

# ------------------------------------------------------ robustness summary
metrics <- read_artifact("results", "final", "stability", "monthly_stability_metrics.csv") %>%
  filter(response %in% selected) %>%
  mutate(response_label = factor(response_label, levels = response_order)) %>%
  select(response_label, sign_consistency, cumulative_direction_consistency) %>%
  pivot_longer(
    cols = c(sign_consistency, cumulative_direction_consistency),
    names_to = "metric",
    values_to = "value"
  ) %>%
  mutate(metric = factor(
    metric,
    levels = c("sign_consistency", "cumulative_direction_consistency"),
    labels = c("Sign consistency", "Cumulative direction consistency")
  ))

sum_w <- PRINTED_WIDTH_IN
sum_h <- 2.98
sum_print <- PRINTED_WIDTH_IN
s <- sum_w / sum_print

robustness_summary <- ggplot(metrics, aes(x = response_label, y = value, fill = metric)) +
  geom_col(position = position_dodge(width = 0.72), width = 0.62,
           colour = RULE, linewidth = lw(0.35 * s)) +
  coord_flip() +
  scale_y_continuous(limits = c(0, 1.05), breaks = seq(0, 1, 0.25),
                     expand = expansion(mult = c(0, 0.02))) +
  scale_fill_manual(values = c("Sign consistency" = NAVY,
                               "Cumulative direction consistency" = STEEL)) +
  guides(fill = guide_legend(nrow = 1)) +
  labs(x = NULL, y = "Share of consistent robustness cells") +
  theme_thesis(s) +
  theme(
    # Under coord_flip the hairline grid belongs to the rendered vertical
    # direction, which carries the share axis.
    panel.grid.major.y = element_blank(),
    panel.grid.major.x = element_line(colour = GRID, linewidth = lw(0.5 * s)),
    axis.line.y = element_line(colour = RULE, linewidth = lw(LW_HAIR * s)),
    axis.line.x = element_blank(),
    axis.ticks.y = element_blank()
  )
write_plot(robustness_summary, "robustness_summary.png", sum_w, sum_h, sum_print)

# --------------------------------------- conceptual transmission flow chart
flow_boxes <- data.frame(
  x = 1:5,
  y = 1,
  label = c(
    "ECB\npolicy-news\nsurprise",
    "Financial\nconditions and\nlending spreads",
    "Housing-finance\nresponses",
    "Affordability-\nsensitive access\npressure",
    "Compensation-\npressure\ndynamics"
  ),
  fill = c(NAVY, NAVY_LIGHT, BRICK, OLIVE, GREY)
)

flow_note <- paste0(
  "Conceptual contribution: persistent financial and housing-finance responses can\n",
  "amplify affordability-sensitive dynamics relative to compensation pressure."
)

# The canvas is cropped vertically relative to the earlier version because the
# removed title, subtitle and caption left a band of dead space under the boxes.
# The box geometry itself is unchanged, so the boxes keep their proportions.
flow_w <- PRINTED_WIDTH_IN
flow_h <- 1.16
flow_print <- PRINTED_WIDTH_IN
s <- flow_w / flow_print

flow <- ggplot(flow_boxes, aes(x = x, y = y)) +
  xlim(0.45, 5.55) +
  ylim(0.71, 1.52) +
  geom_rect(
    aes(xmin = x - 0.39, xmax = x + 0.39, ymin = 0.78, ymax = 1.22, fill = fill),
    colour = NA
  ) +
  geom_segment(
    data = data.frame(x = 1.40:4.40, xend = 1.60:4.60),
    aes(x = x, xend = xend, y = 1, yend = 1),
    inherit.aes = FALSE,
    arrow = arrow(type = "closed", length = unit(0.05 * s, "inches")),
    linewidth = lw(LW_THIN * s),
    colour = RULE
  ) +
  geom_text(aes(label = label), colour = "white", family = SERIF,
            size = ts(FS_SMALL * s), lineheight = 1.05) +
  annotate(
    "text",
    x = 0.61, y = 1.50, hjust = 0, vjust = 1,
    label = flow_note,
    family = SERIF,
    size = ts(FS_SMALL * s),
    lineheight = 1.25,
    colour = GREY
  ) +
  scale_fill_identity() +
  theme_void(base_family = SERIF, base_size = FS_TICK * s) +
  theme(
    text = element_text(family = SERIF, colour = INK),
    plot.title = element_blank(),
    plot.subtitle = element_blank(),
    plot.caption = element_blank(),
    plot.background = element_rect(fill = "white", colour = NA),
    plot.margin = margin(rep(5 * s, 4))
  )
write_plot(flow, "conceptual_affordability_transmission_flow.png", flow_w, flow_h, flow_print)

message("Created enhancement figures in ", fig_dir)
