# CR-001: tests the repository can run by itself

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off and implemented 2026-10-12

## Why
The oracle tier compared full bursts with the old `ponzi-ccd` implementation. That proved the rebuild; it now costs 17 minutes and 6 GB, needs data outside the repository, cannot run in CI, and two of its eight cases were stale.

## What changes
- Removed: `test_parity_t017.py`, the `oracle` marker and its gate, and three tests that open `ponzi-ccd` files (`test_real_legacy_store_opens`, `test_reference_bright_labels_open`, `test_reference_legacy_cache_opens`). The synthetic legacy-format tests stay.
- Added: `test_a_run_reproduces_the_stored_numbers`, a whole run on the synthetic store against `tests/data/runner_golden.npz`.
- Kept as they are: the kernel golden files, and the `ml` TiDE tests (they still need an artefact and a store on the machine; see open point).

## Do results change?
No. Tests only.

## Open point
The TiDE adapter has no numeric test that runs without external files. A small synthetic TorchScript model in the repository would close that; proposed for the calibration or models step.
