# verification/scripts/ (legacy / historical)

This directory holds **one legacy demo shim** retained as a marker
of the pre-rebuild CLI chain.

## Contents

- `run_canonical_public_demo.py` — a thin shim that tries to delegate
  to a `reporting/scripts/run_canonical_public_demo.py` driver from
  the pre-rebuild repo layout. That driver was removed in commit
  `910f27a` ("Sweep older proof bundles, reporting scripts, and
  legacy doctrine docs"), so the shim **cannot execute today**. The
  module names it references (`health_model.agent_*_cli`) were also
  part of the pre-rebuild package and no longer exist.

## Why it is still here

It is preserved so that anyone reading older proof bundles or
pre-rebuild commit messages and chasing the entry-point name can
land on a clear "this is historical" signpost rather than a 404.
The file's own docstring already labels it a "Legacy pre-rebuild
demo shim."

## Do not

- Do not run it.
- Do not extend it or wire it back up.
- Do not treat it as the demo entry point for the current runtime.

For the frozen HAI reference runtime, see
[`../../README.md`](../../README.md) and
[`../../docs/hai_reference_runtime.md`](../../docs/hai_reference_runtime.md).
The canonical operator flow is through `hai doctor`, `hai daily`,
`hai today`, and `hai explain` — not this shim.
