# C8: Change store

`ponzi.contracts.change`. The state-machine output of one run at the canonical thresholds: episodes, NMS onsets, detectability and the raw state. Always written. Re-thresholded variants are made afterwards by `replay` into a store of the same contract.

## Producer and consumers

Producers: `ponzi.core.runner` through `ZarrChangeSink` (`{out_dir}/change.zarr`, the grid and chunks of C7), and `ponzi.core.statemachine.replay` (`ponzi replay SCORE --out OUT [--alpha] [--delta] [--recovery-steps] [--nms-window] [--noise-floor] [--label LABEL]`, C4b: `OUT/change_{label}.zarr` when a label is given and `OUT` is not a `.zarr` path, else `OUT`; chunks `(1, Y, X)`). Consumer: `ponzi.evaluation.rows` (the as-run `change_event` flags of `score_rows` and `quiet_rows`, C20).

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `change_period` | `(time, y, x)` | uint8 | 0 | 1 while the pixel is in state CHANGE and `detectability > 0` |
| `change_event` | `(time, y, x)` | uint8 | 0 | 1 at the NMS-selected onset of each episode (argmax `anomaly_score` over the first `nms_window` steps) |
| `detectability` | `(time, y, x)` | uint8 | 0 | 0 none, 1 low, 2 medium, 3 high: `sensitivity` below the whole, two thirds or one third of `predicted_median - noise_floor` |
| `state` | `(time, y, x)` | uint8 | 0 | Raw state after the step: 0 NORMAL, 1 CHANGE; not gated by detectability |

Grid (`time`, `y`, `x`, `process_pixels`), chunks and attrs: as C7 ([Grid and attrs of a run's stores](score_store.md#grid-and-attrs-of-a-runs-stores)). The fill is 0, never null, so unwritten anchors read 0.

A `replay` store carries the stamp of the run it derives from with `ponzi_change_alpha`, `ponzi_delta`, `ponzi_recovery_steps`, `ponzi_nms_window`, `ponzi_noise_floor` replaced by the replay values (an unset one is the source's) and `ponzi_replay_of` set to the source's `ponzi_scoring_spec_hash`; a new `alpha` becomes `ponzi_change_alpha` and scales the sensitivity by `alpha / ponzi_alpha` before the detectability ladder.

## Invariants

- All arrays are 0 outside `[t_lo, t_hi]` and where `process_pixels == 0`.
- `change_period == 1` implies `state == 1` and `detectability > 0`. The converse fails at an anchor whose aggregate score is NaN inside an episode: the machine skips the anchor (state frozen), so `state` stays 1 while `change_period` is 0.
- `change_event == 1` implies `change_period == 1` at that anchor; at most one event per episode.
- `detectability` is 0 wherever `anomaly_score` (C7) is NaN.
- Detection mode: `change_event` equals the detectability-gated `change_period` (no history, so no episode to suppress).

## Functions

`ponzi.contracts.change`: `CHANGE_ARRAYS`, `Flags` (one anchor's arrays), `ChangeMeta`, `ChangeDataset`, `open_change_store(path)` (validates; opens with `mask_and_scale=False` so the arrays stay uint8), `create_change_store(path, grid, stamp, process_pixels, chunks=None)` (the same `GridMeta` as C7), `write_change_slice(group, t, flags)`, `validate_change_store(path)` (the checks of C7), `stores_share_stamp(score_path, change_path) -> bool`.
