# CR-002: subpackages by role

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off and implemented 2026-10-12

## Why
"Everything computed from one unit" put contracts, the run and evaluation under one name. Grouping by role matches the version rule of the standard: `ponzi.core` is what a major version redoes; calibration, evaluation and products come after the run.

## What changes
`ponzi.core.contracts` becomes `ponzi.contracts`; `ponzi.core.evaluation` becomes `ponzi.evaluation`; tests move to a flat `tests/`. Import order: contracts, then core, then the rest.

## Do results change?
No. Import paths only; the same 278 tests, including the results lock.

## Left for the clean-up requests
Three function-level imports still point the wrong way and are listed as exceptions in `tests/test_layering.py`: `contracts/pred.py` to core, `core/cli.py` to evaluation, `core/forecasting_stats.py` to evaluation. Candidates to cut or shrink, one request each: the older evaluation (`detection`, `monitoring`, `bags`, `results`, `aggregate`, `forecasting`, about 1,560 lines), the stored-prediction machinery (`contracts/pred.py`, `forecast/external.py`), the all-channel store, and support for old sample caches. The state machine and the flags store move to `ponzi.products`.
