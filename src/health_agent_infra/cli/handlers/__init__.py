"""Handler-group modules for the ``hai`` CLI.

W-29.1 placeholder. Per ``reporting/plans/v0_1_17/w29_boundary_refresh.md``
§(b) + §(d) + §(e), the 11 handler groups land here as sibling modules
at W-29.2:

- ``auth.py`` — credential surface
- ``pull_clean.py`` — evidence acquisition
- ``state.py`` — DB lifecycle + projection (incl. ``backup``,
  ``restore``, ``export``, and the F-PV14-02 ``hai sync purge`` add)
- ``config_init.py`` — config + first-run setup
- ``intake.py`` — typed user inputs
- ``intent.py`` — W49 intent ledger
- ``target.py`` — W50 target ledger (incl. v0.1.15 W-C
  ``hai target nutrition``)
- ``recommend.py`` — propose + synthesize + daily pipeline
- ``review.py`` — review schedule + record + summary
- ``inspect.py`` — read-only operator surfaces
- ``tools.py`` — admin / demo / research / eval

This module exists at W-29.1 only to anchor the ``cli/handlers/``
package layout. The actual handler bodies migrate at W-29.2; the
``register(...)`` parser-attachment refactor lands at W-29.3.
"""
