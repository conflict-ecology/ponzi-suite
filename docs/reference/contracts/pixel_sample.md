# C3: Pixel sample

`ponzi.core.sample`. A frozen set of pixels of one burst, extracted once from the coherence store, so that a run over the sample is the same computation as the full run at those pixels at a fraction of the cost. The runner accepts it in place of a coherence store.

## Producer and consumers

Producers: `ponzi.core.sample.extract_sample`, driven by the onboarding's `sample` step (`ponzi_pipeline.onboard.onboard.extract_burst_sample`, `ponzi-pipeline onboard ... --frames FILE`, written as `<out_dir>/samples/<burst>_sample.zarr`), which opens the store with its sidecar, gathers the frames' `(y, x)` layers, and codes the frame and stratum columns; and `ponzi_models.panels.export_pixels` (`ponzi-models export-pixels`, through `write_sample_store`, from the masked input of a panel, as `{OUT}/bursts/{burst}/{burst}_{layer}.zarr`).

Consumers: `ponzi.core.runner` (through `open_input`, which recognises a sample by its `pix` dimension or a `pix_y` array; another layer, a sidecar or a mask store on a sample is refused; a run's `scoring.target` may name another `pair` variable the sample carries), `ponzi_models` (training, `export-pixels --check`), and anything that maps a sampled run back to the source grid (`unfold` with `pix_y`, `pix_x`).

## Arrays and tables

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `coh` | `(time, pix, baseline)` | float32 | NaN | The sampled coherence, all baselines of the source or a subset |
| `time` | `(time,)` | datetime64[ns] | | Copied from the source |
| `baseline` | `(baseline,)` | int32 | | Index |
| `pix_y`, `pix_x` | `(pix,)` | int32 | | Row and column of each pixel on the source grid |
| `weight` | `(pix,)` | float64 | NaN | Optional, producer-defined |
| `frame_code`, `stratum_code`, `label` | `(pix,)` | uint8 | 0 | Optional codes; the onboarding codes a frames column from 1 in name order (0 = none), names in the attrs `frame_names`, `stratum_names`. `label` is the frames' column as is, a diagnostic (an evaluation reads a label store, C11) |
| `built`, `land` | `(pix,)` | float32 | NaN | Optional per-pixel covariates, from the store or its sidecar |
| every `(time,)` and `(time, baseline)` variable | | | | Copied from the source (the pair tables, `n_finite`, the sidecar's `era5_*` series), the baselines subset with `coh` |
| every other `pair` variable of the input's layers | `(time, pix, baseline)` | as the source | NaN | CR-102: with its attrs, on the sample's baselines; chunked as `coh` |
| every `acquisition` variable | `(time, pix)` | as the source | NaN | CR-102: with its attrs; chunked `(T, min(4096, n_px))` |
| every other `static` variable | `(pix,)` | as the source | | CR-102: with its attrs; not the masks `valid_pixels` and `process_mask` (the fold replaces them), and not a name `extra` gives |

Chunks: `coh` `(T, min(4096, n_px), B)`, every other array one chunk. There are no `y`, `x` arrays. `frames.parquet` (the selection table: `y`, `x` and the optional `weight`, `frame`, `stratum`, `label`) is a pipeline artefact, not part of this contract.

## Attrs

| Attr | Type | Meaning |
|---|---|---|
| every attr of the source store | as C1 | Copied first, then the ones below are set |
| `baseline_days`, `revisit_days`, `epsg`, `burst_id`, `sensor` | as C1 | Of the source (`baseline_days` of the extracted baselines) |
| `producer`, `contract_version` | str, str | `ponzi.core.sample` (an export: `ponzi-models export-pixels`), the hash of the contract's declaration (ponzi-core CR-085; pinned in `test_contract_versions.py`); another fails `identity` |
| `source_store`, `source_digest` | str | Name and structural digest of the coherence store |
| `edge_margin` | int | Required. The margin the pixels were drawn with (the onboarding takes it from the sidecar's `process_mask`, C2); a run over the sample stamps it into `run_meta.pixels.edge_margin` and `ponzi_edge_margin` (C7) |
| `n_px` | int | Number of pixels |
| `frame_names`, `stratum_names` | JSON str | Optional: `{code: name}` of the code arrays |
| `platform_filter`, `n_time_source`, `n_time_kept` | str, int, int | Optional: written when `extract_burst_sample` is called with `platform` (the acquisitions whose primary image is that platform, e.g. a 6-day S1A/S1B store cut to its 12-day S1A series); `revisit_days` is then the recomputed one |
| `export_*` | | Optional: the provenance of a `ponzi-models export-pixels` store |

## Invariants

- The pair tables travel as the coherence store holds them. They are carried because the runner hands every such variable to the forecaster (`runner._time_covariates`), so a sampled run sees what the full run sees.
- `pix_y`, `pix_x` are inside the source grid and unique as pairs.
- Folded grid: `G = ceil(sqrt(n_px))`, pixels row-major, padding cells invalid; the folded grid is processed whole (no second erosion). A sampled run's output stores carry `sample_n_px`, `sample_grid_side` and `frames_edge_margin` in their attrs (`sample_grid_meta`).
- A run over the sample equals the full run at `(pix_y, pix_x)` bit for bit, for every C7 and C8 array.

## Functions

`ponzi.core.sample`: `SampleMeta`, `SampleDataset`, `open_sample_store` (validates), `validate_sample_store` (checks `structure`, `baseline_days`, `revisit_days`, `crs`, `edge_margin`, `pixels` (unique pairs), `identity` (fail without `sensor`, `contract_version` or `source_digest`), `consolidated`; `coh` is never read), `is_sample_store`, `write_sample_store`, `extract_sample(coh, pix_y, pix_x, out, *, edge_margin, extra=None, baseline_days=None, path=None)`, `SampleSliceSource`, `sample_grid_meta`, `grid_side`, `fold`, `unfold`.
