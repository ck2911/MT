# Thesis LaTeX source

This folder compiles the thesis PDF. The code, data and the reproduction of the results are described in the [README one level up](../README.md).

The compiled thesis is already in `../deliverables/`. Compiling is only needed to check that the source produces it.

---

## 1. Requirements

A TeX distribution with XeLaTeX, biber and latexmk. Tested with TeX Live 2026 (XeTeX 0.999998, biber 2.21, latexmk 4.88).

| System | Install |
|---|---|
| macOS | MacTeX from [tug.org/mactex](https://www.tug.org/mactex/) |
| Windows | TeX Live from [tug.org/texlive](https://www.tug.org/texlive/), or MiKTeX from [miktex.org](https://miktex.org/) with "install missing packages on the fly" switched on |
| Linux | the `texlive-full` package |

The LaTeX packages used are all part of a full TeX Live installation. They are loaded in `preamble/packages.tex` and `preamble/diagrams.tex`. The main ones are `biblatex` (APA style, biber backend), `fontspec`, `hyperref`, `cleveref`, `booktabs`, `tabularx` and `tikz`.

**Font.** The text font is Times New Roman. If it is not installed, the build switches to TeX Gyre Termes, which ships with TeX Live. No font has to be installed by hand.

**Figures and tables.** The thesis reads its figures from `../results/final/figures/` and its tables from `tables/`. Both are in the repository, so the thesis compiles without running any Python or R. A full re-estimation rewrites both, so compile after re-estimating, not before.

---

## 2. Build

Open a terminal in this `LATEX` folder and run one of these:

| Situation | Command |
|---|---|
| macOS or Linux | `make pdf` |
| Windows, or no `make` | `latexmk -norc -xelatex -outdir=build main.tex` |
| No `latexmk` | Run in order: `mkdir build`, `xelatex -output-directory=build main.tex`, `biber --input-directory build --output-directory build main`, then `xelatex -output-directory=build main.tex` twice. |

The PDF appears at `build/main.pdf`. The build takes about 30 seconds and gives 81 pages with no undefined references or citations. All temporary files stay in `build/`.

| Command | Effect |
|---|---|
| `make clean` | Removes the temporary build files and keeps the PDF. |
| `make cleanall` | Removes the PDF as well. |

---

## 3. If something goes wrong

| You see | Do this |
|---|---|
| `xelatex`, `biber` or `latexmk: command not found` | TeX is not installed or not on PATH. Install it as in section 1 and open a new terminal. |
| `??` in the PDF, or "Citation undefined" | biber did not run. Run the build again. If it persists, see the next row. |
| biber stops right after "Found BibTeX data source" with no error message | biber's unpack cache is damaged. Run `biber --cache` to print its location, delete that folder, and build again. It is rebuilt automatically. |
| A missing `.sty` file (MiKTeX) | Allow MiKTeX to install missing packages, or install the package with the MiKTeX console. |
| Old content after a change | Run `make clean`, then `make pdf`. |

---

## 4. Layout

```text
LATEX/
  main.tex          entry point
  preamble/         packages, formatting, commands, metadata (title, author, dates)
  frontmatter/      title page, abbreviations, symbols, AI statement and declaration
  chapters/         chapters 1 to 8 and the appendix wrapper
  appendix/         appendix sections
  tables/           every table of the thesis, one file each
  bibliography/     references.bib
  scripts/          table generator and the two R figures
  build/            generated PDF and temporary files
```

Tables:

- `tables/gen_*.tex` are written by `scripts/generate_thesis_tables.py` from the CSV outputs in `../results/final/`. Do not edit them by hand. Run `python scripts/reproduce_thesis_tables.py` from the repository root to rewrite them.
- `tables/static_*.tex` are the five tables typeset directly in LaTeX: persistence synthesis, hypothesis assessment, artifact registry, data sources, software and tools.

Figures are included with the `\thesisfigure{file}{caption}{label}` macro from `preamble/commands.tex`, which reads the image directly from `../results/final/figures/`. No figure or table is copied into this folder.
