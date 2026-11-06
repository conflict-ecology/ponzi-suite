# CR-003: `ponzi.calibration`

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off and implemented 2026-10-12; checked once on a real run (see Tests)

## Why
The score-to-code arithmetic existed in five copies outside any package (`ops/hpc/gaza_pcodes.py`, `lebanon_replay/pvalues.py`, three in `unosat_audit`), and the ceiling-conditional lookup lived in a side analysis that production runs. Both tracks (conflicts and paper) need one definition.

## What changes
New subpackage with `codes`, `conditional` and `product` (the `Calibration` file). The functions are the monorepo's, line for line in their arithmetic. Nothing calls them from the run yet; writing a code store and the registry layout are later requests.

## Do results change?
No existing output changes.

## Tests
Unit tests on synthetic inputs only (owner 2026-10-12: tests are self-contained, no reproductions of earlier runs).

One-off check on a real run, outside the repository (2026-10-12, HPC job 5770106 on hina01, 2 minutes; script in `ponzi-apps/hpc/pvalues_check.py`): `ponzi pvalues` on the Tehran burst t028_058198_iw3 with the registered calibrations `mt04-plain` and `mt04-ceiling` of `tide_c30_pdcompact_mt0.4`, compared with the stored codes of that run (`pcodes.zarr` and `runs_cc/.../pcodes.zarr`): 1,049,944,940 values each (222,324,180 scored), 0 mismatches for both.
