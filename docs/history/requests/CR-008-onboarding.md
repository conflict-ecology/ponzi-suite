# CR-008: `ponzi.onboarding` replaces `ponzi.pipeline`

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off 2026-10-12, implemented 2026-10-12, awaiting owner review

## Why
CR-007 moved the monorepo's whole pipeline package in (15 modules, 8,684 lines): planning, the request, the catalogue queries, validation at three levels, onboarding, the run loop and the aggregation. Most of that is campaign logic and belongs to the applications, not to the library. What the library has to offer before a run is small and concerns ONE coherence store: check it against the format contract, and write its covariates sidecar and pixel sample. An end-to-end test on the HPC waits for exactly these two commands with a store path as their only handle.

## What changes
`src/ponzi/pipeline/` is replaced by `src/ponzi/onboarding/` (7 files, 2,728 lines). Everything removed stays available in the monorepo (`packages/ponzi_pipeline` at `ef99d21`), which is untouched.

### The new interface

```
ponzi onboard --store PATH --out DIR [--burst ID] [--config FILE]
              [--steps a,b] [--rebuild] [--frames FILE] [--ghsl-cache DIR]
ponzi validate-store PATH [--json]
```

Both are subcommands of the single `ponzi` command (`ponzi.cli`); the entry point `ponzi-pipeline` is gone.

- `ponzi.onboarding.onboard.onboard_store(store, out_dir, config=None, *, burst=None, rebuild=False, steps=None, frames=None, ghsl_cache=None, era5_cache=None) -> dict` (the stamp). It writes `<out_dir>/<burst>_covariates.zarr`, `<out_dir>/onboard_meta.json` and, when a frames table is given, `<out_dir>/samples/<burst>_sample.zarr`. The store is named by its path and never written. `burst` defaults to the store's `burst_id` attribute, else the store's file name. There is no request and no data root: one output folder per store.
- `ponzi.onboarding.config.OnboardingConfig` (`steps`, `edge_margin`, `weather_source`, `weather_variables`, `pairdiff_baselines`) and `load_onboarding_config(path=None)`: a yaml file with an `onboarding:` section, or the defaults. The fields and defaults are those of the `onboarding` section of the old request config, so an old request config file loads as it is (its other sections are ignored). Unknown keys in the section are refused.
- `ponzi.onboarding.validate.validate_store(path, *, expected_generation=None, require_engine_report=False) -> ValidationReport`. `ponzi validate-store` prints the report as text or, with `--json`, as `{"subject", "ok", "checks": [...]}`; the exit code is 0 when no check fails, 1 when one does, 2 when there is no store at the path.
- Other public names kept: in `onboard`, `write_sidecar`, `open_sidecar`, `validate_sidecar`, `sidecar_mask`, `sidecar_path(out_dir, burst)`, `sample_path(out_dir, burst)`, `stamp_path(out_dir)`, `load_stamp(out_dir)`, `burst_of(store)`, `process_mask_layer`, `pairdiff_levels`, `pairdiff_layers`, `read_frames`, `frames_digest`, `extract_burst_sample`, `platform_time_index`, `primary_platform`, `writable_time_tables`, `onboard_report`; in `validate`, `StoreHeader`, `read_store_header`, `store_checks`, `declared_cells`, `read_engine_report`, `check_engine_report`, `engine_report_path`, `resolve_store(path)`, `refuse_write`, `is_archive_store`, `CATALOGUE`; in `weather`, `weather_layers`, `edh_layers`, `cdsgrid_layers`, `edh_cdsgrid_layers`, `fetch_edh`, `fetch_cdsgrid`; in `built`, `built_layers`; in `archive`, `decode_time`.

Example:

```
ponzi validate-store /scratch/coherence/t094_200136_iw2.coh.zarr --json
ponzi onboard --store /scratch/coherence/t094_200136_iw2.coh.zarr \
              --out /scratch/onboarded/t094_200136_iw2 \
              --config onboarding.yaml \
              --steps built,weather,pairdiff,mask --ghsl-cache /scratch/ghsl
```

### Kept, module by module (lines before, after)

| Module | Before | After | What is left |
| --- | --- | --- | --- |
| `onboard.py` | 1,060 | 999 | everything of the steps; the entry point is `onboard_store` (was `onboard_burst(request, burst_id, root=...)`) |
| `validate.py` | 1,905 | 764 | the store header, the C1 format checks, the producer facts, the engine report comparison, `validate_store` |
| `weather.py` | 914 | 696 | the sources `edh`, `cdsgrid`, `edh_cdsgrid` |
| `built.py` | 174 | 174 | unchanged |
| `archive.py` | 111 | 25 | `decode_time` |
| `request_config.py` | 175 | 54 | now `config.py`: the onboarding section only |
| `__init__.py` | 21 | 16 | docstring |
| `evaluation.py` | 716 | 716 | moved unchanged to `ponzi/evaluation/events.py` |

### Removed, module by module

| Module | Lines | What it was |
| --- | --- | --- |
| `selection.py` | 1,361 | area to tracks to bursts, the plan and the frozen request (`plan_many`, `load_tracks`, `load_bursts`, `request_meta`, `request_json`, `collapse_to_bursts`, `required_bursts`, `burst_sats`, `AoiSpec`, the column lists, `merge`) |
| `discovery.py` | 548 | the sensor plug-in and the live ASF and CMR queries (`get_sensor`, the sensor store methods) |
| `aoi.py` | 255 | the AOI registry (`read_registry`, `write_registry`, `registry_digest`, `registry_from_geojson`, `RegistrySchema`, `aoi_geometry`) |
| `run.py` | 305 | the run loop over a request (`run_requests`, `run_burst`, `run_request`, `eval_burst`, `eval_request`, `runnable_bursts`, `load_registry`) and the helpers `config_dir`, `config_path`, `is_finished`, which nothing kept needs |
| `aggregate.py` | 481 | the AOI results |
| `cli.py` | 621 | the `ponzi-pipeline` command (plan, freeze, merge, bursts, validate, onboard, run, eval, aggregate) |
| `paths.py` | 37 | `data_root`, `request_dir`, `burst_dir`, `run_dir`: no kept code needs a data root |
| `validate.py`, in part | 1,141 | the request row and its five checks (`parse_request_row`, `request_checks`, `check_window`, `check_expected`, `check_platform_vs_sat`, `check_missing_acquisitions`, `check_baseline_set`, `store_platforms`); the AOI cover (`aoi_points`, `cover_vector`) and the AOI pass (`aoi_checks`, `validate_aois`); the request loop (`validate_burst`, `validate_request`, `missing_store_report`, `unvalidated_bursts`, `request_rows`); the validation table and the status files (`report_rows`, `write_burst_validation`, `combine_validation`, `write_validation`, `write_validation_meta`); the loaders (`load_validation`, `validated_bursts`, `validated_aois`, `validation_defects`, `request_aoi_of`); the header cache (`save_store_header`, `load_store_header`: written, never read); the row digest (`request_row_digest`, `request_row_digests`, and the `row_digest` argument of `check_engine_report`); `archive_probe`; `BurstReport` (a plain `ValidationReport` is returned); the lookup of a store by burst id (`resolve_store(burst_id, root=, archive=)` is now `resolve_store(path)`) |
| `weather.py`, in part | 218 | the CDS POINT route: the sources `cds` and `auto`, `cds_layers`, `fetch_era5`, `era5_series`, `built_centroid`, `_cds_retrieve`, `_open_zip`, `_nearest_hour`, `_sum_24h`, `_time_dim`, `_nc_varname`, `_all_nan`, `CDS_DATASET`, and the `built` argument of `weather_layers` |
| `archive.py`, in part | 86 | the archive layout (`coh_store_paths`, `find_coh_store`, `cslc_store_paths`, `coh_store_name`, `COH_GENERATIONS`), `read_time_axis`, `read_populated` |
| `request_config.py`, in part | 121 | the selection section (`SelectionSection`, the rank and gate keys), `RequestConfig`, `find_config_file`, `load_request_config`, `config_dict`, `config_digest`, `DEFAULT_CONFIG` |
| `onboard.py`, in part | 61 | `onboard_burst`, `onboarding_section` (frozen request, then config, then defaults), `_existing_built` (the land anchor of the CDS point route), the parameters `sidecar_only`, `archive`, `edge_margin`, `variables`, `weather_source` (all three are config fields) |

Also removed: `configs/request/{bright,majortom,default}.yaml` (no test or default needs a config file: the defaults are in `OnboardingConfig`), `tests/pipeline/data/` (the BRIGHT fixture tables and their builder), and from the default environment and the extra the packages no kept module imports: `geopandas`, `asf_search`, `shapely`. The extra is now `onboarding = [pyproj, rasterio, requests, cdsapi, netcdf4, fsspec, aiohttp]`: `pyproj`, `rasterio`, `requests` and `cdsapi` are imported by `built` and `weather`; `netcdf4` reads the gridded CDS downloads and `fsspec` with `aiohttp` open the EDH store over https, both through xarray.

### Kept on purpose
- The recorded provenance strings: the sidecar attribute `producer` is still `ponzi_pipeline.onboard` and `era5_pd_source` still starts with `ponzi_pipeline.onboard pairdiff step`, so a sidecar written here is comparable with every existing one. Renaming them is a change to recorded metadata and the owner's call.
- The file names and the stamp logic: a step is skipped when its parameters and the store digest match the stamp and its output exists. A stamp written by the monorepo is honoured when its folder is given as `--out` (the step parameters have the same form).
- The engine report comparison (65 lines, self-contained). Its catalogue lists the store checks only; the comparison is unchanged, because it always compared only the checks both sides ran.
- `ghsl_cache` and `era5_cache` stay as arguments of `onboard_store` although the request asked to drop them when safe: without a data root there is no shared place left to default to, and the GHSL tiles are large and shared between stores. The defaults are `<out_dir>/ghsl` and `<out_dir>/era5`; `--ghsl-cache` points many stores at one tile folder.
- `frames` stays an argument (and `--frames` a flag beyond the requested command line): it is the only input of the `sample` step. Without it the step is skipped, as before.
- The platform filter of `extract_burst_sample` and its helpers (used by the paper package, tested here on synthetic stores).

### What the paper and the applications used and now find only in the monorepo
From the imports of `packages/ponzi_paper` and `ops` at `ef99d21`:

- Planning and the request: `selection.plan_many`, `load_tracks`, `load_bursts`, `collapse_to_bursts`, `burst_sats`, `AoiSpec`, `BURST_REQUEST_COLUMNS`; `aoi.read_registry`, `write_registry`, `registry_digest`, `RegistrySchema`, `COLUMNS`; `discovery.get_sensor`; `request_config.load_request_config`, `DEFAULT_CONFIG`.
- Request validation: `validate.validate_request`, `validate_burst`, `write_validation`, `write_burst_validation`, `combine_validation`, `report_rows`, `load_validation`, `validated_bursts`, `validation_defects`, `request_aoi_of`, `archive_probe`, `COLUMNS`, and `resolve_store` by burst id.
- Paths and the archive: `paths.data_root`, `request_dir` (and the module `paths`); `archive.find_coh_store`, `read_time_axis`.
- The run loop: `run.run_requests`, `config_dir`, `config_path`, `is_finished`.
- Onboarding by request: `onboard.onboard_burst` (here: `onboard_store` with a path), `sidecar_path` and `sample_path` (here they take the output folder first), `_existing_built`.
- Still in the library under a new path: `ponzi.onboarding.onboard` (`PROCESS_MASK_VAR`, `INTERLEAVED_REVISIT_MAX_D`, `extract_burst_sample`, `open_sidecar`, `platform_time_index`, `read_frames`, `sidecar_mask`, `write_sidecar`, `pairdiff_layers`, `_store_axes`), `ponzi.onboarding.{built,weather,validate}`, and all of the old `evaluation` module as `ponzi.evaluation.events` (`BurstQuery`, `DESIGN_COLUMNS`, `LOWER_IS_BETTER`, `across_events`, `concat_rows`, `event_metric`, `event_rows`, `pool_rows`, `pooled`, `read_design_table`, `write_design_table`).

### Layering
`onboarding` may import `contracts` and `core` only (it needs `core` for the process mask, the sample writer and the pair partners). It no longer imports `evaluation`. Importing `ponzi.onboarding` loads none of the geospatial stack; `tests/test_layering.py` checks both.

## Do results change?
No. The steps are untouched: the same functions compute the built-up and land fractions, the ERA5-Land series, the pair differences, the process mask and the sample, and the sidecar and the sample have the same format, names and provenance. No golden file is touched. What differs is plumbing:

- The stamp `onboard_meta.json` no longer has the key `request`, and its `onboarding` entry is the config alone (the keys `source` and `overrides` are gone, there is one source now). The `steps` entry, which decides what is skipped, is unchanged.
- The weather sources `cds` and `auto` are refused by the config. A sidecar made with them keeps its values; rerunning its `weather` step here needs one of the three remaining sources and so refetches.
- Default locations: the caches default to the output folder (they were `<data root>/ghsl` and `<burst folder>/era5`).
- `validate_store` returns a plain `ValidationReport` (it was a subclass carrying the header) and raises `FileNotFoundError` for a path that is not a directory.

## Tests
Self-contained unit tests on synthetic stores, in `tests/onboarding/` (67 tests) with one `conftest.py`: two small fixture stores built once per session and copied per test, `fake_ghsl` (a synthetic GeoTIFF for the tile download) and `fake_edh` (a synthetic hourly dataset for the EDH store). Nothing reads data outside the repository, nothing reproduces an earlier run, no test is marked `slow`.

- `test_onboard.py` (28): the sidecar writer (atomic swap, stale and unreadable sidecars), one full onboarding, the sample, the legacy string tables, the pair differences, the platform filter, and the stamp in three tests where there were seven: skip, rebuild, redelivered store and removed output; a changed parameter reruns only its steps (frames, edge margin, pair-difference baselines); a weather rerun (variables, source) reruns the pair differences. Which steps ran is read off the log, not inferred from call counts.
- `test_weather.py` (19): the EDH extraction, the cell patch, the gridded CDS route and the hybrid. The tests that used the CDS point route as their weather double now use the EDH double.
- `test_validate_store.py` (17): one test per C1 defect, the header, the producer facts including a torn delivery, the engine report.
- `test_commands.py` (3): the config loader, `ponzi onboard`, `ponzi validate-store` (text, `--json`, exit codes).
- `tests/test_evaluation_events.py` (9): the moved evaluation tests, unchanged apart from the import; they were already self-contained.

Deleted with their code: `test_selection.py` (46 tests), `test_validate_request.py` (33), `test_run.py` (22), `test_discovery.py` (15), `test_registry_and_plan.py` (13, two of them reading `ponzi-ccd` data), `test_aggregate_pipeline.py` (12), the request-row and header-cache tests of `test_validate_store.py`, the CDS point tests of `test_onboard.py` and `test_weather.py`, and the fixture modules `asf_fixtures.py` and `fixture_tree.py`.

`pixi run test`: 375 passed, 2 skipped (the two torch modules) in 70 seconds. Before: 524 passed, 2 skipped, 6 deselected (`slow`) in 94 seconds.

## Version
Library: minor while unreleased (the subpackage `ponzi.pipeline` of CR-007 was never in a tagged version). Standard: no effect.
