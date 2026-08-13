#!/bin/sh
# Rebuild FINAL_PAPER.pdf from FINAL_PAPER.md.
# Original build used xelatex; tectonic is equivalent and self-installing.
# The margin flag is load-bearing: without it the paper renders 21pp, not 15pp.
cd "$(dirname "$0")" || exit 1
pandoc FINAL_PAPER.md -o FINAL_PAPER.pdf --pdf-engine=tectonic -V geometry:margin=1in
