# GovernedAgentBench — Design Sensitivity Analysis

_Generated 2026-07-05T14:36:29Z · exact binomial enumeration, stdlib only, no model/network calls._

**This is a design-sensitivity analysis, computed before data, not a post-hoc power calculation.** It characterises what the locked aggregation and decision rules can and cannot resolve, so the pre-registration states honest detectability up front.

## Methods

Each cell pools Bernoulli pass/violate outcomes into a count k of n reps (base cell n=9; canary arm n=6). Outcomes are treated as independent Binomial(n, p) draws. The decision statistic is the observed pooled violation-rate contrast between two cells, `k_off/n - k_enforced/n`, compared against the locked SESOI of 10 percentage points. `p0` denotes the enforced-arm violation rate; a true effect `delta` places the off arm at `p0 + delta`. Probabilities are computed by exact enumeration over the (n+1)x(n+1) outcome grid (n <= 15, so this is exact, not sampled). A fixed-seed Monte-Carlo run cross-checks a spread of cells. Null bounds are one-sided 95% Clopper-Pearson upper limits (the p solving P(X<=k | n, p) = 0.05), with rule-of-three shown alongside for 0/n. Four model conditions run independently; every number below is per model condition.

A granularity caveat drives most of what follows: because k/n is discrete, the 10pp bar collapses onto an integer rep gap. At n=9 a single net rep of difference (1/9 = 11.1%) already clears 10pp; at n=12 you need a 2-rep gap (1/12 = 8.3% does not clear). So n=9 and n=6 cells carry the LOOSEST possible bar.

### Detection table: P(observed contrast >= 10pp)

Rows = true underlying effect `delta` (pp). Columns = enforced-arm base violation rate `p0`. `delta = 0` rows are FALSE-ALARM rates.

Effective integer rep-gap bar (net off-minus-enforced reps needed to clear 10pp): n=6->1, n=9->1, n=12->2, n=15->2.

**n = 6 per cell** (bar = 1-rep gap)

| delta (pp) | p0=0.0 | p0=0.05 | p0=0.1 | p0=0.5 |
|---|---|---|---|---|
| 0 (false alarm) |   0.0% |  20.2% |  29.1% |  38.7% |
| 5 |  26.5% |  37.1% |  41.5% |  45.6% |
| 10 |  46.9% |  51.1% |  52.4% |  52.7% |
| 15 |  62.3% |  62.5% |  61.9% |  59.8% |
| 20 |  73.8% |  71.8% |  70.1% |  66.8% |
| 30 |  88.2% |  84.9% |  82.6% |  79.9% |
| 50 |  98.4% |  96.9% |  95.8% |  98.4% |

**n = 9 per cell** (bar = 1-rep gap)

| delta (pp) | p0=0.0 | p0=0.05 | p0=0.1 | p0=0.5 |
|---|---|---|---|---|
| 0 (false alarm) |   0.0% |  25.5% |  33.4% |  40.7% |
| 5 |  37.0% |  45.7% |  47.9% |  49.2% |
| 10 |  61.3% |  61.3% |  60.3% |  57.8% |
| 15 |  76.8% |  73.1% |  70.6% |  66.2% |
| 20 |  86.6% |  81.8% |  78.9% |  74.1% |
| 30 |  96.0% |  92.4% |  90.1% |  87.4% |
| 50 |  99.8% |  99.2% |  98.7% |  99.8% |

**n = 12 per cell** (bar = 2-rep gap)

| delta (pp) | p0=0.0 | p0=0.05 | p0=0.1 | p0=0.5 |
|---|---|---|---|---|
| 0 (false alarm) |   0.0% |   7.1% |  14.4% |  27.1% |
| 5 |  11.8% |  22.5% |  28.0% |  35.8% |
| 10 |  34.1% |  40.0% |  42.5% |  45.4% |
| 15 |  55.7% |  56.4% |  56.3% |  55.4% |
| 20 |  72.5% |  70.0% |  68.3% |  65.3% |
| 30 |  91.5% |  87.9% |  85.6% |  82.9% |
| 50 |  99.7% |  99.1% |  98.5% |  99.7% |

**n = 15 per cell** (bar = 2-rep gap)

| delta (pp) | p0=0.0 | p0=0.05 | p0=0.1 | p0=0.5 |
|---|---|---|---|---|
| 0 (false alarm) |   0.0% |   9.3% |  17.3% |  29.2% |
| 5 |  17.1% |  28.4% |  33.2% |  39.3% |
| 10 |  45.1% |  48.6% |  49.6% |  50.2% |
| 15 |  68.1% |  65.9% |  64.3% |  61.3% |
| 20 |  83.3% |  78.9% |  76.2% |  71.8% |
| 30 |  96.5% |  93.4% |  91.2% |  88.6% |
| 50 | 100.0% |  99.7% |  99.5% | 100.0% |

### Null-bound table: what a clean null can rule out

One-sided 95% Clopper-Pearson upper bound on the true violation rate given the observed k/n. Rule-of-three (3/n) shown for 0/n as the familiar cross-check.

| observed k/n | point est. | CP 95% upper | rule-of-three |
|---|---|---|---|
| 0/9 | 0.0% | 28.3% | 33.3% |
| 0/12 | 0.0% | 22.1% | 25.0% |
| 0/15 | 0.0% | 18.1% | 20.0% |
| 1/9 | 11.1% | 42.9% | - |
| 1/12 | 8.3% | 33.9% | - |
| 2/15 | 13.3% | 36.3% | - |

### Canary gate table: P(admissibility gate trips)

Gate = observed positive-control contrast >= 10pp, at n=6 reps per arm (bar = 1-rep gap). `delta = 0` is the DEAD-INSTRUMENT false-trip rate (must be low); `delta >= 30pp` is the working-instrument pass rate (must be high).

| true delta (pp) | clean p0=0.0 | clean p0=0.1 |
|---|---|---|
| 0 (dead instr.) |   0.0% |  29.1% |
| 30 |  88.2% |  82.6% |
| 50 |  98.4% |  95.8% |
| 80 | 100.0% |  99.9% |
| 100 | 100.0% | 100.0% |

### Self-verification: exact enumeration vs Monte Carlo

Fixed seed 20260705, 400,000 draws per cell. MC standard error ~ 0.0008; tolerance (5 SE) = 0.0040.

| cell | exact | monte carlo | abs diff |
|---|---|---|---|
| n9 p0=0 delta=20 |  86.6% |  86.5% | 0.0007 |
| n9 p0=0.5 delta=0 (false alarm) |  40.7% |  40.7% | 0.0005 |
| n12 p0=0.1 delta=30 |  85.6% |  85.7% | 0.0006 |
| n6 canary delta=50 |  98.4% |  98.4% | 0.0000 |
| n15 p0=0.05 delta=50 |  99.7% |  99.7% | 0.0001 |

Max abs diff = 0.0007. Verdict: **AGREE** (<= 5 SE tolerance).

## Interpretation (for the appendix)

- **Detecting a real enforcement effect.** Under a true 20pp effect at n=9, the design flags it with probability 86.6% when the enforced arm is clean (p0=0) and 78.9% when the enforced arm already violates 10% of the time. A true effect exactly at the SESOI (10pp, p0=0) is a coin-flip to clear its own bar (61.3%): the design is built to resolve effects comfortably above 10pp, not right at it.

- **What a clean null rules out.** A clean 0/9 cell is consistent with any true violation rate below 28% at one-sided 95% (rule-of-three: 33%). Even 0/15 only pushes that ceiling down to 18%. The honest claim is therefore bounded: a null says 'the enforced-off gap is not large', not 'the gap is zero'. Small residual effects are simply not resolvable at these n.

- **The canary gate behaves at the extremes.** With a clean control arm (p0=0), the gate trips with probability 88.2% under a true 30pp positive-control effect and 98.4% at 50pp — near-certain to pass when the instrument works — while firing only 0.0% of the time under a dead instrument (delta=0). That is the desired asymmetry.

## Design implications (flagged, with numbers)

1. **The 10pp bar at n=9 is flaky at intermediate base rates.** When the true effect is zero but both arms violate ~50% of the time, the observed contrast still clears 10pp 40.7% of the time (a 1-rep net gap is enough). At p0=0.1 the false-alarm rate is 33.4%, at p0=0.05 it is 25.5%, and at p0=0 it is 0.0%. So the design is only trustworthy when the load-bearing metric keeps both compared cells at LOW violation rates. Tasks calibrated so that even the off arm sits well under 50% violation are essential; a metric that puts cells near 50/50 makes both the headline contrast and any 6-rep canary read as noise.

2. **Canary flakiness rides on the SAME base-rate sensitivity.** With a noisy control arm (p0=0.1), the dead-instrument false-trip rate rises to 29.1% and a genuine 30pp canary passes only 82.6% of the time at n=6. Keep canary control arms clean (near-zero baseline violation) or the admissibility gate loses its teeth.

3. **Bigger cells buy a stricter bar cheaply.** Moving from n=9 to n=12 changes the effective bar from a 1-rep to a 2-rep gap, cutting the p0=0.5 false alarm from 40.7% to 27.1%. If a metric cannot be kept in the low-violation regime, the cheapest fix is more reps per cell, not a different threshold.

_Provenance: regenerate with `python benchmark/governed_agent_bench/scripts/sensitivity_analysis.py`._
