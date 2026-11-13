# C1: Input layers

`ponzi.contracts.input` and `ponzi.contracts.coherence`. The input of every run (CR-102): an ordered list of LAYERS, zarr v3 stores of one burst on the burst's axes, each written whole by one producer. The SAR layer holds the coherence time series on a fixed grid, dense over `(time, y, x, baseline)`; the onboarding layer holds the weather series and the static layers the onboarding makes (`built`, `land`, `process_mask`; it was the covariates sidecar, C2). The core reads `revisit_days`, `baseline_days` and the target array (`coh` unless the scoring spec names another, `scoring.target`) and assumes nothing else about the sensor.

A coherence store written before CR-102 (`{burst}.coh.zarr`) is a SAR layer as it stands, and a covariates sidecar (`{burst}_covariates.zarr`) an onboarding layer: both are read, never rewritten.

## Producer and consumers

Producers: the SAR layer, `ponzi_pipeline.assemble.assemble` (`ponzi-pipeline assemble`, worker stage `assemble`). It writes `{burst}.sar.zarr.partial` one acquisition at a time through `CoherenceWriter`, runs the engine's checks, writes the engine report `{burst}.sar.zarr.validation.json` (C18), and on a passing report renames the store to `{burst}.sar.zarr` and writes the `{burst}.sar.zarr_complete` sentinel. A layer made elsewhere enters the worker's cache through the stage `ingest-layer` (`ingest-coherence`, its name before CR-102), which requires a SAR layer's engine report beside it. In the cache a layer is a `ponzi-input-layer` Item, its store the asset `layer`, its name `ponzi:layer`; the `ponzi-coherence` and `ponzi-sidecar` Items made before are read as layers. The onboarding layer, `ponzi_pipeline.onboard.onboard_store` (`ponzi-pipeline onboard`, worker stage `onboard`), as `{burst}.onboard.zarr` (the variables and steps of [C2](covariates_sidecar.md)).

Consumers: `ponzi.core.runner.open_input` (which calls `ponzi.contracts.input.open_layers`), `ponzi.contracts.validate` (`ponzi validate-store`, C15), `ponzi_pipeline.onboard` (reads the SAR layer, writes the onboarding layer and C3, never the SAR layer), `ponzi_models` (panels, training, `export-pixels`, all through `open_input`).

A layer is zarr v3: the writers write it, and the opener refuses another zarr format. Archive SAR layers are immutable. The reader never accepts a flat `(sample, y, x)` layout; converting one is a producer concern.

## Variable kinds

Every data variable of a layer is of one kind, read off its dims (`ponzi.contracts.input.KINDS`):

| Kind | Dims | Time chunk | Examples |
|---|---|---|---|
| `pair` | `(time, y, x, baseline)` | 1 | `coh`, a second coherence estimate |
| `acquisition` | `(time, y, x)` | 1 | an amplitude |
| `pair_table` | `(time, baseline)` | one chunk | `bperp`, `secondary_date`, `n_finite`, `platform` |
| `series` | `(time,)` | one chunk | `era5_*`, `era5_pd_*` |
| `static` | `(y, x)` | one chunk | `valid_pixels`, `process_mask`, `built`, `land` |

A variable carries `long_name`, `units`, `source` (the step that made it and its spec's hash) and, where it has one, `valid_range`. A `pair` or `acquisition` variable made by an estimator carries the estimator's `estimator_params`; a store of before CR-102 records them once, in the store's attrs, for `coh`.

## The layers of one input

`open_layers(paths, target)` opens the layers in the order given and refuses them (`ContractError`) unless:

- every axis two layers both carry (`time`, `y`, `x`) has the same values in both, and every dim a layer's variables use has the size of the other layers'. A layer may leave out an axis it has no variable on (a layer of static variables has no `time`);
- the grid attrs (`burst_id`, `epsg`, `revisit_days`, `baseline_days`) are equal in every layer that records them;
- no variable name is in two layers (CR-102 D2; the sidecar's variable won before);
- one layer holds the target, a `pair` variable.

The layer holding the target gives the input's meta (`CoherenceMeta`); the grid attrs it lacks are read off the other layers, and `valid_pixels` may be in any layer. The variables of every layer are merged into one dataset. `ponzi validate-store --input LAYER --input LAYER` reports the same as the check `layers` (C15).

## The SAR layer: arrays and tables

| Name | Dims | dtype | Fill | Chunks | Notes |
|---|---|---|---|---|---|
| `coh` | `(time, y, x, baseline)` | float32 | NaN | `(1, Y, X, B)` | NaN = no pair or no data. Attrs `long_name`, `units` (`1`), `valid_range` (`[0, 1]`), `estimator_params`, `source` (the coherence spec's hash). The time chunk MUST be 1; spatial chunks smaller than the grid are allowed (warn); the baseline chunk is unconstrained |
| `time` | `(time,)` | datetime64[ns] | | | Strictly increasing dates of the later image of each pair; an assembled series lists every acquisition, also those without a pair. `validate-store` fails `time_axis` on an axis of another dtype (`ponzi.contracts.time_axis.decode_time`) |
| `y`, `x` | `(y,)`, `(x,)` | float64 | | | Pixel-centre coordinates in `epsg` |
| `baseline` | `(baseline,)` | int32 | | | Index `0..B-1`; the days are in the attrs |
| `valid_pixels` | `(y, x)` | uint8 | 0 | any | Required. 1 where the burst footprint has data (`CoherenceWriter`: where any acquisition is finite) |
| `n_finite` | `(time, baseline)` | int32 | 0 | any | Optional here, required of the engine by C18. Finite pixels the producer wrote into the cell, counted while writing; 0 for an unwritten pair. It is how PONZI judges availability without reading the data |
| `bperp` | `(time, baseline)` | float32 | NaN | | Optional. Perpendicular baseline of the pair; an assembled store leaves it out when no pair has one |
| `platform`, `platform_secondary` | `(time, baseline)` | str | "" | | Optional. Platform of each image of the pair; a non-empty `platform` marks a declared pair |
| `secondary_date` | `(time, baseline)` | datetime64[ns] | NaT | | Optional. Earlier image of the pair; when present it gives the pair partners of the runner's pair transforms and of the sidecar's `era5_pd_*` (C2) |
| `cell_quality` | `(time, baseline)` | | | | Optional producer table; nonzero = a low-validity cell |

Any other variable is preserved. The runner reads every `(time,)` and `(time, baseline)` variable of every layer as a forecaster covariate (`runner._time_covariates`: numeric ones as float32, the baselines subset to the run's) and the `(y, x)` layers `built` and `land`, when present, as the L0 strata. Every array carries `dimension_names`, so xarray opens the store directly.

## Attrs

| Attr | Type | Meaning |
|---|---|---|
| `layer` | str | The layer's name, `sar` (CR-102). Read as `sar` for a store with `coh` and none |
| `baseline_days` | list[int], len B, strictly increasing, positive | Temporal baseline of position `b` in days |
| `revisit_days` | int > 0 | Nominal acquisition cadence |
| `epsg` | int | CRS of `y`, `x` |
| `burst_id` | str | Identifier of the grid, copied into every output. Without it the reader takes the file name without `.sar.zarr`, `.coh.zarr`, `_coh.zarr` or `.zarr` |
| `sensor` | str | e.g. `S1`. Read as `S1` when absent |
| `producer` | str | The writer (`ponzi-pipeline {version}` for an assembled store). Read as the empty string when absent |
| `contract_version` | str | the hash of the contract's declaration (ponzi-core CR-085; pinned in `test_contract_versions.py`): the kinds, the layer rules, its variables, dims, dtypes, attrs, meta model and the check thresholds and catalogue of C18. An onboarding layer carries the same version. Read as empty when absent; `validate-store` warns when it is not ours |
| `relative_orbit`, `orbit_state` | int, str | Optional (`ponzi.contracts.orbit`): the track and `ascending` or `descending`. Without them the track comes from a `burst_id` of the form `tNNN_NNNNNN_iwN` and the state is unknown |
| `estimator_params` | JSON str or dict | Optional, and since CR-102 also on `coh` itself, which the reader prefers: `looks_rg`, `looks_az`, `sigma_rg`, `sigma_az` of the coherence estimator, optionally `truncate` (the Gaussian window's truncation in sigmas; without it the half width is 2 samples) and `kind`. From it `noise_floor` derives the zero coherence level used by `state_machine.noise_floor: derived` (C4) and by the ceiling. An assembled store records it from its coherence spec (`ponzi_pipeline.assemble.estimator_params`) |
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

`ponzi.contracts.input`:

- `open_layers(paths, target="coh") -> CoherenceDataset`: opens the layers, checks them (above) and merges them; the result's `.layers` lists the opened layers and `.target_path` is the layer holding the target.
- `Layer(path)`, `check_agreement(layers)`, `target_layer(layers, target)`: the pieces of `open_layers`.
- `variable_kind(dims)`, `KINDS`, `layer_name(path, attrs, names)`, `estimator_params(attrs, var_attrs)`.
- `sar_layer_name(burst)`, `onboard_layer_name(burst)`, `is_sar_layer_name(name)`: the file names, new and old.

`ponzi.contracts.coherence`:

- `CoherenceMeta` (pydantic): the attrs above plus `T, Y, X, B` and the chunk shape; built from a store, never by hand.
- `open_coherence_store(path, sidecar=None, target="coh") -> CoherenceDataset`: the store and its sidecar as the two layers of one input (`open_layers`). The meta is parsed without validating (`coherence_meta` raises `ContractError` only on what makes a store unreadable: no target array, a wrong rank or dimension order, no `valid_pixels`, no `baseline_days`, `revisit_days` or `epsg`). Returns `.ds`, `.meta`, `.target`, `.coh` (the target, lazy), `.valid_pixels` (uint8 ndarray, fill applied), `.time` (DatetimeIndex), `.baseline_index(days)` and `.estimator_params()` (the target's, else the store's).
- `write_coherence_store(path, ds, chunks=None, *, consolidate=True)`: a conforming v3 store, every array other than `coh` in one chunk.
- `CoherenceWriter(path, time, y, x, baseline_days, attrs, tables=None, coh_attrs=None)`: the same format one acquisition at a time, with `layer: sar` and the attrs of `coh` (`COH_ATTRS` and `coh_attrs`); `write(t, slab)` writes a `(Y, X, B)` slab and counts `n_finite`, `finish(tables, attrs)` writes the remaining tables, `n_finite` and `valid_pixels` and consolidates.
- `noise_floor(attrs)`: the estimator's zero coherence level from `estimator_params`; ValueError when the store records none.
- `ponzi.contracts.fixtures.make_coherence_fixture(path, **options)`: a synthetic store for the tests (deterministic pairs, a no-data column, optional empty slices, a missing or empty footprint, absent attrs, unconsolidated metadata).
