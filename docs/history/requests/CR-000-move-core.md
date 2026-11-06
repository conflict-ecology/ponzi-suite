# CR-000: move the per-unit engine into `ponzi.core`

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off 2026-10-12

## Why
First step of the restructure (monorepo `docs/target_architecture_2026-10-09.md`, section 9c): one library with subpackages.

## What changes
The monorepo's `ponzi` package at tag `pre-restructure` becomes `ponzi.core`. Only import paths change. The state machine and `change.zarr` come across as they are; moving them to the detection recipe is a later request.

## Do results change?
No.

## Tests
The 277 fast tests of the package, unchanged; the golden-fixture parity tests; the full-burst parity oracle on t017_035219_iw1.

## Version
Library: first development version (0.x). Standard: none yet.
