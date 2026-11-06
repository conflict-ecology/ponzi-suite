# CR-010: run performance, five changes that keep every result bit-identical, a GPU fix, and one opt-in change that does not (item 6)

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off 2026-10-12; implemented on branch `perf`; verified on the HPC (see the section near the end); merged into main 2026-10-13. Item 6 (canonical batching) is RESULTS-CHANGING, opt-in and NOT ADOPTED: the default is the batching of before.

## Why
Measured on a real burst (grid 1541 x 3097, 1,710,186 processed pixels of 4.77 million, C = 30, 5 baselines x 5 horizons, the TiDE TorchScript model on CPU, batch 4096, 8 threads): 45 s per anchor, a peak of 25.5 GB, and fewer than 4 of the 8 cores busy. A reading of the code found five causes, none of them in the science.

## What changes
Five changes, each its own commit so that each can be verified separately on the HPC. The bar for every one: results bit-identical to the code before it, on the same machine with the same thread count. No interface, contract, store format or default changes; `estimate_run_memory` gains three optional arguments and four keys.

| # | Commit | Change | Files |
| --- | --- | --- | --- |
| P1 | 1 | free the previous anchor's arrays before the next anchor is built | `core/runner.py` |
| P4 | 2 | with `save_all_channels`, blank only what something reads afterwards | `core/runner.py`, `core/aggregate.py` |
| P2 | 3 | TiDE windows built batch by batch in one small buffer per worker | `core/forecast/tide.py`, `core/forecast/fm_windows.py` |
| P5 | 4 | a background writer for the store writes of the loop | `core/sinks.py`, `core/runner.py` |
| P3 | 5 | the loop on the processed pixels only, and the memory estimate of the new loop | `core/compact.py` (new), `core/runner.py`, `core/forecast/tide.py` |

### P1: free the previous anchor's arrays
The loop kept the previous anchor's predictive (the quantile grid, 4.9 GiB on the burst above) and its six channel arrays (2.7 GiB) alive until the names were rebound, so two anchors' worth were resident during every forecast. The names (`pred`, `ch`, `px`, `flags`, `flush`) are dropped at the end of the loop body, before the buffer rolls.

Identity: nothing is computed differently. Every consumer was checked for a kept reference: the zarr sinks copy into the store; the statistics keep sums and counts; the state machine copies what its ring needs (`state.copy()`, `score[improved]`, a fresh slice per flush); the in-memory prediction sink keeps a reference on purpose, which keeps the array alive, as it should.

### P4: no blanking pass that nothing reads
With `save_all_channels` every anchor set the off-pyramid cells of the quantile grid and of the six channel arrays to NaN.
- (a) The predictive is blanked only when a prediction sink or the statistics are on.
- (b) The channel arrays are blanked only when the channel sink or the statistics are on. The aggregation takes the pyramid mask instead (`aggregate(..., channels=mask)`).

Identity of (b): `aggregate` reads a channel only through `valid = isfinite(z)`. Every reduction is over `where(valid, w, 0)` and `w * where(valid, x, 0)`. With the mask, `valid & mask` on the all-channel scores is the same bool array as `valid` on the blanked scores (blanked z is finite exactly where the unblanked z is finite and the channel is on the pyramid), and the operands of the valid channels are the same values, so every sum has the same operands in the same order. A run without the option passes no mask and takes the code path of before.

### P2: fused, templated window building in the TiDE adapter
Each worker job gathered its pixels, allocated the windows of its whole block (`x_past`, about 832 MB per job on the burst above, and `x_future`) and filled them one covariate column at a time over the whole array. Three quarters of those bytes are the same for every pixel of the anchor. Now: one `(batch, C, B + F)` and `(batch, H, F)` buffer pair per worker, kept between anchors; per anchor the pixel-invariant part (the burst-wide covariate columns of the past, the whole future) is written into them once (`fm_windows.SingleAnchorTemplate`); per batch only the targets and the obs indicators are rewritten, the module is called, the quantiles are sorted in place and written straight into the output. The thread pool takes batches instead of whole blocks, which balances the workers.

Identity: a pixel's last float digit depends on which pixels share its forward pass and on the intra-op thread count, so these are untouched: the blocks (`TideForecaster.plan`, the old job list, its sizes fixed by a test), the batches inside each block (`params.batch` from the block's start), the worker count and the torch thread count (both still follow the number of blocks, not of batches). The inputs of every forward pass are, bit for bit, the windows `assemble_single_anchor` builds (same values through the same float32 casts, only the order of the writes differs; tested on bytes). The sort is the same sort done in place. `assemble_single_anchor` stays as the reference.

`support` was to be taken from the per-batch finite masks only if exactly equivalent. It is not: the masks cover the processed pixels only (`support` counts every pixel of the grid, and the prediction store records it) and they count a zero coherence as missing. It is left as it was, the finite count of the whole context, but counted block of rows by block of rows, which is exact for integers and avoids a bool copy of the whole context.

### P5: a background writer
The store writes of one anchor (score, change, the event slice, and the channel z, prediction and channel stores where on) are one job of `sinks.BackgroundWriter`: one thread, a bounded queue (one anchor waiting, one being written, then the loop blocks), first in first out. An exception in a write is raised in the main thread at the next hand-over or at the end. The writer is closed (everything written, the thread joined) before the sinks are closed and before `run_meta.json` is written, and on any failure of the loop.

Identity: one thread in submission order gives every store the sequence of writes it had, also for chunks that span several anchors. Nothing changes an array after it is handed over: each anchor builds fresh arrays, and the one in-place change (the pyramid blanking of the channel arrays, P4) is preceded by a drain and a direct write of the channel z. Interaction with P1: a job holds its arrays until it is written and drops them then. By default that is only the pixel scores and flags. With a prediction or channel store the job holds the predictive or the channel arrays, so the loop waits for it before the next forecast; those two options gain nothing from the writer and keep the memory they had.

### P3: the loop on the processed pixels only
Every array of the loop spanned the whole grid although only the process-mask pixels are computed (36 % on the burst above). `core/compact.py` gathers the processed pixels, in row-major order, into rows of the true width `X` with a padded tail (`Compaction`, the fold of `core/sample.py` applied to the process mask). The context buffer reads through `CompactSource` (the full slice is read, gathered and released), the forecaster, scorer, aggregation, statistics and state machine run on the pseudo-grid unchanged, and the outputs are scattered back to `(Y, X)` on the writer's thread. The science modules are not changed.

Identity:
- TiDE forms its blocks from the mask and the width. The pseudo-grid has the true width, the same pixels in the same order, and always at least one padding cell (so its mask is never all true and the row-block path is never taken by accident): blocks and batches are those of the whole grid.
- Scoring, aggregation and the state machine work per channel or per pixel; the statistics gather the valid pixels of a channel in row-major order, which the compaction keeps, so every sum has the same terms in the same order.
- Outside the mask a whole-grid run holds NaN scores and zero counts and flags, which is what the scatter fills.
- The rolling fit forms row blocks of the grid, so a pixel sits in another block than before. That its result does not depend on the block is the property the pixel sample already rests on (contract C3, `test_sample.py`); it is tested here again, on bytes, for the per-baseline and the pooled fit. This is the one place where identity rests on a numerical library treating every pixel of a batch alike, see the HPC checks.

The loop stays on the whole grid, as before, when: the mask leaves nothing out, or is empty; the input is a pixel sample; `save_pred` or `save_channels` is on (a forecaster may forecast pixels outside the mask, the rolling fit does, and counts their support; those stores record it); the forecaster is not known to be pixelwise (`stored` is not; an `external` callable declares it with a true `pixelwise` attribute). `runner.COMPACT = False` switches the compact loop off; the tests use it as the reference.

`estimate_run_memory` now describes this loop: `loop_pixels` (the pseudo-grid; buffer, channel arrays, predictive, transients and state scale with it, the input slices as read and the scattered outputs stay on the whole grid), `forecaster_bytes` (the TiDE adapter's buffers and forward passes, `TideForecaster.working_bytes`, which replaces the rolling fit's `block`), `all_channels` (was added to the total in `run`), and a `writer` term. `transient` is two grids instead of six for the blocked quantile scorer, which builds no whole-grid temporary. For the burst above: 7.63 GiB (8.2 GB), 8.23 GiB with `save_all_channels`; the code before returned 17.79 GiB against a measured 25.5 GB. Checked against a measured peak on a synthetic burst only (500 x 800, 36 % processed: 0.83 GiB measured against 1.56 estimated for TiDE, 0.50 against 0.80 for the rolling fit).

## Added after the five commits

### GPU inference fix (commit 6, no result on the CPU changes)
With `device: cuda` in the TiDE params the run failed in the first forward pass ("Expected all tensors to be on the same device ... cpu and cuda:0 ... wrapper_CUDA_addmm"): `load_artifact` loaded the TorchScript module onto the CPU and the adapter sent only the batch tensors to the device. `main` has the same defect (its `load_artifact` has the same `map_location="cpu"` and its `predict` the same `.to(self.params.device)` on the inputs only), so the `device` parameter has never worked for anything but `cpu`.

Now: `load_artifact(ts_dir, device)` loads the module onto the device (`TideForecaster.setup` passes `params.device`); off the CPU each batch is copied from its host buffer to the device (`.to(device, non_blocking=True)`; the buffers stay plain host memory) and the output is brought back with `.cpu()` before it is sorted and written; and there is ONE worker thread whatever `workers` or `PONZI_TIDE_WORKERS` say, because several Python threads feeding one GPU gain nothing and are not known to be safe. With one worker the blocks of `plan` do not depend on the thread count there. `working_bytes` counts one worker off the CPU.

Identity on the CPU: the job, batch, worker and thread logic is untouched; the two `.to("cpu")` calls on tensors that were already on the CPU, which returned the same tensors, are no longer made. The existing `ml` tests and the local harness against `main` (12 runs, 3,242 files) are byte for byte the same.

Not tested: CUDA itself (no GPU where this was written). What is tested is the off-CPU branch forced with the device left at `cpu` (one worker, the copy to the device and back, bytes of one CPU worker), and a test that runs only where `torch.cuda.is_available()` (module on the device, quantiles within 1e-5 of the CPU's). A GPU result is not expected to equal a CPU result to the last float32 digit. A TorchScript module that was traced with a CPU device written into its graph cannot be moved by loading it; that would show as the same error and is a matter of the export.

### Item 6: canonical batching for TiDE on the CPU (commit 7). RESULTS-CHANGING, opt-in, not adopted
**This item changes results, at the last float32 digit of the quantiles and in whatever is derived from them. It is off by default. Nothing above depends on it, and the bit-identity of P1 to P5 is stated for the default.**

What the default (`batching: legacy`) does: workers = min(4, threads // 2), torch intra-op threads = threads // workers, and the size of the blocks of `plan` depends on the worker count. A pixel's batch, and the thread count of its forward pass, therefore depend on `threads`, so a result is reproducible only at the same thread count; and at 16 threads only 4 workers exist.

New, selected by `forecaster.params.batching: canonical`:
1. The batches are a pure function of the pixel order and the batch size: `params.batch` consecutive processed pixels over the whole anchor, the last one short (`TideForecaster.batches`). No blocks, no `row_block`, no worker count.
2. On the CPU the workers are the requested threads (the torch thread count that `runner.apply_threads` sets from `threads`; at least 1, at most the number of batches; `workers` and `PONZI_TIDE_WORKERS` still override). Every forward pass runs with ONE intra-op thread: `torch.set_num_threads(1)` for the time of `predict`, in the main thread and in every worker (an OpenMP thread count belongs to the calling thread), put back before `predict` returns. The setting is process-wide; nothing else in a run uses torch while an anchor is forecast (the scoring is numpy, the background writer writes stores). The batches go to the workers one by one through the pool's queue, so no worker waits while batches are left.
3. The quantiles are then the same bytes for any `threads` at a given batch size. They still depend on the batch size.
4. The default `batch` stays 4,096. Measured on the HPC on this branch at 8 threads with the legacy workers: 19.9 s per anchor at 256, 17.6 at 1,024, 18.0 at 4,096, 18.4 at 16,384, so the batch size hardly matters.
5. Off the CPU (the GPU fix above) there is one worker and the torch thread count is left alone; `canonical` only changes the batches there.

The switch and the config hash: `TideParams.batching` is `"legacy"` (default) or `"canonical"`. `config_hash` is taken on the dump of the resolved params, so a new field with a default would have changed the hash of every existing TiDE config. `TideParams` therefore leaves `batching` out of its dump when it is `legacy`: an existing config has the params and the hash it had, whether it names `batching: legacy` or not. `canonical` is in the dump and gives another hash, as a results-changing setting must. Pinned by a test: the hash of `configs/run/exp_b5h5_base.yaml` (already pinned) and of two TiDE configs, the numbers taken before the field existed.

Memory: `TideForecaster.working_bytes` counts one buffer pair and one forward pass per worker, and the canonical worker count is the thread count, so the adapter's term grows with `threads` (at C 30, batch 4,096: about 94 MB per worker, 1.5 GB at 16 threads against 0.37 GB for the 4 legacy workers). `estimate_run_memory` takes it through `forecaster_bytes` as before.

`RunRequest`'s docstring said that runs differing only in `threads` give identical arrays. That was never true for TiDE. It now says when it holds (the rolling fits; TiDE with canonical batching) and when it does not (TiDE with legacy batching).

No speed is claimed: the scheme is written to use all cores, but it has not been timed on the HPC, and local timings are not representative.

## Left out
- `support` from the batch masks (P2): not equivalent, see above.
- The compact loop with `save_pred` or `save_channels`, and for `stored` and undeclared `external` forecasters (P3): they run on the whole grid as before.
- Reading only the chunks that hold processed pixels: the full slice is still read and decompressed.
- No tuning of block sizes, batch size, worker or thread counts: by default all are as they were (item 6 is opt-in).
- Adopting item 6 as the default: an owner decision after the HPC check; it would change the hash and the last digit of every TiDE run.

## Do results change?
By default, no. Every output store, the statistics file and `run_meta.json` (apart from its timings) are the same byte for byte, and every existing config keeps its hash.

With `batching: canonical` (item 6), YES: the TiDE quantiles change at the last float32 digit against the legacy batching, and the scores and everything derived from them can follow. Such a run has another config hash. No golden file was regenerated.

## Tests
The existing suite stays green after every commit, with no golden file regenerated; the fixtures' no-data column makes almost every runner test, the whole-run lock included, go through the compact loop. New, all on synthetic data:
- P1: the predictive and channel arrays of anchor t are gone when anchor t + 1 is forecast (weak references), also with a prediction and channel store.
- P4: `aggregate` with a mask against `aggregate` of blanked arrays (bytes); the option alone against a run without it; `_to_pyramid` with each pass left out.
- P2: the template against `assemble_single_anchor` (bytes; default environment). Marked `ml`, self-contained (`tests/test_tide_templated.py`, a TorchScript model built in the test): the new path against the adapter of before written out plainly, bytes equal, with a process mask, NaN gaps, several blocks, short last batches, pooled workers and buffer reuse over two anchors; the block sizes of `plan` as numbers.
- P5: the writer by itself (order, one thread, the bound, errors, no reference kept); a failing write fails the run; no thread outlives a run.
- P3: `Compaction` and `CompactSource`; the compact loop against the whole-grid loop, every file of the output compared as bytes, for the per-baseline rolling fit with the default outputs, all channels, statistics, both, detection mode and time-spanning chunks, and for the pooled fit and a quantile forecaster with a subset of those; what keeps the loop on the whole grid; the estimate. Marked `ml`: the adapter on the pseudo-grid against the adapter on the whole grid (bytes).

- GPU fix: marked `ml`, the off-CPU branch on the CPU against one CPU worker (bytes); `load_artifact` with a device; CUDA against the CPU where a GPU exists (skipped elsewhere).
- Item 6: marked `ml`, the quantiles of canonical batching as bytes for 1, 2, 3 and 8 threads, with a process mask and NaN gaps and with every pixel processed, on the whole grid and on the pseudo-grid of the compact loop, equal to a plain single-thread loop over the processed pixels; every forward pass seen with one intra-op thread and the thread count put back; the batches as numbers; the worker count and `working_bytes`. Default environment (`tests/test_config.py`): the TiDE config hashes of before, with and without `batching: legacy`, and another hash for `canonical`.

Run the `ml` tests where torch is installed: `pytest tests/test_tide_templated.py -m ml`.

## To check on the HPC
1. Each commit against the one before on one real burst: stores byte for byte, same node type, same thread count.
2. P2 and P3 with the real model: the identity rests on the forward pass giving the same bytes for the same batch whatever buffer it is read from. Locally (the C 30 covariate model, 30,000 synthetic pixels, six thread and batch settings) it does.
3. P3 with the rolling fit: the identity rests on the fit not depending on a pixel's place in its row block (BLAS behind `einsum`); true locally and already assumed by the pixel sample.
4. Peak memory against the new estimate, since the estimate is a refusal threshold.
5. GPU fix: one burst with `forecaster.params.device: cuda` on a GPU node (it must run; one worker; compare with the CPU run of the same burst as numbers, not bytes), and `pytest tests/test_tide_templated.py -m ml` on that node so the CUDA test is not skipped. The `device` value is part of the config hash, so a `cuda` run has another hash than the `cpu` run.

6. Item 6, thread independence with the real model: one burst with `forecaster.params.batching: canonical` (`batch: 4096`, `device: cpu`) at `threads` 4, 8 and 16; the stores must be the same byte for byte across the three. This rests on a forward pass with one intra-op thread giving the same bytes for the same batch whichever worker's buffer it is read from (the property P2 already needs) and on the worker threads really running with one intra-op thread on that build of torch. Locally (the synthetic harness, three run variants at 1, 2, 3 and 8 threads) every file is the same.
7. Item 6, cost and size of the change: seconds per anchor and peak memory at 8 and 16 threads against the legacy run of the same burst, and the size of the differences against it (expected at the last float32 digit of the quantiles; the count of pixels whose state or flag differs is the number the owner needs for adoption).

## Checked on the HPC (2026-10-12 and 13)

All on the Tehran burst t028_058198_iw3 (1.71 million processed pixels), 8 threads, all-channel store on. Job files in `ponzi-apps/hpc/`.

- P1 to P5, commit by commit, against a reference run of main on the same node: every store identical.
- Per anchor on yatagarasu: main 48.3 s, 23.6 GB peak, 3.7 cores busy; after P1 to P5 about 18 to 22 s, 6.0 GB, 6.1 cores.
- Full burst (65 anchors) on hina01: 15 min 51 s against 49 min 25 s on main; peak 6.3 GB against 25.5 GB; score store identical.
- Threads after P1 to P5, seconds per anchor: 1: 79.3, 2: 49.7, 4: 27.1, 8: 18.0, 16: 16.9. Batch size 256 to 16,384: 17.6 to 19.9.
- GPU fix (job 5771761, aerosmith, A100): the run works; 8.4 to 9.6 s per anchor against 6.5 s on the CPUs of the same node. Off the CPU one worker fills the windows and handles the output, which outweighs the faster forward pass.
- Item 6, thread independence (job 5771840, yatagarasu04, 3 anchors): the score store is identical at 1, 4, 8 and 16 threads; 78.4, 23.8, 15.1 and 14.0 s per anchor.
- Item 6 against legacy over the full burst (job 5773988, yatagarasu04, both at 8 threads): the score, change and all-channel stores are IDENTICAL (13.1 billion channel z values, 0 differ). 19.1 against 21.8 s per anchor (21 min 2 s against 24 min 0 s), peak 6.4 against 6.3 GB. So on this burst, node and thread count the canonical batches give the bytes of the legacy ones; the request still treats item 6 as results-changing in general, because legacy depends on the thread count and canonical does not.
- Inside the forecast stage under item 6 (job 5774018, hina01, 13.2 s per anchor of which 9.1 s forecast): forward pass 63 % of the worker time, filling the windows 18 %, output copy, sort and idle 20 %; 0.3 s per anchor is serial.

## Version
Library: patch.
