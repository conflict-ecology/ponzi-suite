# CR-102: input layers in place of the coherence store and its sidecar, and SAR features made from CSLCs

- **Requested by / date:** owner, 2026-11-13 ("PONZI should probably have different modules for CSLC creation and feature creation from CSLC (currently just coherence computation but might test some other coherence estimation techniques plus some other outputs like amplitude which would all take CSLC but produce different outputs). And then instead of having coherence + sidecar we could just have a general "input data" format that can contain pairwise or timestep specific variables (coherence, amplitude, weather, LUC, etc.) and then the model just splits into input data it forecasts vs input data used as covariates"; "draft all of 1 and 2 together")
- **Status:** draft
- **Builds on:** CR-008 (onboarding, the sidecar), CR-032 (the coherence chain, the engine report; its D4 left the CSLC route out), CR-085 (contract versions), CR-089 and CR-091 (standard keys), CR-099 (the tiered home).
- **Touches:** CR-101 parts (b) to (e), not started: their appended "coherence store and sidecar" become appended layers (D8).
- **Leaves for a later request:** per-pixel covariates read by the forecasters (amplitude, land use as model inputs: CR-103), and forecasting a variable other than coherence. This request stores, validates and samples such variables; no model reads them yet.

## Why
Two limits of today's layout block the experiments the lab wants next:

1. **The chain makes one output.** `ponzi_pipeline.coherence.isce3.process_pair` runs coregistration, the interferogram, the estimator and geocoding as one step per pair, and keeps only the coherence raster. Testing another coherence estimator means a new backend; an amplitude series cannot be made at all, though it needs the same SLCs, orbits, DEM and geometry. The coregistered SLCs are never kept, so each experiment repeats the costliest step.
2. **Inputs come in two fixed shapes.** A run reads one coherence store (C1, `coh` and the pair tables) and one sidecar (C2, the onboarding's weather, `built`, `land`, `process_mask`), merged at open with the sidecar winning. The name `coh` is written into the contracts, the engine checks, the sample, the runner and the models (about 58 places). A second coherence estimate or an amplitude variable has no defined place, and a run cannot say which variable it forecasts.

Much of the general form exists already: `open_coherence_store(path, sidecar)` merges the two; `runner._time_covariates` reads every `(time,)` and `(time, baseline)` variable of the merged dataset as a covariate; a model's `fcov_spec` names the covariates it reads. This request makes that the contract: a run's input is a set of layers on one grid, each variable declares its shape, and the scoring spec names its target.

## What changes

### Part 1. Input layers (C1 and C2 become one contract)

**1.1 A layer.** C1 is renamed *Input layer* and C2 is folded into it. A layer is one zarr v3 store of one burst on the burst's axes, written whole by one producer. A run's input is an ordered list of layers (D1). Today's two files are two layers: the SAR layer (`ponzi-pipeline assemble`) and the onboarding layer (`ponzi-pipeline onboard`).

**1.2 Variable kinds, by dims.** Every data variable is one of:

| Kind | Dims | Time chunk | Examples |
|---|---|---|---|
| `pair` | `(time, y, x, baseline)` | 1 | `coh`, a second coherence estimate |
| `acquisition` | `(time, y, x)` | 1 | `amp_db` |
| `pair_table` | `(time, baseline)` | one chunk | `bperp`, `secondary_date`, `n_finite`, `platform` |
| `series` | `(time,)` | one chunk | `era5_*`, `era5_pd_*` |
| `static` | `(y, x)` | one chunk | `valid_pixels`, `process_mask`, `built`, `land` |

Each data variable carries `long_name`, `units`, `source` (the step and its spec hash) and, where it has one, `valid_range`. A `pair` or `acquisition` variable made by an estimator carries that estimator's parameters in its own `estimator_params` attr. Today that attr belongs to the store, and moving it lets two coherence estimates sit in one input, each with its own noise floor.

**1.3 Layer attrs.** Every layer: `layer` (its name: `sar`, `onboard`, ...), `producer`, `contract_version`, and the grid identity: `burst_id`, `epsg`, `revisit_days`, and `baseline_days` when it has a `baseline` axis. A layer made from another records `source_digest` of it, as the sidecar does today. The SAR layer keeps today's C1 attrs (`sensor`, the orbit attrs, `coherence_spec` as `sar_spec`, the producer bookkeeping).

**1.4 Opening an input.** `ponzi.contracts.input.open_input(layers)` replaces `open_coherence_store(path, sidecar)`. It checks that every layer has the same `time`, `y`, `x` and, where present, `baseline_days`, `epsg` and `burst_id`, then merges. A variable name found in two layers is refused (D2), where today the sidecar wins. Recognising a C3 sample by its `pix` dimension stays as it is.

**1.5 Legacy stores.** A store written to C1 before this change, with or without its C2 sidecar, opens as a SAR layer (and an onboarding layer). Its store-level `estimator_params` is read as the `estimator_params` of `coh`. Archive stores are immutable and are never rewritten: they are read through this path.

**1.6 What a run forecasts.** The scoring spec gets `scoring.target` (default `coh`): the `pair` variable the run forecasts and scores. In this request it must be a `pair` variable with `valid_range` `[0, 1]` and an `estimator_params` that gives a noise floor, which every coherence estimator does. Any other target is refused with that reason. `noise_floor` is read from the target's `estimator_params`.

The rest of the input is read as today: every `pair_table` and `series` variable is a covariate the forecasters may name in `fcov_spec`, and `built` and `land` are the L0 strata. Other `pair`, `acquisition` and `static` variables are checked and carried into the sample (1.8), but not read by a run.

**1.7 Run requests and commands.** `RunRequest.inputs: list[path]` replaces `coh`, `sidecar` and `extra_sidecar` (`runner.merge_extra_series` becomes one more layer); `ponzi run --input PATH` (repeatable) replaces `--coh` and `--sidecar`, which remain as deprecated spellings of `--input` for one major. `ponzi validate-store` validates a layer, or an input with `--input` repeated (the cross-layer checks of 1.4).

**1.8 The pixel sample (C3).** The sample copies every `pair` and `acquisition` variable of the input as `(time, pix, baseline)` and `(time, pix)`, every `static` one as `(pix,)`, and every `pair_table` and `series` as today. The variables keep their names and attrs. `coh` is no longer special in C3 except as the default target.

**1.9 The engine report (C18).** The checks that name `coh` today (`structure`, `dtype`, `range`, `chunking`, `chunk_completeness`, `finite_fraction`, `availability_matrix`) run on every `pair` and `acquisition` variable of a SAR layer. `range` checks against each variable's `valid_range`. The report gets one row per check and variable. `n_finite` becomes per variable: `n_finite_<name>`, with `n_finite` kept as the target's count. The file keeps its name pattern with the layer's name: `{burst}.sar.zarr.validation.json`.

**1.10 Names on disk and in the cache** (D3). A SAR layer is `{burst}.sar.zarr` and an onboarding layer `{burst}.onboard.zarr`. The worker's collections `ponzi-coherence` and `ponzi-sidecar` become one collection, `ponzi-input-layer`, with the property `ponzi:layer`. The stage `run` takes `inputs: ponzi-input-layer[]`, `onboard` takes the SAR layer and writes an onboarding layer, and `ingest-coherence` becomes `ingest-layer` (a SAR layer still needs its engine report). Items of the old collections stay readable as layers.

### Part 2. CSLCs and features

**2.1 The SAR spec** (D7). `CoherenceSpec` becomes `SarSpec` (`specs/sar_specs/`) in two blocks:

```yaml
backend: isce3
polarisation: VV
platforms: [S1A]
revisit_days: 12
baseline_days: [12, 24, 36, 48, 60]
pair_tolerance_days: 1
grid: {posting_m: 40.0, buffer_m: 0.0}
dem: {source: glo_30, margin_km: 5.0}
cslc:
  coregistration: pair        # pair (today's chain) | stack (one reference for the series)
  reference: first            # stack only: the acquisition every other one is coregistered onto
features:
  - {name: coh, kind: coherence, looks: {range: 10, azimuth: 2},
     window: {kind: gaussian, sigma_range: 1.0, sigma_azimuth: 1.0, truncate: 2}}
  - {name: amp_db, kind: amplitude, looks: {range: 10, azimuth: 2},
     window: {kind: gaussian, sigma_range: 1.0, sigma_azimuth: 1.0, truncate: 2}, calibration: beta0}
```

A coherence spec in today's form is read as a SAR spec with `coregistration: pair` and one feature `coh` of kind `coherence` with its looks and window. It keeps its `spec_hash`: a spec equal to a legacy one hashes in its legacy form, so existing standards keep their keys. `specs/coherence_specs/isce3-gaussian.yaml` stays as it is.

**2.2 The CSLC module** (`ponzi_pipeline.cslc`). It produces coregistered complex SLCs on one radar grid:

- `pair` (default, D4): today's chain, unchanged. For each pair, the reference SLC as is and the secondary resampled onto it (`topo` per reference, `coregister`). Nothing is kept beyond the pair's work folder, as today.
- `stack`: one reference acquisition per burst series (`reference: first`). Its `topo` runs once, every other acquisition is coregistered onto it once (Geo2Rdr, ResampSlc with the azimuth carrier), and each result is kept as that acquisition's CSLC: a full-resolution complex64 GeoTIFF in the reference's radar geometry. The CSLC is a cache entry (`ponzi-cslc`, D5) whose content id is (the SLC, the orbit, the reference's SLC and orbit, the DEM, the spec's `cslc` block and `polarisation`). A pair then costs one multiply instead of one coregistration, and a new acquisition costs one coregistration instead of B. This is what makes the CR-101 append cheap.

**2.3 The features module** (`ponzi_pipeline.features`). A feature is an estimator with one of two signatures, a registered `kind`, and the parameters that fill its variable's `estimator_params`:

- a pair feature: `(ref, sec) -> float32 raster` on the multilooked radar grid, `(ref, sec)` complex on one radar grid;
- an acquisition feature: `(slc, calibration) -> float32 raster` on the multilooked radar grid.

Every feature's raster is geocoded onto the burst lattice by the one shared `geocode` (today's `GeocodeFloat32` INTERP onto the lattice; the radar grid comes from the feature's looks). Kinds in this request:

- `coherence`: today's estimator (`coherence/estimator.py` moves to `features/coherence.py`, byte-identical), with `noise_floor` as part of its kind. A new coherence estimator is a new kind with its own window block and its own noise floor. A kind without a noise floor cannot be a run's target (1.6).
- `amplitude` (D6): calibrated beta0 power from the burst's calibration (s1reader), the same NaN-aware multilook and window as coherence, in dB, `valid_range` `[-50, 20]`. No terrain flattening (gamma0, RTC) in this request.

**2.4 Stages and commands.** The pipeline's stages become `discover`, `dem`, `cslc` (stack only: one job per acquisition), `features` (one job per pair for the pair features, one per acquisition for the acquisition features; in `pair` mode a pair job coregisters first, as `coherence` does today), and `assemble` (every feature's rasters into the SAR layer, one acquisition at a time). The work folder keeps `rasters/{date}_{b}_{name}.tif` and `rasters/{date}_{name}.tif`, plus `cslc/{date}.slc.tif` in stack mode. `ponzi-pipeline coherence` stays as an alias of `features` for one major. The worker's stages follow (`ponzi_worker.stages.pipeline`).

**2.5 What stays.** `ponzi.grid`, the burst lattice, discovery, pairing (`pairs.py`), the DEM, orbits and acquisition are unchanged. So are the onboarding steps, except that they write an onboarding layer.

### Docs
Contracts: C1 (rewritten as *Input layer*), C2 (retired; points to C1), C3, C18, C17 (the onboarding writes a layer), C4 (`scoring.target`, the noise floor's source), `run_request.md`, `command_args.md`, `staged_store.md` and C7 where they name C1. Method: `method/coherence.md` (CSLCs, features, the two coregistration modes, amplitude). Using: `using/` pages naming `--coh` and `--sidecar`. Service: `service/worker.md` (the collection, the stages). The API reference. ponzi-visual if it shows `ponzi-coherence` or `ponzi-sidecar` Items (its own change).

## Do results change?
- **Part 1: no**, and that is the condition. Every scoring spec over every existing store, opened as legacy layers, gives bit-for-bit the outputs it gives today, and the golden files under `packages/core/tests/data/` are not regenerated. The one behaviour that changes is a name found in two layers: refused, where today the sidecar wins (D2). Before the change lands, every store and sidecar in the archive is scanned for such a name.
- **Part 2, `coregistration: pair` with feature `coh`: no.** The rasters equal today's `process_pair` byte for byte, and the assembled `coh` equals today's store.
- **Part 2, `coregistration: stack`: RESULTS-CHANGING** for any store made with it. Both images of a pair are resampled (except pairs with the stack reference), the coregistration spans the whole series, and the coherence values will differ from the pair chain. It is a new SAR spec hash, so it is a new store and needs a new standard to be run. Before a standard uses it, a comparison on bursts from the benchmark (pair against stack: the distribution of `coh` per baseline, and the scores and events of the current champion on both) is run on the cluster and reported. That run is the owner's (compute), not part of the implementation.
- **Amplitude:** a new variable that no run reads. No existing result changes.

## Tests
- **Layers** (ponzi): a legacy store and sidecar open as two layers equal to today's `open_coherence_store(path, sidecar)` dataset. A name in two layers is refused. Mismatched `time`, `y`, `x`, `baseline_days`, `epsg` or `burst_id` is refused, each with its reason. Each kind's dims and chunks are checked, and a variable of no kind fails `structure`.
- **Parity** (ponzi): the golden tests unchanged, run once through `--coh`/`--sidecar` and once through `--input`. `scoring.target` naming a second coherence variable scores that variable. A target that is not `pair`, outside `[0, 1]` or without a noise floor is refused.
- **Sample** (ponzi): a sample of an input with an `acquisition` variable carries it as `(time, pix)`. A sampled run equals the full run at the sampled pixels, as today.
- **Engine agreement** (ponzi-pipeline, `test_engine_agreement.py`): the shared checks agree per variable on a two-variable SAR layer, on a float64 variable, and on an absent chunk of either variable.
- **Spec** (ponzi-pipeline): `isce3-gaussian.yaml` loads as a SAR spec with its old `spec_hash`. A spec differing in any field of `cslc` or `features` gets another hash.
- **Features** (ponzi-pipeline): `features.coherence` equals the old estimator on the reference implementation's bytes. `amplitude` against a hand-computed multilook of a synthetic SLC with a constant calibration. In the `isce3` environment with its test burst, the pair mode's raster equals today's `process_pair` byte for byte.
- **Stack** (ponzi-pipeline, `isce3` environment): the stack reference's CSLC equals its SLC. A pair's coherence from two stack CSLCs is within a stated tolerance of the pair chain's on the test burst (the tolerance is reported, not assumed). A CSLC evicted and remade is byte-identical.
- **Worker** (ponzi-worker): the stages with the new collection. A job on a legacy `ponzi-coherence` Item runs. `ingest-layer` refuses a SAR layer without its engine report.
- **Models** (ponzi-models): `open_input` callers (panels, training, `export-pixels`) on legacy and new inputs. Panels from the same data are unchanged.

## Decisions for the owner
- **D1. Layout** — recommended: one store per layer, as today's two files, each its own cache entry; a run names its layers. The alternative, one zarr with a group per layer, ties the immutable SAR part to the re-runnable onboarding in one path and one cache entry.
- **D2. A name in two layers** — recommended: refused. Today the sidecar wins, which lets a layer silently replace a variable. A layer that is meant to replace another is a new layer, made instead of the old one.
- **D3. Names** — recommended: new names (`{burst}.sar.zarr`, `{burst}.onboard.zarr`, the collection `ponzi-input-layer`, the stage `ingest-layer`), old ones read. The alternative keeps `.coh.zarr`, `_covariates.zarr`, `ponzi-coherence` and `ponzi-sidecar` and changes only their contents. That is less churn, but the names then lie.
- **D4. Default coregistration** — recommended: `pair` until the comparison (Do results change?) is done. Stack is opt-in by spec.
- **D5. CSLC retention** — recommended: a cache entry in the warm tier (CR-099), evictable and remade from the SLC on demand. A burst's CSLC is in the order of a few hundred MB per acquisition, so a year of one burst is several GB. The alternative is keeping CSLCs in the archive as a product.
- **D6. Amplitude** — recommended: beta0 in dB, with the coherence's looks and window, no terrain flattening. Gamma0 (RTC, ISCE3) is a later kind if amplitude proves useful. Sigma0 or linear power are the other choices.
- **D7. The spec's name** — recommended: `SarSpec`, `specs/sar_specs/`, with `coherence_specs` read and their hashes kept. The alternative keeps `CoherenceSpec` for a spec that now makes more than coherence.
- **D8. Order** — recommended: (a) part 1, the layers and `scoring.target`; (b) the features module and the pair mode refactored onto it, with byte parity, and amplitude; (c) the stack mode and the CSLC cache entry; (d) the comparison run (owner, cluster). Each part is implemented and reviewed on its own. Part (a) lands before CR-101 part (b), so the burst series appends layers and is written once.

## Version
`ponzi` major (C1 rewritten, C2 retired, C3 and C18 changed, `open_input`, `RunRequest.inputs`, `scoring.target`; contract versions change). `ponzi-pipeline` major (the SAR spec, the stages, the layer names, the `cslc` and `features` modules). `ponzi-spec` major (the collection `ponzi-input-layer`, the run payload's inputs). `ponzi-models` minor (callers of `open_input`). ponzi-worker major (stages and collections); ponzi-server minor if it lists the collections. Standard: the specs a standard names keep their hashes (legacy SAR spec hashing, `scoring.target` defaulting to `coh`). But a standard's `requires` must be raised to the new majors to run on them, and that alone makes a new key (CR-101 D6). The new key's outputs equal the old key's by the parity above. If CR-101's raise and this one land in the same release, a standard needs only one new key. A standard using `stack` or reading another target is a new key in any case.
