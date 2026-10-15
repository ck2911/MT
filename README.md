# Financial Intermediation and Asset Price Dynamics in the Post-COVID Monetary Expansion

M.Sc. thesis, Chirag Khanna, University of Tübingen, submitted 15 October 2026.

This repository holds everything behind the thesis: the data, the code, the results and the LaTeX source. This README covers the code and data. How to compile the thesis PDF is in [`LATEX/README.md`](LATEX/README.md).

The compiled thesis and all of its tables in one PDF are already in `deliverables/`, so nothing has to be run to read them.

---

## 1. Requirements

| Component | Needed for | Tested version | Minimum |
|---|---|---|---|
| Python | everything: estimation, figures, tables, notebook | 3.13.11 | 3.11 |
| Python packages | as above | pinned in `requirements.txt` (listed below) | the pinned versions |
| R | full re-estimation only: rebuilding the processed data from `data/raw/` and two figures | 4.4.2 | 4.4 |
| R packages | as above | readxl 1.4.3, dplyr 1.1.4, tidyr 1.3.1, jsonlite 1.8.9, ggplot2 3.5.1, systemfonts 1.1.0 | same |
| TeX Live | compiling the thesis and the tables PDF | 2026 (XeLaTeX, biber 2.21, latexmk 4.88) | see `LATEX/README.md` |

Python packages in `requirements.txt`: numpy 2.4.1, pandas 3.0.0, scipy 1.17.0, statsmodels 0.14.6, matplotlib 3.10.8, and for the notebook jupyterlab 4.6.4, nbconvert 7.17.1, ipykernel 7.4.0. Everything else the code imports is in the Python standard library.

`systemfonts` is optional. Without it the two R figures fall back to a default font.

No step needs internet after installation. All inputs are in `data/raw/`.

### Install Python and the packages

Install Python from [python.org](https://www.python.org/downloads/). On Windows, tick "Add python.exe to PATH". Then open a terminal in this folder:

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

All commands below assume this environment is active and the terminal is in this folder.

### Install R and the R packages (full re-estimation only)

1. Install R 4.4 or newer from [cran.r-project.org](https://cran.r-project.org/).
2. From an R prompt:

   ```r
   install.packages(c("readxl", "dplyr", "tidyr", "jsonlite", "ggplot2", "systemfonts"))
   ```

3. Check that `Rscript --version` works in a terminal. On Windows this usually means adding R's `bin` folder to PATH.

---

## 2. Reproduce the results

There are three levels. Each one runs on its own.

| Level | What it does | Needs | Command |
|---|---|---|---|
| A. Thesis tables | Writes every thesis table, numbered as in the thesis, from the stored results | Python (+ TeX for `--pdf`) | `python scripts/reproduce_thesis_tables.py --pdf` |
| B. Full re-estimation | Rebuilds the data from the raw files, re-estimates every model, redraws every figure and table, then audits the outputs | Python and R (+ TeX for `--pdf`) | `python scripts/reproduce_thesis_tables.py --full-rebuild --pdf` |
| C. Notebook | Walks through the results with commentary. Re-estimates first if R is installed | Python (+ R) | open `1. thesis_master_notebook.ipynb` and Run All |

### Full re-estimation

Level B. This is the complete reproduction from the raw data:

```bash
python scripts/reproduce_thesis_tables.py --full-rebuild --pdf
```

It first runs `scripts/run_full_pipeline.py`, which executes in order:

1. `Rscript src/data/build_final_dataset.R`: processed EU/DE data from the raw extracts
2. `python -m src.data.ecb_monetary_surprises`: monthly ECB surprise series
3. `Rscript src/data/build_monthly_model_dataset.R`: the monthly model dataset
4. `scripts/run_first_stage_tournament.py`: relevance diagnostics (Table 6.2)
5. `scripts/run_information_effect_screening.py`: event screen (Table 6.1)
6. `scripts/run_proxy_validation.py`: monthly proxy screening
7. `scripts/run_monthly_reduced_form_lp.py`: local projections, bootstraps, stability, regimes, sequential timing (Tables 5.1, 5.3, 5.4, 6.4, A.1)
8. `scripts/run_residual_diagnostics.py`: residual tests (Table 6.3)
9. `scripts/rebuild_figures.py` and `LATEX/scripts/create_enhancement_figures.R`: all thesis figures
10. `LATEX/scripts/generate_thesis_tables.py`: thesis tables
11. `scripts/final_empirical_audit.py`: integrity audit of the outputs

Then it writes the numbered tables as in level A. Every output in `results/final/` is overwritten in place. Temporary working folders are deleted before the audit, so a run leaves exactly one set of outputs.

`run_full_pipeline.py` can also be run on its own. It accepts `--skip-data` and `--skip-instrument` to reuse the processed data and shock series, and `--skip-audit`.

### Thesis tables (the "Do-file")

Level A. This estimates nothing and runs in seconds:

```bash
python scripts/reproduce_thesis_tables.py --pdf
```

It reads the stored outputs in `results/final/` and

1. runs `LATEX/scripts/generate_thesis_tables.py`, which writes the LaTeX tables the thesis compiles from (`LATEX/tables/gen_*.tex`),
2. derives the order and numbering of the tables from `LATEX/main.tex` and the chapter files, exactly as LaTeX assigns them,
3. writes one numbered file per table to `results/final/thesis_tables/` (for example `Table_4.1_descriptive_statistics.tex`) plus `MANIFEST.md`, which lists the caption and source files of every table,
4. with `--pdf`, typesets all tables into `results/final/thesis_tables/thesis_tables.pdf`, with the thesis bibliography. Table notes that refer to a thesis chapter take its number from the compiled thesis, so `--pdf` compiles the thesis once first if that has not been done.

Add `--strict` to stop with an error unless the numbering matches the compiled thesis exactly. It needs the compiled thesis (`LATEX/build/main.lot`), so run it after `--pdf` or after compiling the thesis.

### Notebook

Level C:

```bash
jupyter lab
```

Open `1. thesis_master_notebook.ipynb` and choose Run, then Run All Cells. In VS Code, open this folder, open the notebook, select the `.venv` interpreter as the kernel, then Run All.

| Your computer has | Run All does |
|---|---|
| Python only | Shows the stored results in `results/final/`, which are the results reported in the thesis. A one-line note says that re-estimation was skipped. |
| Python and R | Runs the full re-estimation first, then shows the results. |

To skip re-estimation on purpose, set `REBUILD_RESULTS = False` in the first code cell. To run the notebook without opening it:

```bash
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 "1. thesis_master_notebook.ipynb"
```

### Integrity check

```bash
python scripts/final_empirical_audit.py
```

Checks that every required output exists, that the columns match their documented contracts, that no stale output folders remain, and that the documentation stays within the interpretation boundary of the thesis. Level B runs it automatically.

### Tested

On 15 October 2026 a fresh clone of this repository was set up only from this README (new virtual environment from `requirements.txt`, R 4.4.2, TeX Live 2026, macOS) and every step passed:

| Step | Result | Time |
|---|---|---|
| Full re-estimation with tables PDF (`--full-rebuild --pdf`) | passed, audit passed | about 2 minutes |
| `--strict` numbering check | passed | seconds |
| Integrity check | passed | seconds |
| Thesis build (`LATEX/README.md`) | 81 pages, no undefined references or citations | about 30 seconds |
| Notebook with R | no errors, re-estimates first | about 1 minute |
| Notebook without R | no errors, shows the stored results | seconds |

The re-estimation reproduces every thesis table byte for byte. A run changes only timestamps, image metadata, and three diagnostic files that are not in the thesis, in the fourteenth significant digit.

---

## 3. Data

| File | Content |
|---|---|
| `data/processed/eu_de/final_monthly_model_dataset.csv` | The monthly dataset every estimate is based on: shock series, response variables, controls. |
| `data/processed/eu_de/monthly_variable_dictionary.csv` | Dictionary for that file: name, label, source, transformation. |
| `data/processed/eu_de/ecb_surprise_monthly.csv` | The monthly ECB surprise series. |
| `data/raw/eu_de/` | Raw extracts as downloaded on 15 and 16 May 2026 (ECB, Eurostat, BIS and ECB series via FRED, Wu-Xia shadow rate, DAX). Needed only for the full re-estimation. |
| `data/raw/eu_de/ecb_monetary_surprises/` | The high-frequency surprise inputs. `SOURCES.md` and `source_manifest.csv` there record the URL, vintage and checksum of each file. |
| `docs/data_source_verification.md` | Origin, series code and access date of every data file (also Table A.2 of the thesis). |

Several series have been revised by their providers since May 2026. Downloading them again would change the results, so the raw files are shipped exactly as they were used.

---

## 4. Where each thesis table comes from

| Table | Caption | Section | Produced by | Input |
|---|---|---|---|---|
| 4.1 | Descriptive statistics for the shock and the canonical response variables | 4.7 | generator | `data/processed/eu_de/final_monthly_model_dataset.csv` |
| 4.2 | Pairwise correlations among the shock and the canonical response variables | 4.7 | generator | `data/processed/eu_de/final_monthly_model_dataset.csv` |
| 5.1 | Ordered timing associations along the intermediation chain | 5.3 | generator | `results/final/mechanism/sequential_timing_outputs.csv` |
| 5.2 | Main synthesis table for persistence evidence | 5.6 | typeset (summary of Tables 5.3 and 5.4 and the stability metrics) | `results/final/tables/normalized_irf_outputs.csv`, `.../cumulative_persistence_table.csv`, `.../stability_metrics.csv` |
| 5.3 | Baseline monthly impulse responses to a one-standard-deviation ECB easing surprise | 5.6 | generator | `results/final/tables/normalized_irf_outputs.csv` |
| 5.4 | Accumulated responses at the medium and long horizons | 5.6 | generator | `results/final/tables/cumulative_persistence_table.csv` |
| 5.5 | Empirical assessment of the three thesis hypotheses | 5.7 | typeset (verdicts on Tables 5.1, 5.3 and 5.4) | as for 5.1, 5.3, 5.4 |
| 6.1 | Information-effect classification of ECB announcement events | 6.4 | generator | `results/final/diagnostics/information_effect_summary.csv` |
| 6.2 | Monthly first-stage relevance of the strongest candidate policy bridges | 6.5 | generator | `results/final/diagnostics/monthly_first_stage_tournament.csv` |
| 6.3 | Residual diagnostics for the baseline local projections | 6.6 | generator | `results/final/uncertainty/residual_diagnostics.csv` |
| 6.4 | Accumulated responses: 90 percent intervals from the dependence-aware bootstraps | 6.6 | generator | `results/final/uncertainty/dependence_aware_cumulative_intervals.csv` |
| A.1 | Peak response magnitude and timing | A.2 | generator | `results/final/tables/peak_response_table.csv` |
| A.2 | Data sources, series codes, and access dates | A.4 | typeset (see `docs/data_source_verification.md`) | `data/raw/eu_de/` |
| A.3 | Canonical pipeline artifacts underlying the reported results | A.5 | typeset (registry of file paths) | none |
| A.4 | Software and tools used in the preparation of this thesis | A.6 | typeset (software versions) | none |

"generator" means `LATEX/scripts/generate_thesis_tables.py`. "typeset" means the table is written directly in LaTeX (`LATEX/tables/static_*.tex`) because it holds no new estimates.

---

## 5. Folder map

| Path | What it holds |
|---|---|
| `1. thesis_master_notebook.ipynb` | The companion notebook. |
| `scripts/` | The pipeline runner, one script per estimation step, the table script and the audit. |
| `src/` | Data construction (`src/data/`), OLS with HAC errors (`src/lpiv/`), figure style (`src/viz/`), notebook helpers (`src/notebook_utils/`). |
| `data/` | Raw extracts and processed datasets (section 3). |
| `config/` | Variable configuration written by the data build. Do not edit by hand. |
| `results/final/` | Every figure, table, diagnostic and working note the thesis and the notebook use. Rewritten on each full run. |
| `docs/` | Data source verification. |
| `LATEX/` | Thesis source. See `LATEX/README.md`. |
| `deliverables/` | The compiled thesis and the tables PDF. |

---

## 6. If something goes wrong

| You see | Do this |
|---|---|
| `python3: command not found` (Windows) | Use `py -3` instead of `python3`, or reinstall Python with "Add to PATH" ticked. |
| `Activate.ps1 cannot be loaded` (Windows) | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again. |
| `ModuleNotFoundError` | The environment is not active. Activate `.venv` and run the command again. In Jupyter or VS Code, pick the `.venv` kernel. |
| `Could not locate THESIS_Model root` | Open the notebook from inside this folder, or set the environment variable `THESIS_MODEL_ROOT` to this folder. |
| Notebook note "Full re-estimation skipped" | Not an error. R or one of its packages is missing, so the stored results are shown. Install them as in section 1. |
| `Rscript: command not found` | R is not on PATH. See section 1. |
| `--strict needs the compiled thesis` | Compile the thesis first (`LATEX/README.md`), or run with `--pdf`, then run it again. |

---

## 7. Findings and interpretation boundary

Easing-signed ECB policy news moves house-purchase lending growth clearly at short and medium horizons, and lending margins move with it. Whether this is stronger than transmission to compensation depends on the measure: the euro-area wage tracker responds weakly and briefly, while the German industry wage bill responds durably. Financial-market responses are mixed. The negative real DAX response is read through an information-effects lens, as one possible interpretation.

The estimates pool easing and tightening surprises across 2005 to 2025, so they do not isolate the post-COVID cycle, which motivates the question rather than defining the sample. They do not show that easing benefits financial markets more than the real economy. The repository supports reduced-form evidence of heterogeneous monetary transmission. It does not identify household welfare effects, inequality, redistribution, exact house-price effects, or structural bank mediation.
