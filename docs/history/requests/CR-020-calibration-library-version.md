# CR-020: a calibration refuses runs made with another major library version

- **Requested by / date:** owner, 2026-10-15
- **Status:** implemented on branch `housekeeping` (not merged)
- **Superseded in part:** the calibration file's integer format is a hash (CR-086), and a results-changing release is a major (CR-085).

## Why

A calibration records the config hash of its panel runs, and `ponzi pvalues` refuses a run with another hash (CR-003, CR-005). A code change that alters the scores without touching the run config keeps the hash, so a calibration built on the old scores would code the new ones without complaint. The library's version rules (CHANGELOG) already say when that may happen: a change of the default behaviour of an existing run config is MAJOR. Comparing the major version of the library that built the calibration with the one that made the run catches what the hash cannot.

## What changes

1. **What "major" is** (`ponzi.calibration.library_major`). The CHANGELOG defines what goes into a major, minor or patch release but not how a 0.y version reads, so the SemVer convention is used: the first number for versions from 1 on (`1.4.2` -> `1`), `0.y` for 0.y versions (`0.3.1.dev4+gabc` -> `0.3`). A version that is missing, the uninstalled fallback `0+unknown`, or not of the form `N[.N...]` is unknown (None).
2. **What the calibration records.** `provenance["ponzi_version"]`, the key `ponzi-models` `calibration/build.py` already writes. `Calibration.estimate` now sets it to `ponzi.__version__` unless the caller recorded one. `Calibration.library_version` reads it. The file format is unchanged (format 2; the key lives in the free provenance record).
3. **What the run records.** `run_meta.ponzi_version` (C9), `ponzi.__version__` when the run was made (also the stamp's `version` in every output store). Unchanged.
4. **The check** (`Calibration.check_library(run_version, *, allow_mismatch=False)`), called by `write_pvalues` right after `check_run`, so by `ponzi pvalues` too:
   - both majors known and equal: passes (`result: match`);
   - both known and different: `LibraryMismatch` (a `CalibrationMismatch`), naming both versions and the override; nothing is written;
   - either unknown: a `UserWarning` naming the side, and it passes (`result: unknown`);
   - `allow_mismatch=True` (`write_pvalues(..., allow_library_mismatch=True)`, `ponzi pvalues --allow-library-mismatch`): a mismatch passes (`result: mismatch allowed`).
5. **The record.** The p-value store (C22) gets the attr `library_check`: `calibration_version`, `run_version`, `calibration_major`, `run_major`, `result` and `allow_library_mismatch` (true when the flag was given), written with every store.
6. **The registry** is unchanged: it files calibrations under a model and checks the config hash against the model card; there is no run at that point to compare with, and the model card records no library version.

## What existing files record (checked 2026-10-15 on the local copy of the registry, `~/projects/ponzi/data/registry`)

- `tide_c30_gaza_f1p_mt0.2` (`mt02-plain`, `mt02-ceiling`) and `tide_c30_pdcompact_mt0.4` (`mt04-plain`, `mt04-ceiling`), registered from the monorepo by `register_existing.py`: no `ponzi_version` (provenance `null_from`, `registered_by`, `note`, `lookup_from`). They warn and pass.
- `tide_s1_mt04` (`v04-ceiling`), built by `ponzi-models` `calibration/build.py`: `ponzi_version: "0.1.0"`.
- Runs: the 400 local monorepo runs checked record `ponzi_version: "0.1.0"`, the static version of the monorepo's `ponzi` package. A run of `ponzi-core` records what `importlib.metadata` finds for the distribution `ponzi`: the local editable environment reports `0.0.1.dev10+gd02fded98.d20261012` (the repository has no tag, and an editable install keeps the version of the day it was installed).

So under the 0.y rule a `ponzi-core` run that records `0.0.x` is refused by `v04-ceiling` (`0.1`) unless `--allow-library-mismatch` is given. The `0.1.0` of `v04-ceiling` is most likely the monorepo distribution's metadata seen through `PYTHONPATH=<ponzi-core>/src`, not a version of `ponzi-core`. Before this check is relied on, `ponzi-core` needs a tag and every environment that runs it an install of `ponzi-core` itself (so that `ponzi.__version__` is the code that runs); see "Open".

## Do results change?

No number changes. `ponzi pvalues` may now refuse a run it used to code (another major), and it warns where a version is unknown.

## Tests

`tests/test_calibration.py`: `library_major` (from 1 on, 0.y, unknown forms); `estimate` records the version and a load keeps it, a caller's version is kept; match, mismatch refused, mismatch allowed, for 1.x and 0.y; the warning for an unknown calibration side and an unknown run side. `tests/test_pvalue_store.py`: a calibration of the run's version writes `result: match`; another major is refused and nothing is written; with the override the store is written and records it; a calibration without a version warns and records `unknown`; the command refuses, and passes with `--allow-library-mismatch`.

## Version

Library: minor. Standard: none affected.

## Open

- Tag `ponzi-core` (a first `0.y.0` or `1.0.0`) and install it in the environments that run it, so that runs and calibrations record a true version. Until then the recorded versions are not a reliable signal, and the check is either silent (unknown) or refuses for the wrong reason (`0.0` against the monorepo's `0.1`).
