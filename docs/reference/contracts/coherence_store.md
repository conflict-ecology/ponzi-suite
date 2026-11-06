# C1: Coherence store

> Note (CR-008, 2026-10-12): a store is checked against this contract by `ponzi.contracts.validate.validate_store` (command `ponzi validate-store PATH [--json]`, exit code 1 on a failing check, 2 when there is no store at PATH).

Status: implemented 2026-09-07, `ponzi.contracts.coherence`.

## Purpose

The input of every run: one burst's coherence time series on a fixed grid, dense over `(time, y, x, baseline)`. This is the S1 format today and the NISAR format tomorrow: the core reads `revisit_days`, `baseline_days` and the `coh` array and assumes nothing else about the sensor.

## Producer and consumers

Producer: `ponzi_pipeline.assemble.assemble` (command `ponzi-pipeline assemble`, worker stage `assemble`), which writes `{burst}.coh.zarr.partial` one acquisition at a time through `CoherenceWriter`, runs the engine's checks (`ponzi_pipeline.engine`), writes the engine report `{burst}.coh.zarr.validation.json` (C18), and on a passing report renames the store to `{burst}.coh.zarr` and writes the `{burst}.coh.zarr_complete` sentinel. A store made elsewhere enters the worker's cache (`~/.ponzi/cache/`, collection `ponzi-coherence`) through the worker stage `ingest-coherence`, which requires the engine report beside it. A NISAR producer later.

Consumers: `ponzi.core.runner` (via `open_input`, which calls `open_coherence_store`), `ponzi.contracts.validate` (`ponzi validate-store`), `ponzi_pipeline.onboard.onboard` (reads the store; writes the sidecar C2 and the sample C3, never the store), `ponzi_models` (panels, `training.prepare`, `export-pixels`, all through `open_input`), and the worker stages `onboard` and `run`.

Archive stores are immutable and may be zarr v2. The opener reads v2 and v3; `write_coherence_store` (used by the fixture generator and by any converter) and `CoherenceWriter` write v3. The reader never accepts a flat `(sample, y, x)` layout; converting one is a producer concern.

## Arrays and tables

| Name | Dims | dtype | Fill | Chunks | Notes |
|---|---|---|---|---|---|
| `coh` | `(time, y, x, baseline)` | float32 | NaN | `(1, Y, X, B)` | NaN = no pair or no data. Time chunk MUST be 1 (fail otherwise); spatial chunks smaller than full extent are allowed (warn); the baseline chunk is unconstrained (the legacy archive uses 5) |
| `time` | `(time,)` | datetime64[ns] | | | Strictly increasing acquisition dates of the later image of each pair; the assembled series lists every acquisition, also those without a pair. Legacy v2 stores may hold CF-encoded integers (a `units` attr), decoded on read |
| `y`, `x` | `(y,)`, `(x,)` | float64 | | | Pixel-centre coordinates in `epsg` |
| `baseline` | `(baseline,)` | int | | | Index `0..B-1`; the day value lives in attrs |
| `valid_pixels` | `(y, x)` | uint8 | 0 | any | 1 where the burst footprint has data (`CoherenceWriter`: where any acquisition is finite). Required |
| `n_finite` | `(time, baseline)` | int32 | 0 | any | finite pixels the producer wrote into the cell, counted while writing the slab; 0 for an unwritten pair. Optional in C1, written by `CoherenceWriter` and required of the coherence engine by C18: it is how PONZI judges the availability of the data without reading it |
| `bperp` | `(time, baseline)` | float32 | NaN | | Optional. Perpendicular baseline of the pair. An assembled store leaves the table out when no pair has one (an all-NaN table writes no chunk) |
| `platform`, `platform_secondary` | `(time, baseline)` | str | "" | | Optional. Platform of each image of the pair; a non-empty `platform` marks a declared pair |
| `secondary_date` | `(time, baseline)` | datetime64[ns] | NaT | | Optional. Earlier image of the pair; when present it gives the pair partners of the runner's pair transforms and of the sidecar's `era5_pd_*` |
| `cell_quality` | `(time, baseline)` | | | | Optional producer table; nonzero = a low-validity cell (validator check `cell_quality`) |

Any other variable is preserved. The core reads every `(time,)` and `(time, baseline)` variable as a forecaster covariate (`runner._time_covariates`, numeric ones as float32, the baselines subset to the run's) and the `(y, x)` `built` and `land` layers, when present, as the L0 strata. Coordinates carry `_ARRAY_DIMENSIONS` (v2) or `dimension_names` (v3) so xarray opens the store directly.

## Attrs

| Attr | Type | Meaning |
|---|---|---|
| `baseline_days` | list[int], len B, strictly increasing, positive | Temporal baseline of position `b` in days |
| `revisit_days` | int > 0 | Nominal acquisition cadence; with `baseline_days` defines the overlap mask |
| `epsg` | int | CRS of `y`, `x`. Required: missing fails the `crs` check |
| `burst_id` | str | Identifier of the grid; stamped into every output. When absent the reader falls back to the store filename without `.coh.zarr`, `_coh.zarr` or `.zarr` |
| `sensor` | str | e.g. `S1`, `NISAR`. Legacy stores without it are read as `S1` with a warning |
| `producer` | str | Free text naming the writer (`ponzi-pipeline {version}` for an assembled store). Legacy stores: taken from `writer_command` or `schema`; when neither exists `producer` is reported missing and read as the empty string |
| `contract_version` | int | This contract's version, 1. Legacy stores (no attr) are treated as 0 |
| `relative_orbit`, `orbit_state` | int, str | Optional (`ponzi.contracts.orbit`): the track (from a burst id `tNNN_NNNNNN_iwN`) and `ascending` or `descending`. A store without them gives its track from `burst_id` and no state |
| `estimator_params` | JSON str or dict | Optional: `looks_rg`, `looks_az`, `sigma_rg`, `sigma_az` of the coherence estimator, and optionally `truncate` (the Gaussian window's truncation in sigmas; without it the window's half width is 2 samples) and `kind`, from which `state_machine.noise_floor: derived` and the ceiling floor are computed (`coherence.noise_floor`). An assembled store records it from its `coherence_spec` (`ponzi_pipeline.assemble.estimator_params`) |
| `n_pairs_packed`, `n_cell_collisions`, `estimation_strategy` | | Optional producer bookkeeping read by the validator (`pairs_declared`, `generation`) |

An assembled store also carries `coherence_spec` (the `ponzi_pipeline.coherence_spec.CoherenceSpec` as JSON) and `coherence_spec_hash` (its `spec_hash`; named `coherence_config` and `coherence_config_hash` before CR-070). All producer attrs are preserved and copied into the output stores (C5 to C8). `baseline_days` may also live on the `baseline` array attrs (legacy fixtures); the group attr wins.

## Invariants

- `time` strictly increasing; `len(baseline_days) == B`.
- `coh` finite values lie in `[0, 1]`; NaN elsewhere.
- `valid_pixels` has at least one nonzero pixel; the validator warns below 1 %.
- The optional pair tables `bperp`, `platform`, `platform_secondary`, `secondary_date`, `n_finite`, when present, are `(time, baseline)`; any other shape is a `structure` failure.
- Overlap rule used everywhere downstream: channel `(b, h)` is valid iff `baseline_days[b] > h * revisit_days`.
- A scoring spec's `scoring.baseline_days` must be a subset of the store's `baseline_days` (any order, matched by value), and `context.C + scoring.H <= T`.

## Functions

`ponzi.contracts.coherence`:

- `CoherenceMeta` (pydantic): the attrs above plus `T, Y, X, B` and the chunk shape; built from a store, never hand-written.
- `open_coherence_store(path, sidecar=None) -> CoherenceDataset`: opens v2 or v3, PARSES the meta (no validation: `coherence_meta` raises `ContractError` only on what makes a store unreadable: no `coh`, a wrong rank or dimension order, no `valid_pixels`, no `baseline_days`, `revisit_days` or `epsg`), merges the sidecar (C2, sidecar wins), returns an xarray Dataset wrapper with `.meta`, `.coh` (lazy), `.valid_pixels` (uint8 ndarray with fill applied), `.time` (DatetimeIndex) and `.baseline_index(days)`.
- `write_coherence_store(path, ds, chunks=None, *, consolidate=True)`: writes a conforming v3 store, consolidated.
- `CoherenceWriter(path, time, y, x, baseline_days, attrs, tables=None)`: the same format one acquisition at a time (CR-032); `write(t, slab)` writes a `(Y, X, B)` slab and counts `n_finite`, `finish(tables, attrs)` writes the remaining tables, `n_finite`, `valid_pixels` and consolidates.
- `noise_floor(attrs)`: the estimator's zero coherence level from `estimator_params`; ValueError when the store records none.
- The validator is `ponzi.contracts.validate`: `store_checks` runs the C1 checks below; `validate_store(path, *, expected_generation=None, require_engine_report=False)` adds the producer facts and the engine report comparison of C18 and is what `ponzi validate-store` prints. The runner only refuses a scoring spec that does not fit the store (`runner.check_config_compat`: baselines present, `C + H <= T`).
- `ponzi.contracts.fixtures.make_coherence_fixture(path, *, burst_id=None, T, Y, X, baseline_days, revisit_days, start, seed, bperp=True, n_finite=True, valid_pixels="uint8", empty_slices=(), chunks=None, consolidate=True, sensor="S1", legacy_attrs=False, epsg=32653)`: synthetic store (deterministic pairs, a no-data column, optional empty slices, a missing or empty footprint, legacy attrs, unconsolidated metadata).

Validator checks (name, severity on failure; the full catalogue with thresholds is C18): `structure` (fail), `dtype` (warn on float64 `coh`), `baseline_days` (fail), `revisit_days` (fail), `time_axis` (fail on duplicates or non-monotonic dates; warn when the largest gap exceeds 1.5 times the median spacing), `chunking` (fail when the time chunk is not 1, warn when spatial chunks are tiled), `valid_pixels` (fail when missing or empty, warn below 1 %), `range` (warn when finite values leave `[0, 1]`; sampled, see below), `crs` (fail when `epsg` is missing), `identity` (warn when `sensor`, `producer` or `contract_version` are missing), `consolidated` (warn).

The validator never reads the whole `coh` array: it touches metadata, coordinates, `valid_pixels` and the pair tables once (the store header), lists the chunk files, and for `range` reads baseline 0 of at most two evenly spaced time steps. Whether a declared pair holds data comes from `n_finite`, the producer's count. A store whose out-of-range values sit only in unsampled slabs passes; the bound is a validator constant, not part of the contract.
