# C4a: Run request

`ponzi.core.runner.RunRequest` (package `packages/core`), a C4b settings model. Everything specific to one invocation of `ponzi run`: which store, which scoring spec, where to write, which anchors (mode and dates), the input selections and runtime knobs. Recorded in `run_meta.request` (C9); no field is part of `scoring_spec_hash`.

## Producer and consumers

Producers: the CLI (`ponzi run` flags, an optional `--args-file` yaml, `PONZI_*` environment variables, C4b); the worker stage `run` (`ponzi_worker.stages.run`), which builds one request per burst from its `RunParams` (the fields that change the outputs, part of the stage's content id) and its `RunExec` (`threads`, `chunks`, `max_memory_gb`, `registry`: no part of it), with `out` the work folder named by the content id; `ponzi-models null-runs` (`calibration.null_runs`: one monitoring request per burst and mask layer of a panel). Consumer: `ponzi.core.runner.run`.

## Fields

| Field | Type | Default | Meaning |
|---|---|---|---|
| `coh` | path | required | Coherence store (C1) or pixel sample (C3) |
| `sidecar` | path or null | null | Covariates sidecar (C2), merged at open |
| `extra_sidecar` | path or null | null | A store of `(time,)` series (e.g. the Sentinel-1 `s1_pd_vv_db_{d}d`) merged into the input's covariates by calendar day; recorded in `run_meta.input.extra_sidecar` |
| `mask_store`, `mask` | path, str or null | null | Both or neither: restrict the run to one named layer of a mask store (C23) on the grid of `coh`. The run processes its usual process mask AND the layer and reads and writes only their bounding window (`run_meta.mask`). Refused with the `stored` forecaster and on a pixel sample |
| `scoring_spec` | path | required | Scoring spec (C4); `--scoring-spec NAME|FILE` |
| `out` | path | required | Output directory; receives `score.zarr`, `change.zarr`, `run_meta.json` and the optional stores |
| `mode` | `monitoring`, `detection` or null | null | Inferred from the dates when null (`windows.infer_mode`): event dates give detection, anything else monitoring |
| `event_date`, `event_end_date` | ISO date or null | null | Detection: the event's anchors |
| `start_date`, `end_date` | ISO date or null | null | Monitoring: the span, each bound defaulting to the scorable edge |
| `chunks` | `(1, y, x)` or null | null | Chunk shape of the score, change and summary stores; command line form `1,256,256`; null = one full slice per anchor |
| `overwrite` | bool | false | Remove an existing `out` first; without it an existing `out` is an error |
| `threads` | int or null | null | The thread count this run asks for. The runner sets `OMP_NUM_THREADS` before a torch forecaster imports its runtime, asks `torch.set_num_threads` and `threadpoolctl` for the pools already up, and records what acted in `run_meta.threads`. Null leaves the environment as the caller set it |
| `max_memory_gb` | float or null | null | Refuse the run when the pre-flight estimate (`estimate_run_memory`) exceeds this; when null, 80 % of the host's available memory is enforced instead. An explicit cap is the caller's to enforce: run under ponzi-core `tools/run_capped.sh` with the same value |
| `forecasting_stats` | bool | false | Also write `forecasting_{scoring_spec_name}.npz` (C10) |
| `save_pred`, `save_channels` | bool | false | Also write `pred.zarr` (C5), `channels.zarr` (C6). Either keeps the loop on the whole grid |
| `save_all_channels` | bool | false | Also write `channels_z.zarr` (C21), the z of all B x H channels |
| `summaries` | list of `et`, `e` | `[]` | Per-pixel summaries computed in the loop, into `summary.zarr` (C24). `et` writes Et; `e` adds E and needs `et`; a name given twice is refused. `--summaries et,e` and the repeated flag are both accepted. `et` needs the baselines `revisit, 2 revisit, ...` and, for an `external` forecaster, its `blanks_off_pyramid` attribute |
| `strict_covariates` | bool | false | Fail, naming the anchors, variables and dates, instead of cutting the anchors at the ends of the range whose covariates are incomplete (the cut is recorded in `run_meta.window.covariate_cut`) |
| `context_keep` | int or null | null | `--context-keep L`, 1 <= L <= C: the forecaster sees only the last L acquisitions of its context; the older C - L are presented as acquisitions missing from the store (NaN coherence for every pair ending on them and for the context pairs reaching back to them, NaN `bperp` there, the `(time,)` covariates unchanged; `ponzi.core.context.ContextKeep`). Everything after the forecaster's input treats it as real missing data. Recorded in a `context_keep` attr of every output store. Refused with the `stored` forecaster |
| `staged` | bool | false | Also score every anchor at the stages 1 .. H - 1 into `staged.zarr` (C26), and run the anchors on past `T - H` to the request's end, each at the stages it has reached. Refused with the `stored` forecaster and with `H < 2` |
| `pred_tile` | int | 512 | Spatial chunk of the stacked stores (`pred.zarr`, `channels.zarr`, `channels_z.zarr`), capped at the grid |

## Invariants

- At most one date family is given, matching the mode (`windows.infer_mode`, `windows.resolve_run_window`); none is monitoring over the whole scorable range.
- The request never changes the computation: two requests differing only in `out`, `chunks` or `overwrite` give identical arrays and an identical `identity_view` of the meta except the paths under `request`.
- `threads` changes the arrays only for TiDE with `batching: legacy`: its blocks, worker count and intra-op thread count follow `threads`, so two such runs differ at the last float32 digit of the quantiles and in what is derived from them. The rolling fits and TiDE with `batching: canonical` (the default, whose batches do not depend on the thread count and whose forward passes run with one intra-op thread) give identical arrays at any thread count.
- `mask_store` and `mask`: at the processed pixels a rolling-fit run holds the bytes of the run without the mask; a TiDE run agrees to the last float32 digit of the quantiles, because a pixel shares its batch with other pixels.
- `staged`, `summaries`, `save_all_channels`: every other output is the bytes of the run without the option. `strict_covariates` changes no number.
- `context_keep`: L = C gives the arrays of the run without it, bit for bit; L < C gives, at every anchor, the forecaster input of a store where those acquisitions are missing.

## Functions

`ponzi.core.runner`: `RunRequest`, `run(request) -> RunResult` (`out`, `meta`), `estimate_run_memory`, `check_memory`, `open_input`. `ponzi.core.cli`: `ponzi run`.
