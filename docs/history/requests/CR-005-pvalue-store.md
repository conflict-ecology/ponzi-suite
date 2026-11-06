# CR-005: the p-value store of a run

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off and implemented 2026-10-12

## Why
The calibrated values of a run were written by scripts outside any package, as two stores per run (`pcodes.zarr` and `<config>_cc/pcodes.zarr`) under a name that says nothing about their content, and a job killed while writing left a store that the next submission skipped as done.

## What changes
- A calibration is ONE mapping from scores to p-values. `Calibration.kind` is `plain` (the whole panel null) or `ceiling` (re-expressed against the null of the ceiling class). Wanting both means two calibrations and two stores.
- `pvalues_<calibration id>.zarr` beside `score.zarr` (`ponzi.contracts.pvalues`), with `anomaly` and `ceiling`.
- Packed storage: the same uint8 as before (`round(20 * -log10 p)`, 255 = no score) with `scale_factor = 0.05` and `_FillValue = 255`, so xarray, GDAL and QGIS show `-log10 p` (3.0 = 1 in 1,000) and missing values.
- `complete` is set last; an incomplete store is refused on opening and rewritten without `overwrite`.
- `ponzi.calibration.write_pvalues(run_dir, calibration)` and `ponzi pvalues RUN_DIR --model ID --calibration ID`. The `ponzi` command now starts in `ponzi.cli`, which hands every other subcommand to the run's command line.

## Do results change?
No existing output changes. The stored bytes of a p-value array are those of the old code stores; the name, the layout (one kind per store) and the metadata differ. The old `pcodes.zarr` stores are not read by the library.

## Tests
Unit tests on the synthetic run: the stored values equal the direct function inside the run window and are no-score outside it; a reader sees `-log10 p` and NaN; refusals (complete store, wrong run config, interrupted store); the command with a registry.
