# SEA 2026 long-track build report

## What this is

The SEA (Scaling Environments for Agents, NeurIPS 2026 workshop)
long-track version of *Told or Enforced*, condensed from the 2026-07-20
FINAL revision by deletion and verbatim relocation only. One shared
LaTeX source, two build configurations:

```
tectonic sea2026_preprint.tex     # non-anonymous (NeurIPS 'preprint' option)
tectonic sea2026_anonymous.tex    # double-blind ('dblblindworkshop' option)
```

Both compile with zero errors and zero overfull boxes (only cosmetic
underfull-box warnings, several from deliberate `\looseness` requests
and the references list). Both end the main text on **page 9**
(references start p10; 14 pages total), verified by pypdf page
iteration and text extraction, not file metadata.

## Source verification

`paper/FINAL_PAPER.md` rebuilt on its original pandoc→tectonic pipeline
to exactly 15 pages before any cutting; the three revision markers the
brief names (§5 "the identity is the finding, not a trick", §5.1
multi-turn + pessimistic-scoring checks, §7 discoverability-aid
treatment) all verified present. The canonical paper files are
byte-untouched (`git status` shows only `paper/sea2026/` as new).

## What was cut

All five cut-list items, in order, plus the deletions the constraints
themselves sanction (abstract sentences under constraint 8; §6
sentences, the §5 remark, and the 5c summary sentence under constraint
5). Full inventory, including every new/modified sentence quoted and
the page-count trajectory, is in `cut-ledger.md`. Nothing was
paraphrased; retained sentences are verbatim (checked mechanically:
every prose chunk of the SEA source matches the FINAL after
normalisation, apart from the ledgered new sentences).

Displaced content landed in: Appendix A (grader detail), Appendix B
(ladder pre-registration disclosures), and a new Appendix C (the full
related-work cell-by-cell mapping and the full Mind-the-GAP
reconciliation).

## Verification results

- **Page boundary:** main text ends p9 in both builds (pypdf).
- **Numbers audit:** every numeral in the cut PDF's main text maps to
  the FINAL with identical value; the only unmatched tokens are axis
  ticks inside the unmodified results-figure graphic. Mapping in
  `cut-ledger.md`.
- **Checklist audit:** all constraint-5 items (a–f) and every
  not-cuttable item verified present by exact quote match in the
  compiled PDF: the owned identity remark, the multi-turn check, the
  pessimistic bound (reported, not adopted), all five
  discoverability-aid elements (outcome-informed-for-the-ladder now in
  Appendix B, where the ladder lives), "indicative rather than exact",
  the single-mechanism scope, the harness-blindness
  finding/falsification/lesson, the same-team caveat, the scorer-edit
  disclosure, the case-study scope, the command-name leak, §8's
  relocation list, and the told-conditional note for evaluation.
- **Dead framings / vocabulary:** no "telling substitutes for enforcing
  in every family", "capability-gated substitution", or "enforcement
  adds nothing above a capability threshold"; no "reward", "training
  signal", or "RL environment" anywhere in the main text.
- **Cross-references:** all Section/Appendix/Figure references resolve
  (powered figure is now Figure 1, ladder figure Figure 2; the two §7
  pointers that followed moved content now read "Appendix B").
- **Anonymous build:** "Anonymous Author(s)" block, line numbers,
  "Submitted to … Do not distribute." footnote; no "Colligan",
  "Imperial", or "gab-run-archive" string anywhere; the same-team
  caveat reads "the benchmark's author"; the archive is "a repository
  release, name withheld for review". All identity strings sit behind
  macros in one preamble block (`\gabarchive`, `\runtimeauthorphrase`,
  `\gabrepo`), so pointing at an anonymized mirror later is a one-line
  change. The mirror itself is not created, per the brief.

## Judgment calls made (flagging per the brief)

1. **The cut list alone did not reach page 9** (it ended at p10, ~47%
   down). Rather than stop there, I used the deletions the brief's own
   constraints sanction: two abstract sentences (constraint 8), six §6
   sentences (constraint 5's explicit §6 allowance, finding +
   falsification + lesson intact), the §5 remark shrunk to header + two
   sentences (constraint 5a), the 5c summary sentence, one
   §5-preamble-duplicate sentence, and the §4 ladder-disclosure
   sentence moved verbatim to Appendix B under cut item 3's
   "ladder detail moves to Appendix B" rule. Plus formatting-only work
   (table environments, figure width, `\looseness`). The absolute STOP
   rule was never tripped because no paraphrase-compression occurred.
   If any of these go too far for your taste, each is one revert in
   `sea2026_main.tex`; the most opinionated three are the §6 corollary
   deletion, the §5 remark compression, and the §8 lead-sentence
   deletion.
2. **Cut-list numbering in the brief was garbled** (1, 4, 3, 4, 5); I
   applied it in listed order as instructed.
3. **§5.2's medical-boundary and probe sentences were deleted rather
   than kept** (both fully covered in Appendix B), which required the
   §7 pointer to move to "(Appendix B)".
4. **Anonymous build uses `dblblindworkshop`** (the 2026 template's
   double-blind workshop track option) with
   `\workshoptitle{Scaling Environments for Agents (SEA)}`, rather than
   the bare default (main-track). At submission stage the style prints
   "Submitted to 40th Conference…" without the workshop name; the name
   appears in `final` mode. If SEA turns out single-blind, change the
   option to `sglblindworkshop` (one word); camera-ready adds `final`.

## Open items for Dom

- **Style file: official, not a stopgap.** `neurips_2026.sty`
  (2026-01-29) obtained from the NeurIPS 2026 formatting zip at
  media.neurips.cc. No stopgap flag needed.
- **Anonymization pending:** both configurations are ready; pick one
  when SEA answers. Default deliverable is the preprint build.
- **NeurIPS paper checklist:** the main-track template ships a
  mandatory checklist section; workshop papers historically do not
  require it and SEA states nothing. Not added. If SEA asks for it,
  `checklist.tex` from the official zip is the starting point.
- **AI-assistance acknowledgment:** none included, per your rule and
  the NeurIPS 2026 handbook ("aid for editing purposes… does not need
  to be documented"). The conditional one-liner is specified in the
  brief if SEA later publishes its own disclosure requirement.
- **Figure legibility:** the results figure runs at 0.72\linewidth to
  meet the budget. It reads fine on screen; if you want it larger,
  roughly two more lines must come from somewhere (the §7 TeamBench
  caution sentence is the least-protected remaining candidate, which I
  deliberately did not touch).
- Warnings: cosmetic underfull boxes only; list via
  `tectonic --print sea2026_preprint.tex`.
