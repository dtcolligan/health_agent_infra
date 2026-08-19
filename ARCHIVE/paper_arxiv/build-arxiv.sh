#!/bin/sh
# Build the arXiv submission bundle from FINAL_PAPER.md.
#
# arXiv will not accept FINAL_PAPER.pdf: "We do not accept dvi, PS, or PDF
# created from TeX/LaTeX source" (info.arxiv.org/help/submit). It wants the
# LaTeX source, so this regenerates it and tars the exact set of files to
# upload.
#
# Two arXiv rules this script obeys, both verified 2026-08-13:
#   1. Do NOT ship the compiled PDF ("do not include any ... resulting output
#      file, e.g. foo.pdf"). The proof build goes to _proof/, outside the tar.
#   2. Do NOT add \pdfoutput=1 ("You should not use \pdfoutput to change the
#      output format"). Pandoc's template already guards the engine with
#      \ifPDFTeX, so the same source compiles under pdflatex and XeTeX.
#
# Figures are shipped as PDF, which arXiv accepts with the standard graphics
# package. It does no format conversion, so they must be pre-converted (they
# are; FINAL_PAPER.md references the .pdf variants).
#
# Verification: the generated .tex must reproduce the canonical 15-page build.
# The script fails if the page count drifts.

set -e
cd "$(dirname "$0")"

OUT=arxiv
TEX="$OUT/FINAL_PAPER.tex"
FIGS="fig1_result.pdf fig2_2x2.pdf fig3_powered.pdf"

mkdir -p "$OUT/figures" "$OUT/_proof"

# 1. Source. Same margin flag as build.sh: without it the paper sets 21pp.
pandoc FINAL_PAPER.md -s -o "$TEX" -V geometry:margin=1in

# 2. Figures, alongside the .tex so the relative paths in it resolve.
for f in $FIGS; do cp "figures/$f" "$OUT/figures/$f"; done

# 3. Proof build, kept OUT of the upload set.
( cd "$OUT" && tectonic -X compile FINAL_PAPER.tex --outdir _proof >/dev/null 2>&1 )

# 4. Gate: the source must still render the approved 15 pages.
PAGES=$(mdls -raw -name kMDItemNumberOfPages "$OUT/_proof/FINAL_PAPER.pdf" 2>/dev/null)
if [ "$PAGES" != "15" ]; then
  echo "FAIL: generated source renders $PAGES pages, expected 15." >&2
  exit 1
fi

# 5. The upload. Files listed explicitly so nothing else can leak in.
( cd "$OUT" && tar -czf arxiv-submission.tar.gz FINAL_PAPER.tex \
    figures/fig1_result.pdf figures/fig2_2x2.pdf figures/fig3_powered.pdf )

echo "OK: $PAGES pages. Upload $OUT/arxiv-submission.tar.gz"
tar -tzf "$OUT/arxiv-submission.tar.gz"
