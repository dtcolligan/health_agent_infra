# REALM @ EMNLP 2026 build report

## Headline: page budget NOT met — Dom decision needed

The ACL two-column port ends the main text **6 lines into page 9**
against the 8-page long-paper limit, in both builds. The sea2026 cut
list was already fully exhausted by the sea2026 build, so the brief's
stopping rule applies: nothing further was cut, nothing was
paraphrased. Two measured close-out options are in
`reformat-ledger.md` ("Overrun and measured options"):

- **Option A** (delete the §7 TeamBench caution sentence): still 2
  lines over — insufficient alone.
- **Option A+B** (also delete the §8 Mechanical Enforcement domain
  sentence): main text ends at the bottom of page 8 — **budget met
  exactly**. Neither sentence is protected by the brief's constraint
  4.5 list, but neither is in the sanctioned cut list either, so the
  choice is yours. Both were test-compiled; applying A+B is a
  two-sentence deletion plus one pointer fix in Appendix C.

Everything else about the build is done and verified.

## What this is

The REALM (Second Workshop for REsearch on Agent Language Models,
EMNLP 2026) long-paper version of *Told or Enforced*, ported from the
approved sea2026 9-page cut (S1--S4 insertions verified present before
porting). One shared LaTeX source, two builds:

```
tectonic realm2026_anonymous.tex   # ACL 'review' mode -- THE SUBMISSION ARTIFACT
tectonic realm2026_preprint.tex    # non-anonymous (ACL 'preprint' mode)
```

Both compile with zero errors and zero overfull boxes. REALM is
double-blind, so the anonymous build is the primary deliverable this
time; the preprint build is kept compiling for the camera-ready/arXiv
path.

## What changed relative to sea2026

- NeurIPS single-column -> official ACL 2026 two-column style
  (`acl.sty` diff-verified unmodified; `review` mode supplies the
  "Anonymous ACL submission" block, line numbers, and page numbers).
- All prose byte-identical to sea2026 except three ledgered items (C1
  new, V6/V9 modified), all inside the new ACL-mandatory unnumbered
  **Limitations** section assembled from existing caveat sentences
  (in-place originals untouched; the mild duplication is the ACL
  norm). Limitations sits after the conclusion, before References,
  and does not count toward the page limit.
- Formatting only: results figure moved into the column at
  `\linewidth`; family table from `table*` to an in-column
  `\footnotesize` table; verbatim block re-broken; `\looseness`
  requests removed; Appendix B ladder table to `table*`. Full list in
  `reformat-ledger.md`.
- No ethics statement (not required; none invented). No
  acknowledgments and no AI-assistance line in either build (your
  standing rule; the REALM CFP publishes no disclosure requirement —
  checked 2026-07-23).

## Verification results

- **Page boundary:** FAILS by 6 lines (the headline above). Verified
  by pypdf column-aware extraction in both builds, not metadata.
- **Prose fidelity:** line-level diff of realm vs sea2026 bodies
  leaves only ledgered formatting classes + C1/V6/V9. The seven
  `\looseness`-stripped paragraphs match byte-for-byte; the verbatim
  block is token-identical.
- **Numbers audit:** clean — no numeral dropped, none added, all
  immutable-list literals present with attached caveats in both
  builds (mapping in `reformat-ledger.md`).
- **Checklist audit:** 28/28 verbatim quotes present in BOTH compiled
  PDFs: must-survive (a)--(f) (identity remark owned, multi-turn
  check, pessimistic bound reported-not-adopted, all discoverability-
  aid elements incl. outcome-informed-for-the-ladder in Appendix B,
  "indicative rather than exact", single-mechanism scope), plus
  harness-blindness finding/falsification/lesson, same-team caveat,
  scorer-edit disclosure, case-study scope, command-name leak, §8
  relocation list, told-conditional note for evaluation, and S1--S4.
- **Dead framings / venue vocabulary:** none present. "reward",
  "training signal", "RL environment" absent ("training" occurs only
  inside the FINAL's own "post-training evaluation ... we do no
  training here" sentence).
- **Anonymous build:** "Anonymous ACL submission" block; line
  numbers; no "Colligan", "Imperial", "colligan25", "dtcolligan", or
  "gab-run-archive" string anywhere in the extracted text; PDF info
  dictionary carries no author/creator field (scrubbed via
  hypersetup, checked with pypdf). Same-team caveat reads "the
  benchmark's author"; archive is "a repository release, name
  withheld for review".
- **Cross-references:** no unresolved refs; the in-column results
  figure is Figure 1, the appendix ladder figure Figure 2, matching
  the sea2026 numbering, so the one `\ref` in prose renders
  identically.

## Judgment calls (flagging per the brief)

1. **Results figure is in-column at `\linewidth` (~3.0 in).** This
   was the single biggest budget lever (a `figure*` band costs double
   its height) and is why the overrun is 6 lines rather than ~20. The
   panels are smaller than the sea2026 rendering you already called
   borderline; if you want it larger, `figure*` at 0.6\textwidth
   costs ~14 lines — only viable together with content cuts beyond
   Option A+B.
2. **Limitations assembly:** I chose the seven caveat classes the
   brief names and stitched them with one new sentence (C1) and two
   single-token-scale modifications (V6, V9), plus one extra verbatim
   §5.1 sentence to keep "these intervals" from dangling. Nothing
   moved out of the main text.
3. **`review` vs manual anonymization:** the ACL style's `review`
   option handles the author block; I additionally scrubbed PDF
   metadata in the preamble (applies to both builds; harmless in the
   preprint).
4. **Test-compiles of options A and A+B** were done in place and
   reverted; the committed source is the STOP-state build.

## Open items for Dom

- **The overrun decision** (headline above). Deadline 5 Aug; QA
  target ~31 Jul.
- **Anonymized mirror:** `\gabrepo` in the anonymous build is
  `https://anonymous.4open.science/r/PENDING` — a placeholder, but
  currently **unused in running text**, so nothing broken ships
  either way. If you want an explicit repo link in the submission,
  create the mirror (needs your GitHub auth in a browser) and swap
  the macro; if not, no action needed.
- **Archival checkbox:** the CFP text describes long papers as
  "(archival)" while listing non-archival as an option at submission;
  confirm the non-archival choice actually exists on the OpenReview
  form for long papers before submitting.
- **Responsible-NLP-checklist notes** (submission-side, if the form
  asks): benchmark is self-built and public; no human subjects; no
  personal data (fixture-only); compute/cost already disclosed in the
  paper (USD 115 and USD 10.44); scientific-artifact license is MIT
  (repo) with the runtime git-pinned.
- **Camera-ready:** gets a 9th content page, so if REALM accepts, the
  A+B sentences (if cut) can come straight back; the preprint build
  already compiles for that path (switch `[preprint]` to `[final]`
  when the time comes).
