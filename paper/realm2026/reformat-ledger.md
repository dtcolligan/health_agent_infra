# Reformat ledger: REALM @ EMNLP 2026 (ACL format) port

Source of truth: `paper/sea2026/sea2026_main.tex`, the approved 9-page
workshop cut (verified before porting: all four author-approved S1--S4
scope insertions present at their sea2026 line positions). The prose
was carried over by file copy, so every retained sentence is
byte-identical to the sea2026 source; the full sea2026 cut-ledger
(including the S1--S4 amendment) is inherited unchanged and not
restated here. `paper/sea2026/` and the canonical `paper/FINAL_PAPER.*`
are untouched.

Target: REALM long-paper track, ACL 2026 style, main text through the
end of the conclusion on or before **page 8** at submission.
References, the unnumbered Limitations section, and appendices are
free space per the CFP and *ACL policy.

Result: **main text ends 6 lines into page 9** in both builds. The
sea2026 cut list was already exhausted by the sea2026 build itself, so
under the brief's stopping rule no further content was removed; the
overrun is reported to Dom with two measured close-out options (see
"Overrun and measured options" below). 13 pages total per build.

## Page-count trajectory (main-text end, anonymous build)

Measured by pypdf text extraction with column-aware coordinates, not
metadata. Page height positions: column top y=770, bottom y=69.

| Step | Main text ends |
|---|---|
| Uncut ACL port (figure* 0.72\textwidth, two table*, \small tables) | p9, y=338 (~32 lines into p9) |
| Family table* -> in-column table; 2x2 tabcolsep fix; figure* 0.6 | p9, y=473 |
| In-column tables to \footnotesize; topsep 4pt -> 2pt | p9, y=487 |
| Results figure figure* -> in-column figure at \linewidth | p9, y=679 |
| Verbatim re-break; topsep 1pt; table width -1pt (overfull fix) | **p9, y=692 (6 lines into p9)** |

## Restorations (brief step 2)

None. The port never had more than half a page free, so the
reverse-order restoration list (§4 texture, §5.2 precursor detail, §2
related-work detail) was never triggered.

## Cuts (brief step 3)

None. All five sea2026 cut-list items were already at their mandated
end state in the ported source (Figure 1 dropped; §2 compressed; §5.2
one paragraph; §4 grader/reproducibility at ~2 sentences each; §8 MtG
at 3 sentences). With the cut list exhausted and the budget unmet, the
brief's stopping rule applies: no paraphrase-compression, report the
overrun.

## Overrun and measured options (NOT applied; Dom's call)

Both were test-compiled and reverted; the committed source contains
neither deletion.

- **Option A** — delete the §7 sentence "TeamBench's caution applies
  to us too: our scorer sees whether the specific guarded violation
  occurs, but an enforcement effect that shifted some finer channel
  while leaving the tracked violation unchanged would go undetected at
  this size." (the sentence the sea2026 report already named
  least-protected). Measured result: main text ends **2 lines into
  page 9** — still over. Side effect if taken: Appendix C's pointer
  "...with a standing caution (Section 7)..." would need a ledgered
  edit.
- **Option A+B** — additionally delete the §8 sentence "Mechanical
  Enforcement [arXiv:2605.14744] finds enforcement helping, but in a
  different domain: it scores decision-rationale quality under
  regulatory pressure, not tool-action compliance under benign use."
  Measured result: main text ends at the **bottom of page 8** — budget
  met exactly. Side effect: the Mechanical Enforcement citation drops
  out of running text (its reference-list entry stays; the §8 MtG
  reconciliation residue then opens at "Mind the GAP ... is better
  read as convergent than contradictory.").

## Formatting-only changes (no content)

- Document class/preamble: NeurIPS preamble replaced by the ACL 2026
  one (`\documentclass[11pt]{article}` + `\usepackage[review]{acl}` /
  `[preprint]{acl}` via the `\REALManonymous` toggle; template-listed
  packages times, latexsym, inconsolata added; NeurIPS-only packages
  dropped). `acl.sty` is the official file, unmodified (diff-verified
  against github.com/acl-org/acl-style-files).
- The seven `\looseness=-1` requests (sea2026 page-budget artifacts)
  removed; the prefixed paragraphs are otherwise byte-identical.
- Results figure: `figure*` band converted to an in-column `figure` at
  `\linewidth` (the band cost double its height in two-column layout).
- Family results table and 2x2 / capability / governance tables:
  in-column at `\footnotesize`, `\tabcolsep` 3pt, explicit p-column
  widths for the five-column family table; governance-table column
  ratio 0.5/0.5 -> 0.3/0.7. Header and cell text unchanged.
- Appendix B ladder table: pandoc minipage tabular -> full-width
  booktabs `table*` (lands in free appendix space).
- Commit-predicate verbatim block: re-broken to six lines at
  `\footnotesize` (token-identical; whitespace only).
- `\topsep` on the inline blocks 4pt/3pt -> 1pt.
- PDF metadata scrubbed via `\hypersetup{pdfauthor={},...}` (review
  build carries no author identity in the info dictionary; verified
  with pypdf).

## New and modified sentences (all in the assembled Limitations section)

The ACL-mandatory unnumbered Limitations section (after the
conclusion, before References; excluded from the page limit) is
assembled from eleven sentences copied verbatim from §4, §5.1, and §7
— the in-place originals do not move — plus:

- **C1 (new):** "The load-bearing limitations of this study are stated
  beside the claims they qualify, in Sections 4, 5, and 7; this
  section collects them."
- **V6 (modified):** the §4 command-name-leak sentence reused with its
  leading "First, " dropped (it was the first item of a two-item list
  in §4): "Even withheld, the prompt still lists command names, so the
  model retains a hint, and B-vs-D and C-vs-D are therefore lower
  bounds on the effect of telling."
- **V9 (modified):** the §5.1 indicative-intervals sentence reused
  with its context-bound "(below)" changed to "(Section 5.1)": "The
  repeat-dependence caveat that keeps the within-family capability
  contrast descriptive (Section 5.1) applies to these intervals too,
  so we read them as indicative rather than exact."

Count: 1 new + 2 modified = 3 items against the ~15 budget. No other
prose differs from the sea2026 source (verified mechanically:
line-level diff of the two bodies leaves only the formatting classes
listed above plus these three items).

## Anonymization placeholders (anonymous build)

- `\gabrepo` = `https://anonymous.4open.science/r/PENDING` —
  **placeholder; the real anonymized mirror URL must be swapped in
  before submission if a repo link is added.** The macro is currently
  UNUSED in running text (inherited sea2026 design), so no link to
  Dom's GitHub — and no placeholder text — appears in the compiled
  submission PDF.
- `\gabarchive` = "a repository release, name withheld for review,
  with SHA-256 checksums" (sentence-form neutralization, inherited
  from sea2026; appears in Appendix A).
- `\runtimeauthorphrase` = "the benchmark's author" (in §4 and the
  Limitations copy of the same-team sentence).

## Numbers audit

Method: every numeric token extracted from the new PDFs and compared
against the sea2026 PDFs. Main text (through Limitations): no numeral
present in the sea2026 main text is missing, and no new numeral
appears (the only realm-side extras in the page window were reference
years and Appendix A exact-test figures pulled in by the page
boundary, all present in sea2026's own appendices). Immutable-list
literals verified present with identical values and attached caveats
in both builds: 41 [35, 47]; +24 [16, 33]; 72/73/7/10; +8/+14/+36/+37;
59 [53, 65]; 35 [29, 41]; 488 of 512 with 24 dropped (12 and 12);
28/28, 22/32, 88/100, 84/97; 8/8 vs 0/8; floors 0.125 and p = 1.0; USD
115 and USD 10.44; 39 tasks / 16-task subset; git 6c82cd0 / tag
gab-runtime-1.0.1; exact tests 0.00016 / 0.33 / 0.029 / 0.00062;
Clopper-Pearson [0, 37] and [63, 100]; 40-percentage-point bar; 652
offline tests / 90 on the detectors; 3.6 times and 1,980 sessions / 7
models; pessimistic ceilings 84% and 91%.
