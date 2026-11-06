# C3: Pixel sample

> Note (CR-008, 2026-10-12): the onboarding sample is written here by `ponzi_pipeline.onboard.onboard` (command `ponzi-pipeline onboard --store PATH --out DIR --frames FILE`) as `<out_dir>/samples/<burst>_sample.zarr`. A panel's pixel export (`ponzi-models export-pixels`) writes the same format as `{OUT}/bursts/{burst}/{burst}_{layer}.zarr`.

Status: implemented 2026-09-07, `ponzi.core.sample`.

## Purpose

A frozen set of pixels of one burst, extracted once from the coherence store, so that a run over the sample is the same computation as the full run at those pixels at a fraction of the cost. The runner accepts it in place of a coherence store.

## Producer and consumers

Producers: `ponzi.core.sample.extract_sample` (core), driven by `ponzi_pipeline.onboard.onboard.extract_burst_sample` (which opens the store with its sidecar, gathers the frames' `(y, x)` layers, codes the frame and stratum columns and normalises the pair-table dtypes), the `sample` step of `onboard_store`; and `ponzi_models.panels.export_pixels` (through `write_sample_store`, from the masked input of a panel). Consumers: `ponzi.core.runner` (through `open_input`, which recognises a sample by its `pix` dimension; a sidecar or a mask store on a sample is refused), `ponzi_models` (`training.prepare`, `export-pixels --check`), and anything that maps a sampled run back to the source grid (`unfold` with `pix_y`, `pix_x`).

## Arrays and tables

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `coh` | `(time, pix, baseline)` | float32 | NaN | The sampled coherence, all baselines of the source or a subset |
| `time` | `(time,)` | datetime64[ns] | | Copied from the source |
| `baseline` | `(baseline,)` | int | | Index |
| `pix_y`, `pix_x` | `(pix,)` | int32 | | Row and column of each pixel on the source grid |
| `weight` | `(pix,)` | float64 | NaN | Optional, producer-defined |
| `frame_code`, `stratum_code`, `label` | `(pix,)` | uint8 | 0 | Optional codes; the onboarding codes a frames column from 1 in name order (0 = none), names in attrs `frame_names`, `stratum_names`. `label` is the frames' column as is, a diagnostic (an evaluation reads a label store, never this) |
| `built`, `land` | `(pix,)` | float32 | NaN | Optional per-pixel covariates, from the store or its sidecar |
| every `(time,)` and `(time, baseline)` variable | | | | Copied from the source (the pair tables, `n_finite`, the sidecar's `era5_*` series), the baselines subset with `coh` |

Chunks: `coh` as `(T, min(4096, n_px), B)`, every other array one chunk; zarr v3, consolidated. Reads are whole-cache. There are no `y`, `x` arrays. `frames.parquet` (the selection table: `y`, `x` and the optional `weight`, `frame`, `stratum`, `label`) is a pipeline artefact, not part of this contract.

## Attrs

| Attr | Type | Meaning |
|---|---|---|
| every attr of the source store | as C1 | Copied first, then the ones below are set |
| `baseline_days`, `revisit_days`, `epsg`, `burst_id`, `sensor` | as C1 | Of the source (`baseline_days` of the extracted baselines) |
| `producer`, `contract_version` | str, int | `ponzi.core.sample` (export: `ponzi-models export-pixels`), 1 |
| `source_store`, `source_digest` | str | Name and structural digest of the coherence store |
| `edge_margin` | int | The boundary margin the pixels were drawn with; it is the sample's own property, stamped into `run_meta.pixels.edge_margin` and `ponzi_edge_margin` (C7) by a run over the sample (no scoring spec carries a margin, so there is nothing to match; the onboarding stage takes it from the `edge_margin` attr of the sidecar's `process_mask`). Required |
| `n_px` | int | Number of pixels |
| `frame_names`, `stratum_names` | JSON str | Optional: `{code: name}` of the code arrays |
| `platform_filter`, `n_time_source`, `n_time_kept` | str, int, int | Optional: written when `extract_burst_sample` is called with `platform` (the acquisitions whose primary image is that platform, e.g. a 6-day S1A/S1B store cut to its 12-day S1A series); `revisit_days` is then the recomputed one |
| `export_*` | | Optional: the provenance of a `ponzi-models export-pixels` store |

## Invariants

- The pair tables travel in a dtype a zarr v3 store can hold: the legacy (zarr v2) archive stores keep `platform` and `platform_secondary` as VLenUTF8, which xarray hands back as numpy `object`, and `ponzi_pipeline.onboard.onboard.writable_time_tables` casts those to fixed width unicode (and object dates to `datetime64[ns]`) before the extraction; a `(time,)` or `(time, baseline)` table with no writable form is left out of the sample with a logged note. They are carried rather than dropped because the runner hands every such variable to the forecaster as a covariate (`runner._time_covariates`), so a sampled run must see what the full run sees.
- `pix_y`, `pix_x` are inside the source grid and unique as pairs.
- Folded grid: `G = ceil(sqrt(n_px))`, pixels row-major, padding cells invalid; the folded grid is processed whole (no second erosion).
- A run over the sample equals the full run at `(pix_y, pix_x)` bit for bit, for every C7 and C8 array.

## Functions

`ponzi.core.sample`: `SampleMeta`, `SampleDataset`, `open_sample_store` (validates, raises on a failed check), `validate_sample_store` (checks `structure`, `baseline_days`, `revisit_days`, `crs`, `edge_margin`, `pixels` (unique pairs), `identity` (fail without `sensor`, `contract_version` or `source_digest`), `consolidated`; `coh` is never read), `is_sample_store`, `write_sample_store`, `extract_sample(coh, pix_y, pix_x, out, *, edge_margin, extra=None, baseline_days=None, path=None)`, `SampleSliceSource`, `sample_grid_meta` (the folded grid of a sampled run's C7 and C8 stores, with `sample_n_px`, `sample_grid_side`, `frames_edge_margin` in their attrs), `grid_side`, `fold`, `unfold`.
