# C2: Covariates sidecar

> Note (CR-008, 2026-10-12): produced here by `ponzi_pipeline.onboard.onboard.onboard_store` (command `ponzi-pipeline onboard --store PATH --out DIR [--onboarding-spec SPEC] [--steps LIST] [--rebuild] [--frames FILE] [--ghsl-cache DIR] [--era5-cache DIR]`), written as `<out_dir>/<burst>_covariates.zarr` with the stamp `<out_dir>/onboard_meta.json`. The worker stage `onboard` calls the same function and keeps the two files as one cache entry (collection `ponzi-sidecar`, assets `covariates` and `onboard_meta`). The format and the recorded `producer` string (`ponzi_pipeline.onboard`) are unchanged. The weather sources are `edh`, `cdsgrid` and `edh_cdsgrid`; the CDS point route (`cds`, `auto`) is gone.

Status: implemented 2026-09-07, `ponzi_pipeline.onboard.onboard`; the
`process_mask` layer added 2026-09-09, the `era5_pd_*` pair differences
2026-09-22.

## Purpose

`{burst_id}_covariates.zarr` beside an immutable coherence store: the per-pixel and per-acquisition covariates a run may read (strata for L0, covariates for forecasters), merged at open with the sidecar winning over same-named store variables. It also carries the run's `process_mask`, so the edge margin is preprocessing rather than a scoring spec field.

## Producer and consumers

Producer: `ponzi_pipeline.onboard.onboard.onboard_store` (above). Consumers: `ponzi.core.runner` (`open_input(coh, sidecar)`, `RunRequest.sidecar`, `ponzi run --sidecar`, the worker stage `run`), `ponzi_pipeline.onboard.onboard.extract_burst_sample` (its series and layers travel into the C3 sample), `ponzi_models` (the masked input of a panel, through `open_input`).

## Arrays

| Name | Dims | dtype | Fill | Meaning |
|---|---|---|---|---|
| `built`, `land` | `(y, x)` | float32 | NaN | GHSL built-up (`GHS_BUILT_S`) and land (`GHS_LAND`) fractions in `[0, 1]`, reprojected and area-averaged onto the store grid |
| `era5_*` | `(time,)` | float32 | NaN | ERA5-Land series aligned to the store's `time` axis (NaN where extraction failed): the unweighted mean over the valid 0.1 degree cells covering the footprint plus one cell, or the nearest valid cell within 3 cells when all are masked. Names: `era5_t2m`, `era5_precip_1h`, `era5_precip_24h`, `era5_snow_cover`, `era5_snow_depth`, `era5_u10`, `era5_v10`, `era5_wind_speed`, `era5_swvl1` (those of the requested `weather_variables`) |
| `era5_pd_{var}_{d}d` | `(time,)` | float32 | NaN | the signed pair difference of the level `era5_{var}` over `d` days |
| `process_mask` | `(y, x)` | bool | False | the store's valid footprint eroded by `edge_margin` (`ponzi.core.context.process_mask`); the pixels the runner processes |
| `time`, `y`, `x` | | | | copied verbatim from the store |

Every array is one chunk; the group is zarr v3, consolidated. Each data variable carries `long_name` and `units` attrs (`weather.variable_long_name`, `weather.variable_units`; a pair difference keeps its level's units).

The pair differences are `v(t) - v(t - d days)`, SIGNED (a rise and a fall are
different states of the ground), in the level's own units, and `0.0` at an
acquisition whose partner is absent. The partner is the image the coherence
pair of that baseline was made with: the store's `secondary_date` table
(`ponzi.core.forecast.model_inputs.pair_partner_secondary`) when the store has
one covering every differenced baseline, else the acquisition `d` days earlier
matched by EXACT date (`pair_partner_index`); both return -1 for an absent
partner and agree on a regular axis. `{var}` is the level name without its `era5_` prefix
(`era5_swvl1` gives `era5_pd_swvl1_12d`); a level that is NaN at either end of a
pair stays NaN in the difference, as the level itself is. The `pairdiff` step
writes every `era5_*` `(time,)` level the sidecar holds (`era5_pd_*` excluded,
so it never differences its own output) by every baseline of
`pairdiff_baselines`, and clears the members an earlier run wrote
that its baselines no longer ask for.

Attrs: `contract_version` (1), `producer` (`ponzi_pipeline.onboard`), `source_store`, `source_digest`, `sidecar_of`, `onboard_steps`, and the provenance of each step: `built_source`, `land_source`; `{var}_source`, `weather_source` and the source's own (`weather_url`, `cds_dataset`, `weather_area`, `cds_area`, `cds_area_key`, `n_cells`, `era5_cell_lat`, `era5_cell_lon`, `era5_burst_value`); `era5_pd_source`, `era5_pd_baselines`, `era5_pd_levels`. `process_mask` carries the `edge_margin` it was eroded with in its OWN attrs: that is where `ponzi.core.runner` reads the margin it stamps into `run_meta.pixels.edge_margin` and `ponzi_edge_margin` (C7), and where the `sample` step takes the margin it stamps into the C3 sample. Without a `process_mask` the runner processes the whole valid footprint and records margin 0; with one it processes `process_mask & valid_pixels`.

## Invariants

- Same `time`, `y`, `x` as the store; the sidecar is rewritten whole and atomically by its producer (the new group is built in a sibling `{name}.tmp-{pid}`, then swapped in with two renames, so at any instant the path holds either the complete old sidecar or the complete new one, and an interrupted write leaves the old one under `{name}.old-{pid}` for the next write to recover) and stamped in `onboard_meta.json` (stamp-idempotent: a step whose parameters match the stamp and whose output exists is skipped; every step reruns when the store's digest changed or with `--rebuild`).
- Never written into an archive store (`ponzi.contracts.validate.refuse_write`); the reader (`open_coherence_store(path, sidecar)`) merges it.
- The steps run in order `built`, `weather`, `pairdiff`, `mask`, `sample`: `mask` before `sample`, because the sample's margin is the mask's attr, and `pairdiff` after `weather`, because it reads the levels that step wrote back off the sidecar and reaches no hub (it fails with a clear error when they are absent). Their parameters are an `OnboardingSpec` (the `onboarding:` section of the `--onboarding-spec` yaml, the identity params of the worker stage `onboard`; defaults: all five steps, `edge_margin` 20, `weather_source` `edh`, `pairdiff_baselines` `[12, 24, 36, 48, 60]`, no `weather_area`), never flags beyond `--steps`; `pairdiff` stamps the levels it differenced, the baselines it used and the `weather` step's parameters, so it re-runs when any of them changes. The `sample` step is skipped without a frames table.

## Functions

`onboard_store`, `OnboardingSpec` and `load_onboarding_spec` (`ponzi_pipeline.onboard.onboarding_spec`, the parameters), `sidecar_path`, `stamp_path`, `load_stamp`, `write_sidecar` (its `drop` argument is how a step clears the members of a family it owns), `open_sidecar`, `validate_sidecar(path, store=None)` (checks `contract_version`, `source`, `axes` with a store, `variables` dims and dtypes, `range` of `built` and `land`), `sidecar_mask`, `process_mask_layer`, `pairdiff_levels`, `pairdiff_layers`; the names and the units come from `ponzi_pipeline.onboard.weather` (`pairdiff_name`, `pairdiff_parts`, `variable_units`, `variable_long_name`). `ponzi-pipeline weather-prefetch` downloads the CDS months of a shared `weather_area` once (CR-023).
