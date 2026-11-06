# C8: Change store

Status: implemented 2026-09-07, `ponzi.contracts.change`.

## Purpose

The state-machine output of one run at the canonical thresholds: episodes, NMS onsets, detectability and the raw state. Always written. Re-thresholded variants are produced post hoc by `ponzi.core.statemachine.replay` into a store of the same contract.

## Producer and consumers

Producer: `ponzi.core.runner` through `ZarrChangeSink` (`{out_dir}/change.zarr`, same grid and chunks as C7), and `replay` (`ponzi replay SCORE --out OUT [--alpha] [--delta] [--recovery-steps] [--nms-window] [--noise-floor] [--label LABEL]`: `OUT/change_{label}.zarr` when a label is given and `OUT` is not a `.zarr` path, else `OUT`; chunks `(1, Y, X)`). Consumers: `ponzi.evaluation.rows` (the as-run `change_event` flags of `score_rows` and `quiet_rows`), the run's STAC Item (asset `change`).

## Arrays and tables

| Name | Dims | dtype | Fill | Chunks | Notes |
|---|---|---|---|---|---|
| `change_period` | `(time, y, x)` | uint8 | 0 | `(1, Y, X)` | 1 while the pixel is in state CHANGE and `detectability > 0` |
| `change_event` | `(time, y, x)` | uint8 | 0 | `(1, Y, X)` | 1 at the NMS-selected onset of each episode (argmax `anomaly_score` over the first `nms_window` steps) |
| `detectability` | `(time, y, x)` | uint8 | 0 | `(1, Y, X)` | 0 none, 1 low, 2 medium, 3 high: `sensitivity` below the whole, two thirds or one third of `predicted_median - noise_floor` |
| `state` | `(time, y, x)` | uint8 | 0 | `(1, Y, X)` | Raw state after the step: 0 NORMAL, 1 CHANGE; not gated by detectability |
| `process_pixels` | `(y, x)` | uint8 | 0 | `(Y, X)` | As C7 |
| `time`, `y`, `x` | | | | | As C7 (`time` int64 with CF attrs) |

Written as zarr v3, consolidated, uint8 with fill 0 (never null: unwritten anchors must read 0, not garbage).

## Attrs

Exactly the attrs of C7 (input attrs plus the same `RunStamp`). A `replay` store carries the stamp of the run it derived from with `ponzi_change_alpha`, `ponzi_delta`, `ponzi_recovery_steps`, `ponzi_nms_window`, `ponzi_noise_floor` replaced by the replay values and `ponzi_replay_of` set to the source `scoring_spec_hash`; a new `alpha` scales the sensitivity by `alpha / ponzi_alpha` before the detectability ladder.

## Invariants

- All arrays are 0 outside `[t_lo, t_hi]` and where `process_pixels == 0`.
- `change_period == 1` implies `state == 1` and `detectability > 0`. The converse does not hold at an anchor whose aggregate score is NaN inside an episode: the machine skips the anchor (state frozen), so `state` stays 1 while `change_period` is 0.
- `change_event == 1` implies `change_period == 1` at that anchor; at most one event per episode.
- `detectability` is 0 wherever `anomaly_score` (C7) is NaN.
- Detection mode: `change_event` equals the detectability-gated `change_period` (no history, so no episode to suppress).

## Functions

`ponzi.contracts.change`: `CHANGE_ARRAYS`, `Flags` (the stage 5 output dataclass), `ChangeMeta` (same parser as `ScoreMeta`), `ChangeDataset`, `open_change_store(path) -> ChangeDataset` (opens with `mask_and_scale=False`, validates), `create_change_store(path, grid, stamp, process_pixels, chunks=None)` (same `GridMeta` input as C7), `write_change_slice(group, t, Flags)`, `validate_change_store(path)` (same checks as C7), `stores_share_stamp(score_path, change_path) -> bool` (the C7 attrs-equality invariant).
