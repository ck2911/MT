SHELL := /bin/bash

LATEXMK := latexmk
MAIN := main.tex
PDF := main.pdf
BUILD_DIR := build

.PHONY: all pdf clean cleanall

all: pdf

pdf:
	@mkdir -p "$(BUILD_DIR)"
	$(LATEXMK) $(MAIN)
	@printf 'PDF written to %s\n' "$(PDF)"

clean:
	$(LATEXMK) -c $(MAIN)
	@find "$(BUILD_DIR)" -type f \( -name '*.aux' -o -name '*.bbl' -o -name '*.bcf' -o -name '*.blg' -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.lof' -o -name '*.log' -o -name '*.lot' -o -name '*.out' -o -name '*.run.xml' -o -name '*.synctex.gz' -o -name '*.toc' -o -name '*.xdv' \) -delete

cleanall: clean
	@rm -f "$(PDF)" "$(BUILD_DIR)/main.pdf"
