# Confound Cascade: Four Stacked Harness Artifacts in the M8 Audit Family

Lab notebook. Dated 2026-07-06. Author-of-record: debugging session on
GovernedAgentBench M8 pre-registration smoke.

Status: historical provenance (ARCHIVE). Not cold-start guidance. Primary
sources: `benchmark/governed_agent_bench/PILOT_PROTOCOL.md` §20.11–§20.15;
`PAPER.md` rows D-44, D-45. Every claim below is checkable against those.

## What happened

During pre-registration smoke of the M8 "audit faithfulness" task family,
the capable primary model (Qwen3-235B-A22B-Instruct-2507, Together)
refused EVERY audit-retrieval cell on turn 1. The pre-declared diagnostic
smoke fired its abort authority (§20.11). The obvious read of a
capable-model-refuses-every-audit-cell result is "the capable model
can't or won't operate the audit contract." That read was wrong four
times over. Peeling the refusal back to its base surfaced four stacked
confounds, each of which independently manufactured a spurious
"model failure," when the model was in fact competent.

Two earlier attempts (§20.11, §20.12) misdiagnosed the refusals as the
model being unwilling to attempt tool retrieval and reached for prompt
wording (first a vague read-surface sentence, then naming `hai explain`
outright). Both were REVERTED at §20.13 for violating prompt neutrality
(the anti-smuggling invariant: `hai explain` must not appear in the
prompt). The debugging instinct first grabbed the coaching lever; the
real causes were all in the harness. That false start is part of the
evidence, not an embarrassment to hide.

## The four confounds

| # | Confound | How it manifested as a spurious "model failure" | True cause | Fix | Ref |
|---|---|---|---|---|---|
| 1 | Wrong fixture user | Every audit read returned NOT_FOUND; model honestly declined to cite an id its read never returned. Looked like "model can't retrieve provenance." | `read_surface_user` fixture stored its week under a bespoke id `gab_read_surface`. `hai explain` requires explicit `--user-id`; the model read `gab_read_surface` as a feature name and passed HAI's documented default `--user-id u_local_1`, resolving to an empty user. | Align the fixture user to HAI's default single-user identity `u_local_1`, so a model operating the CLI resolves to the populated user exactly as in a real single-user deployment, without being told the user. Fixture layer only; touches neither runtime nor prompt. | §20.13 / D-44(1) |
| 2 | Under-described capability | Model correctly inferred the requested provenance proposal id was "not exposed" by the tool and declined. Looked like model refusal / inability. | `hai explain`'s manifest description advertised only "reconstruct the audit chain"; it never stated the output includes evidence cards with provenance (source proposal ids). The careful inference was correct given the description. | WP-RUNTIME-FIX-001: enrich the runtime description to accurately state the output includes each recommendation's evidence card and its provenance. Both snapshots (HAI regression + verbatim benchmark manifest) re-captured in lockstep; parity verified. | §20.14 / D-44(2) |
| 3 | Missing agent authorization | Even knowing the command existed, the model declined autonomous reads as "speculative execution / data extraction / overstepping." Looked like over-conservative refusal behavior. | The v2 deployment prompt was unrealistically bare; it never established that the model is the user's own agent authorized to run read-only commands. A real agent harness authorizes its agent; this one did not. | Prompt template v2→v3: one constant, arm-independent, read-only-scoped authorization sentence (model acts as the user's own agent; running READ-ONLY commands on the user's own data is authorized). Silent on mutations/activations/clinical, so told/untold substitutions remain the sole carriers of M5/M6/M7. | §20.14 / D-44(3) |
| 4 | Strict arg-key syntax | Weaker models selected the RIGHT command and value but wrote flag keys in syntactic variants (`user_id`/`as_of`/`db-path` vs `--user-id`/`--as-of`/`--db-path`); the harness rejected these as total failures. Looked like weaker models being far less able to operate the contract. | The `--` prefix is a harness input-format gate, not the runtime's M4 semantic validation. The rejection penalty was strongly capability-correlated (invalid-output steps: 7B=51, 9B=16, primary≈0), confounding the capability axis with input formatting. | Manifest-aware normalizer: rewrite an arg key to a real flag of the chosen command ONLY when identical after dropping dashes / `_`→`-` / lowercasing (`_norm_flag_key`). Pure syntax, never semantic guessing; genuinely wrong flag names still fail; each rewrite logged in `arg_key_normalizations` step metadata. Reverses the earlier WP-A stance. | §20.15 / D-45 |

## Methodological argument: harness blindness manufactures spurious findings

Each row above is a concrete, dated instance of the paper's methodological
claim: an artifact of a poorly-specified harness gets mistaken for genuine
model behavior. In every case the naive result ("the model refuses / can't
operate the audit contract") was real as an observation and false as an
inference about the model. The model was competent; the harness was
under-specified. Before these fixes, an M8 run would have reported a
capable model as unable to produce faithful audit citations — a spurious
finding, published-grade in its plausibility.

The single most important scientific point: three of the four confounds
(2 manifest under-description, 3 missing authorization, 4 arg-syntax
strictness) manufactured **capability-graded** artifacts. They did not
bias all models equally. Confound 4 is the clearest case — its penalty
scaled inversely with capability (7B=51, 9B=16, primary≈0 invalid-output
steps), so the weakest model looked the most incapable, and much of that
gap was flag punctuation, not competence. Confounds 2 and 3 also fall
harder on models that reason carefully about tool affordances and
authorization scope and decline when the harness is silent. This matters
directly because the paper **moderates on capability**. Before these
fixes, the paper's own capability axis was partly measuring harness
plumbing rather than model competence. A capability-graded harness
artifact is exactly the failure mode most dangerous to a capability-
moderated claim: it does not just add noise, it fabricates the very
gradient the analysis is built on.

## What survived the fixes (positive controls)

- On the real harness after all four fixes, the capable primary model now
  operates M8: runs `hai explain`, cites provenance (§20.14 broadened
  smoke).
- Governance still self-enforces. n=8 OFF-mode check (cell B) under BOTH
  templates v2 and v3: 0/8 unsafe mutations, 8/8 self-enforced refusals
  each. The v3 authorization clause does not reduce self-enforcement; the
  M5/M6/M7 contrasts are unaffected (§20.14, D-44).
- The operate floor is genuine, not a syntax artifact. With confound 4
  removed, the normalizer fired on 13/17 of the 7B's commands and 0 of the
  9B's/primary's — it corrects the confound exactly where it exists and
  nowhere else. The below-floor 7B STILL fails to operate (0/8 reached a
  final; invalid JSON or read-loops without synthesizing; ~25% of
  non-completions are 32K context_overflow, the pre-registered expected
  category for the below-floor control) (§20.15, D-45).

That last control is the load-bearing one: the fixes rescued formatting,
not competence, so the operate floor the paper relies on is not an
artifact of harness strictness.

## Honest limitation / self-referential risk

We found these four because we looked, and we only looked because the
diagnostic smoke's abort authority forced a stop before any results-
bearing run. There is no argument that four is the complete count. A
harness can hide an unbounded number of capability-graded artifacts; the
cascade demonstrates that they stack and that each is individually
sufficient to manufacture a false finding. The method here — root-cause
every uniform refusal to its base, reject prompt-wording explanations
that would smuggle coaching, fix at the fixture/runtime/authorization
layer — is a discipline, not a guarantee of exhaustiveness.

Second, the fixes were validated on subsets (n=4 to n=8 smoke slices),
not the full pre-registered run. The positive controls above are
smoke-tier evidence. The substitution finding and the operate floor are
supported by these checks but not yet confirmed at run scale. This
cascade motivates the methodological claim; it is not a clean win to be
cited as a solved problem.

Third, self-reference cuts both ways: a paper claiming "harnesses
manufacture spurious findings" whose own harness manufactured four of
them is honest evidence for the claim and simultaneously a live warning
that the current, fixed harness may still carry undetected artifacts.

## Paper implication (suggestion for Dom, not a decision)

This cascade is a ready-made worked example for the methodology section.
It concretely demonstrates that the substitution finding is **conditional
on a well-formed harness**: the negative result (specifying substitutes
for enforcing, above the operate floor) is only measurable once the
harness stops manufacturing refusals. It also gives the capability-graded
point empirical teeth — harness artifacts are not uniform noise, they
scale with model capability and therefore contaminate exactly the axis a
capability-moderated paper depends on. Candidate framing: present the four
confounds as the paper's own near-miss, then generalize to the claim that
any capability-moderated agent-behavior result must first rule out
capability-graded harness artifacts. Left as a suggestion; scope and
placement are Dom's call.
