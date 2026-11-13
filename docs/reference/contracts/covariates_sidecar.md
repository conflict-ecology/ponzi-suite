# C2: Covariates sidecar (the onboarding layer)

!!! note "Folded into C1 (CR-102)"
    Since CR-102 the sidecar is the onboarding layer of an input ([C1](coherence_store.md)): `{burst}.onboard.zarr`, with `layer: onboard`, C1's `contract_version` and the SAR layer's `burst_id`, `epsg` and `revisit_days`, and each variable's `source` (the step and the onboarding spec's hash). A name the SAR layer also has is refused when the two are opened together, where the sidecar won before. A `{burst}_covariates.zarr` written before is read as an onboarding layer, and its C2 `contract_version` is still accepted by `validate_sidecar`. What follows is what the onboarding layer holds; the functions keep their `sidecar` names.


`ponzi_pipeline.onboard.onboard`. `{burst_id}.onboard.zarr` (`{burst_id}_covariates.zarr` before CR-102) beside an immutable SAR layer: the per-pixel and per-acquisition covariates a run may read (strata for L0, covariates for forecasters), merged at open; a name in both is refused (CR-102). It also carries the run's `process_mask`, so the edge margin is preprocessing rather than a scoring spec field.

## Producer and consumers

Producer: `ponzi_pipeline.onboard.onboard.onboard_store` (`ponzi-pipeline onboard --store PATH [--out DIR] [--burst ID] [--onboarding-spec SPEC] [--steps LIST] [--rebuild] [--frames FILE] [--ghsl-cache DIR] [--era5-cache DIR]`, or the worker stage `onboard`; `--out` defaults to the store's folder, and the two caches to the PONZI home's `downloads/ghsl` and `downloads/era5`), which writes `<out_dir>/<burst>.onboard.zarr` and the stamp `<out_dir>/onboard_meta.json`; the worker keeps the two as one cache entry (assets `covariates` and `onboard_meta`). Its parameters are the onboarding spec (C17).

Consumers: `ponzi.core.runner` (`open_input(coh, sidecar)`, `RunRequest.sidecar`, `ponzi run --sidecar`, the worker stage `run`), the onboarding's `sample` step (`extract_burst_sample`: the series and layers travel into the C3 sample), `ponzi_models` (the masked input of a panel, through `open_input`).

## Arrays

| Name | Dims | dtype | Fill | Meaning |
|---|---|---|---|---|
| `built`, `land` | `(y, x)` | float32 | NaN | GHSL built-up (`GHS_BUILT_S`) and land (`GHS_LAND`) fractions in `[0, 1]`, reprojected and area-averaged onto the store grid |
| `era5_*` | `(time,)` | float32 | NaN | ERA5-Land series on the store's `time` axis (NaN where extraction failed): the unweighted mean over the valid 0.1 degree cells covering the footprint plus one cell, or the nearest valid cell within 3 cells when all are masked. One per requested `weather_variables`: `era5_t2m`, `era5_precip_1h`, `era5_precip_24h`, `era5_snow_cover`, `era5_snow_depth`, `era5_u10`, `era5_v10`, `era5_wind_speed`, `era5_swvl1` |
| `era5_pd_{var}_{d}d` | `(time,)` | float32 | NaN | The signed pair difference of the level `era5_{var}` over `d` days (below) |
| `process_mask` | `(y, x)` | bool | False | The store's valid footprint eroded by `edge_margin` (`ponzi.core.context.process_mask`): the pixels the runner processes. Its own attr `edge_margin` records the margin |
| `time`, `y`, `x` | | | | Copied verbatim from the store |

Every array is one chunk. Each data variable carries `long_name` and `units` attrs (`weather.variable_long_name`, `weather.variable_units`; a pair difference keeps its level's units).

The pair differences are `v(t) - v(t - d days)`, signed (a rise and a fall are different states of the ground), in the level's units, and `0.0` at an acquisition whose partner is absent. The partner is the image the coherence pair of that baseline was made with: the store's `secondary_date` table (`ponzi.core.forecast.model_inputs.pair_partner_secondary`) when it covers every differenced baseline, else the acquisition `d` days earlier matched by exact date (`pair_partner_index`); both return -1 for an absent partner and agree on a regular axis. `{var}` is the level name without `era5_` (`era5_swvl1` gives `era5_pd_swvl1_12d`); a level that is NaN at either end of a pair gives NaN. The `pairdiff` step differences every `era5_*` `(time,)` level the sidecar holds (never an `era5_pd_*`) by every baseline of `pairdiff_baselines`, and drops the members an earlier run wrote that its baselines no longer ask for.

## Attrs

`layer` (`onboard`), `contract_version` (C1's since CR-102; the hash of C2's declaration before, ponzi-core CR-085; `validate_sidecar` accepts these two and fails another), the SAR layer's `burst_id`, `epsg` and `revisit_days`, `producer` (`ponzi_pipeline.onboard`), `source_store`, `source_digest`, `sidecar_of`, `onboard_steps`, and the provenance of each step: `built_source`, `land_source`; `{var}_source`, `weather_source` and the source's own (`weather_url`, `cds_dataset`, `weather_area`, `cds_area`, `cds_area_key`, `n_cells`, `era5_cell_lat`, `era5_cell_lon`, `era5_burst_value`); `era5_pd_source`, `era5_pd_baselines`, `era5_pd_levels`.

The margin lives in the `edge_margin` attr of `process_mask`: the runner stamps it into `run_meta.pixels.edge_margin` and `ponzi_edge_margin` (C7), and the `sample` step into the C3 sample. Without a `process_mask` the runner processes the whole valid footprint and records margin 0; with one it processes `process_mask & valid_pixels`.

## Invariants

- Same `time`, `y`, `x` as the store.
- Written whole and atomically: the new group is built in a sibling `{name}.tmp-{pid}` and swapped in with two renames, so the path holds either the complete old sidecar or the complete new one; an interrupted swap leaves the old one under `{name}.old-{pid}` for the next write to recover.
- Stamp-idempotent: `onboard_meta.json` records each step and its parameters; a step whose parameters match the stamp and whose output exists is skipped; every step reruns when the store's digest changed or with `--rebuild`. `pairdiff` stamps the levels it differenced, its baselines and the `weather` step's parameters.
- The steps run in the order `built`, `weather`, `pairdiff`, `mask`, `sample` whatever order they are named in: `pairdiff` reads back the levels `weather` wrote (it fails with a clear error when they are absent), and `sample` reads the margin of `mask`. `sample` is skipped without a frames table.
- Never written into an archive store (`ponzi.contracts.validate.refuse_write` guards every write).

## Functions

`ponzi_pipeline.onboard.onboard`: `onboard_store`, `sidecar_path`, `stamp_path`, `load_stamp`, `write_sidecar` (its `drop` argument is how a step clears members of a family it owns), `open_sidecar`, `validate_sidecar(path, store=None)` (checks `contract_version`, `source`, `axes` with a store, `variables` dims and dtypes, `range` of `built` and `land`), `sidecar_mask`, `process_mask_layer`, `pairdiff_levels`, `pairdiff_layers`. Names and units: `ponzi_pipeline.onboard.weather` (`pairdiff_name`, `pairdiff_parts`, `variable_units`, `variable_long_name`). `ponzi-pipeline weather-prefetch` downloads the CDS months of a shared `weather_area` once.
