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

Result: **main text ends on page 8** in both builds (conclusion ends
right column, Limitations follows on the same page, references start
page 9; 13 pages total). The initial build ended 6 lines into page 9
with the sea2026 cut list exhausted; per the brief's stopping rule
that overrun was reported to Dom, who approved the two-sentence
close-out (Option A+B below) on 2026-07-23.

## Page-count trajectory (main-text end, anonymous build)

Measured by pypdf text extraction with column-aware coordinates, not
metadata. Page height positions: column top y=770, bottom y=69.

| Step | Main text ends |
|---|---|
| Uncut ACL port (figure* 0.72\textwidth, two table*, \small tables) | p9, y=338 (~32 lines into p9) |
| Family table* -> in-column table; 2x2 tabcolsep fix; figure* 0.6 | p9, y=473 |
| In-column tables to \footnotesize; topsep 4pt -> 2pt | p9, y=487 |
| Results figure figure* -> in-column figure at \linewidth | p9, y=679 |
| Verbatim re-break; topsep 1pt; table width -1pt (overfull fix) | p9, y=692 (6 lines into p9; STOP state, reported) |
| Option A+B applied (Dom-approved 2026-07-23) | **p8, right column, y=130** |
| Artifact-availability footnote added (Dom-approved 2026-07-27) | **p8, conclusion ends line 749**; Limitations heading pushed to p9 |

The 2026-07-27 footnote consumed the p8 slack that the Limitations
heading had been sitting in. The conclusion — the page-limited
boundary — still ends on page 8 at line 749. Limitations now opens
page 9, which is free space under *ACL policy, so the 8-page content
budget is still met.

## Restorations (brief step 2)

None. The port never had more than half a page free, so the
reverse-order restoration list (§4 texture, §5.2 precursor detail, §2
related-work detail) was never triggered.

## Cuts (brief step 3; Option A+B, Dom-approved 2026-07-23)

All five sea2026 cut-list items were already at their mandated end
state in the ported source (Figure 1 dropped; §2 compressed; §5.2 one
paragraph; §4 grader/reproducibility at ~2 sentences each; §8 MtG at
3 sentences). With the cut list exhausted and the budget unmet, the
brief's stopping rule applied: the 6-line overrun was reported to Dom
with two test-compiled options, and Dom approved both deletions
(neither on the protected list; neither carries a number or a
claim-discipline pair; both can return at camera-ready, which unlocks
a 9th content page):

- **A (§7, deleted):** "TeamBench's caution applies to us too: our
  scorer sees whether the specific guarded violation occurs, but an
  enforcement effect that shifted some finer channel while leaving
  the tracked violation unchanged would go undetected at this size."
  (Alone: still 2 lines over.)
- **B (§8, deleted):** "Mechanical Enforcement [arXiv:2605.14744]
  finds enforcement helping, but in a different domain: it scores
  decision-rationale quality under regulatory pressure, not
  tool-action compliance under benign use." (Its reference-list entry
  stays; the citation also remains live in §2's running text. §8's
  MtG residue now opens at "Mind the GAP ... is better read as
  convergent than contradictory.")

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

One further new sentence outside Limitations, added 2026-07-27 (Dom-approved):

- **C2 (new, footnote on the Contributions paragraph):** the paper
  claims "we release GovernedAgentBench" and refers to "the released
  repository" throughout, but the submission PDF carried no artifact
  link and no availability statement — a soft target on a workshop
  track that explicitly values data and simulation environments. The
  footnote is build-conditional via the existing `\REALManonymous`
  toggle, so it states availability without breaking blinding:
  - anonymous build: "The task suite, deterministic offline grader,
    analysis code, and git-pinned reference runtime are publicly
    released; the link is omitted here to preserve double-blind
    review."
  - preprint build: same sentence ending "...are publicly released at
    \gabrepo." (resolves to the real repository URL).

One further modification outside Limitations, forced by cut A:

- **M1 (Appendix C):** the TeamBench sentence's cross-reference
  " (Section 7)" removed, since the caution it pointed at no longer
  appears in §7: "...convergent evidence for the substitution shape
  in a different, multi-agent domain where the rule is never
  withheld, with a standing caution that aggregate parity can mask
  sub-metric enforcement value." The caution's content survives
  intact in this sentence itself.

Count: 2 new + 3 modified = 5 items against the ~15 budget. No other
prose differs from the sea2026 source (verified mechanically:
line-level diff of the two bodies leaves only the formatting classes
listed above, the two Dom-approved deletions, and these four items).

## Anonymization placeholders (anonymous build)

- `\gabrepo` = `https://anonymous.4open.science/r/PENDING` —
  **placeholder, and still UNUSED in the anonymous build.** As of the
  2026-07-27 C2 footnote the macro is referenced only in the preprint
  branch of `\gabavailability`, where it resolves to the real GitHub
  URL. The anonymous build's footnote states availability in words and
  emits no URL at all, so neither Dom's GitHub nor the `PENDING`
  placeholder appears in the compiled submission PDF (verified: zero
  URLs of any kind in the extracted text). Swapping in a real
  anonymized mirror is therefore optional, not blocking.
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
