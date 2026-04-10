# Contributing

Thanks for taking a look at Health Lab.

## Current contribution shape

This repo is currently easiest to review as a bounded proof repo around the CLI-first flagship loop in `health_model/`, not as a broad platform or polished product.

Start here:
- `docs/health_lab_canonical_public_demo.md`
- `artifacts/public_demo/captured/`
- `artifacts/flagship_loop_proof/2026-04-09/`
- `STATUS.md`

## Contribution boundaries

Please keep contributions truthful to current repo reality:
- do not overclaim clinical, diagnostic, or production readiness
- do not treat local runtime data under `data/` as public-safe demo material
- prefer small changes that preserve fail-closed CLI behavior and artifact truth
- separate proven flagship-loop work from older adjacent repo surfaces unless a change is explicitly a cleanup

## Before opening a PR

1. Read the canonical demo and proof surfaces above.
2. Keep README and status wording aligned with what is actually proven on disk.
3. Run the flagship CLI smoke tests:

```bash
python3 -m unittest tests.test_agent_contract_cli tests.test_agent_bundle_cli tests.test_agent_voice_note_cli tests.test_agent_context_cli tests.test_agent_recommendation_cli
```

4. If you change proof-facing docs or artifacts, make sure links resolve from the repo root and that claims stay narrower than the code and checked-in artifacts.

## Good first changes

- repo truth and documentation cleanups
- bounded CLI reliability improvements
- tighter proof artifacts and audit notes
- tests that strengthen the existing flagship loop

Large renames, product reframes, hosted-service work, UI expansion, or broader data integrations should be discussed before implementation.
