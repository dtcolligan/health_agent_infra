# HAI verification/

Test, eval, and verification surfaces for the frozen HAI reference
runtime. From the repository root, run these tests as
`uv run pytest hai/verification/tests -q`. The runtime itself lives in
[`../src/health_agent_infra/`](../src/health_agent_infra/); nothing under
`verification/` is imported by the package.

## Subdirectories

| Path | Class | Role |
|---|---|---|
| [`tests/`](tests/) | active tests | The full pytest suite: schemas, classify, policy, projectors, migrations, CLI surfaces, atomic-transaction semantics, skill-boundary contracts, eval runner, scenario pack. Run from repo root with `uv run pytest hai/verification/tests -q`. |
| [`evals/`](evals/) | active eval-doc reference + skill-harness pilot | Dev-reference docs for the eval framework (`README.md`, `skill_harness_blocker.md`), the frozen scenario pack, and the Phase E skill-harness pilot under `skill_harness/`. The eval **runner itself** lives inside the wheel at `src/health_agent_infra/evals/` and is invoked via `hai eval run`. |
| [`scripts/`](scripts/) | legacy / historical | A single legacy demo shim retained as a marker of the pre-rebuild CLI chain. See [`scripts/README.md`](scripts/README.md). Do not run; do not extend. |

## Symlinks (committed, intentional)

`verification/` also contains two committed symlinks:

| Symlink | Target | Purpose |
|---|---|---|
| `verification/artifacts` | `../artifacts/` | Lets tests and local replays reach into the gitignored top-level `artifacts/` directory using a stable relative path. |
| `verification/data` | `../data/` | Same idea for the gitignored top-level `data/` runtime data root. |

Neither target is checked into the repo. `data/` is gitignored
outright; `artifacts/` is left out of git purely by convention.
Historical proof bundles now live under `../../ARCHIVE/`, not the
top-level runtime-output roots. Both targets only materialize when the runtime is
exercised locally (`hai pull`, `hai state init`, eval runs). The
symlinks are the durable thing; the data behind them is not.

## What is intentionally not here

- No runtime code. The package is imported from
  [`../src/health_agent_infra/`](../src/health_agent_infra/) only.
- No operator documentation. The eval framework is described inside
  [`evals/README.md`](evals/README.md); higher-level HAI docs live under
  [`../docs/`](../docs/).
- No CI configuration. That lives under `../../.github/`.
