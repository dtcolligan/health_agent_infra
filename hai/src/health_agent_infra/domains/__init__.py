"""Per-domain modules. Each domain owns its own schemas, classify, policy,
and intake. Cross-domain reasoning lives in core/synthesis_policy (Phase 2).

Dependency direction is strictly domains → core, never the reverse.
"""
