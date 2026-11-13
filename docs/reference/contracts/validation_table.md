# C15: Validation table

`ponzi.contracts.validate`. The judgment of ONE delivered coherence store (the core reads stores and never validates them), in one open: the C1 format checks, the producer facts and the comparison with the engine's report beside the store (C18). The rule, threshold and severity of every check are in the [C18 catalogue](engine_report.md#the-catalogue).

## Rows

A `ValidationReport` ([shared conventions](../contracts.md#shared-conventions)) whose `subject` is the store's `burst_id` attr, else its file name up to the first dot. `ValidationReport.rows()` gives one dict per check with the keys `subject`, `name`, `severity`, `detail`, `value` (number or None), `items` (list of strings), in check order.

`ponzi validate-store PATH` prints the text form; `--json` prints `{"subject", "ok", "checks": rows()}`. Exit code 0 when ok, 1 on a failure, 2 when there is no store at the path.

## Checks

In report order: the C1 checks (`store_checks`) `dtype` (only for a float64 `coh`, reported just before `structure`), `structure`, `baseline_days`, `revisit_days`, `time_axis`, `chunking`, `valid_pixels`, `range`, `crs`, `identity`, `consolidated`; then `complete_sentinel`, `partial`, `generation`, `window` (only when the dates do not match `T`, fail), `pairs_declared`, `cell_quality`, `chunk_completeness`, `availability_matrix`, `finite_fraction` and, last, `engine_report`.

The store is opened once into a `StoreHeader` (attrs, per-array metadata, the values of every small array, the sentinel facts). Validation reads metadata, the pair tables, two coherence chunks (`range`: baseline 0 of `RANGE_SAMPLE_STEPS` evenly spaced time steps) and one directory listing (`chunk_completeness`); it never reads the whole `coh` array. Whether a declared pair holds data comes from the producer's `n_finite` (C1); a store without it is trusted on availability and says so (info). A store whose out-of-range values sit only in unsampled slabs passes. An absent engine report is info; `validate_store(..., require_engine_report=True)` makes it a failure (the command has no flag for it).

## Functions

`ponzi.contracts.validate`: `validate_store(path, *, expected_generation=None, require_engine_report=False) -> ValidationReport`, `validate_input(paths, target="coh", *, require_engine_report=False)` (the layers of one input: the store checks of the layer holding the target and the check `layers`, CR-102; `ponzi validate-store --input LAYER ...`), `read_store_header`, `store_checks` (C1), `declared_cells`, `engine_report_path`, `read_engine_report`, `check_engine_report`, `resolve_store`, `is_archive_store`, `refuse_write`. The validator opens stores read-only; `refuse_write` (raises on a `*.sar.zarr`, a `*.coh.zarr` or a store with a `_complete` sentinel) is the guard the onboarding (`ponzi_pipeline.onboard.onboard`) calls before every write.
