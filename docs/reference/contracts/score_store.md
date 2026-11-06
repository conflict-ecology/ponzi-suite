# C7: Score store

`ponzi.contracts.score`. The per-anchor, per-pixel aggregate scores of one run: what the state machine reads and what re-thresholding (`replay`), p-value coding and evaluation consume. Always written. This page also defines the grid, the attrs and the run stamp every output store of a run shares.

## Producer and consumers

Producer: `ponzi.core.runner` through `ZarrScoreSink` (`{out_dir}/score.zarr`; `ponzi run`, the worker stage `run`). Consumers: `ponzi.core.statemachine.replay` (`ponzi replay`, C8), `ponzi.calibration` (`write_pvalues`, C22; the staged calibration, C26), `ponzi.evaluation.rows` (`score_rows`, `bag_rows`, `quiet_rows`, C20), `ponzi-models null-rows` (`anomaly_score` and `ceiling_score` for the ceiling lookup).

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `anomaly_score` | `(time, y, x)` | float32 | NaN | Aggregate z; NaN = unscored |
| `difference` | `(time, y, x)` | float32 | NaN | Aggregate `obs - predicted median` |
| `sensitivity` | `(time, y, x)` | float32 | NaN | Aggregate minimum detectable drop at `scoring.alpha` |
| `predicted_median` | `(time, y, x)` | float32 | NaN | Aggregate predicted median |
| `ceiling_score` | `(time, y, x)` | float32 | NaN | The score the pixel would get if every channel were observed at the noise floor: the largest alarm it can raise. Optional for a reader: a store without it validates with the `optional` check at info |
| `n_channels` | `(time, y, x)` | uint8 | 0 | Valid `(b, h)` channels aggregated; 0 iff `anomaly_score` is NaN inside the window |

Chunks `(1, Y, X)` by default, or the request's `chunks` (`RunRequest.chunks`, `ponzi run --chunks t,y,x`); `process_pixels` takes the spatial part. There are no `baseline` or `horizon` coordinates; the baselines are the stamp's `ponzi_baseline_days`.

## Grid and attrs of a run's stores

Every output store of a run (C5, C6, C7, C8, C21, C24, C26) has:

- **The grid.** `time` (int64, the [shared time encoding](../contracts.md#shared-conventions)), `y`, `x` (float64), each one chunk, copied from the input, and `process_pixels` `(y, x)` uint8, fill 0: 1 where the run scored (the input's process mask). Shapes keep the full `(T, Y, X)` of the input; only anchors in `[t_lo, t_hi]` are written, the rest reads as fill. The input's grid is the coherence store's, the folded `G x G` grid of a pixel sample (C3), or, for a run restricted by a mask (C23), the bounding window of the mask layer and the process mask.
- **The input attrs.** Every attr of the input store (C1, or C3 for a sample) verbatim, plus the input conditions the runner adds unprefixed: `context_keep` (when given); `mask_layer`, `mask_window`, `mask_full_shape` (a masked run); `sample_n_px`, `sample_grid_side`, `frames_edge_margin` (a sampled run, so a consumer can unfold the arrays).
- **The run stamp.** `RunStamp` (`ponzi.contracts.stamp`) as `ponzi_*` attrs, below. The model field is the attr name without the prefix (`ponzi_version` is `RunStamp.version`). On read, the input attrs are every attr without the prefix, so an input store must never carry a `ponzi_*` attr of its own; the stamp's `ponzi_contract_version` is distinct from the input's `contract_version`. Optional fields that are None are not written.

| Attr | Type | Meaning |
|---|---|---|
| `ponzi_contract_version` | int | 1 |
| `ponzi_version` | str | `ponzi.__version__` |
| `ponzi_scoring_spec_hash` | str | C4 `spec_hash` |
| `ponzi_scoring_spec_name` | str | C4 `name`, else the scoring spec file's stem |
| `ponzi_forecaster` | str | `forecaster.name` |
| `ponzi_context_window`, `ponzi_horizon_length` | int | `C`, `H` |
| `ponzi_baseline_days` | list[int] | `scoring.baseline_days` |
| `ponzi_min_support`, `ponzi_min_channels` | int | |
| `ponzi_edge_margin` | int | The margin of the input's process mask (the sidecar's `process_mask` attr, C2, or the sample's `edge_margin`, C3); 0 when it records none |
| `ponzi_struct_weight` | bool | |
| `ponzi_alpha`, `ponzi_change_alpha`, `ponzi_delta`, `ponzi_noise_floor` | float | Scoring z, change threshold, difference threshold, detectability floor (`state_machine.noise_floor` resolved: `derived` is the input's `noise_floor(attrs)`, C1) |
| `ponzi_ceiling_floor` | float, optional | The coherence the ceiling was evaluated at: the estimator's derived floor where the input's attrs give it, else `ponzi_noise_floor` |
| `ponzi_recovery_steps`, `ponzi_nms_window` | int | Resolved (`nms_window` never 0 here) |
| `ponzi_window_schema` | int | 1 |
| `ponzi_run_mode` | str | `monitoring` or `detection` |
| `ponzi_t_lo`, `ponzi_t_hi` | int | Scored anchor index range, inclusive (in a staged run, the last anchor with a final score) |
| `ponzi_t_requested` | list[int], optional | Requested range before clamping to `[C, T - H]` |
| `ponzi_anchor_date_lo`, `ponzi_anchor_date_hi` | str (ISO date) | Dates of `t_lo`, `t_hi` |
| `ponzi_event_date`, `ponzi_event_end_date`, `ponzi_start_date`, `ponzi_end_date` | str, optional | The request's dates |
| `ponzi_sample` | bool | True on the folded sample grid |
| `ponzi_replay_of` | str, optional | A `replay` store only (C8) |

## Invariants

- Outside `[t_lo, t_hi]` every float array is NaN and `n_channels` is 0; a reader tells "not scored" from "no change" only through the attrs.
- Inside the window, `anomaly_score` is NaN wherever `process_pixels == 0`.
- `n_channels <= len(baseline_days) * H`.
- The attrs of `score.zarr` equal those of `change.zarr` from the same run (`stores_share_stamp`); a `replay` store is exempt.

## Functions

`ponzi.contracts.score`: `SCORE_ARRAYS`, `GridMeta` (shape, the three coordinates and the input attrs to copy; each input view of the runner builds it, `sample_grid_meta` for a sample), `PixelScores` (one anchor without the time axis; `ceiling_score` None is written as NaN), `ScoreMeta`, `open_score_store(path) -> ScoreDataset` (validates; `.ds` lazy, `.meta`, `.stamp`, `.window` with `t_lo`, `t_hi`, `run_mode` (alias `mode`) and `n_anchors`), `create_score_store(path, grid, stamp, process_pixels, chunks=None) -> zarr.Group` (allocates the arrays and consolidates; the sink only writes slices), `write_score_slice(group, t, scores)`, `validate_score_store(path)` (checks `structure` (fail: arrays, dims, dtypes, fills, `dimension_names`, coordinate lengths), `optional` (info), `stamp` (fail), `window` (fail unless `t_lo <= t_hi <= T - 1`), `consolidated`), `store_attrs(path)`.

`ponzi.contracts.stamp`: `RunStamp` with `to_attrs()`, `from_attrs()`, `has_stamp()`; `RunWindow.stamp_fields` (`ponzi.core.windows`) fills the window part.
