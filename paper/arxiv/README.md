# arXiv submission bundle

Everything needed to post the paper, the moment an endorsement lands.

**Upload `arxiv-submission.tar.gz`.** Regenerate it with `../build-arxiv.sh`
after any edit to `FINAL_PAPER.md`; the script fails if the source stops
rendering the approved 15 pages.

## Why this exists

`FINAL_PAPER.pdf` cannot be submitted. arXiv, verbatim: *"We do not accept dvi,
PS, or PDF created from TeX/LaTeX source"*, and ours is pandoc to tectonic, so
it is exactly that. arXiv wants the LaTeX source, which did not exist until
this bundle.

## What is in the tarball

```
FINAL_PAPER.tex
figures/fig1_result.pdf
figures/fig2_2x2.pdf
figures/fig3_powered.pdf
```

Four files, listed explicitly in the build script so nothing else can leak in.
PDF figures are fine: arXiv accepts JPEG, PNG or PDF with the standard graphics
package, and does no conversion of its own, so they are pre-converted here.

`_proof/` holds a local compile used only to check the page count. It is **not**
uploaded, per arXiv: *"do not include any associated auxiliary file or
intermediate or resulting output file, e.g. ... foo.pdf"*.

## Three arXiv rules this obeys (all verified 2026-08-13)

1. **No compiled PDF in the upload.** See above.
2. **No `\pdfoutput=1`.** arXiv: *"You should not use \pdfoutput to change the
   output format."* Pandoc's template already guards the engine with
   `\ifPDFTeX`, so the same source compiles under pdflatex and XeTeX.
3. **No `.bbl` needed.** The references are a plain list in the markdown, not a
   BibTeX run, so there is nothing for arXiv to resolve.

## Verified equivalence

The generated source reproduces the canonical build exactly: **15 pages**, and
the content bytes are identical to `../FINAL_PAPER.pdf` up to the metadata
trailer (only the timestamp and document ID differ). No wording, number or
figure changed in the conversion.

## Metadata for the submission form

Already decided, and recorded in the comment block at the top of
`FINAL_PAPER.md`:

| Field | Value |
|---|---|
| Primary category | **cs.AI** |
| Cross-list | **cs.LG, cs.CR** |
| Licence | **CC BY 4.0** |
| Title | Told or Enforced: Measuring When In-Context Contracts Substitute for Runtime Enforcement in Agent Harnesses |
| Author | Dom Colligan, Imperial College London |
| Abstract | paste the `## Abstract` section of `FINAL_PAPER.md`, unwrapped |

Submit from the arXiv account **`dtcolligan`** (dominic.colligan25@imperial.ac.uk),
which is the address the endorsement is attached to and the contact line in the
paper.

## Clearance

Posting does not conflict with the REALM submission. The REALM CFP allows a
public arXiv preprint provided the *submitted* PDF carries no de-anonymizing
links, which is already satisfied (its GitHub and benchmark links were
anonymized at submission). REALM is also non-archival, which is what preserves
the arXiv and ICLR routes in the first place.

## Source is public

arXiv publishes the uploaded source, not just the PDF. The generated `.tex` was
checked for leaked internal notes: the markdown's private comment block (build
provenance, verification notes) is dropped by pandoc, and the only remaining
comments are pandoc's own template boilerplate. **Re-check this after any
future regeneration** if new comments have been added to the markdown.
