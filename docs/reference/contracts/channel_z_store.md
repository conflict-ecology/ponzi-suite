# C21: All-channel z store

`ponzi.contracts.channels` (the `channel_z` functions, package `packages/core`). `{out_dir}/channels_z.zarr`, optional: the drop-positive z of EVERY `(baseline, horizon)` channel of every anchor, the off-pyramid channels included (those the overlap rule `baseline_days[b] > h * revisit_days` excludes from aggregation). For break dating and ongoing or settled analyses over all B x H cells.

## Producer and consumers

Producer: `ponzi.core.runner` with `RunRequest.save_all_channels` (`ponzi run --save-all-channels`, the worker stage `run`'s `save_all_channels`), through `ponzi.core.sinks.ZarrChannelZSink`. Consumers: side analyses through `open_channel_z_store`; no library code reads it.

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `z` | `(time, y, x, baseline, horizon)` | float16 | NaN | Channel z of all B x H cells; NaN outside the run window, outside the process mask, where the observation is missing or the forecast unusable |
| `baseline`, `horizon` | `(baseline,)`, `(horizon,)` | float64 | | Baseline days of the scoring spec, horizon steps `0 .. H-1` |

Grid and attrs as C7, chunks the stacked layout of [C5](prediction_store.md#stacked-layout). Chunks that are all NaN are not written (zarr's default, `write_empty_chunks` off), so the store holds the process mask and the run window only.

## Attrs

Besides those of C7:

| Attr | Meaning |
|---|---|
| `channel_z_baseline_days` | the run's baseline days, in the order of the `baseline` axis |
| `channel_z_horizons` | `[0, .., H-1]`, the order of the `horizon` axis |
| `channel_z_revisit_days` | revisit of the input store |
| `channel_z_pyramid` | the `(B, H)` overlap mask as a 0/1 list of lists: 1 = pyramid cell (aggregated by the run), 0 = off-pyramid |
| `channel_z_definition` | the definition below, as a sentence |

## Definition of `z`

Exactly the runner's channel z (`ponzi.core.scoring.score`, the C6 `z`): `z = -ndtri(PIT)` of the observed coherence under the channel's predictive distribution, positive for a drop below the forecast; for the quantile family the Gaussian tails beyond the outer knots as in `QuantilePredictive.z`. The scoring uses the run's `scoring.alpha` and the ceiling floor (`ponzi_ceiling_floor`), with an all-true overlap mask; the forecaster is called with an all-true overlap as well, so TiDE does not blank the off-pyramid cells. Stored as the float16 cast of the float32 value.

## Invariants

- On the pyramid cells (`channel_z_pyramid == 1`), `z` equals the C6 `z` of the same run cast to float16, NaN pattern included.
- Every other output of the run is bit-identical to the run without the option: everything downstream of scoring gets a copy with the off-pyramid cells set to NaN (`runner._to_pyramid`; `packages/core/tests/test_all_channels.py`).
- Off-pyramid cells are finite where observed for TiDE, rolling OLS and a blanking external callable; a `stored` forecaster gives whatever the prediction store holds there (NaN for a store written by a TiDE run); an `external` callable without a `blanks_off_pyramid` attribute is refused.

## Functions

`ponzi.contracts.channels`: `CHANNEL_Z_ARRAYS`, `create_channel_z_store`, `write_channel_z_slice` (one anchor's `(Y, X, B, H)`, cast to float16), `validate_channel_z_store`, `open_channel_z_store` (validates, then a lazy xarray Dataset without mask-and-scale).
