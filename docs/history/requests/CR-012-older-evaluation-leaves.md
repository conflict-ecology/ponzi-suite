# CR-012: the older evaluation leaves the library

- **Requested by / date:** owner, 2026-10-13
- **Status:** requested 2026-10-13; implemented on branch `cleanup`, awaiting owner review

## Why

The library carried two evaluations. The newer one is the row-set primitive of decision 29 (labels, rows at labelled pixels, metrics, events, the L0 reductions), and it is the one every current analysis uses. The older one (bag reduction into L1 detection and L2 monitoring results, the long metrics table and the AOI aggregation on it) was used only by itself, by the `ponzi eval` command and by its own tests: nothing else in this repository, in `ponzi-apps` or in `ponzi-models` imports it. The library should hold only code that is still needed, and the monorepo backup keeps all of it.

## What changes

Removed (1,305 lines of modules, 151 more in the files that used them):

| File | Lines | What it was |
| --- | --- | --- |
| `evaluation/bags.py` | 232 | `bag_reduce`, `BagScores`, `threshold_suffix`, `CONFIG_SUFFIX` |
| `evaluation/detection.py` | 325 | `evaluate_detection`, `DetectionResult`, `read_stamp` and the L1 helpers |
| `evaluation/monitoring.py` | 379 | `evaluate_monitoring`, `MonitoringResult` and the L2 helpers |
| `evaluation/results.py` | 190 | `MetricsSchema`, `COLUMNS`, `to_long`, `write_metrics`, `read_metrics` (contract C12) |
| `evaluation/aggregate.py` | 179 | `to_aoi`, `across_aois`, `paired_deltas`, `paired_matrix`, `AOI_COLUMNS`, `KEY`, `EMPTY` |
| `core/cli.py`, in part | 115 | the `ponzi eval` subcommand: `EvalArgs`, `_run_eval`, `_change_suffix` |
| `evaluation/__init__.py`, in part | 36 | the exports of the above and the `try: ... except ImportError` blocks around them |

`ponzi.evaluation` no longer exports `BagScores`, `bag_reduce`, `DetectionResult`, `evaluate_detection`, `MonitoringResult`, `evaluate_monitoring`, `to_long`, `write_metrics`, `read_metrics`, `to_aoi`, `across_aois`, `paired_deltas`, `paired_matrix`. The command `ponzi eval` is gone; `ponzi run`, `ponzi replay` and `ponzi forecasting-summary` are unchanged.

What stays, untouched: `evaluation/labels.py` (with `bag_table` and `BagTable`), `rows.py`, `metrics.py`, `events.py`, `forecasting.py` and `contracts/row_set.py`.

The layering exception of `core/cli.py` to `evaluation` stays, because `ponzi forecasting-summary` still imports `ponzi.evaluation.forecasting.windowed_calibration` inside its command function. Its comment in `tests/test_layering.py` now says so.

Contract documents: `docs/contracts/eval_result.md` (C12) and `docs/contracts/aoi_results.md` (C16) are kept with a note that the code they describe stays in the monorepo, as CR-008 did for the request contracts.

## Do results change?

No. No kept module imported any of the removed ones, so no number that the run, the row sets or the metrics produce can move. What disappears is a command and the files it wrote (`eval_<mode>_<config>.json`, `metrics.parquet`, `eval_meta.json`).

## Tests

- Removed, because they test removed code only: `tests/test_evaluation.py` (the bag reduction, the two level evaluations, the long table, `ponzi eval`), `tests/test_aggregate_metrics.py` and its reference files `tests/data/paired_golden/`. 15 tests.
- `tests/test_cli.py`: the bad-choice test now uses `ponzi run --mode sideways` (it used `ponzi eval --mode sideways`).
- The suite with the `ml` tests: 457 passed, 1 skipped (no CUDA device), was 472 and 1.

## Version

Library: minor (public names and a command disappear; no run config changes). Standard: not affected.
