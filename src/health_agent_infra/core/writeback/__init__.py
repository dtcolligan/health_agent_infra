"""WRITEBACK layer — schema-validated bounded local persistence.

As of v0.1.4 D2 this package contains only the DomainProposal writeback
path. The legacy recovery-only ``perform_writeback`` (`hai writeback`
CLI) was removed; recommendations now reach ``recommendation_log``
exclusively through the atomic ``hai synthesize`` commit.
"""
