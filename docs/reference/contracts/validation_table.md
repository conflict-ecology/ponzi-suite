# C15: Validation table

> Note (2026-11-04): this repository has the report of ONE store, `ponzi.contracts.validate.validate_store` (command `ponzi validate-store PATH [--json]`), in the row shape of the table below. The table itself (`validation.parquet`, the per-burst files), the request-row checks, the AOI level, the status file and the header cache are not in this repository.

Status: implemented 2026-09-07, reshaped 2026-09-09; the one-store report since CR-008 (2026-10-12), `ponzi.contracts.validate`.

## Purpose

The judgment of a delivered coherence store (the core reads and never validates). One store, one open: the C1 format checks, the producer facts and the comparison with the engine's own report beside the store (C18).

Every rule and threshold is written down once, in the C18 catalogue and as the constants at the top of `ponzi/contracts/validate.py`.

## Rows

A `ValidationReport` (`ponzi.contracts.base`): `subject` (the store's `burst_id` attr, else its file name up to the first dot) and one `CheckResult` per check. `ValidationReport.rows()` gives one dict per check with the keys `subject`, `name`, `severity` (`ok`, `info`, `warn`, `fail`), `detail`, `value` (number or None), `items` (list of strings), in check order. `ok` is false when any check failed.

`ponzi validate-store PATH` prints the text form; `--json` prints `{"subject", "ok", "checks": rows()}`. Exit code 0 when ok, 1 on a failure, 2 when there is no store at the path.

## Checks

In report order: the C1 checks `structure`, `dtype` (only a float64 `coh`, warn), `baseline_days`, `revisit_days`, `time_axis`, `chunking`, `valid_pixels`, `range`, `identity`, `crs`, `consolidated`; then `complete_sentinel`, `partial`, `generation`, `window` (only when the dates do not match `T`, fail), `pairs_declared`, `cell_quality`, `chunk_completeness`, `availability_matrix`, `finite_fraction` and, last, `engine_report`.

Validation is metadata, two coherence chunks (`range`) and one directory listing (`chunk_completeness`). Whether a declared pair holds data (`availability_matrix`, `finite_fraction`) comes from the producer's `n_finite (time, baseline)` count (C1, required of the engine by C18); a store without it is trusted on availability and says so. `validate_store(..., require_engine_report=True)` fails a store without a report.

## Functions

`ponzi.contracts.validate`: `validate_store(path, *, expected_generation=None, require_engine_report=False) -> ValidationReport`, `read_store_header`, `store_checks` (C1), `declared_cells`, `engine_report_path`, `read_engine_report`, `check_engine_report`, `resolve_store`, `is_archive_store`, `refuse_write`. The validator opens stores read-only; `refuse_write` (raises on a `*.coh.zarr` or a store with a `_complete` sentinel) is the guard the onboarding (`ponzi_pipeline.onboard.onboard`) calls before every write.
