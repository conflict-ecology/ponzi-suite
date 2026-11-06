# C21: All-channel z store

Status: implemented 2026-09-27, `ponzi.contracts.channels` (the `channel_z` functions, package `packages/core`). Opt-in and experimental: it is written only with `RunRequest.save_all_channels` (`ponzi run --save-all-channels`).

## Purpose

`{out_dir}/channels_z.zarr`, optional: the drop-positive z-score of EVERY `(baseline, horizon)` channel of every anchor, the off-pyramid channels included (those the overlap mask `baseline_days[b] > h * revisit_days` excludes from aggregation). For break-dating and ongoing/settled experiments over all B x H cells. Nothing in ponzi-core or ponzi-service reads it outside its own opener and the tests.

## Producer and consumers

Producer: `ponzi.core.runner` with `save_all_channels` (`ponzi.core.sinks.ZarrChannelZSink`); the ponzi-worker `run` stage passes `RunParams.save_all_channels` through. Consumers: side analyses (Gaza break dating) through `open_channel_z_store`; no library consumer. The `ponzi-run` STAC collection declares an optional C21 asset `all_channels` (`ponzi_spec.collections`), the file `channels_z.zarr` of a run folder (`ponzi.stac.items.RUN_ASSETS`).

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `z` | `(time, y, x, baseline, horizon)` | float16 | NaN | channel z of all B x H cells; NaN outside the run window, outside the process mask, where the observation is missing or the forecast unusable |
| `process_pixels` | `(y, x)` | uint8 | | the run's process mask, as C7 |
| `time`, `y`, `x` | | | | as C7 |
| `baseline`, `horizon` | `(baseline,)`, `(horizon,)` | float64 | | baseline days of the scoring spec, horizon steps `0 .. H-1` |

zarr v3. Chunks `(1, tile, tile, B, H)` with the request's `pred_tile` (default 512), the tile capped at the grid; chunks that are all NaN are not written (zarr's `write_empty_chunks` off, its default), so the store holds the process mask and the run window only. zstd compressed (the zarr v3 default). In a run restricted by a named mask (CR-014) the grid is the mask's bounding window, as for every output store of the run.

## Attrs

The input attrs (with `context_keep` when the request sets it, CR-022) and the `RunStamp` (`ponzi_*`) as C5 and C6, plus:

| Attr | Meaning |
|---|---|
| `channel_z_baseline_days` | the run's baseline days, in the order of the `baseline` axis |
| `channel_z_horizons` | `[0, .., H-1]`, the order of the `horizon` axis |
| `channel_z_revisit_days` | revisit of the input store |
| `channel_z_pyramid` | the `(B, H)` overlap mask as a 0/1 list of lists: 1 = pyramid cell (aggregated by the run), 0 = off-pyramid |
| `channel_z_definition` | the sentence below |

## Definition of `z`

Exactly the runner's channel z (`ponzi.core.scoring.score`, the C6 `z`): `z = -ndtri(PIT)` of the observed coherence under the channel's predictive distribution, positive for a drop below the forecast; for the quantile family the Gaussian tails beyond the outer knots as in `QuantilePredictive.z`. The scoring uses the run's `scoring.alpha` and the ceiling floor (the input estimator's zero coherence level where the store's attrs give it, `ponzi_ceiling_floor` in the stamp), with an all-true overlap mask; the forecaster is called with an all-true overlap as well, so TiDE does not blank the off-pyramid cells. Stored as the float16 cast of the float32 value.

## Invariants

- On the pyramid cells (`channel_z_pyramid == 1`), `z` equals the C6 `z` of the same run cast to float16, NaN pattern included.
- A run with the option writes `score.zarr`, `change.zarr`, `pred.zarr`, `channels.zarr`, the forecasting stats and the `run_meta.json` anchor counts bit-identical to the same run without it: everything downstream of scoring gets a copy with the off-pyramid cells set to NaN (`runner._to_pyramid`). Tested in `packages/core/tests/test_all_channels.py`.
- Off-pyramid cells are finite where observed for TiDE, rolling OLS and a blanking external callable; a `stored` forecaster gives whatever the prediction store holds there (NaN for a store written by a TiDE run); an `external` callable without a `blanks_off_pyramid` attribute is refused.

## Functions

`ponzi.contracts.channels`: `CHANNEL_Z_ARRAYS`, `create_channel_z_store`, `write_channel_z_slice` (one anchor's `(Y, X, B, H)`, cast to float16), `validate_channel_z_store`, `open_channel_z_store` (validates, then a lazy xarray Dataset without mask-and-scale).
