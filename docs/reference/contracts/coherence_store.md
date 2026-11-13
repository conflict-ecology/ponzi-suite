# C1: Coherence store

`ponzi.contracts.coherence`. The input of every run: one burst's coherence time series on a fixed grid, dense over `(time, y, x, baseline)`. The core reads `revisit_days`, `baseline_days` and the `coh` array and assumes nothing else about the sensor.

## Producer and consumers

Producer: `ponzi_pipeline.assemble.assemble` (`ponzi-pipeline assemble`, worker stage `assemble`). It writes `{burst}.coh.zarr.partial` one acquisition at a time through `CoherenceWriter`, runs the engine's checks, writes the engine report `{burst}.coh.zarr.validation.json` (C18), and on a passing report renames the store to `{burst}.coh.zarr` and writes the `{burst}.coh.zarr_complete` sentinel. A store made elsewhere enters the worker's cache through the stage `ingest-coherence`, which requires the engine report beside it.

Consumers: `ponzi.core.runner.open_input` (which calls `open_coherence_store`), `ponzi.contracts.validate` (`ponzi validate-store`, C15), `ponzi_pipeline.onboard` (reads the store, writes C2 and C3, never the store), `ponzi_models` (panels, training, `export-pixels`, all through `open_input`).

A store is zarr v3: the writers write it, and the opener refuses another zarr format. Archive stores are immutable. The reader never accepts a flat `(sample, y, x)` layout; converting one is a producer concern.

## Arrays and tables

| Name | Dims | dtype | Fill | Chunks | Notes |
|---|---|---|---|---|---|
| `coh` | `(time, y, x, baseline)` | float32 | NaN | `(1, Y, X, B)` | NaN = no pair or no data. The time chunk MUST be 1; spatial chunks smaller than the grid are allowed (warn); the baseline chunk is unconstrained |
| `time` | `(time,)` | datetime64[ns] | | | Strictly increasing dates of the later image of each pair; an assembled series lists every acquisition, also those without a pair. `validate-store` fails `time_axis` on an axis of another dtype (`ponzi.contracts.time_axis.decode_time`) |
| `y`, `x` | `(y,)`, `(x,)` | float64 | | | Pixel-centre coordinates in `epsg` |
| `baseline` | `(baseline,)` | int32 | | | Index `0..B-1`; the days are in the attrs |
| `valid_pixels` | `(y, x)` | uint8 | 0 | any | Required. 1 where the burst footprint has data (`CoherenceWriter`: where any acquisition is finite) |
| `n_finite` | `(time, baseline)` | int32 | 0 | any | Optional here, required of the engine by C18. Finite pixels the producer wrote into the cell, counted while writing; 0 for an unwritten pair. It is how PONZI judges availability without reading the data |
| `bperp` | `(time, baseline)` | float32 | NaN | | Optional. Perpendicular baseline of the pair; an assembled store leaves it out when no pair has one |
| `platform`, `platform_secondary` | `(time, baseline)` | str | "" | | Optional. Platform of each image of the pair; a non-empty `platform` marks a declared pair |
| `secondary_date` | `(time, baseline)` | datetime64[ns] | NaT | | Optional. Earlier image of the pair; when present it gives the pair partners of the runner's pair transforms and of the sidecar's `era5_pd_*` (C2) |
| `cell_quality` | `(time, baseline)` | | | | Optional producer table; nonzero = a low-validity cell |

Any other variable is preserved. The runner reads every `(time,)` and `(time, baseline)` variable as a forecaster covariate (`runner._time_covariates`: numeric ones as float32, the baselines subset to the run's) and the `(y, x)` layers `built` and `land`, when present, as the L0 strata. Every array carries `dimension_names`, so xarray opens the store directly.

## Attrs

| Attr | Type | Meaning |
|---|---|---|
| `baseline_days` | list[int], len B, strictly increasing, positive | Temporal baseline of position `b` in days |
| `revisit_days` | int > 0 | Nominal acquisition cadence |
| `epsg` | int | CRS of `y`, `x` |
| `burst_id` | str | Identifier of the grid, copied into every output. Without it the reader takes the file name without `.coh.zarr`, `_coh.zarr` or `.zarr` |
| `sensor` | str | e.g. `S1`. Read as `S1` when absent |
| `producer` | str | The writer (`ponzi-pipeline {version}` for an assembled store). Read as the empty string when absent |
| `contract_version` | str | the hash of the contract's declaration (ponzi-core CR-085; pinned in `test_contract_versions.py`): its variables, dims, dtypes, attrs, meta model and the check thresholds and catalogue of C18. Read as empty when absent; `validate-store` warns when it is not ours |
| `relative_orbit`, `orbit_state` | int, str | Optional (`ponzi.contracts.orbit`): the track and `ascending` or `descending`. Without them the track comes from a `burst_id` of the form `tNNN_NNNNNN_iwN` and the state is unknown |
| `estimator_params` | JSON str or dict | Optional: `looks_rg`, `looks_az`, `sigma_rg`, `sigma_az` of the coherence estimator, optionally `truncate` (the Gaussian window's truncation in sigmas; without it the half width is 2 samples) and `kind`. From it `noise_floor` derives the zero coherence level used by `state_machine.noise_floor: derived` (C4) and by the ceiling. An assembled store records it from its coherence spec (`ponzi_pipeline.assemble.estimator_params`) |
| `coherence_spec`, `coherence_spec_hash` | JSON, str | An assembled store: its `ponzi_pipeline.coherence_spec.CoherenceSpec` and its `spec_hash` |
| `n_pairs_packed`, `n_cell_collisions`, `estimation_strategy` | | Optional producer bookkeeping read by the validator (`pairs_declared`, `generation`) |

Every attr is preserved and copied into the run's output stores (C7).

## Invariants

- `time` strictly increasing; `len(baseline_days) == B`.
- `coh` finite values lie in `[0, 1]`.
- `valid_pixels` has at least one nonzero pixel.
- The optional pair tables `bperp`, `platform`, `platform_secondary`, `secondary_date`, `n_finite`, when present, are `(time, baseline)`.
- Overlap rule used everywhere downstream: channel `(b, h)` is valid iff `baseline_days[b] > h * revisit_days`.
- A scoring spec fits a store when its `scoring.baseline_days` are a subset of the store's (any order, matched by value) and `context.C + scoring.H <= T` (`runner.check_config_compat`, the one check the runner makes).

How a delivered store is judged (the checks, their thresholds and severities): C15 and the catalogue of [C18](engine_report.md#the-catalogue).

## Functions

`ponzi.contracts.coherence`:

- `CoherenceMeta` (pydantic): the attrs above plus `T, Y, X, B` and the chunk shape; built from a store, never by hand.
- `open_coherence_store(path, sidecar=None) -> CoherenceDataset`: opens the store and parses the meta without validating (`coherence_meta` raises `ContractError` only on what makes a store unreadable: no `coh`, a wrong rank or dimension order, no `valid_pixels`, no `baseline_days`, `revisit_days` or `epsg`), merges the sidecar (C2, the sidecar wins), and returns `.ds`, `.meta`, `.coh` (lazy), `.valid_pixels` (uint8 ndarray, fill applied), `.time` (DatetimeIndex) and `.baseline_index(days)`.
- `write_coherence_store(path, ds, chunks=None, *, consolidate=True)`: a conforming v3 store, every array other than `coh` in one chunk.
- `CoherenceWriter(path, time, y, x, baseline_days, attrs, tables=None)`: the same format one acquisition at a time; `write(t, slab)` writes a `(Y, X, B)` slab and counts `n_finite`, `finish(tables, attrs)` writes the remaining tables, `n_finite` and `valid_pixels` and consolidates.
- `noise_floor(attrs)`: the estimator's zero coherence level from `estimator_params`; ValueError when the store records none.
- `ponzi.contracts.fixtures.make_coherence_fixture(path, **options)`: a synthetic store for the tests (deterministic pairs, a no-data column, optional empty slices, a missing or empty footprint, absent attrs, unconsolidated metadata).
