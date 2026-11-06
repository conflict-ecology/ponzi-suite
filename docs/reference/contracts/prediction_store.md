# C5: Prediction store

Status: implemented 2026-09-07, `ponzi.contracts.pred`.

## Purpose

`{out_dir}/pred.zarr`, optional: the per-anchor predictive distribution of every channel, so a forecaster's output can be persisted once (for example GPU inference elsewhere) and replayed by the `stored` forecaster, or inspected.

## Producer and consumers

Producer: `ponzi.core.runner` with `RunRequest.save_pred` (`ponzi run --save-pred`, the worker stage `run`'s `save_pred`), through `ZarrPredSink`, or an external inference job writing the same layout. The sink allocates the store on the first anchor it writes, from that predictive's family and levels, so a run whose window is empty writes none. `save_pred` keeps the run's loop on the whole grid (no compact loop, CR-010). Consumers: `ponzi.core.forecast.external.StoredForecaster` (forecaster `stored`, param `path`; refused for a run restricted by a mask), the run's STAC Item (asset `pred`, `ponzi.stac.items.run_item`).

## Arrays

| Name | Dims | dtype | Fill | Family | Notes |
|---|---|---|---|---|---|
| `mean`, `std` | `(time, y, x, baseline, horizon)` | float32 | NaN | normal | |
| `q` | `(time, y, x, baseline, horizon, level)` | float32 | NaN | quantile | ascending along `level` |
| `level` | `(level,)` | float64 | | quantile | the quantile levels, also attr `quantile_levels` |
| `support` | `(time, y, x, baseline)` | uint8 | 0 | both | finite context observations per channel |
| `process_pixels`, `time`, `y`, `x` | | | | both | as C7 (`time` int64 with CF attrs) |

`baseline` and `horizon` have no coordinate arrays; the days are the stamp's `ponzi_baseline_days`. Chunks `(1, tile, tile, B, H[, K])`, `process_pixels` `(tile, tile)`, with `tile = min(pred_tile, Y, X)`; `pred_tile` (`RunRequest.pred_tile`, `--pred-tile`) defaults to 512. Zarr v3, consolidated at creation. Attrs: input attrs, the `RunStamp` (C7), `family` (`normal` or `quantile`), and `quantile_levels` for the quantile family.

Legacy: a `pred_quantiles.zarr` store (`pred_quantiles (time, y, x, baseline, horizon, level) float16`, attrs `quantile_levels`, `t_range`, `baseline_days`, `horizon_length` required and `fm_context_depth` optional) opens as family `quantile` with `legacy = True`, no stamp and no support (read as zeros).

## Invariants

- Written anchors are exactly the stamp window; outside it the arrays read fill.
- `q` is non-decreasing along `level`; `std > 0` where `mean` is finite.

## Functions

`ponzi.contracts.pred`: `PredMeta`, `PredDataset` (`.read_pred_slice(t)`, `.family`, `.legacy`, `.levels`, `.stamp`, `.window`, `.context_depth`, `.baseline_days`, `.horizon`), `open_prediction_store` (validates, raises on a failed check), `create_prediction_store(path, grid, stamp, process_pixels, family, B, H, levels=None, tile=512)`, `write_pred_slice`, `read_pred_slice(source, t) -> Predictive` (a path or a `PredDataset`), `validate_prediction_store` (checks `structure`, `stamp`, `window`, `consolidated`, `family`, `levels`; the legacy layout `structure`, `legacy_attrs`), `is_legacy_store`. `create_stack_store` is the stacked-store machinery C6 and C21 reuse.
