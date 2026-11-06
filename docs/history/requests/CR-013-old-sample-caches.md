# CR-013: old sample caches are no longer read

- **Requested by / date:** owner, 2026-10-13
- **Status:** requested 2026-10-13; implemented on branch `cleanup`, awaiting owner review

## Why

`ponzi.core.sample` still opened the pixel caches written by the old `ponzi-ccd` implementation (cache protocol 3): it looked for their margin in a file beside the store, filled in a producer name, and turned two contract failures into warnings for them. The rebuild is proven and the tests that used such a cache left with CR-001, so nothing in this repository, in `ponzi-apps` or in `ponzi-models` reads one any more. The monorepo backup can still read them.

## What changes

In `src/ponzi/core/sample.py` (662 lines before, 624 after):

- Removed: `_is_legacy`, `_frames_meta` and the constant `FRAMES_META`. The `edge_margin` is read from the store's attr only, never from a sibling `frames_meta.json`.
- Removed: the producer default `ponzi-ccd paper/sample.py` and the fallback from `source_store` to the old attr name `source_coh_zarr` in `sample_meta`.
- A repeated `(pix_y, pix_x)` pair always fails the `pixels` check (it was a warning for a protocol 3 cache).
- Missing `sensor`, `contract_version` or `source_digest` attrs fail the `identity` check (they were a warning that named the store a legacy cache). The contract (C3) lists the three as attrs of every sample store, and `extract_sample` has always written them.
- The docstrings and `docs/contracts/pixel_sample.md` no longer describe the old cache.

What stays: everything else in the module (the fold, the reader, the writer, `extract_sample`, the slice source), the `not consolidated` warning (it is not about old caches), and every other thing called legacy in the library: the coherence store readers for both zarr formats (`contracts/coherence.py`, `onboarding/validate.py`, `onboarding/archive.py`, `onboarding/onboard.py`) and the `window` handling of the label reader (`evaluation/labels.py`). None of those files is touched.

Who is affected: a sample store that `extract_sample` or `ponzi onboard` wrote opens as before. A store written by hand through `write_sample_store` without `sensor`, `contract_version`, `source_digest` or `edge_margin` attrs is now refused by `open_sample_store`, as is any store with a repeated pixel.

## Do results change?

No. A store that passed the validation without warnings is read exactly as before, so every run over such a sample gives the same arrays. The change is in which stores are accepted at all.

## Tests

- New in `tests/test_sample.py`: a sample with a repeated pixel fails `pixels`, and a sample without `edge_margin`, `source_digest` or `contract_version` fails `edge_margin` or `identity`; `open_sample_store` raises `ContractError` for each.
- No test was removed: the tests on a real `ponzi-ccd` cache went with CR-001.
- The sampled-run identity (`test_sampled_run_is_bit_identical_to_the_full_run`) and the onboarding sample tests are unchanged and pass.

## Version

Library: minor (stores that opened with warnings are refused; the public constant `FRAMES_META` was never exported in `__all__`). Standard: not affected.
