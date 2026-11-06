# C22: p-value store

`ponzi.contracts.pvalues`. The calibrated scores of one run under one calibration.

## Producer and consumers

Producer: `ponzi.calibration.write_pvalues` (`ponzi pvalues RUN_DIR --calibration FILE [--overwrite] [--allow-library-mismatch]`, or the worker stage `pvalues`), from the run's `score.zarr` (C7), `run_meta.json` (C9) and, for a staged run, `staged.zarr` (C26). Consumers: `ponzi.products` (`detect`, `detect_path`, `tile_path`: `ponzi detect`, `detect-path`, `tile` and the worker stages `detect` and `tile`, C25), which read `anomaly` (and, for a provisional detection spec, `anomaly_staged`) through `open_pvalue_store`, and the grid and `epsg`.

Location: `<run folder>/pvalues_<calibration id>.zarr` (`pvalue_store_name`). The worker writes it through a folder of links to the run's files and keeps it as its own cache entry; the readers see it beside the run's files again through such a folder.

## Arrays

| Array | Dims | Stored | Read as |
| --- | --- | --- | --- |
| `anomaly` | `(time, y, x)` | uint8, chunks `(1, Y, X)`, fill 255 | `-log10 p` of the anomaly score; NaN = no score |
| `ceiling` | `(time, y, x)` | same | `-log10 p` of the ceiling score, the largest the anomaly could reach |
| `time`, `y`, `x`, `process_pixels` | | copied from the score store (values, attrs, dims) | |

Packing: stored = `round(20 * -log10 p)`, attrs `scale_factor = 0.05`, `_FillValue = 255`, `units` `1`, `long_name`, `packing`. So 3.0 is 1 in 1,000, at 0.05 decades per step, up to 12.7. A reader that applies the usual scale and fill conventions (xarray by default) sees `-log10 p` as a float.

Group attrs: the score store's attrs; `calibration` {`model_id`, `calibration_id`, `panel_id`, `kind`, `n_null`, `scoring_spec_hash`}; `t_lo`, `t_hi` (anchors outside hold no score); `library_check` (`calibration_version`, `run_version`, `calibration_major`, `run_major`, `result` `match`, `unknown` or `mismatch allowed`, and `allow_library_mismatch`); `complete` (False until the last write, then True, when the metadata is consolidated).

### Staged runs

A run with `staged.zarr` (C26) coded with a staged calibration (format 3, below) also holds `anomaly_staged` and `ceiling_staged`, `(stage, time, y, x)` uint8, chunks `(1, 1, Y, X)`, packed as above, each stage coded with its own mapping (`Calibration.codes_stage`) for the anchors `t_lo` .. `staged_t_hi`, and `stage` `(stage,)` int16 (1 .. H - 1); attrs `stages`, `staged_t_hi`, `staged_rule` (copied from `staged.zarr`), and `calibration.n_null_by_stage` (stages 1 .. H - 1). Nothing is overwritten as a pyramid fills: every stage keeps its code. `PValueStore.latest(t, name)` gives the current view of anchor t: the final code where it exists, else the code of the highest stage present, and that stage (H for the final code, 0 for none). A calibration without stages codes the final stage only, with a warning, and the store is that of an unstaged run.

## Invariants

- One calibration per store; the calibration's `scoring_spec_hash` equals the run's `scoring_spec.hash` (`CalibrationMismatch` otherwise).
- The calibration's library version (`provenance.ponzi_version`) has the major of the run's (`run_meta.ponzi_version`; SemVer: the first number from 1 on, `0.y` below; `LibraryMismatch` otherwise), unless written with `--allow-library-mismatch`; a side without a known version is warned about, not refused.
- A staged calibration made under another `staged_rule`, or with other stages, than the run's is refused (`CalibrationMismatch`).
- A store without `complete` is refused by `open_pvalue_store` (`IncompletePValueStore`); a complete store is written again only with `overwrite`, an interrupted one always.

## The calibration file

What `--calibration FILE` names (`ponzi.calibration.Calibration.save` and `load`): one `.npz` (`np.savez_compressed`) per kind, `plain` or `ceiling`. `meta` is a JSON string with `format`, `scale`, `model_id`, `panel_id`, `calibration_id`, `kind`, `edges`, `scoring_spec_hash`, `n_null`, `provenance`, `specs` (the scoring and panel specs it was made for: name, hash, suite commit); the arrays are `null` (the sorted finite panel scores) and, for a ceiling calibration, `lookup` (`(classes, 256)` int16).

- **Format 2**: one mapping, the final stage. `ponzi-models calibrate` writes it.
- **Format 3** (staged): `null` (the final stage) and `null_s1` .. `null_s{H-1}`; a ceiling calibration's `lookup` is `(stages, classes, 256)` with the final stage last; meta `stages` (1 .. H), `n_null_by_stage` (keyed 1 .. H, as `provenance.n_null_by_stage`) and `staged_rule`. `Calibration.estimate(..., stages=, staged_rule=)` builds it, the null of stage s from the stage s `anomaly_score` of staged panel runs wherever it is finite (`ponzi.calibration.staged_inputs`, which also refuses runs of different staged rules or scoring spec hashes), each stage's lookup built as the final one's; the final mapping is the plain calibration of the final scores, on the bytes. `ponzi-models calibrate-staged` builds the plain and the ceiling one from the staged panel runs of `ponzi-models null-runs --staged`.

A file whose meta has `run_config_hash` is refused with a message: it predates the rename to `scoring_spec_hash` and is made again on the runs.
