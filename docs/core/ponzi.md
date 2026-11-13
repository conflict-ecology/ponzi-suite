# ponzi

The method: from a burst's coherence store to calibrated p-values and dated events. It names no dataset and loads neither torch nor the geospatial stack at import, except where a subpackage says so.

| Subpackage | What it does |
| --- | --- |
| `ponzi.core` | the forecast run of one burst: the context buffer, the forecasters (TiDE, the rolling fit, stored and external predictions), scoring, aggregation and the anchor loop |
| `ponzi.calibration` | scores to codes: the p-value of a score against a panel's null, stored as `round(20 * -log10 p)` |
| `ponzi.products` | what is made from finished runs: the detection of events, along one path or on Major TOM cells |
| `ponzi.evaluation` | labels, the rows at labelled pixels and their metrics, for evaluation only |
| `ponzi.contracts` | the schema, opener, writer and checks of every store ([Store formats](../reference/contracts.md)) |
| `ponzi.grid` | putting bursts, paths and outlines on a grid, and the Major TOM grid ([Grids](../method/grids.md)) |
| `ponzi.stac` | the STAC Items of a run's stores, beside the stores |

How the four steps fit together (forecast, score, calibrate, detect) is in [How PONZI works](../method/workflows.md#the-method).

## The `ponzi` command

```
# score one coherence store under a scoring spec
ponzi run ...
# re-threshold a run's score store into a change store
ponzi replay ...
# the forecasting statistics of a run
ponzi forecasting-summary ...
# the p-value store of a finished run
ponzi pvalues RUN_DIR --calibration FILE
# events of one run
ponzi detect RUN_DIR --calibration ID
# events of the bursts of one path
ponzi detect-path RUN_DIR... --calibration ID
# events on every Major TOM cell the bursts reach
ponzi tile RUN_DIR... --calibration ID
# check a store against its contract
ponzi validate-store PATH [--json]
```

`ponzi --help` and each subcommand's `--help` give the options. The arguments of `run`, `replay` and `forecasting-summary` can also come from `--args-file` or `PONZI_<ARGUMENT>` ([Folders and environment variables](../getting-started/paths.md#running)). What `detect`, `detect-path` and `tile` write goes beside the runs they read unless `--out` says else.

Its [API reference](../reference/api/ponzi.md) is generated from its docstrings.
