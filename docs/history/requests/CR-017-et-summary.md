# CR-017: the dating statistic computed in the run

- **Requested by / date:** owner, 2026-10-14
- **Status:** signed off 2026-10-14; implemented on branch `dating-recipe` (not merged)

## Why

The Gaza release dates each per-path flag run by Et, the Welch t break statistic of the channel z around a gap (decision 40). Today that takes three steps outside the library: a run with `save_all_channels` (C21, about 30 GB per burst), then `ops/gaza_release/estat.py run` on the HPC over that store, then the release pipeline. The detection recipe (CR-018) needs E and Et as an ordinary run output, and a run should not have to write 30 GB of channel z to give it.

## What changes

1. **The request.** `RunRequest.summaries: list["et"]`, default empty; flag `--summaries et` (repeated for more names). Recorded in `run_meta.request`. Not part of `config_hash` or the stamp: it selects an extra output and changes no number of the others, like `save_all_channels`. No reason was found to hash it.
2. **The statistic** (`ponzi.core.summary`), EXACTLY `estat.py`'s `e_stat` with j = 4, ported arithmetic for arithmetic: at time index k over the anchors k - 4 .. k, the group S of the (anchor, cell) pairs whose pair spans the gap k (anchor k - d, cells d <= h <= d + b) against the group N of the other cells of those anchors; E the difference of the means, Et the Welch t; NaN when either group has fewer than 5 scored cells. Same cell set (all B x H channel cells, `SPAN` as in `estat.py`), same `_sums` (float32 values, float64 sums), same accumulation order (d = 0 .. 4), float32 result. The z is cast to float16 first, because the release computed E and Et from the float16 C21 store; with that, the streamed values equal `estat.py` on the all-channel store of the same run bit for bit. The cell set is meaningful only when baseline b is b + 1 revisits, so a run whose baselines are not `revisit, 2 revisit, ...` is refused with the summary.
3. **In the loop.** `et` scores every B x H channel as `save_all_channels` does (decision 39: the forecaster gets an all-true overlap, every other output gets the pyramid copy), WITHOUT writing them. After an anchor is scored its z (processed pixels only, float16) goes into a ring of five anchors (`EtSummary`, `5 * pixels * B * H * 2` bytes), and every time index up to that anchor not yet given out is computed and handed to the background writer. After the last anchor the four time indices that follow are given out too. A time index without an anchor contributes nothing, as in the old store, where its z was NaN. The all-channel store is not needed; with `save_all_channels` as well, both are written. Works with the compact loop (the ring holds the loop's processed pixels; the writer scatters), with a mask and its window (CR-014: the store is on the window), and with every forecaster that the all-channel scoring accepts: TiDE, the rolling fits, a prediction store, and an `external` callable that declares `blanks_off_pyramid` (refused without, as for `save_all_channels`).
4. **The store** `summary.zarr` (C24, `ponzi.contracts.summary`, `docs/contracts/summary_store.md`): `E` and `Et`, float16 `(time, y, x)`, `_FillValue` NaN, chunks `(1, Y, X)` (or the request's `chunks`), coordinates, `process_pixels`, input attrs and stamp as C7, plus `summaries`, `summary_t_lo`, `summary_t_hi` (first anchor to last anchor plus 4, cut to the time axis), `et_definition`, `et_j`, `et_min_cells`, `et_baseline_days`, `et_horizons`, `et_input`. Written by `sinks.ZarrSummarySink` through the background writer. float16 because the old store was float16 and its docstring shows it keeps the dating (the Et pick from it equals the float32 pick on all but 2 of 42,793 page runs of t094_200646_iw1, both near ties below 0.005).
5. **Memory.** `estimate_run_memory(..., summary_et=True)` adds a key `summary`: the ring, the E and Et the writer may hold (`(WRITE_QUEUE_DEPTH + 1)` time indices on the loop grid, one scattered to the whole grid under the compact loop) and the temporaries of one block of 65,536 pixels. For t094_200646_iw1 (1,560 x 3,307, 1,844,942 processed pixels, C 30, B = H = 5, K 11, the forecaster's own bytes left out): 7.73 GB without, 8.27 GB with the summary (+0.50 GB, of which 0.46 GB is the ring); `save_all_channels` instead adds 0.58 GB.

## What the old definition says about the first anchors

The request said the first anchors (fewer than five behind) should be NaN "as in the old definition". The old definition does not do that: `estat.py` shifts zeros in for the anchors that do not exist, and at the first anchor of a run S has 15 and N 10 cells (B = H = 5), both at least 5, so E and Et are finite there whenever enough cells are scored. The implementation follows `estat.py` (tested: equal at every time index, the first anchors and the four after the last included); NaN only before the first anchor and wherever a group has fewer than 5 cells. If the owner wants NaN at the first four anchors, that is a change of the definition and of the dating near the start of a record.

## Size per burst

Two float16 grids per written time index. t094_200646_iw1: 151 time indices, 3.1 GB raw; the processed pixels are 36 % of the grid and the rest compresses to almost nothing, so about 1.0 to 1.1 GB on disk. The release's `estat.zarr` held only the release lattice cells (about 0.1 GB per burst); C21 was about 30 GB.

## Do results change?

No. Every existing output of every existing run config is unchanged; the option is new and off by default. With the option the score, change, channel and prediction stores, the statistics file and the counts of `run_meta.json` are those of the run without it (the decision 39 invariant, tested).

## Tests

`tests/test_summary_et.py` (16; one `ml`):

- `estat.py`'s `e_stat` is copied into the test unchanged (B and H read from the array, the one edit, so the three-baseline TiDE test can use it). On a synthetic store with a missing acquisition, for the rolling fit, the pooled rolling fit, a blanking external forecaster and TiDE (the tiny TorchScript model of `test_tide_templated.py`): the streamed E and Et equal `e_stat` on the all-channel store written by the same run, at every pixel and time index, bit for bit in float16.
- The ring alone against `e_stat` on random float16 z with gaps, a missing anchor and pixels that stop being scored: equal bit for bit in float32.
- The first anchor and the four time indices after the last follow the old definition; nothing before the first anchor; the store's written range.
- Score and change stores identical with and without the option (four forecasters); the summary without `save_all_channels` is the same bytes; compact loop against the whole-grid loop; a masked run against the full run at the masked pixels (rolling fit).
- Refusals (baselines, unknown name, an undeclared external callable), the command line flag, the memory term.

## Version

Library: minor (a new opt-in output). Standard: no new major; a standard that uses Et names the option.

## Not in this request

- Other summaries. The store and the request field take a list so that more can be added by name.
- Removing `save_all_channels`: it stays for side analyses.
