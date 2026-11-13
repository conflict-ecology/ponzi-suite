# C5: Prediction store

`ponzi.contracts.pred`. `{out_dir}/pred.zarr`, optional: the per-anchor predictive distribution of every channel, so a forecaster's output can be persisted once (for example GPU inference elsewhere) and replayed by the `stored` forecaster, or inspected. This page also defines the stacked layout C6 and C21 reuse.

## Producer and consumers

Producer: `ponzi.core.runner` with `RunRequest.save_pred` (`ponzi run --save-pred`, the worker stage `run`'s `save_pred`), through `ZarrPredSink`, or an external inference job writing the same layout. The sink allocates the store on the first anchor it writes, from that predictive's family and levels, so a run whose window is empty writes none. `save_pred` keeps the run's loop on the whole grid. Consumer: `ponzi.core.forecast.external.StoredForecaster` (forecaster `stored`, param `path`; refused for a run restricted by a mask).

## Arrays

| Name | Dims | dtype | Fill | Family | Notes |
|---|---|---|---|---|---|
| `mean`, `std` | `(time, y, x, baseline, horizon)` | float32 | NaN | normal | |
| `q` | `(time, y, x, baseline, horizon, level)` | float32 | NaN | quantile | ascending along `level` |
| `level` | `(level,)` | float64 | | quantile | the quantile levels, also attr `quantile_levels` |
| `support` | `(time, y, x, baseline)` | uint8 | 0 | both | finite context observations per channel |

Attrs: as C7 ([Grid and attrs of a run's stores](score_store.md#grid-and-attrs-of-a-runs-stores)), plus `family` (`normal` or `quantile`) and, for the quantile family, `quantile_levels`.

## Stacked layout

The stacked stores (C5, C6, C21; `create_stack_store`) have the grid of C7 and chunks `(1, tile, tile, ...)`: one anchor, a spatial tile, every other dimension whole; `process_pixels` is chunked `(tile, tile)`. `tile = min(pred_tile, Y, X)`, with `RunRequest.pred_tile` (`--pred-tile`, default 512). In C5 and C6 `baseline` and `horizon` have no coordinate arrays; the days are the stamp's `ponzi_baseline_days`.

## Invariants

- Written anchors are exactly the stamp window; outside it the arrays read fill.
- `q` is non-decreasing along `level`; `std > 0` where `mean` is finite.

## Functions

`ponzi.contracts.pred`: `PRED_ARRAYS`, `PredMeta`, `PredDataset` (`.read_pred_slice(t)`, `.family`, `.levels`, `.stamp`, `.window`, `.context_depth`, `.baseline_days`, `.horizon`), `open_prediction_store` (validates), `create_prediction_store(path, grid, stamp, process_pixels, family, B, H, levels=None, tile=512)`, `write_pred_slice`, `read_pred_slice(source, t) -> Predictive` (a path or a `PredDataset`), `validate_prediction_store` (checks `structure`, `stamp`, `window`, `consolidated`, `family`, `levels`), `create_stack_store`. A store without the C5 layout and stamp fails `family` when it has no valid `family` attr, which stops the validation there, and otherwise fails `structure` and `stamp`.
