# C6: Channel scores store

`ponzi.contracts.channels`. `{out_dir}/channels.zarr`, optional: the per-channel scores before aggregation, for diagnostics of the pyramid, for channel-level evaluation rows and for the calibration's null rows.

## Producer and consumers

Producer: `ponzi.core.runner` with `RunRequest.save_channels` (`ponzi run --save-channels`, the worker stage `run`'s `save_channels`), through `ZarrChannelSink`; like `save_pred` it keeps the loop on the whole grid. Consumers: `ponzi.evaluation.rows` (`channel_rows`, and `quiet_rows` at channel level, C20), `ponzi-models null-rows` (the per-channel `z` of the runs `ponzi-models null-runs` makes with `save_channels`).

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `u`, `z`, `d`, `s`, `m` | `(time, y, x, baseline, horizon)` | float32 | NaN | `ChannelScores` (PIT, drop-positive z, observed minus median, sensitivity, predicted median); NaN = invalid channel |
| `c` | `(time, y, x, baseline, horizon)` | float32 | NaN | The ceiling: the z the channel would get if observed at the noise floor. Required (ponzi-core CR-086); NaN throughout where scores were made without a predictive |

Grid and attrs as C7, chunks the stacked layout of [C5](prediction_store.md#stacked-layout); no `family` attr.

## Invariants

- The NaN pattern is identical across `u`, `z`, `d`, `s`, `m` and equals the channel validity; `c` is NaN at least there.

## Functions

`ponzi.contracts.channels`: `CHANNEL_ARRAYS`, `ChannelMeta`, `ChannelDataset`, `open_channel_store` (validates), `create_channel_store(path, grid, stamp, process_pixels, B, H, tile=512)`, `write_channel_slice`, `validate_channel_store` (checks `structure`, `stamp`, `window`, `consolidated`). The same module holds C21.
