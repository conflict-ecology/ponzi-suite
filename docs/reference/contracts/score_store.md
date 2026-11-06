# C7: Score store

Status: implemented 2026-09-07, `ponzi.contracts.score`; `ceiling_score` and `ponzi_ceiling_floor` were added later.

## Purpose

The per-anchor, per-pixel aggregate scores of one run: what the state machine reads and what any re-thresholding (`replay`), p-value coding or evaluation consumes. Always written.

## Producer and consumers

Producer: `ponzi.core.runner` through `ZarrScoreSink` (`{out_dir}/score.zarr`; `ponzi run`, the worker stage `run`, whose run folder is a cache entry of collection `ponzi-run`). Consumers: `ponzi.core.statemachine.replay` (`ponzi replay`), `ponzi.calibration.store.write_pvalues` (`ponzi pvalues`, the worker stage `pvalues`) and `ponzi.calibration.staged`, `ponzi.evaluation.rows` (`score_rows`, `bag_rows`, `quiet_rows`), `ponzi_models.calibration.null_rows` (the ceiling lookup), the run's STAC Item (asset `score`).

## Arrays and tables

Shapes keep the full `(T, Y, X)` of the input; only anchors in `[t_lo, t_hi]` are written, the rest reads as fill. The input's grid is the coherence store's, the folded `G x G` grid of a pixel sample (C3), or, for a run restricted by a mask (CR-014), the bounding window of the mask layer and the process mask.

| Name | Dims | dtype | Fill | Chunks | Notes |
|---|---|---|---|---|---|
| `anomaly_score` | `(time, y, x)` | float32 | NaN | `(1, Y, X)` | Aggregate z; NaN = unscored |
| `difference` | `(time, y, x)` | float32 | NaN | `(1, Y, X)` | Aggregate `obs - predicted median` |
| `sensitivity` | `(time, y, x)` | float32 | NaN | `(1, Y, X)` | Aggregate minimum detectable drop at `scoring.alpha` |
| `predicted_median` | `(time, y, x)` | float32 | NaN | `(1, Y, X)` | Aggregate predicted median |
| `ceiling_score` | `(time, y, x)` | float32 | NaN | `(1, Y, X)` | The score the pixel would get if every channel were observed at the noise floor: the largest alarm it can raise. Optional: stores written before it lack it (validator `optional`, info) |
| `n_channels` | `(time, y, x)` | uint8 | 0 | `(1, Y, X)` | Valid `(b, h)` channels aggregated; 0 iff `anomaly_score` is NaN inside the window |
| `process_pixels` | `(y, x)` | uint8 | 0 | `(Y, X)` | 1 where the run scored (the input's process mask) |
| `time`, `y`, `x` | | int64 / float64 / float64 | | one chunk | Copied from the input. `time` is int64 with CF attrs (`units` `nanoseconds since 1970-01-01`, `calendar` `proleptic_gregorian`) so it decodes to `datetime64[ns]` under any xarray setting |

Chunk shape is a write-time argument (`RunRequest.chunks`, `ponzi run --chunks t,y,x`, passed to `create_score_store`); the default is one full slice per anchor, and `process_pixels` takes its spatial part. Written as zarr v3, consolidated. There are no `baseline` or `horizon` coordinates; the baselines are in the attrs (`ponzi_baseline_days`).

## Attrs

All attrs of the input store (C1, or C3 for a sample) verbatim, plus the run stamp (`RunStamp`, identical in C5 to C8). The model field is the attr name without the `ponzi_` prefix (`ponzi_version` is `RunStamp.version`); `ponzi_contract_version` is the stamp's version and is distinct from the input's unprefixed `contract_version`, which is why the prefix split is exact. On read, `input_attrs` is every attr without the prefix, so an input store must never carry a `ponzi_*` attr of its own (C3 sample attrs stay unprefixed).

The runner adds unprefixed input conditions beside the input attrs: `context_keep` (CR-022, when given); `mask_layer`, `mask_window`, `mask_full_shape` (a masked run, CR-014); `sample_n_px`, `sample_grid_side`, `frames_edge_margin` (a sampled run, so a consumer can unfold the arrays).

| Attr | Type | Meaning |
|---|---|---|
| `ponzi_contract_version` | int | 1 |
| `ponzi_version` | str | `ponzi.__version__` |
| `ponzi_scoring_spec_hash` | str | C4 hash (`ScoringSpec.spec_hash`; `ponzi_config_hash` before CR-070) |
| `ponzi_scoring_spec_name` | str | C4 `name`, else the scoring spec file's stem (`ponzi_config_name` before CR-070) |
| `ponzi_forecaster` | str | `forecaster.name` |
| `ponzi_context_window`, `ponzi_horizon_length` | int | `C`, `H` |
| `ponzi_baseline_days` | list[int] | `scoring.baseline_days` |
| `ponzi_min_support`, `ponzi_min_channels` | int | |
| `ponzi_edge_margin` | int | The margin of the input's process mask (the sidecar's `process_mask` attr, C2, or the sample's `edge_margin`, C3); 0 when it records none |
| `ponzi_struct_weight` | bool | |
| `ponzi_alpha`, `ponzi_change_alpha`, `ponzi_delta`, `ponzi_noise_floor` | float | scoring z, change threshold, difference threshold, detectability floor (`state_machine.noise_floor` resolved: `derived` is the store's `noise_floor(attrs)`, C1) |
| `ponzi_ceiling_floor` | float, absent on older stores | The coherence the ceiling was evaluated at: the estimator's derived floor where the input's attrs give it, else `ponzi_noise_floor` |
| `ponzi_recovery_steps`, `ponzi_nms_window` | int | resolved (`nms_window` never 0 here) |
| `ponzi_window_schema` | int | 1 |
| `ponzi_run_mode` | str | `monitoring` or `detection` |
| `ponzi_t_lo`, `ponzi_t_hi` | int | Scored anchor index range, inclusive |
| `ponzi_t_requested` | list[int] or absent | Requested range before clamping to `[C, T - H]` |
| `ponzi_anchor_date_lo`, `ponzi_anchor_date_hi` | str (ISO date) | Dates of `t_lo`, `t_hi` |
| `ponzi_event_date`, `ponzi_event_end_date`, `ponzi_start_date`, `ponzi_end_date` | str, present only when given | The request's dates |
| `ponzi_sample` | bool | True when written on the folded sample grid (C3 attrs are then also present) |
| `ponzi_replay_of` | str, `replay` stores only | See C8 |

## Invariants

- Outside `[t_lo, t_hi]` every float array is NaN and `n_channels` is 0; a reader distinguishes "not scored" from "no change" only through the attrs.
- Inside the window, `anomaly_score` is NaN wherever `process_pixels == 0`.
- `n_channels <= len(baseline_days) * H`.
- The attrs dict of `score.zarr` equals that of `change.zarr` from the same run (`stores_share_stamp`); a `replay` store is exempt.

## Functions

`ponzi.contracts.score`: `GridMeta` (shape, the three coordinates and the input attrs to copy; each input view of the runner builds it, `sample_grid_meta` for a sample, so this module does not import C1), `PixelScores` (the stage 4 output dataclass, one anchor without the time axis; `ceiling_score` optional, written as NaN when None), `ScoreMeta` (pydantic, parses the stamp and the input attrs), `open_score_store(path) -> ScoreDataset` (validates, exposes `.meta`, `.stamp`, `.window` with `t_lo/t_hi/run_mode` (`mode` is an alias) and `n_anchors`, lazy `.ds`), `create_score_store(path, grid, stamp, process_pixels, chunks=None) -> zarr.Group` (allocates the arrays and consolidates the metadata, returns a writable handle; the sink only writes slices afterwards), `write_score_slice(group, t, PixelScores)`, `validate_score_store(path)` with checks `structure` (fail: arrays, dims, dtypes, fills, `dimension_names`, coordinate lengths), `optional` (info: an optional array absent), `stamp` (fail), `window` (fail: `t_lo <= t_hi <= T - 1`), `consolidated` (warn), `store_attrs(path)`.

`ponzi.contracts.stamp`: `RunStamp` (the `ponzi_*` fields above as a pydantic model with `to_attrs()` (None fields omitted) / `from_attrs()` / `has_stamp()`); `RunWindow.stamp_fields` (`ponzi.core.windows`) fills the window part.
