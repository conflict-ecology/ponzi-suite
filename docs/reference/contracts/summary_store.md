# C24: Summary store

`ponzi.contracts.summary`, `ponzi.core.summary`. `{out_dir}/summary.zarr`, optional: per-pixel summaries a run computes while its anchor loop runs, so that nothing that needs the z of every channel has to read the all-channel store (C21) afterwards. Two summaries exist: `et`, the break statistic Et that dates a run of flags (the Gaza release's `estat.py`), and `e`, the difference of means E that Et is made from. `et` alone writes Et only; `e` is written only next to `et` (`summaries: [et, e]`; `[e]` alone is refused, as is a name given twice). The detection (C25) reads Et only.

## Producer and consumers

Producer: the runner with `RunRequest.summaries` (`ponzi run --summaries et`, or `--summaries et,e`, or the flag repeated; the worker stage `run`'s `summaries`, which a standard's workflow sets to `[et]`, `ponzi_models.standards.workflow`), through `ponzi.core.summary.EtSummary` and `ponzi.core.sinks.ZarrSummarySink`. Consumers: `ponzi.products` (`detect`, `detect_path`, `tile_path`, C25), which validate the store, require `et` in `summaries` and read `Et` only.

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `Et` | `(time, y, x)` | float16 | NaN | summary `et`: the Welch t statistic of the two groups below |
| `E` | `(time, y, x)` | float16 | NaN | summary `e` only: E(k), the mean z of the spanning cells minus the mean z of the others |

Grid, chunks and attrs as C7. Written time indices: `summary_t_lo` (the first anchor) to `summary_t_hi` (the last anchor plus 4, cut to the time axis); every other slice reads as NaN, as do pixels outside the process mask and pixel-times without a statistic.

## Attrs

Besides those of C7:

| Attr | Meaning |
|---|---|
| `summaries` | the summaries in the store, in the order the request named them: `et`, or `et` and `e` |
| `summary_t_lo`, `summary_t_hi` | the written time indices |
| `et_definition` | the definition below, as a sentence |
| `et_j`, `et_min_cells` | 4 and 5 |
| `et_baseline_days`, `et_horizons` | the cell set: the run's baselines and H |
| `et_input` | what z the statistic is computed from |

## Definition of `E` and `Et`

At time index k, over the anchors k - 4 .. k: the group S holds the (anchor, cell) pairs whose pair spans the gap k, that is at anchor k - d the cells (b, h) with d <= h <= d + b (b and h the 0-based baseline and horizon index; the baselines must be 1, 2, ... revisits, `check_baselines`); the group N holds the other cells of the same anchors. E(k) is the mean z of S minus the mean z of N, Et(k) the Welch t statistic `(mean S - mean N) / sqrt(var S / n S + var N / n N)` with the sample variances; both NaN when either group has fewer than 5 scored cells. z is the drop-positive channel z of every B x H cell, cast to float16 first (as C21 stores it); sums in float64, the result float32, stored float16. A time index without an anchor (before the first, after the last, a skipped one) contributes nothing, so E and Et exist at the first anchor already (one anchor gives 15 and 10 cells at B = H = 5) and at up to four time indices after the last.

This is the Gaza release's `e_stat` (`estat.py`, j = 4), arithmetic for arithmetic: on the all-channel store of the same run the two agree bit for bit (tested).

## Size

One float16 grid per written time index with `et` (`2 * Y * X` bytes raw), two with `et, e`; `anchors + 4` time indices (fewer where the time axis ends). Outside the process mask the chunks are NaN and compress to almost nothing; dense float16 gains about 10 %. For the Gaza release burst t094_200646_iw1 (1,560 x 3,307 pixels, 1,844,942 processed, anchors 30 to 176 of 181 time indices, so 151 written): with `et` 1.6 GB raw, about 0.5 GB on disk; with `et, e` twice that.

## Memory of the run

`estimate_run_memory(..., summary_et=True)` (with `summary_e=True` for `e`) adds `summary`: the float16 z of all B x H cells of the last five anchors on the loop's pixels (`5 * pixels * B * H * 2` bytes: 0.46 GB for the 1.84 million processed pixels of t094_200646_iw1 at B = H = 5), the Et (and with `e` the E) the writer may hold, and the temporaries of one block of 65,536 pixels. For t094_200646_iw1 at C 30 with TiDE (the forecaster's own bytes left out) the term is 0.52 GB with `et` and 0.54 GB with `et, e`.

## Invariants

- The score, change, channel and prediction stores, the statistics and the counts of `run_meta.json` are those of the run without the option (tested for the rolling fits, a blanking external forecaster and TiDE); `scoring_spec_hash` and the stamp are unchanged; `run_meta.request.summaries` records the option.
- The compact loop and the whole-grid loop write the same bytes; a masked run holds the full run's values at its pixels (rolling fit, tested).
- E and Et are always computed together; `e` changes what is written, not a value (the Et of a run with `et` is the bytes of the run with `et, e`, tested).

## Functions

`ponzi.contracts.summary`: `SUMMARY_ARRAYS`, `create_summary_store`, `write_summary_slice`, `validate_summary_store` (the checks of C7; a store without the `summaries` attr raises `ValueError`), `open_summary_store`. The statistic: `ponzi.core.summary`: `EtSummary`, `e_stat_window`, `span_masks`, `check_baselines`.
