# CR-019: the summary store writes Et only by default

- **Requested by / date:** owner, 2026-10-15
- **Status:** implemented on branch `housekeeping` (not merged)

## Why

Since CR-017 `summaries: [et]` writes both E and Et to `summary.zarr`. The detection recipe (CR-018, `ponzi.products`) reads only Et, and E is kept by nothing else in the library. The store is about 1 GB per Gaza burst, half of it E.

## What changes

1. **The request.** `RunRequest.summaries: list["et" | "e"]`. `et` writes Et only. `e` adds E and is a second token of the same summary, not a summary of its own: `[e]` alone is refused, and so is a name given twice. `--summaries et,e`, `--summaries et --summaries e`, `summaries: [et, e]` and `summaries: ["et,e"]` are the same request. Recorded in `run_meta.request` as before; still no part of `config_hash` or the stamp.
2. **The store** (C24, `docs/contracts/summary_store.md`): the table of `ponzi.contracts.summary` is `et -> Et`, `e -> E`; the store's `summaries` attr is `["et"]` or `["et", "e"]` and its arrays follow it. The arithmetic and the float16 storage are unchanged: `EtSummary` computes E and Et together as before, and the run only leaves E out of what it hands to the writer.
3. **Memory.** `estimate_run_memory(..., summary_et=True, summary_e=False)`: the writer's share of `summary` counts one float16 grid per time index (two with `summary_e`). For t094_200646_iw1 (1,844,942 processed pixels, C 30, B = H = 5, K 11, the forecaster's own bytes left out) the term is 0.52 GB with `et` and 0.54 GB with `et, e`; the ring (0.46 GB) dominates either way.
4. **Products.** `ponzi.products.detect` reads `Et` only (checked: E is read nowhere in `src`), so nothing changes there.

## Size per burst

t094_200646_iw1, 151 written time indices: with `et` 1.6 GB raw and about 0.5 GB on disk (151 x 2 bytes x 1.84 million processed pixels, less about 10 % for compression; the rest of the grid is NaN chunks); with `et, e` 3.1 GB raw and about 1.0 GB on disk, as CR-017 stated.

## Do results change?

No number changes. What a request with `summaries: [et]` writes changes: Et without E. CR-017 is not released yet (it is under Unreleased in the CHANGELOG), so the store format of a released version does not change. A store written before this change with `summaries: ["et"]` holds E as well; it still validates (extra arrays are allowed) and its Et is read as before.

## Tests

`tests/test_summary_et.py`: the runs compared against `estat.py` now ask for `et, e` (E and Et still equal bit for bit, four forecasters and TiDE); `et` alone writes no E and its Et is the bytes of the run with both; the masked run; refusals (`[e]` alone, a name twice); the comma form in the request and on the command line (`--summaries et,e` writes both); the memory term for `et` and for `et, e`.

## Version

Library: minor. Standard: none affected; a standard that uses Et names `et`.
