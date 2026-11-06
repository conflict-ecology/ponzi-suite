# C10: Forecasting stats

`ponzi.core.forecasting_stats` (package `packages/core`). `{out_dir}/forecasting_{scoring_spec_name}.npz` (the stamp's `ponzi_scoring_spec_name`): the L0 accumulators of one run, per anchor and channel, from which any window's forecasting block (CRPS, RMSE, PIT calibration, exceedance, interval coverage) is reduced afterwards without predictions on disk.

## Producer and consumers

Producer: `ponzi.core.runner` with `RunRequest.forecasting_stats` (`--forecasting-stats`; the worker stage `run` and `ponzi-models null-runs` pass it through), the `ForecastingStats` consumer inside the loop. Consumers: `ponzi.evaluation.forecasting.windowed_calibration`, `ponzi forecasting-summary`, `ponzi.evaluation.metrics.forecasting` (on a `RunHandle` from `ponzi.evaluation.rows.open_run`, which finds the file by `run_meta.scoring_spec.name`).

## Arrays

`T` is the input time axis, `B, H` the run's pyramid, `K = 20` PIT bins, `Z = 3` thresholds. Unwritten anchors are 0 (sums, counts) or NaN (per-anchor statistics).

| Key | Shape | dtype | Meaning |
|---|---|---|---|
| `crps_sum_per_t_uw`, `crps_cnt_per_t_uw` | `(T, B, H)` | float64 | CRPS sum and count of valid channels per anchor |
| `rmse_sum_per_t_uw`, `rmse_cnt_per_t_uw` | `(T, B, H)` | float64 | Squared error against the median, and count |
| `pit_per_t_uw` | `(T, K, B, H)` | float32 | PIT histogram per anchor |
| `ks_per_t_uw`, `cvm_per_t_uw`, `ws_per_t_uw` | `(T, B, H)` | float32 | Per-anchor histogram distance from uniform (Linf, L2 squared, L1) |
| `width_sum_per_t_uw`, `coverage_sum_per_t_uw` | `(T, Z, B, H)` | float64 | One-sided interval width (`z * sum(std)`, normal family; NaN at the written anchors of a quantile family, which has no comparable width) and coverage counts (`(x - mean) / std >= -z`, or for the quantile family `PIT >= ndtr(-z)`) at each z |
| `valid_cnt_per_t`, `exceed_cnt_per_t` | `(T,)`, `(T, Z)` | int64 | Valid aggregate scores and exceedances `anomaly_score > z` |
| `valid_cnt_{s}_per_t`, `exceed_cnt_{s}_per_t`, `crps_sum_{s}_per_t_uw`, `crps_cnt_{s}_per_t_uw`, `rmse_sum_{s}_per_t_uw`, `rmse_cnt_{s}_per_t_uw` | as above | | Per stratum `s`: `built` (`built >= 0.1`) and `landnb` (`land >= 0.5`, not built), inside the process mask; a stratum whose covariate the input lacks is absent |
| `z_thresh_exceed` | `(Z,)` | float32 | The thresholds, `(2, 3, 4)` |
| `overlap` | `(B, H)` | bool | The valid-channel mask |
| `run_t_lo`, `run_t_hi`, `run_mode`, `schema_version` (1), `scoring_spec_hash` | scalars | | Provenance; `read_forecasting_stats` returns them as python `int` and `str` |

Written with `np.savez` (uncompressed), keys in sorted order, no pickled objects.

## Invariants

- Counts are zero outside `[run_t_lo, run_t_hi]`; `crps_cnt == rmse_cnt` per channel.
- `pit_per_t_uw[t, :, b, h]` is the `floor(u K)` histogram of the finite PIT values `u` of channel `(b, h)` at `t` (`ponzi.core.scoring.pit_histogram`), so its sum is their count.
- In a staged run (C26) the tail anchors past `run_t_hi` are not accumulated.

## The windowed reduction

`ponzi.evaluation.forecasting.windowed_calibration(stats, t_start, t_end, valid_channels)` collapses the anchors `[t_start, t_end)` into the forecasting block. CRPS and RMSE are the sums and counts added over the window per channel, divided once, rooted for RMSE, then meaned over the valid channels (so the full range reproduces the burst aggregate); KS, CvM and WS are the nanmean of the per-anchor statistics over the same channels; the coverage is read off the pooled PIT histogram.

The block carries the same reduction per stratum beside the whole-run value: `crps_by_stratum`, `rmse_by_stratum`, `exceedance_by_stratum` and `n_valid_by_stratum`, one entry per stratum the accumulators hold. The strata do NOT partition the grid (a processed pixel that is neither built nor land is in neither), so their counts need not add up to `n_valid_pixeltimesteps`. `ponzi.evaluation.metrics.forecasting` emits them as rows with `stratum` the name beside the `all` rows.

## Functions

`ponzi.core.forecasting_stats`: `ForecastingStats` (`update`, `finalise(t_lo, t_hi, run_mode, scoring_spec_hash) -> dict`), `write_forecasting_stats(path, stats)`, `read_forecasting_stats(path)`. `ponzi.evaluation.forecasting`: the reductions. `ponzi forecasting-summary --stats FILE [--window t_lo,t_hi] [--out PATH]` (C4b): the block of one window (both bounds inclusive, default the recorded run window, valid channels the npz's `overlap`), plus `scoring_spec_hash`, printed and written as JSON to `--out`, else to `FILE` with the suffix `.summary.json`.
