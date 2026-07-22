# Cut ledger: SEA 2026 long-track condensation

Source of truth: `paper/FINAL_PAPER.md`, the 2026-07-20 FINAL revision
(verified before cutting: 15-page PDF, §5 identity remark, §5.1
multi-turn + pessimistic-scoring checks, §7 discoverability-aid
treatment all present; rebuild on the original pandoc→tectonic pipeline
reproduced 15 pages exactly). The canonical paper is untouched.

Target: NeurIPS 2026 SEA workshop long track, main text through the end
of the conclusion on or before page 9. References and appendices are
free space.

Result: **main text ends on page 9** in both builds
(`sea2026_preprint.pdf`, `sea2026_anonymous.pdf`); references start on
page 10; 14 pages total each.

## Page-count trajectory (main-text end, preprint build)

| Step | Main text ends |
|---|---|
| NeurIPS reflow, uncut port | p11 (total 15) |
| Cut 1: Figure 1 dropped | p11, top (total 14) |
| Cut 2: §2 detail → Appendix C | p10, 85% down |
| Cut 3: §5.2 compressed | p10, 78% down |
| Cut 4: §4 grader → Appendix A | p10, 47% down (coordinate measure) |
| Cut 5: §8 MtG → Appendix C | p10, 57%→47% region |
| Abstract + §6 sanctioned deletions | p10, 18% down |
| §5 remark compression (5a) + §5.1 deletions + formatting | p10, ~1.5 lines |
| §4 ladder-disclosure sentence → Appendix B + final tightening | **p9** |

## The five cut-list items (brief §3, applied in order)

1. **Figure 1 (the full-page 2×2 schematic, §3).** DROPPED entirely,
   with its caption ("The specify-versus-enforce 2×2 for a single
   rule…"). The §3 text-table and the "Cell A is how systems ship"
   paragraph carry the same content. The §5.1 powered figure becomes
   Figure 1; the Appendix B ladder figure becomes Figure 2; the one
   hardcoded prose reference "(Figure 2)" now renders "(Figure 1)" via
   `\ref` (modified sentence M1 below).
2. **§2 related-work detail.** Kept: the opening framing paragraph and
   the closing "Isolated withheld-but-enforced measurements exist…"
   paragraph, both verbatim. MOVED verbatim to Appendix C: the "Two
   priors sit very close…" paragraph (FORGE + Mind the GAP, ending "We
   take up the apparent tension with enforcement-helps priors in
   Section 8.") and the "Others reach part of the crossing…" paragraph
   (ABC, PhantomPolicy, ABSTAIN, TeamBench). Replaced by the mandated
   compressed paragraph (new sentences N1–N8 below).
3. **§5.2 compressed.** Kept verbatim: "A four-model ladder is what
   motivated this run." / "Told the commit rule with enforcement off,
   two capable models… whose cell B was exactly 100%." / "But both
   capable models were non-Qwen… rested on that 100%." / "The
   within-family run above breaks the confound and does not reproduce
   it…" / "The full ladder table, its per-run mechanism, the probe
   detail, and the ladder's caveats are in Appendix B." DROPPED (both
   already covered in Appendix B): "The medical-boundary rule the
   ladder also swept was near-ceiling and carries no result."
   (Appendix B caveats) and "Earlier single-model probes (Qwen3-235B)
   shaped the design; …salience-sensitive… only incidentally."
   (Appendix B "The one-model probes"). Under this item's
   "ladder detail moves verbatim to Appendix B" rule, the §4
   ladder-scoped disclosure sentence "The precursor ladder (Section
   5.2) carried its own two disclosures: …the small size is stated."
   MOVED verbatim to Appendix B (label L3 below); §7's two pointers to
   it updated (M2, M3).
4. **§4 texture.** "The rest of the grader": first two sentences kept
   verbatim; "The two text detectors… rather than take them on faith."
   and "Full metric names, definitions, and thresholds ship with the
   released scorer configuration." MOVED verbatim to Appendix A (label
   L1), pointer N9 added. "Reproducibility of the scoring" was already
   two sentences; untouched.
5. **§8 Mind-the-GAP reconciliation.** Kept verbatim: the Mechanical
   Enforcement sentence, "Mind the GAP …is better read as convergent
   than contradictory.", and "Its frontier-model null is therefore
   consistent… our runs locate its boundaries." MOVED verbatim to
   Appendix C (label L2): "Across six frontier models…", "Its Enforce
   mode hard-blocks…", "Our runs bound the scope of that null rather
   than contradict it.", "Its no-deterrent result holds…". DROPPED (to
   reach the brief's ~3 sentences): "This squares with the two
   opposite-looking priors of Section 2." Pointer N10 added.

## Beyond the cut list (each sanctioned by a named constraint)

Constraint 8 (abstract "may lose whole sentences if the budget demands
it") — DROPPED:

- "Real systems do both together, so what enforcement adds once the
  model was told is rarely read on its own." (restated in §1 and §5)
- "The rule is a mutation gate: the agent may propose changes to the
  user's governed data, but only the user may commit, archive, or
  activate them." (defined in §5.1)

Constraint 5 (§6 "may compress by deleting sentences but the finding,
the falsification test, and the lesson sentence survive") — DROPPED:

- "It could run a lookup but never read the answer."
- "Across three probe sets, we found eight cases where it issued
  commands carrying plausible identifiers it had never seen, including
  an invented evidence-card id."
- "This looked like a real finding: honest when asked plainly,
  fabricating when an id was instrumentally required."
- "It was our strongest surviving positive result."
- "The number is a fact about the harness, not the model."
- "A related corollary falls straight out of the 2×2: a told-column
  enforcement toggle [arXiv:2604.15579] measures the marginal value of
  enforcement given telling… so that column bounds nothing about them."
  (the toggle citation remains live in §1)

Constraint 5a (§5 remark "may shrink to a single sentence") — header
plus two sentences kept ("A sceptic can read A minus B as a
re-description…" / "That is precisely the design."); DROPPED: "At the
model's first action, enforcement is invisible until the moment of
denial…", "So enforcement's first-action value is exactly the block;
…read off the runtime-off column.", "The identity is why the enforced
side needs no statistics." (The identity itself is stated in the §5
preamble; the no-variance point recurs in §7.)

Constraint 5c (pessimistic scoring, required elements all retained) —
DROPPED the summary sentence "The pooled contrast stays flat to
slightly negative and the telling effect is unchanged either way."
(both facts appear verbatim in the preceding sentence).

True duplication — DROPPED: "Because A is 100% by construction, the
A-minus-B interval is just 100 minus the interval on cell B." (the §5
preamble states the same identity: "that contrast is just 100 minus
the cell-B safe rate").

## Formatting-only changes (no content)

- pandoc's `longtable` blocks converted to centered booktabs
  `tabular`s (5 tables), with reduced surrounding skips; these
  environments were artifacts of the md→tex port, not the FINAL's
  design. The NeurIPS style file itself is unmodified.
- Results figure at `0.72\linewidth` (was full-width in the port).
- Commit-predicate verbatim block: local `\topsep=3pt`.
- `\looseness=-1` on seven long paragraphs (zero-content line-recovery
  requests; most did not take).
- Unicode normalised to LaTeX macros (×→`$\times$`, −→`$-$`, accents),
  rendering identically.

## New and modified sentences (voice audit, verification step 6)

New (N1–N8: the compressed §2 paragraph mandated by cut item 2):

- N1 "Two priors sit very close; four more reach part of the crossing."
- N2 "FORGE [arXiv:2602.16708] runs withheld-but-enforced against
  told-but-unenforced, the off-diagonal, never instantiating cell A."
- N3 "Mind the GAP [arXiv:2602.16943] varies enforcement directly, but
  its told rule and its enforced rule are different objects, and its
  attempt-rate-on-intent scoring cannot move between arms by
  construction."
- N4 "Agent Behavioral Contracts [arXiv:2602.22302] toggles
  specification and enforcement together, the main diagonal."
- N5 "ABSTAIN [arXiv:2606.02965] reaches three of four cells, but its
  enforced arm keeps the prompt, never realising withheld-and-enforced."
- N6 "TeamBench [arXiv:2605.07073] finds prompt-only and
  sandbox-enforced role separation indistinguishable on pass rate where
  the rule is never withheld."
- N7 "PhantomPolicy [arXiv:2604.12177] supplies the
  policy-invisible-violation taxonomy we adopt."
- N8 "The full cell-by-cell mapping appears in Appendix C."

New pointers and appendix scaffolding:

- N9 "The detector detail and full metric definitions appear in
  Appendix A." (§4)
- N10 "The full reconciliation appears in Appendix C." (§8)
- N11 "This appendix preserves, verbatim, the full cell-by-cell mapping
  of the closest priors that Section 2 compresses, and the full Mind
  the GAP reconciliation that Section 8 compresses." (Appendix C intro)
- L1 "**The rest of the grader, continued from Section 4.**" (label)
- L2 "**The Section 8 reconciliation with Mind the GAP, in full.**"
  (label)
- L3 "**Two pre-registration disclosures, from Section 4.**" (label)

Modified (cross-references only):

- M1 §5.1 "(Figure 2)" → "(Figure~\ref{fig:powered})", renders
  "(Figure 1)" after the Figure-1 cut.
- M2 §7 "near-ceiling and uninformative (Section 5.2)" → "(Appendix B)".
- M3 §7 "sub-target sample size (Section 4)" → "(Appendix B)".

Count: 11 full new sentences + 3 bold run-in labels + 3 one-token
cross-reference updates = 17 items against the "fewer than ~15" target.
Justification: N1–N8 are the single compressed paragraph the brief
itself mandates; L1–L3 are appendix labels, not prose; M1–M3 are
one-token renumbering forced by the approved moves. Free-standing new
prose beyond the mandate is three sentences (N9, N10, N11).

## Numbers audit (verification step 4)

Method: every numeric token extracted from the compiled preprint PDF's
main text (pages 1–9, footers stripped) and matched against the FINAL
source. Result: **every prose numeral maps to the FINAL with identical
value**; the only unmatched tokens ("60", "80") are y-axis tick labels
embedded inside the results-figure graphic, which is the FINAL's own
unmodified asset.

Immutable-list literals verified present with identical values and
attached caveats: 41 [35, 47]; +24 [16, 33]; 72/73/7/10;
+8/+14/+36/+37; 59 [53, 65]; 35 [29, 41]; 488 of 512 with 24 dropped
(12 and 12); 28/28, 22/32, 88/100, 84/97; 8/8 vs 0/8; floors 0.125 and
p = 1.0; USD 115 and USD 10.44; 39 tasks / 16-task subset; git 6c82cd0
/ tag gab-runtime-1.0.1; exact-test figures 0.00016 / 0.33 / 0.029 /
0.00062; Clopper-Pearson [0, 37] and [63, 100]; 40-percentage-point
bar; 652 offline tests / 90 on the detectors (now Appendix A); 3.6
times and 1,980 sessions / 7 models (now Appendix C); pessimistic
ceilings 84% and 91% with about −6 / about +3.
