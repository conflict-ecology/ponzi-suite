# CR-014: a run restricted by a named mask, reading only its window

- **Requested by / date:** owner, 2026-10-13
- **Status:** implemented on branch `mask-window`, not merged; awaiting sign-off

## Why

Calibration and testing of a model should go through exactly the production path. Today a panel (the Major-TOM package) is run through the pixel-sample path of the runner: another input contract (C3), another opener, the fold. The new design defines the panel by MASKS on the full burst stores: a panel run is the production run (`ponzi run` on the full coherence store with the production sidecar, the registered model and its config) restricted by a named mask, `sample` (the pixels already sampled, the fast version) or `cell` (every pixel of the burst inside the cell). Training data is to be read through the same opener, so that training, calibration and production share one input path.

Two conditions shaped the design:

- A production sidecar must stay byte-identical, so the masks live in their own small store beside it, never inside it.
- A cell is a small part of a burst (10 km of about 20 by 85 km), so a restricted run must not read or write the whole grid.

## What changes

1. **The mask store (C23, `ponzi.contracts.masks`, `docs/contracts/mask_store.md`).** A small zarr: `y`, `x` (float64, equal to the coherence store's) and any number of bool `(y, x)` layers. Group attrs: `source_store` (path of the coherence store the masks are for), `source_digest` (its structural digest, empty where the writer could not know it), `layers`, `producer`, `contract_version`, and whatever the writer adds. `write_mask_store(path, y, x, layers, *, source_store, source_digest="", attrs=None, overwrite=False)`, `open_mask_store(path) -> MaskDataset` (`layers`, `layer(name)`, `check_grid(y, x)`), `validate_mask_store(path) -> ValidationReport`. The hard rule is the grid: `y` and `x` must equal the store's, value for value. Another `source_digest` than the store's is a warning, not an error: the grid check already says the masks fit, and an archive store whose attrs changed keeps its pixels.

2. **The request.** `RunRequest.mask_store: Path | None` and `RunRequest.mask: str | None` (the layer name), flags `--mask-store` and `--mask`, both or neither. The pixels a run processes are its usual process mask (the valid footprint, or the sidecar's `process_mask`) AND the layer.

3. **The window.** With a mask the run reads and writes only the BOUNDING WINDOW of those pixels. `runner.WindowedInput` wraps the coherence input: `Y`, `X`, the footprint, the process mask, the static covariates and the coordinates of `grid_meta` are the window's, and every coherence slice is read as `coh[t, y0:y1, x0:x1, baselines]` (`ZarrSliceSource(..., window=)`), never as the whole slice. Everything along time is the store's. The loop gets this view from `open_input` and does not ask whether it is a window; the compact loop of CR-010 works inside the window unchanged. The output stores are on the window's grid, with the window's slice of `y` and `x`, and carry three more group attrs: `mask_layer`, `mask_window` (`[y0, y1, x0, x1]`, rows `y0 <= y < y1`, columns `x0 <= x < x1`) and `mask_full_shape`.

4. **One opener for everything.** `open_input(path, sidecar, extra_sidecar, *, mask_store=None, mask=None)` is public and is the call `run` itself makes. Nothing of the view is private to `run`. What a caller outside the loop (a builder of training windows) reads from it: `window` and `full_shape`; `grid_meta()` (shape, `time`, `y`, `x`); `process_mask()` (the selected pixels, `(Y, X)` bool on the window); `times`, `baseline_days`, `revisit_days`, `baseline_index(days)`; `time_covariates(indices)` (every `(time,)` and `(time, baseline)` variable, the sidecar's and the extra sidecar's included); `covariate(name)` (a static layer on the window); `slice_source(indices)` with `read(t)` and `read_range(t0, t1)`, which return the window's `(Y, X, B)` and `(n, Y, X, B)`; indexing that with `process_mask()` gives the selected pixels in row-major order. No training code is part of this request.

5. **The record.** `run_meta.mask` (`MaskRecord`, null without a mask): `store`, `digest`, `layer`, `window`, `n_layer` (pixels of the layer on the whole grid), `n_pixels` (the pixels processed, equal to `pixels.n_process`). `run_meta.input.Y` and `X` stay the store's own grid; `pixels.n_valid` and `n_process` count the window. `run_meta.request` holds the two new fields.

6. **Not part of the config hash.** The mask is a selection of the input, like `threads`: `config_hash`, the stamp of the stores and the calibration a run may be read with are those of the run without it.

7. **Errors.** A layer that leaves no pixel in the process mask ("leaves no pixel to process", with the two counts); a layer name the store does not have (the names it has are listed); a mask store on another grid; one of the two fields without the other; a mask on a pixel sample; a mask with the `stored` forecaster (a prediction store is on the whole grid).

Without the two fields nothing changes: `open_input` returns the object it returned, `ZarrSliceSource` makes the same reads, and `run_meta.json` gains `mask: null` and the two null fields under `request`.

## What depends on the processed pixels

Checked stage by stage, for a pixel that is processed in both runs:

| Stage | Depends on the other pixels or on the grid extent? |
| --- | --- |
| Process mask | No. The layer is ANDed with the mask on the whole grid, before the window is cut; nothing is eroded at the window's edge. |
| Reading | No. The window read returns the bytes of the whole-slice read at those pixels. |
| Rolling fit (per baseline and pooled) | The row block a pixel is fitted in changes (blocks of 32 rows of the grid the loop sees). The fit of a pixel does not depend on its block: tested on bytes here, with a grid taller than one block, and it is what the pixel sample and the compact loop already rest on. |
| **TiDE** | **Yes, at the last float32 digit of the quantiles.** The batches are consecutive PROCESSED pixels (`canonical`), or blocks formed from the mask and the width (`legacy`), so a pixel shares its forward pass with other pixels, and with another number of them, in the two runs. With one batch for the whole anchor the difference is still there, so the batch SIZE alone is enough. |
| Scoring | No: elementwise per channel. The blocked quantile kernel splits rows by a byte budget; the blocks do not enter the arithmetic. |
| Aggregation | No: per pixel over its channels. |
| State machine | No: per pixel over time (NMS is along time). |
| Channel, prediction and all-channel stores | Per pixel. `support` counts the context of every pixel of the grid the loop sees; at a masked pixel it is the same integer. |
| Forecasting statistics (`forecasting_stats`) | Yes, by design: sums and histograms over the processed pixels, per stratum. A summary, left out of the invariant. |
| `run_meta` counts (`anchors[].n_scored` and so on, `pixels`) | Yes, by design: counts over the processed pixels. |
| Memory estimate and the refusal | Yes: taken on the window, which is the point. No result depends on it. |
| Output chunking | The default chunk is one slice of the window. No value depends on it. |
| Seeds, strata, statistics across pixels | None in the run: no random draw, no normalisation over pixels, no spatial filter. The strata masks are used by the statistics only. |

## Do results change?

No existing run changes: without the two fields every array and every shape is what it was (the results lock `tests/data/runner_golden.npz` passes unchanged).

For a masked run against the run without the mask, at the masked pixels:

- **Rolling fits: identical, bit for bit**, for every variable of the score, change, channel, prediction and all-channel stores (per baseline and pooled, monitoring and detection, compact loop and whole window).
- **TiDE: NOT bit for bit, and not made so.** The quantiles differ by at most the last float32 digit (measured: at most 6e-8, one unit in the last place, in 77 to 1,257 of 66,150 values on the test model). Everything derived from them inherits that digit, multiplied by one over the spacing of the quantiles where a score divides by it. On the HPC with the registered model (2026-10-13, a full store masked to its sample against the sample run): two bursts identical on every score variable, a third different in 60 of 38,766 anomaly scores by at most 5e-7. The integer outputs (channel counts, flags, states, detectability, support) were equal in every case tested; in principle a score one digit from a threshold can flip a flag. The batching is not changed by this request.
- **The pixel sample against the masked run of the same pixels (rolling fit): identical, bit for bit**, every variable of the four stores, and the counts per anchor.

Consequence for calibration: a TiDE null made through the masked route is not byte-equal to one made through the sample route, and a `sample` null is not byte-equal to the same pixels of a `cell` run. The differences are at the last digit of the scores.

## Reading and memory of a windowed run

- At opening: the metadata of the store and the sidecar, the time axis, the `(time,)` and `(time, baseline)` tables, and three whole `(Y, X)` 2-d arrays: `valid_pixels`, the sidecar's `process_mask`, the mask layer (plus `built` and `land` with `forecasting_stats`). No `coh`.
- Priming: `C + H` slices of the window, eight per request (`coh[t0:t1, y0:y1, x0:x1, b0:b1]`).
- Per anchor: one slice of the window.
- zarr fetches and decompresses every chunk the window touches. A store chunked in space reads only those chunks; a store with one chunk per time slice still decompresses the slice, but only the window is kept.
- Memory is `estimate_run_memory` on the window: with the compact loop the buffer and the loop's arrays hold the processed pixels only, the slices as read and the scattered outputs hold the window. With `save_pred` or `save_channels` the loop is not compact (CR-010) and every array of the loop holds the whole window.

## Tests

- `tests/test_mask_store.py` (4): round trip, the grid rule, what the writer refuses, what the validation names.
- `tests/test_mask_window.py`:
  - the invariant for the rolling fits on bytes, 8 cases (default, channel and prediction stores, all channels, statistics, detection, time chunks; pooled twice), on a 40 by 23 grid so that a pixel changes its row block, with a layer that also names unprocessed pixels;
  - the invariant for TiDE (`ml`, the tiny TorchScript model of `test_tide_templated.py`, 4 cases over canonical, one batch and legacy): integers exact, floats on their NaN pattern and within a stated tolerance (2 units in the last place for the quantiles and the median, 4 for differences of two coherences, 1e-4 of the largest magnitude for what divides by the quantile spacing), and an assertion that the quantiles DO differ, so the test cannot quietly become a claim of identity;
  - the pixel sample against the masked run on bytes, with and without the channel and prediction stores;
  - the window is what is read (no read of the whole grid), written (coordinates, attrs, valid stores) and recorded; a run without a mask is the run of before; the view outside a run; the refusals and the digest warning; the command line flags and the unchanged config hash.
- Left out of the invariant by name (`SUMMARIES` in the test): the forecasting statistics file and the counts of `run_meta.json`.
- `tests/test_layering.py` unchanged, no new exception.

## Version

Library: minor (a new opt-in capability; every existing run config and request stays bit-identical). Standard: no new major. A standard that names its panel should name the mask layer and the mask store's digest next to the run config.

## Not in this request

- The writer of a panel's masks (`ponzi-models`, `panels/masks.py`) and the exports of a panel (a pixel dataset, spatial crops).
- Any training code.
- A TiDE batching that would make a pixel's result independent of the other pixels of its batch.
- The readers of a run were not changed: they read the stores' own grid, which for a windowed run is the window. `replay` is tested on one; `ponzi pvalues` and `ponzi.evaluation.rows` were not run on one here.
