# C4a: Run request

Status: implemented 2026-09-07, `ponzi.core.runner.RunRequest` (package `packages/core`).

## Purpose

Everything specific to one invocation of `ponzi run`: which store, which scoring spec, where to write, which anchors (mode and dates), and runtime knobs. Stamped into the output stores (through `RunStamp`) and into `run_meta.json`; never part of `scoring_spec_hash`.

## Producer and consumers

Producers: the CLI (`ponzi run` flags, an optional `--args-file` yaml, `PONZI_*` environment variables, C4b); the ponzi-worker `run` stage (`ponzi_worker.stages.run`), which builds one request per burst from its `RunParams` (the fields that change the outputs, part of the stage's content id) and its `RunExec` (`threads`, `chunks`, `max_memory_gb`, no part of it), with `out` the work folder named by the content id; ponzi-models `calibration.null_runs` (one monitoring request per burst and mask layer of a panel). Consumer: `ponzi.core.runner.run`.

## Fields

| Field | Type | Default | Meaning |
|---|---|---|---|
| `coh` | path | required | Coherence store (C1) |
| `sidecar` | path or null | null | Covariates sidecar (C2), merged at open |
| `extra_sidecar` | path or null | null | A store of `(time,)` series (e.g. the Sentinel-1 `s1_pd_vv_db_{d}d`) merged into the input's covariates by calendar day; recorded in `run_meta.input.extra_sidecar` |
| `scoring_spec` | path | required | Scoring spec yaml (C4); `--scoring-spec NAME|FILE` |
| `out` | path | required | Output directory; receives `score.zarr`, `change.zarr`, `run_meta.json` |
| `mode` | `monitoring`, `detection` or null | null | Inferred from the dates when null (`windows.infer_mode`): event dates give detection, anything else monitoring |
| `event_date`, `event_end_date` | ISO date or null | null | Detection: the event's anchors |
| `start_date`, `end_date` | ISO date or null | null | Monitoring: the span, each bound defaulting to the scorable edge |
| `chunks` | `(1, y, x)` or null | null | Chunk shape of the score and change arrays (and of `summary.zarr`); the command line form is `1,256,256`; null = one full slice per anchor |
| `overwrite` | bool | false | Remove an existing `out` first; without it an existing `out` is an error |
| `threads` | int or null | null | Thread count this run asks for. The runner sets `OMP_NUM_THREADS` before a torch forecaster imports its runtime, asks `torch.set_num_threads` and `threadpoolctl` for the pools that are already up, and records what acted in `run_meta.threads`. Null leaves the environment exactly as the caller set it (a batch job's own `OMP_NUM_THREADS`) |
| `max_memory_gb` | float or null | null | Refuse the run when the pre-flight estimate (`runner.estimate_run_memory`) exceeds this; when null, 80 % of the host's available memory is enforced instead. An explicit cap is the caller's responsibility: run under `tools/run_capped.sh` with the same value |
| `forecasting_stats` | bool | false | Also write `forecasting_{scoring_spec_name}.npz` (C10) |
| `pred_tile` | int | 512 | Spatial chunk of the optional stack stores (`pred.zarr`, `channels.zarr`, `channels_z.zarr`), capped at the grid |

CR-014 adds `mask_store` (path or null) and `mask` (layer name or null), both or neither: the run is restricted to one named layer of a mask store (C23) on the grid of `coh`, processes its usual process mask AND the layer, and reads and writes only the bounding window (`run_meta.mask`). Like `threads` they are a selection of the input and no part of `scoring_spec_hash`. Refused with the `stored` forecaster (its prediction store is on the whole grid).

CR-016 adds `strict_covariates` (bool, default false; `--strict-covariates`): by default a run cuts the anchors at the ends of its range whose covariates are incomplete and records them in `run_meta.window.covariate_cut`; with the option it fails instead, naming the anchors, the variables and the dates. For a reanalysis, where every requested anchor has to be scored. It changes no number and is no part of `scoring_spec_hash`.

CR-017 adds `summaries` (list, default empty; `--summaries et`, repeated for more): per-pixel summaries computed while the loop runs, written to `summary.zarr` (C24). `et` is the E and Et break statistics (`ponzi.core.summary`); it scores every B x H channel as `save_all_channels` does, without writing them, needs the baselines `revisit, 2 revisit, ...` and, for an `external` forecaster, its `blanks_off_pyramid` attribute. It changes no other output and is no part of `scoring_spec_hash`. CR-019: `et` writes Et only; `e` adds E and is accepted only next to `et` (`--summaries et,e`, the comma form and the list form alike; a name given twice is refused).

CR-022 adds `context_keep` (int or null, default null; `--context-keep L`, 1 <= L <= C of the scoring spec): at every anchor the forecaster sees only the last L acquisitions of its context; the older C - L are presented exactly as acquisitions missing from the store (NaN coherence for every pair ending on them and for the context pairs reaching back to them, NaN `bperp` there, the `(time,)` covariates unchanged; `ponzi.core.context.ContextKeep`). Everything after the forecaster's input (the `min_support` gate, scoring, aggregation, the state machine) treats it as real missing data. An input condition like the mask: no part of `scoring_spec_hash`; recorded here and in a `context_keep` attr of every output store. Refused with the `stored` forecaster, and `L > C` is refused.

CR-021 adds `staged` (bool, default false; `--staged`): every anchor is also scored at the stages 1 .. H - 1 before its pyramid is full, into `staged.zarr` (C26), and the anchors run on past `T - H` to the request's end (the last acquisition by default), each at the stages it has reached and without a final score. The forecaster declares `future_rows` (`unused`: the rolling fits; `blanked`: TiDE, one forecast per stage with the covariate rows not yet known presented as unknown; an `external` callable as an attribute); the `stored` replay is refused, as is a scoring spec with `H < 2`. Every other output and the stamp (its `t_hi` is the last anchor with a final score) are those of the run without it; no part of `scoring_spec_hash`.

`save_pred` and `save_channels` (bool, default false) ask for the optional C5 and C6 stores. `save_all_channels` (default false) asks for the optional C21 store, the z of all B x H channels; it changes no other output.

## Invariants

- At most one of the date families is given, matching the mode (`windows.infer_mode` and `windows.resolve_run_window` enforce it); none is monitoring over the whole scorable range.
- The request never changes the computation: two requests differing only in `out`, `chunks` or `overwrite` produce identical arrays and an identical `identity_view` of the meta except for the paths recorded under `request`.
- `threads` is the one exception, and only for TiDE with `batching: legacy`: its blocks, worker count and intra-op thread count follow `threads`, so two such runs differ at the last float32 digit of the quantiles and in whatever is derived from them; `run_meta.threads` records it. The rolling fits and TiDE with `batching: canonical`, the default (CR-011), whose batches do not depend on the thread count and whose forward passes each run with one intra-op thread (CR-010), give identical arrays at any thread count.

- `mask_store` and `mask`: at the masked pixels a rolling-fit run holds the bytes of the run without the mask; a TiDE run holds them to the last float32 digit of the quantiles, because a pixel shares its batch with other pixels (CR-014).

- `staged`: score, change, summary and every other store are the bytes of the run without it (CR-021).

- `context_keep`: L = C gives the arrays of the run without it, bit for bit; L < C gives, at every anchor, the forecaster input of a store where those acquisitions are missing, on the bytes (CR-022).

## Functions

`ponzi.core.runner`: `RunRequest`, `run(request) -> RunResult`, `RunResult(out, meta)`, `estimate_run_memory`, `check_memory`, `open_input`. `ponzi.core.cli`: `ponzi run`.
