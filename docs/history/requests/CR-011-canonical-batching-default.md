# CR-011: canonical batching is the TiDE default

- **Requested by / date:** owner, 2026-10-13 ("Switch on now")
- **Status:** signed off 2026-10-13; implemented on branch `canonical-default`

## Why

CR-010 item 6 added canonical batching as an opt-in. On the HPC it is faster and its result does not depend on the thread count:

- Full Tehran burst t028_058198_iw3, 65 anchors, 8 threads, one node (job 5773988, yatagarasu04): 19.1 s per anchor against 21.8 s with the legacy batching (21 min 2 s against 24 min 0 s), the same peak memory.
- The same job: the score, change and all-channel stores of the two runs are identical (13.1 billion channel z values, 0 differ).
- Job 5771840: the canonical score store is identical at 1, 4, 8 and 16 threads.

## What changes

1. `TideParams.batching` defaults to `canonical` (was `legacy`). `legacy` stays available by naming it.
2. The dump of the params leaves out the default, as before. So a run config that does not name `batching` keeps the params and the `config_hash` it had before the field existed, and it now runs canonical. A config that names `batching: legacy` has the field in its params and gets another hash.

Why the hash of existing configs is kept rather than changed:

- The hash never fixed the last float32 digit of a legacy TiDE run: the legacy result follows the thread count and the node type, and neither is part of the hash. Two runs with one hash could already differ at that digit. The canonical default narrows that; it does not widen it.
- The registered calibrations and model cards carry the hash of their run config. `ponzi pvalues` refuses a run whose hash differs from the calibration's. A new hash for the default would have made every registered calibration refuse every new run until it was registered again, for a difference that the full-burst check did not find.

What this costs: a run folder made before this change and one made after it carry the same hash, although one used the legacy batches and one the canonical ones. `run_meta.json` records the library version, which tells them apart.

## Do results change?

RESULTS-CHANGING in general, at the last float32 digit of the TiDE quantiles and of whatever is derived from them, for every TiDE run config that does not name `batching`. The unit tests show the difference on a tiny synthetic model with small batches. On the real model it was not found: the full-burst check above gave identical stores. Runs of the rolling fits and of external predictions do not change.

A legacy run is still reproducible: `forecaster.params.batching: legacy` at the thread count of the original run.

## Tests

- `test_config.py`: a TiDE config without the field keeps its frozen hash, reads back as canonical, and `batching: canonical` gives the same hash; `batching: legacy` is in the params and gives another hash.
- The tests that describe the legacy batches (`test_tide_templated.py`, `test_tide_mask.py`) name `batching="legacy"`; the canonical tests of CR-010 are unchanged.
- Fast tier and the `ml` tests green.

## Version

Library: minor (a default changes). Standard: no new major on the evidence above; the next standard should state `batching` in its run config so the choice is on record there.
