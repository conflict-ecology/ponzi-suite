# C6: Channel scores store

Status: implemented 2026-09-07, `ponzi.contracts.channels`; the ceiling `c` was added later.

## Purpose

`{out_dir}/channels.zarr`, optional: the per-channel scores before aggregation, for diagnostics of the pyramid, for channel-level evaluation rows and for the calibration's null rows.

## Producer and consumers

Producer: `ponzi.core.runner` with `RunRequest.save_channels` (`ponzi run --save-channels`, the worker stage `run`'s `save_channels`), through `ZarrChannelSink`; like `save_pred` it keeps the loop on the whole grid. Consumers: `ponzi.evaluation.rows` (`channel_rows`, `quiet_rows` at channel level), `ponzi_models.calibration.null_rows` (`ponzi-models null-rows`: the per-channel `z` of the runs `ponzi-models null-runs` made with `save_channels`), the run's STAC Item (asset `channels`).

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `u`, `z`, `d`, `s`, `m` | `(time, y, x, baseline, horizon)` | float32 | NaN | `ChannelScores` of stage 3 (PIT, drop-positive z, observed minus median, sensitivity, predicted median); NaN = invalid channel |
| `c` | `(time, y, x, baseline, horizon)` | float32 | NaN | The ceiling: the z the channel would get if observed at the noise floor. Optional: stores written before it lack it (validator `optional`, info); NaN throughout where scores were made without a predictive |
| `process_pixels`, `time`, `y`, `x` | | | | as C7 |

Chunks and attrs as C5 (`(1, tile, tile, B, H)` with the run's `pred_tile`, input attrs plus the `RunStamp`); no `family` attr and no `baseline` or `horizon` coordinates.

## Invariants

- The NaN pattern is identical across `u`, `z`, `d`, `s`, `m` and equals the channel validity of stage 3; `c` is NaN at least there.

## Functions

`ponzi.contracts.channels`: `CHANNEL_ARRAYS`, `ChannelMeta`, `ChannelDataset`, `open_channel_store` (validates, raises on a failed check), `create_channel_store(path, grid, stamp, process_pixels, B, H, tile=512)`, `write_channel_slice`, `validate_channel_store` (checks `structure`, `stamp`, `window`, `consolidated`). The same module holds C21 (`channels_z.zarr`).
